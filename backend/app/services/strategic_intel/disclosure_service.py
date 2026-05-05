"""DART 공시 어댑터 (Phase D)

DART(전자공시시스템) Open API 를 호출해 한국 3사 공시를 트리거 데이터로 적재.
임상시험·계약·수주·유증·결산 같은 강한 시그널을 가설 엔진의 입력으로 공급.

API: https://opendart.fss.or.kr/  (DART_API_KEY 필요)

대상:
  - sugentech  : KOSDAQ 253840
  - greencross : KOSDAQ 142280
  - bodytech   : KOSDAQ 206640
  (MADx 비상장 — 대상 제외)

저장:
  - competitor_news 테이블 재사용 (source='dart')
  - 후속 stage_classify / stage_generate 가 자연스럽게 픽업 — 신규 모델 불필요

Strategic Intel 모듈 전용. 외부 사용자 노출 금지.
"""
from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from datetime import date, datetime
from typing import Iterable

import httpx
from sqlalchemy.orm import Session

from ...database.competitor_models import CompetitorCompany, CompetitorNews

logger = logging.getLogger(__name__)

DART_LIST_URL = "https://opendart.fss.or.kr/api/list.json"
DART_DOC_VIEW_URL = "https://dart.fss.or.kr/dsaf001/main.do?rcpNo={rcpt_no}"

# 4사 중 한국 3사만 — MADx 비상장
STOCK_CODE_MAP: dict[str, str] = {
    "sugentech": "253840",
    "greencross": "142280",
    "bodytech": "206640",
}


# 공시 제목 키워드 → competitor_news.category 매핑 (UI 노출용)
_CATEGORY_RULES: list[tuple[str, list[str]]] = [
    ("regulatory", ["임상시험", "허가", "승인", "허가취소", "회수"]),
    ("partnership", ["계약", "수주", "납품", "공급", "양해각서", "MOU", "기술이전"]),
    ("financial", ["유상증자", "무상증자", "전환사채", "신주", "주식분할", "배당", "결산", "분기보고서", "사업보고서", "감사보고서"]),
    ("product", ["출시", "신제품", "특허"]),
]


def _classify_category(report_nm: str) -> str:
    """공시 제목 → category. 매칭 없으면 'general'."""
    if not report_nm:
        return "general"
    for cat, keywords in _CATEGORY_RULES:
        if any(k in report_nm for k in keywords):
            return cat
    return "general"


@dataclass
class DisclosureCollectResult:
    company_code: str
    fetched: int
    inserted: int
    error: str | None = None


class DartDisclosureService:
    """DART Open API list.json 어댑터"""

    def __init__(self, api_key: str | None = None, timeout: float = 30.0):
        self.api_key = api_key or os.getenv("DART_API_KEY")
        self.timeout = timeout

    def _has_key(self) -> bool:
        return bool(self.api_key)

    # ------------------------------------------------------------------
    # API 호출
    # ------------------------------------------------------------------

    def fetch_list(
        self,
        stock_code: str,
        *,
        since: date,
        until: date,
        page_count: int = 100,
    ) -> list[dict]:
        """list.json 호출 → list of dict.

        - status '000' : 정상
        - status '013' : 조회된 데이터가 없음 (warn 후 빈 리스트)
        - 그 외        : 경고 로그 + 빈 리스트
        """
        if not self._has_key():
            raise ValueError("DART_API_KEY 가 설정되지 않았습니다.")
        params = {
            "crtfc_key": self.api_key,
            "stock_code": stock_code,
            "bgn_de": since.strftime("%Y%m%d"),
            "end_de": until.strftime("%Y%m%d"),
            "page_count": page_count,
        }
        try:
            resp = httpx.get(DART_LIST_URL, params=params, timeout=self.timeout)
            resp.raise_for_status()
        except httpx.HTTPError as e:
            logger.warning("DART list.json 호출 실패 stock_code=%s: %s", stock_code, e)
            return []
        try:
            data = resp.json()
        except ValueError as e:
            logger.warning("DART 응답 JSON 파싱 실패 stock_code=%s: %s", stock_code, e)
            return []
        status = data.get("status")
        if status == "013":
            logger.info("DART 조회 데이터 없음 stock_code=%s (%s ~ %s)", stock_code, since, until)
            return []
        if status != "000":
            logger.warning(
                "DART 응답 비정상 stock_code=%s status=%s message=%s",
                stock_code, status, data.get("message"),
            )
            return []
        items = data.get("list") or []
        return items if isinstance(items, list) else []

    # ------------------------------------------------------------------
    # 적재
    # ------------------------------------------------------------------

    def collect_company(
        self,
        db: Session,
        company_code: str,
        *,
        since: date,
        until: date,
    ) -> DisclosureCollectResult:
        """단일 회사 공시 → competitor_news 적재 (URL 기반 dedupe)."""
        if not self._has_key():
            return DisclosureCollectResult(
                company_code=company_code,
                fetched=0,
                inserted=0,
                error="DART_API_KEY 미설정",
            )
        stock_code = STOCK_CODE_MAP.get(company_code)
        if not stock_code:
            return DisclosureCollectResult(
                company_code=company_code, fetched=0, inserted=0,
                error=f"stock_code 매핑 없음 ({company_code})",
            )
        company = db.query(CompetitorCompany).filter(
            CompetitorCompany.code == company_code
        ).first()
        if not company:
            return DisclosureCollectResult(
                company_code=company_code, fetched=0, inserted=0,
                error=f"competitor_companies 에 회사 없음 ({company_code})",
            )

        try:
            items = self.fetch_list(stock_code, since=since, until=until)
        except Exception as e:
            return DisclosureCollectResult(
                company_code=company_code, fetched=0, inserted=0, error=str(e),
            )

        inserted = 0
        for entry in items:
            rcept_no = entry.get("rcept_no")
            if not rcept_no:
                continue
            url = DART_DOC_VIEW_URL.format(rcpt_no=rcept_no)
            existing = db.query(CompetitorNews.id).filter(CompetitorNews.url == url).first()
            if existing:
                continue
            published_at = _parse_dart_date(entry.get("rcept_dt"))
            report_nm = (entry.get("report_nm") or "").strip()
            filer = (entry.get("flr_nm") or "").strip()
            desc_parts = [report_nm]
            if filer:
                desc_parts.append(f"제출인: {filer}")
            desc = " | ".join(desc_parts) or "(공시 제목 없음)"
            try:
                news = CompetitorNews(
                    company_id=company.id,
                    source="dart",
                    title=report_nm[:500] or "(제목 없음)",
                    description=desc,
                    url=url,
                    published_at=published_at,
                    category=_classify_category(report_nm),
                    is_relevant=True,
                )
                db.add(news)
                db.commit()
                inserted += 1
            except Exception as e:
                db.rollback()
                logger.warning(
                    "DART 공시 저장 실패 company=%s rcept_no=%s: %s",
                    company_code, rcept_no, e,
                )

        return DisclosureCollectResult(
            company_code=company_code, fetched=len(items), inserted=inserted,
        )

    def collect_all(
        self,
        db: Session,
        *,
        since: date,
        until: date,
        company_codes: Iterable[str] | None = None,
    ) -> list[DisclosureCollectResult]:
        """3사 일괄 수집"""
        targets = list(company_codes) if company_codes else list(STOCK_CODE_MAP.keys())
        results: list[DisclosureCollectResult] = []
        for code in targets:
            try:
                results.append(self.collect_company(db, code, since=since, until=until))
            except Exception as e:
                logger.exception("collect_company 실패 %s: %s", code, e)
                results.append(DisclosureCollectResult(
                    company_code=code, fetched=0, inserted=0, error=str(e),
                ))
        return results


# ---------------------------------------------------------------------------
# 유틸
# ---------------------------------------------------------------------------


def _parse_dart_date(s: str | None) -> datetime | None:
    """DART rcept_dt (YYYYMMDD) → datetime"""
    if not s:
        return None
    try:
        return datetime.strptime(s.strip(), "%Y%m%d")
    except (ValueError, AttributeError):
        return None
