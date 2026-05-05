"""외부 트리거 어댑터 (Phase D-잔여)

Strategic Intel 가설 엔진에 추가 트리거 데이터를 공급하는 외부 API 어댑터:

  1) FDA 510(k) — openFDA device endpoint, 알러지 IVD 승인 → 'industry' 회사로 매핑
  2) ClinicalTrials.gov — 4사 sponsor 또는 알러지 IVD 키워드 trial → 4사/'industry' 매핑

저장:
  - 공통적으로 competitor_news 테이블 재사용 (source='fda_510k' / 'clinicaltrials')
  - 후속 stage_classify 가 자동 픽업

원칙:
  - 외부 API 실패는 graceful skip — DART 어댑터와 동일 방어선
  - URL 기반 dedupe — 재실행 시 중복 적재 X
  - 회사 매칭 못 하면 'industry' 회사로 분류 (전체 추적 4사 + industry 모두 분류 대상)

Strategic Intel 모듈 전용. 외부 사용자 노출 금지.
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from datetime import date, datetime
from typing import Iterable

import httpx
from sqlalchemy.orm import Session

from ...database.competitor_models import CompetitorCompany, CompetitorNews

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# 공통 헬퍼
# ---------------------------------------------------------------------------


def _get_company(db: Session, code: str) -> CompetitorCompany | None:
    return db.query(CompetitorCompany).filter(CompetitorCompany.code == code).first()


def _exists_news(db: Session, url: str) -> bool:
    return db.query(CompetitorNews.id).filter(CompetitorNews.url == url).first() is not None


def _save_news(
    db: Session,
    *,
    company: CompetitorCompany,
    source: str,
    title: str,
    description: str,
    url: str,
    published_at: datetime | None,
    category: str,
) -> bool:
    """CompetitorNews 1건 저장. URL dedupe + 예외 격리."""
    if _exists_news(db, url):
        return False
    try:
        news = CompetitorNews(
            company_id=company.id,
            source=source,
            title=(title or "(제목 없음)")[:500],
            description=(description or "")[:5000],
            url=url[:1000],
            published_at=published_at,
            category=category,
            is_relevant=True,
        )
        db.add(news)
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        logger.warning("외부 트리거 저장 실패 source=%s url=%s: %s", source, url, e)
        return False


# ---------------------------------------------------------------------------
# FDA 510(k) 어댑터
# ---------------------------------------------------------------------------


@dataclass
class FdaCollectResult:
    fetched: int
    inserted: int
    error: str | None = None


# 알러지 IVD 510(k) 검색 — applicant/device_name 키워드 OR
# (openFDA device/510k 는 product_code 'JST'(allergen extract) 등 활용 가능)
FDA_510K_QUERY_TERMS = [
    "allergen", "allergy", "IgE", "specific IgE",
    "ImmunoCAP", "allergy panel", "allergen extract",
]


class Fda510kService:
    """openFDA device/510k.json — 알러지 IVD 신규 승인 어댑터"""

    BASE_URL = "https://api.fda.gov/device/510k.json"

    def __init__(self, timeout: float = 30.0):
        self.timeout = timeout

    def _build_query(self, since: date, until: date) -> str:
        kw_or = " OR ".join(f'"{k}"' for k in FDA_510K_QUERY_TERMS)
        date_range = f"[{since.strftime('%Y%m%d')}+TO+{until.strftime('%Y%m%d')}]"
        return f"(device_name:({kw_or})) AND decision_date:{date_range}"

    def fetch_recent(
        self,
        since: date,
        until: date,
        *,
        limit: int = 50,
    ) -> list[dict]:
        params = {
            "search": self._build_query(since, until).replace(" ", "+"),
            "limit": limit,
        }
        try:
            # openFDA 는 search 파라미터 인코딩에 민감 — params 대신 url 직접 빌드
            url = f"{self.BASE_URL}?search={params['search']}&limit={limit}"
            resp = httpx.get(url, timeout=self.timeout)
            if resp.status_code == 404:
                # 결과 없음
                return []
            resp.raise_for_status()
        except httpx.HTTPError as e:
            logger.warning("FDA 510(k) 호출 실패: %s", e)
            return []
        try:
            data = resp.json()
        except ValueError as e:
            logger.warning("FDA 510(k) JSON 파싱 실패: %s", e)
            return []
        results = data.get("results") or []
        return results if isinstance(results, list) else []

    def collect(self, db: Session, since: date, until: date) -> FdaCollectResult:
        industry = _get_company(db, "industry")
        if not industry:
            return FdaCollectResult(0, 0, error="competitor_companies 에 'industry' 회사 없음")
        try:
            items = self.fetch_recent(since, until)
        except Exception as e:
            return FdaCollectResult(0, 0, error=str(e))
        inserted = 0
        for entry in items:
            k_number = entry.get("k_number")
            if not k_number:
                continue
            url = f"https://www.accessdata.fda.gov/scripts/cdrh/cfdocs/cfPMN/pmn.cfm?ID={k_number}"
            decision_dt = _parse_fda_date(entry.get("decision_date"))
            device_name = (entry.get("device_name") or "").strip()
            applicant = (entry.get("applicant") or "").strip()
            statement = (entry.get("statement_or_summary") or "").strip()
            title = f"[FDA 510(k) {k_number}] {device_name}".strip()
            desc_parts = [device_name]
            if applicant:
                desc_parts.append(f"Applicant: {applicant}")
            if statement:
                desc_parts.append(statement[:500])
            if _save_news(
                db,
                company=industry,
                source="fda_510k",
                title=title,
                description=" | ".join(desc_parts),
                url=url,
                published_at=decision_dt,
                category="regulatory",
            ):
                inserted += 1
        return FdaCollectResult(fetched=len(items), inserted=inserted)


def _parse_fda_date(s: str | None) -> datetime | None:
    if not s:
        return None
    try:
        return datetime.strptime(s.strip(), "%Y%m%d")
    except (ValueError, AttributeError):
        try:
            return datetime.strptime(s.strip(), "%Y-%m-%d")
        except (ValueError, AttributeError):
            return None


# ---------------------------------------------------------------------------
# ClinicalTrials.gov 어댑터
# ---------------------------------------------------------------------------


@dataclass
class ClinicalTrialsCollectResult:
    company_code: str
    fetched: int
    inserted: int
    error: str | None = None


# 4사 sponsor 매칭 (대소문자 무시) — sponsor 이름이 study 데이터에 등장하면 해당 회사로 매핑
COMPANY_SPONSOR_PATTERNS: dict[str, list[str]] = {
    "sugentech": ["sugentech", "수젠텍"],
    "greencross": ["green cross", "녹십자"],
    "bodytech": ["boditech", "바디텍"],
    "madx": ["macroarray", "macro array", "madx"],
}

# 알러지 IVD 키워드 — 4사 매칭 안 되면 industry 로 분류
CT_KEYWORDS = "(allergy OR IgE OR allergen) AND (diagnostic OR IVD OR microarray OR multiplex)"


class ClinicalTrialsService:
    """ClinicalTrials.gov v2 API — 알러지 IVD 임상시험 어댑터"""

    BASE_URL = "https://clinicaltrials.gov/api/v2/studies"

    def __init__(self, timeout: float = 30.0):
        self.timeout = timeout

    def fetch_recent(
        self,
        *,
        since: date,
        until: date,
        page_size: int = 50,
    ) -> list[dict]:
        """알러지 IVD 도메인 + 시작일 윈도우 내 study 목록"""
        # ClinicalTrials.gov v2 query 문법:
        # query.term=...; filter.advanced=AREA[StudyFirstPostDate]RANGE[since, until]
        params = {
            "query.term": CT_KEYWORDS,
            "filter.advanced": (
                f"AREA[StudyFirstPostDate]RANGE[{since.strftime('%Y-%m-%d')},"
                f"{until.strftime('%Y-%m-%d')}]"
            ),
            "pageSize": page_size,
            "format": "json",
        }
        try:
            resp = httpx.get(self.BASE_URL, params=params, timeout=self.timeout)
            resp.raise_for_status()
        except httpx.HTTPError as e:
            logger.warning("ClinicalTrials 호출 실패: %s", e)
            return []
        try:
            data = resp.json()
        except ValueError as e:
            logger.warning("ClinicalTrials JSON 파싱 실패: %s", e)
            return []
        return data.get("studies") or []

    def _match_company(self, study: dict) -> str:
        """study sponsor / lead organization 에서 4사 매칭. 매칭 실패 시 'industry'."""
        protocol = study.get("protocolSection") or {}
        sponsor = (
            protocol.get("sponsorCollaboratorsModule") or {}
        ).get("leadSponsor") or {}
        sponsor_name = (sponsor.get("name") or "").lower()
        for code, patterns in COMPANY_SPONSOR_PATTERNS.items():
            if any(p in sponsor_name for p in patterns):
                return code
        return "industry"

    def collect(
        self,
        db: Session,
        *,
        since: date,
        until: date,
    ) -> list[ClinicalTrialsCollectResult]:
        try:
            studies = self.fetch_recent(since=since, until=until)
        except Exception as e:
            return [ClinicalTrialsCollectResult("industry", 0, 0, error=str(e))]

        per_company: dict[str, list[dict]] = {}
        for s in studies:
            code = self._match_company(s)
            per_company.setdefault(code, []).append(s)

        results: list[ClinicalTrialsCollectResult] = []
        for company_code, items in per_company.items():
            company = _get_company(db, company_code)
            if not company:
                results.append(ClinicalTrialsCollectResult(
                    company_code=company_code, fetched=len(items), inserted=0,
                    error=f"competitor_companies 에 '{company_code}' 없음",
                ))
                continue
            inserted = 0
            for s in items:
                protocol = s.get("protocolSection") or {}
                ident = protocol.get("identificationModule") or {}
                status = protocol.get("statusModule") or {}
                nct_id = ident.get("nctId")
                if not nct_id:
                    continue
                url = f"https://clinicaltrials.gov/study/{nct_id}"
                title = (ident.get("briefTitle") or "")[:500]
                summary = (
                    (protocol.get("descriptionModule") or {}).get("briefSummary") or ""
                )[:1500]
                first_post = _parse_iso_date(status.get("studyFirstPostDateStruct", {}).get("date"))
                if _save_news(
                    db,
                    company=company,
                    source="clinicaltrials",
                    title=f"[NCT {nct_id}] {title}",
                    description=summary or title,
                    url=url,
                    published_at=first_post,
                    category="regulatory",
                ):
                    inserted += 1
            results.append(ClinicalTrialsCollectResult(
                company_code=company_code, fetched=len(items), inserted=inserted,
            ))
        return results


def _parse_iso_date(s: str | None) -> datetime | None:
    if not s:
        return None
    s = s.strip()
    # ClinicalTrials 는 'YYYY-MM-DD' 또는 'YYYY-MM' 형식
    for fmt in ("%Y-%m-%d", "%Y-%m"):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    return None
