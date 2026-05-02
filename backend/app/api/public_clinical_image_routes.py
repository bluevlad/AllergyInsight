"""임상 이미지 갤러리 비회원 공개 라우터 (Phase 4 P4-PR1)

논문/전문기관 출처의 알러지 임상 이미지를 알러젠/증상 필터로 단방향 조회한다.

원칙:
- 사용자 사진 업로드/매칭/비교는 제공하지 않는다 (의료기기 인허가 영역 회피)
- 라이선스(CC-BY/CC0/Public Domain) 메타가 없는 항목은 노출하지 않는다
- 모든 응답에 disclaimer 동반
"""
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy import or_
from sqlalchemy.orm import Session

from ..database.clinical_image_models import ClinicalImage
from ..database.connection import get_db

router = APIRouter(prefix="/public/clinical-images", tags=["Public Clinical Images"])

_limiter = Limiter(key_func=get_remote_address)


_DISCLAIMER = (
    "본 갤러리는 논문 · 전문기관 출처의 임상 이미지를 라이선스에 따라 단방향으로 표시합니다. "
    "사용자가 업로드한 사진의 분석 · 비교 · 진단은 제공하지 않습니다. "
    "이미지는 교육 · 정보 매칭 목적이며 의료 진단을 대체하지 않습니다."
)

_NO_RESULTS_MESSAGE = (
    "조건에 맞는 임상 이미지를 찾지 못했습니다. 본 갤러리는 단계적으로 큐레이션 중이며, "
    "라이선스(CC-BY/CC0/Public Domain) 메타가 검증된 이미지만 노출됩니다."
)


@router.get("")
@_limiter.limit("60/minute")
async def list_images(
    request: Request,
    allergen: str | None = Query(None, max_length=30, description="알러젠 코드 (예: peanut, dust_mite)"),
    symptom: str | None = Query(None, max_length=100, description="증상 키워드 (부분 일치)"),
    severity: str | None = Query(None, regex="^(mild|moderate|severe)$"),
    body_part: str | None = Query(None, max_length=50),
    limit: int = Query(24, ge=1, le=60),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """필터 조건으로 임상 이미지 목록 조회.

    is_active=true 이고 라이선스 메타가 있는 항목만 노출.
    Phase 4 P4-PR1 단계에서는 시드 데이터가 비어 있을 수 있으며, 그때는
    빈 items + 안내 message 가 반환된다.
    """
    query = db.query(ClinicalImage).filter(
        ClinicalImage.is_active.is_(True),
        ClinicalImage.license.isnot(None),
        ClinicalImage.image_url.isnot(None),
    )

    if allergen:
        query = query.filter(ClinicalImage.allergen_code == allergen.strip())

    if symptom:
        like = f"%{symptom.strip()}%"
        # PostgreSQL JSON 부분 매칭은 단순 문자열 LIKE 로 대체 (캡션 + JSON 직렬화 둘 다 검사)
        query = query.filter(or_(
            ClinicalImage.caption_kr.ilike(like),
            ClinicalImage.caption_en.ilike(like),
        ))

    if severity:
        query = query.filter(ClinicalImage.severity_level == severity)

    if body_part:
        query = query.filter(ClinicalImage.body_part == body_part.strip())

    total = query.count()
    rows = (
        query.order_by(ClinicalImage.indexed_at.desc())
        .limit(limit)
        .offset(offset)
        .all()
    )

    items = [r.to_dict() for r in rows]

    return {
        "success": True,
        "items": items,
        "total": total,
        "limit": limit,
        "offset": offset,
        "filter": {
            "allergen": allergen,
            "symptom": symptom,
            "severity": severity,
            "body_part": body_part,
        },
        "message": _NO_RESULTS_MESSAGE if total == 0 else None,
        "disclaimer": _DISCLAIMER,
    }


@router.get("/{image_id}")
async def get_image(image_id: int, db: Session = Depends(get_db)):
    """이미지 단건 조회 (라이선스/출처 상세)."""
    img = (
        db.query(ClinicalImage)
        .filter(ClinicalImage.id == image_id, ClinicalImage.is_active.is_(True))
        .first()
    )
    if not img:
        raise HTTPException(status_code=404, detail="이미지를 찾을 수 없습니다.")

    return {
        "success": True,
        **img.to_dict(),
        "disclaimer": _DISCLAIMER,
    }
