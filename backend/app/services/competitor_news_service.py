"""통합 경쟁사 뉴스 검색 서비스

네이버 뉴스 API와 Google News RSS를 통합하여 검색하고,
DB에 저장/관리합니다.
"""
import time
import logging
from concurrent.futures import ThreadPoolExecutor
from typing import Optional
from dataclasses import dataclass

from sqlalchemy.orm import Session

from .naver_news_service import NaverNewsService
from .google_news_service import GoogleNewsService
from ..models.competitor_news import (
    NewsArticle, NewsSearchResult, DEFAULT_COMPETITORS,
)
from ..database.competitor_models import CompetitorCompany, CompetitorNews

logger = logging.getLogger(__name__)


@dataclass
class CompanyNewsResult:
    """업체별 뉴스 검색 결과"""
    company_code: str
    company_name: str
    naver_articles: list[NewsArticle]
    google_articles: list[NewsArticle]
    total_count: int
    search_time_ms: float


class CompetitorNewsService:
    """통합 경쟁사 뉴스 검색 서비스"""

    def __init__(
        self,
        naver_client_id: Optional[str] = None,
        naver_client_secret: Optional[str] = None,
    ):
        self.naver = NaverNewsService(
            client_id=naver_client_id,
            client_secret=naver_client_secret,
        )
        self.google = GoogleNewsService()
        self._executor = ThreadPoolExecutor(max_workers=4)

    def _get_company_keywords(self, company_code: str, db: Optional[Session] = None) -> list[str]:
        """업체 검색 키워드 조회 (DB 우선, 없으면 기본값)"""
        if db:
            company = db.query(CompetitorCompany).filter(
                CompetitorCompany.code == company_code,
                CompetitorCompany.is_active == True,
            ).first()
            if company and company.keywords:
                return company.keywords

        competitor = DEFAULT_COMPETITORS.get(company_code)
        if competitor:
            return competitor["keywords"]
        return []

    def search_company_news(
        self,
        company_code: str,
        max_results: int = 20,
        sources: Optional[list[str]] = None,
        db: Optional[Session] = None,
    ) -> CompanyNewsResult:
        """
        특정 업체 뉴스 검색

        Args:
            company_code: 업체 코드 (예: 'sugentech')
            max_results: 소스당 최대 결과 수
            sources: 검색 소스 목록 ['naver', 'google']
            db: DB 세션 (키워드 조회용)

        Returns:
            CompanyNewsResult: 업체별 뉴스 결과
        """
        start_time = time.time()

        if sources is None:
            sources = ["naver", "google"]

        keywords = self._get_company_keywords(company_code, db)
        if not keywords:
            return CompanyNewsResult(
                company_code=company_code,
                company_name=company_code,
                naver_articles=[],
                google_articles=[],
                total_count=0,
                search_time_ms=0,
            )

        competitor = DEFAULT_COMPETITORS.get(company_code, {})
        company_name = competitor.get("name_kr", company_code)

        all_naver = []
        all_google = []

        # 키워드별 병렬 검색
        futures = []
        for keyword in keywords:
            if "naver" in sources:
                futures.append(
                    ("naver", keyword, self._executor.submit(
                        self.naver.search, keyword, max_results
                    ))
                )
            if "google" in sources:
                futures.append(
                    ("google", keyword, self._executor.submit(
                        self.google.search, keyword, max_results=max_results
                    ))
                )

        # 결과 수집
        seen_urls = set()
        for source, keyword, future in futures:
            try:
                result = future.result(timeout=15)
                for article in result.articles:
                    if article.url in seen_urls:
                        continue
                    seen_urls.add(article.url)
                    article.company = company_code
                    article.search_keyword = keyword

                    if source == "naver":
                        all_naver.append(article)
                    else:
                        all_google.append(article)
            except Exception as e:
                logger.warning(f"뉴스 검색 실패 ({source}/{keyword}): {e}")

        return CompanyNewsResult(
            company_code=company_code,
            company_name=company_name,
            naver_articles=all_naver,
            google_articles=all_google,
            total_count=len(all_naver) + len(all_google),
            search_time_ms=(time.time() - start_time) * 1000,
        )

    def search_all_companies(
        self,
        max_results_per_company: int = 10,
        sources: Optional[list[str]] = None,
        db: Optional[Session] = None,
    ) -> list[CompanyNewsResult]:
        """
        전체 업체 뉴스 일괄 검색

        Args:
            max_results_per_company: 업체당 소스별 최대 결과 수
            sources: 검색 소스 목록
            db: DB 세션

        Returns:
            list[CompanyNewsResult]: 업체별 뉴스 결과 목록
        """
        # DB에서 활성 업체 목록 조회, 없으면 기본값 사용
        company_codes = list(DEFAULT_COMPETITORS.keys())
        if db:
            active_companies = db.query(CompetitorCompany).filter(
                CompetitorCompany.is_active == True
            ).all()
            if active_companies:
                company_codes = [c.code for c in active_companies]

        results = []
        for code in company_codes:
            result = self.search_company_news(
                code, max_results_per_company, sources, db
            )
            results.append(result)

        return results

    def collect_and_save(
        self,
        db: Session,
        company_code: Optional[str] = None,
        max_results_per_company: int = 10,
    ) -> dict:
        """
        뉴스 수집 후 DB 저장 (중복 URL 제거)

        Args:
            db: DB 세션
            company_code: 특정 업체만 수집 (None이면 전체)
            max_results_per_company: 업체당 소스별 최대 결과 수

        Returns:
            dict: 수집 결과 요약
        """
        # 업체 테이블 초기화 (없으면 생성)
        self._ensure_companies(db)

        if company_code:
            results = [self.search_company_news(company_code, max_results_per_company, db=db)]
        else:
            results = self.search_all_companies(max_results_per_company, db=db)

        total_new = 0
        total_duplicate = 0
        company_stats = {}

        for result in results:
            new_count = 0
            dup_count = 0

            # 업체 ID 조회
            company = db.query(CompetitorCompany).filter(
                CompetitorCompany.code == result.company_code
            ).first()
            if not company:
                continue

            all_articles = result.naver_articles + result.google_articles
            for article in all_articles:
                # 중복 URL 체크
                existing = db.query(CompetitorNews).filter(
                    CompetitorNews.url == article.url
                ).first()
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
        """기본 경쟁사 목록이 DB에 없으면 생성"""
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
        """리소스 정리"""
        self._executor.shutdown(wait=False)
