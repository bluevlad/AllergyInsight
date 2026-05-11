"""통합 경쟁사 뉴스 검색 서비스 (Registry 기반).

Naver News API + Google News RSS 를 ``app.core.sources`` registry 를 통해
통합 검색하고, DB 에 저장/관리합니다.

Step 1.E 리팩토링:
- 2 hardcoded service instantiation → ``registry.all_of_kind(SourceKind.NEWS)``
- ``sources=["naver","google"]`` 단축 별칭은 backward-compat 으로 유지
  (실제로는 registry 키 ``naver_news`` / ``google_news_rss`` 매핑)

미결 O1 결정: ``relevance_score`` 는 Service 계층 (post-fetch AI 분석) 에서 처리.
Connector 는 raw news 만 반환.
"""
from __future__ import annotations

import logging
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from typing import Optional

from sqlalchemy.orm import Session

from ..core.sources import registry
from ..core.sources.base import SourceKind
from ..core.sources.news.base import (
    NewsSourceConnector,
    normalized_to_news_article,
)
# Auto-register news connectors on import
from ..core.sources.news import (  # noqa: F401
    naver_news as _naver_module,
    google_news_rss as _google_module,
)

from ..models.competitor_news import (
    NewsArticle,
    NewsSearchResult,
    DEFAULT_COMPETITORS,
)
from ..database.competitor_models import CompetitorCompany, CompetitorNews

logger = logging.getLogger(__name__)


# 호출자가 쓰는 단축 이름 ↔ registry 키 매핑 (backward compat)
_SOURCE_ALIAS: dict[str, str] = {
    "naver": "naver_news",
    "google": "google_news_rss",
}


@dataclass
class CompanyNewsResult:
    """업체별 뉴스 검색 결과.

    Step 1.E 에서 ``errors`` 필드 추가 (default 빈 dict, backward-compat).
    """
    company_code: str
    company_name: str
    naver_articles: list[NewsArticle]
    google_articles: list[NewsArticle]
    total_count: int
    search_time_ms: float
    errors: dict[str, str] = field(default_factory=dict)


class CompetitorNewsService:
    """통합 경쟁사 뉴스 검색 서비스 (registry 기반).

    Step 1.E 리팩토링: ``naver_client_id``/``naver_client_secret`` 생성자 인자는
    backward-compat 으로 유지되지만, 실제 호출은 ``NaverNewsConnector`` 가
    환경변수 (``NAVER_CLIENT_ID``/``NAVER_CLIENT_SECRET``) 를 통해 처리한다.
    명시적으로 전달된 인자는 환경변수가 없을 때 fallback 으로 사용.
    """

    def __init__(
        self,
        naver_client_id: Optional[str] = None,
        naver_client_secret: Optional[str] = None,
    ):
        # 생성자 인자로 들어오면 env override (legacy 호출자 호환)
        import os
        if naver_client_id:
            os.environ.setdefault("NAVER_CLIENT_ID", naver_client_id)
        if naver_client_secret:
            os.environ.setdefault("NAVER_CLIENT_SECRET", naver_client_secret)

        # Registry-based connectors
        self._connectors: dict[str, NewsSourceConnector] = {
            c.name: c for c in registry.all_of_kind(SourceKind.NEWS)
        }
        self._executor = ThreadPoolExecutor(max_workers=4)

    # ───────── helpers ─────────

    def _resolve_sources(
        self, sources: Optional[list[str]]
    ) -> list[NewsSourceConnector]:
        """단축 별칭 / registry 키 둘 다 수용 + is_available 필터링."""
        if sources is None:
            wanted = set(self._connectors.keys())
        else:
            wanted = set()
            for s in sources:
                wanted.add(_SOURCE_ALIAS.get(s, s))

        result: list[NewsSourceConnector] = []
        for name, conn in self._connectors.items():
            if name not in wanted:
                continue
            try:
                if not conn.is_available():
                    logger.debug("%s connector unavailable — skipped", name)
                    continue
            except Exception as e:
                logger.warning("%s.is_available() 예외 (skip): %s", name, e)
                continue
            result.append(conn)
        return result

    @staticmethod
    def _connector_to_legacy_alias(name: str) -> str:
        """connector registry name → CompanyNewsResult 의 naver/google 분류 키."""
        inv = {v: k for k, v in _SOURCE_ALIAS.items()}
        return inv.get(name, name)

    def _get_company_keywords(
        self, company_code: str, db: Optional[Session] = None
    ) -> list[str]:
        """업체 검색 키워드 조회 (DB 우선, 없으면 DEFAULT_COMPETITORS)."""
        if db:
            company = (
                db.query(CompetitorCompany)
                .filter(
                    CompetitorCompany.code == company_code,
                    CompetitorCompany.is_active == True,
                )
                .first()
            )
            if company and company.keywords:
                return company.keywords

        competitor = DEFAULT_COMPETITORS.get(company_code)
        if competitor:
            return competitor["keywords"]
        return []

    # ───────── 검색 ─────────

    def search_company_news(
        self,
        company_code: str,
        max_results: int = 20,
        sources: Optional[list[str]] = None,
        db: Optional[Session] = None,
    ) -> CompanyNewsResult:
        """특정 업체 뉴스 검색.

        Args:
            company_code: 업체 코드
            max_results: 소스당 키워드별 최대 결과 수
            sources: 검색 소스 단축 이름 (e.g. ["naver","google"]) 또는
                registry 키 (e.g. ["naver_news","google_news_rss"])
            db: DB 세션 (키워드 조회용)
        """
        start_time = time.time()

        keywords = self._get_company_keywords(company_code, db)
        if not keywords:
            return CompanyNewsResult(
                company_code=company_code,
                company_name=company_code,
                naver_articles=[],
                google_articles=[],
                total_count=0,
                search_time_ms=0.0,
            )

        competitor = DEFAULT_COMPETITORS.get(company_code, {})
        company_name = competitor.get("name_kr", company_code)

        selected = self._resolve_sources(sources)

        # 키워드 × 소스 fan-out
        futures = []
        for keyword in keywords:
            for conn in selected:
                futures.append(
                    (
                        conn.name,
                        keyword,
                        self._executor.submit(
                            conn.search, keyword, max_results
                        ),
                    )
                )

        articles_by_alias: dict[str, list[NewsArticle]] = {
            "naver": [],
            "google": [],
        }
        errors: dict[str, str] = {}
        seen_urls: set[str] = set()

        for conn_name, keyword, future in futures:
            alias = self._connector_to_legacy_alias(conn_name)
            try:
                result = future.result(timeout=15)
            except Exception as e:
                logger.warning(
                    "뉴스 검색 실패 (%s/%s): %s", conn_name, keyword, e
                )
                errors[f"{conn_name}:{keyword}"] = f"{type(e).__name__}: {e}"
                continue

            if result.has_error:
                errors[f"{conn_name}:{keyword}"] = result.meta.get("error", "")

            for doc in result.docs:
                # URL 기반 중복 제거
                if doc.url in seen_urls:
                    continue
                seen_urls.add(doc.url)

                article = normalized_to_news_article(doc)
                # 호출 측 컨텍스트 (회사 코드, 검색 키워드) 주입
                article.company = company_code
                article.search_keyword = keyword
                # legacy NewsArticle.source 가 "naver"/"google" 별칭이어야 함
                # (기존 to_dict() 및 DB 저장 호환)
                article.source = alias

                if alias in articles_by_alias:
                    articles_by_alias[alias].append(article)
                else:
                    # 새로운 news source 추가 시 (e.g. third connector) 무손실 처리
                    articles_by_alias.setdefault(alias, []).append(article)

        return CompanyNewsResult(
            company_code=company_code,
            company_name=company_name,
            naver_articles=articles_by_alias.get("naver", []),
            google_articles=articles_by_alias.get("google", []),
            total_count=sum(len(v) for v in articles_by_alias.values()),
            search_time_ms=(time.time() - start_time) * 1000,
            errors=errors,
        )

    def search_all_companies(
        self,
        max_results_per_company: int = 10,
        sources: Optional[list[str]] = None,
        db: Optional[Session] = None,
    ) -> list[CompanyNewsResult]:
        """전체 업체 뉴스 일괄 검색."""
        company_codes = list(DEFAULT_COMPETITORS.keys())
        if db:
            active_companies = (
                db.query(CompetitorCompany)
                .filter(CompetitorCompany.is_active == True)
                .all()
            )
            if active_companies:
                company_codes = [c.code for c in active_companies]

        results = []
        for code in company_codes:
            result = self.search_company_news(
                code, max_results_per_company, sources, db
            )
            results.append(result)
        return results

    # ───────── 수집 & 저장 ─────────

    def collect_and_save(
        self,
        db: Session,
        company_code: Optional[str] = None,
        max_results_per_company: int = 10,
    ) -> dict:
        """뉴스 수집 후 DB 저장 (중복 URL 제거)."""
        self._ensure_companies(db)

        if company_code:
            results = [
                self.search_company_news(
                    company_code, max_results_per_company, db=db
                )
            ]
        else:
            results = self.search_all_companies(max_results_per_company, db=db)

        total_new = 0
        total_duplicate = 0
        company_stats = {}

        for result in results:
            new_count = 0
            dup_count = 0

            company = (
                db.query(CompetitorCompany)
                .filter(CompetitorCompany.code == result.company_code)
                .first()
            )
            if not company:
                continue

            all_articles = result.naver_articles + result.google_articles
            for article in all_articles:
                existing = (
                    db.query(CompetitorNews)
                    .filter(CompetitorNews.url == article.url)
                    .first()
                )
                if existing:
                    dup_count += 1
                    continue

                news = CompetitorNews(
                    company_id=company.id,
                    source=article.source,
                    title=article.title,
                    description=article.description,
                    url=article.url,
                    published_at=article.published_at,
                    search_keyword=article.search_keyword,
                )
                db.add(news)
                new_count += 1

            total_new += new_count
            total_duplicate += dup_count
            company_stats[result.company_code] = {
                "new": new_count,
                "duplicate": dup_count,
            }

        db.commit()
        return {
            "total_new": total_new,
            "total_duplicate": total_duplicate,
            "company_stats": company_stats,
        }

    def _ensure_companies(self, db: Session):
        """기본 경쟁사 목록이 DB 에 없으면 생성."""
        existing = db.query(CompetitorCompany).count()
        if existing > 0:
            return

        for code, data in DEFAULT_COMPETITORS.items():
            company = CompetitorCompany(
                code=code,
                name_kr=data["name_kr"],
                name_en=data["name_en"],
                category=data["category"].value,
                keywords=data["keywords"],
                homepage_url=data.get("homepage_url"),
                is_active=True,
            )
            db.add(company)

        db.commit()
        logger.info(f"기본 경쟁사 {len(DEFAULT_COMPETITORS)}개 등록 완료")

    def close(self):
        """리소스 정리 (connector + executor)."""
        for conn in self._connectors.values():
            try:
                conn.close()
            except Exception:
                pass
        self._executor.shutdown(wait=False)
