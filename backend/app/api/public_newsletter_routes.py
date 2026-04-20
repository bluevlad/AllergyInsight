"""뉴스레터 공개 API — 헤드라인 · 기업 동향

인증 없음. NewsletterPlatform collector 가 호출하는 데이터 인터페이스.
응답 스키마: NEWSLETTER_REDESIGN_SPEC § 3.2.1 / § 3.2.2.
"""
from __future__ import annotations

import logging
from datetime import date

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..database.connection import get_db
from ..services.headline_selection_service import select_top_headlines
from ..services.company_digest_service import build_company_digest

logger = logging.getLogger(__name__)

router = APIRouter()


def _parse_exclude_ids(raw: str) -> set[int]:
    """콤마 구분 정수 문자열 파싱. 비정수 토큰은 조용히 무시."""
    if not raw:
        return set()
    out: set[int] = set()
    for token in raw.split(","):
        stripped = token.strip()
        if stripped.isdigit():
            out.add(int(stripped))
    return out


def _parse_fallback_days(raw: str, base_days: int) -> list[int]:
    """fallback_days 쿼리 파싱. 빈 값이면 [base_days] (확장 비활성)."""
    fallback_raw = (raw or "").strip()
    if not fallback_raw:
        return [base_days]
    windows: list[int] = []
    for token in fallback_raw.split(","):
        stripped = token.strip()
        if stripped.isdigit():
            value = int(stripped)
            if 1 <= value <= 30:
                windows.append(value)
    return windows or [base_days]


def _run_headline_selection(
    db: Session,
    *,
    limit: int,
    one_per_company: bool,
    days: int,
    windows: list[int],
    exclude_ids: set[int],
) -> dict:
    headlines, excluded_from_selection, effective_days = select_top_headlines(
        db,
        limit=limit,
        one_per_company=one_per_company,
        days=days,
        fallback_days=windows,
        exclude_ids=exclude_ids or None,
    )
    return {
        "data": {
            "headlines": headlines,
            "excluded_ids": sorted(excluded_from_selection),
        },
        "meta": {
            "report_date": date.today().isoformat(),
            "pool_size": len(headlines),
            "effective_days": effective_days,
            "requested_days": days,
            "excluded_input_count": len(exclude_ids),
        },
    }


@router.get("/headlines/today")
def get_headlines_today(
    limit: int = Query(5, ge=1, le=20),
    one_per_company: bool = Query(True),
    days: int = Query(1, ge=1, le=7),
    fallback_days: str = Query(
        "1,3,7",
        description=(
            "limit 미달 시 확장할 lookback 후보 (콤마 구분). "
            "최초 days 풀로 부족하면 다음 값으로 재선정. 빈 문자열이면 확장 없음."
        ),
    ),
    exclude_ids: str = Query(
        "",
        description=(
            "원천 제외할 기사 ID (콤마 구분). NewsLetterPlatform 최근 7일 발송 이력 전달. "
            "URL 길이 부담 시 POST /headlines/today:select 사용 권장."
        ),
    ),
    db: Session = Depends(get_db),
):
    """오늘의 핵심 헤드라인 Top N.

    1기업 1헤드라인 · MinHash 제목 중복 제거 · URL canonical 중복 제거.
    pool이 limit에 미달하면 fallback_days 순서대로 lookback을 확장한다.
    excluded_ids 를 company-digest 호출 시 전달하여 교차 중복 방지.
    exclude_ids 로 최근 발송 이력을 전달하면 풀에서 원천 제외된다.
    """
    return _run_headline_selection(
        db,
        limit=limit,
        one_per_company=one_per_company,
        days=days,
        windows=_parse_fallback_days(fallback_days, days),
        exclude_ids=_parse_exclude_ids(exclude_ids),
    )


class HeadlinesSelectBody(BaseModel):
    """POST /headlines/today:select 요청 본문.

    GET 경로 URL 길이 한계(약 2048 bytes) 를 넘어서는 대량 exclude_ids 전달용.
    """

    limit: int = Field(5, ge=1, le=20)
    one_per_company: bool = True
    days: int = Field(1, ge=1, le=7)
    fallback_days: list[int] | None = Field(
        default=None,
        description="lookback 후보 리스트. None/빈 리스트면 [days] (확장 없음).",
    )
    exclude_ids: list[int] = Field(default_factory=list)


@router.post("/headlines/today:select")
def post_headlines_today(
    body: HeadlinesSelectBody,
    db: Session = Depends(get_db),
):
    """헤드라인 선정 POST alias (대량 exclude_ids 전용).

    GET 엔드포인트와 동일한 응답 스키마. 운영 동작은 같다.
    """
    if body.fallback_days:
        windows = [d for d in body.fallback_days if 1 <= d <= 30] or [body.days]
    else:
        windows = [body.days]
    return _run_headline_selection(
        db,
        limit=body.limit,
        one_per_company=body.one_per_company,
        days=body.days,
        windows=windows,
        exclude_ids={int(i) for i in body.exclude_ids},
    )


@router.get("/company-digest")
def get_company_digest(
    days: int = Query(7, ge=1, le=30),
    exclude_ids: str = Query("", description="콤마 구분 기사 ID (헤드라인 선정분 제외)"),
    limit_per_company: int = Query(1, ge=1, le=5),
    max_companies: int = Query(20, ge=1, le=50),
    db: Session = Depends(get_db),
):
    """산업·기업 동향 다이제스트.

    exclude_ids 로 헤드라인에 선정된 기사를 제외해 disjoint 보장.
    """
    parsed_exclude: set[int] = set()
    if exclude_ids:
        for token in exclude_ids.split(","):
            token = token.strip()
            if token.isdigit():
                parsed_exclude.add(int(token))

    companies = build_company_digest(
        db,
        days=days,
        exclude_ids=parsed_exclude,
        limit_per_company=limit_per_company,
        max_companies=max_companies,
    )

    return {
        "data": {
            "companies": companies,
        },
        "meta": {
            "days": days,
            "excluded_count": len(parsed_exclude),
        },
    }
