"""약물 성분 정보 비회원 공개 라우터 (Phase 3)

알러지 치료에 사용되는 약물의 성분명(INN)·작용기전(MoA)·ATC 분류·출처를
교육 목적으로 노출한다.

약사법 회피 원칙:
- 제품명·복용량·효능효과·복약 지시·주의사항은 응답에서 절대 노출하지 않음
- 출처(FDA / 식약처 / RxNav)는 동적 URL 생성으로 표시
- 모든 응답에 disclaimer 동반
"""
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy import or_
from sqlalchemy.orm import Session

from ..database.connection import get_db
from ..database.drug_models import DrugIngredient
from ..services.drug_safety import (
    ALLERGY_ATC_PREFIXES,
    PUBLIC_DISCLAIMER,
    is_allergy_related,
    list_allergy_categories,
    serialize_ingredient_public,
)

router = APIRouter(prefix="/public/drugs", tags=["Public Drugs"])

_limiter = Limiter(key_func=get_remote_address)


@router.get("/updates")
async def list_drug_updates(
    days: int = Query(7, ge=1, le=30, description="조회 기간(일)"),
    type: str = Query("all", description="all | new_approvals | label_changes | blackbox_warnings | recalls"),
):
    """약물 업데이트 stub — NewsletterPlatform collector 연동 (P2 본 구현 전).

    NewsletterPlatform 의 `_collect_drug_updates` 가 404 를 fatal 로
    인식해 발송이 stale cache 모드로 빠지는 문제를 막기 위한 stub.
    응답 스펙은 NEWSLETTER_REDESIGN_SPEC P2 / collector.py:427 의
    fail-safe 빈 구조와 동일하다.

    본 구현 시 drug_ingest(openFDA · MFDS) 기반 신규 승인/라벨 변경/
    blackbox/recall 을 채워 넣을 자리이다. 현재는 total=0 으로 응답해
    NewsletterPlatform template 이 섹션을 자동 숨김 처리한다.
    """
    return {
        "new_approvals": [],
        "label_changes": [],
        "blackbox_warnings": [],
        "recalls": [],
        "total": 0,
        "window_days": days,
        "type": type,
        "disclaimer": PUBLIC_DISCLAIMER,
    }


@router.get("/allergy-classes")
async def list_allergy_classes():
    """알러지 치료 약물의 ATC 약리군 카탈로그 (7개 그룹).

    각 카테고리: atc_prefix, name_kr, name_en, description.
    """
    return {
        "success": True,
        "items": list_allergy_categories(),
        "total": len(ALLERGY_ATC_PREFIXES),
        "disclaimer": PUBLIC_DISCLAIMER,
    }


@router.get("/search")
@_limiter.limit("30/minute")
async def search_ingredients(
    request: Request,
    q: str | None = Query(None, max_length=100, description="성분명(INN) 검색어"),
    allergy_only: bool = Query(True, description="알러지 약리군 한정 (R01/R03/R06/D07/V01/S01G/H02AB)"),
    atc_prefix: str | None = Query(None, max_length=10, description="특정 ATC prefix 필터"),
    limit: int = Query(20, ge=1, le=50),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """약물 성분 검색.

    성분명(INN, 한·영 모두 inn 컬럼에 저장됨), RxNorm ID, ATC 코드 부분 일치.
    응답에는 제품 정보가 일절 포함되지 않으며, 성분 메타와 출처만 반환한다.
    """
    query = db.query(DrugIngredient)

    if q:
        like = f"%{q.strip()}%"
        query = query.filter(or_(
            DrugIngredient.inn.ilike(like),
            DrugIngredient.rxcui.ilike(like),
            DrugIngredient.atc_code.ilike(like),
        ))

    if atc_prefix:
        query = query.filter(DrugIngredient.atc_code.ilike(f"{atc_prefix.strip().upper()}%"))
    elif allergy_only:
        # 알러지 약리군 화이트리스트로 필터 (DB 레벨 OR)
        query = query.filter(or_(*[
            DrugIngredient.atc_code.ilike(f"{prefix}%") for prefix in ALLERGY_ATC_PREFIXES
        ]))

    total = query.count()
    rows = query.order_by(DrugIngredient.inn).limit(limit).offset(offset).all()

    items = [serialize_ingredient_public(row) for row in rows]

    return {
        "success": True,
        "items": items,
        "total": total,
        "limit": limit,
        "offset": offset,
        "filter": {
            "q": q,
            "allergy_only": allergy_only,
            "atc_prefix": atc_prefix,
        },
        "disclaimer": PUBLIC_DISCLAIMER,
    }


@router.get("/{identifier}")
async def get_ingredient(
    identifier: str,
    db: Session = Depends(get_db),
):
    """성분 단건 조회. identifier 는 rxcui 또는 내부 id.

    제품 정보는 노출하지 않으며, 알러지 약리군 외 성분도 정보 제공은 가능하다
    (단 is_allergy_related 플래그로 사용자가 명시 인지하도록).
    """
    ingredient: DrugIngredient | None = None
    if identifier.isdigit():
        # 숫자면 rxcui 우선, 없으면 id 로 재시도
        ingredient = (
            db.query(DrugIngredient)
            .filter(DrugIngredient.rxcui == identifier)
            .first()
        )
        if not ingredient:
            ingredient = (
                db.query(DrugIngredient)
                .filter(DrugIngredient.id == int(identifier))
                .first()
            )
    else:
        ingredient = (
            db.query(DrugIngredient)
            .filter(DrugIngredient.inn.ilike(identifier))
            .first()
        )

    if not ingredient:
        raise HTTPException(
            status_code=404,
            detail=f"성분을 찾을 수 없습니다: {identifier}",
        )

    return {
        "success": True,
        **serialize_ingredient_public(ingredient),
    }
