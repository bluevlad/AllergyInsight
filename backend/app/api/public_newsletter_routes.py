"""뉴스레터 공개 API — 헤드라인 · 기업 동향

인증 없음. NewsletterPlatform collector 가 호출하는 데이터 인터페이스.
응답 스키마: NEWSLETTER_REDESIGN_SPEC § 3.2.1 / § 3.2.2.
"""
from __future__ import annotations

import logging
from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ..database.connection import get_db
from ..services.headline_selection_service import select_top_headlines
from ..services.company_digest_service import build_company_digest

logger = logging.getLogger(__name__)

router = APIRouter()


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
    db: Session = Depends(get_db),
):
    """오늘의 핵심 헤드라인 Top N.

    1기업 1헤드라인 · MinHash 제목 중복 제거 · URL canonical 중복 제거.
    pool이 limit에 미달하면 fallback_days 순서대로 lookback을 확장한다.
    excluded_ids 를 company-digest 호출 시 전달하여 교차 중복 방지.
    """
    fallback_raw = fallback_days.strip()
    if fallback_raw:
        windows: list[int] = []
        for token in fallback_raw.split(","):
            stripped = token.strip()
            if stripped.isdigit():
                value = int(stripped)
                if 1 <= value <= 30:
                    windows.append(value)
        windows_arg = windows or [days]
    else:
        # 빈 문자열 → 확장 비활성
        windows_arg = [days]

    headlines, excluded_ids, effective_days = select_top_headlines(
        db,
        limit=limit,
        one_per_company=one_per_company,
        days=days,
        fallback_days=windows_arg,
    )

    return {
        "data": {
            "headlines": headlines,
            "excluded_ids": sorted(excluded_ids),
        },
        "meta": {
            "report_date": date.today().isoformat(),
            "pool_size": len(headlines),
            "effective_days": effective_days,
            "requested_days": days,
        },
    }


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
