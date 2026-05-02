"""MAST 비회원 공개 라우터 (Phase 1)

병원/진단소에서 받은 MAST 알러지 등급(Class 0~4)을 입력하면
해당 알러젠에 대한 식이 제한·예상 증상·교차반응·응급 가이드 정보를
논문·전문기관 출처 기반으로 매칭해 반환한다.

본 라우터는 인증을 요구하지 않으며, 모든 응답은 의료 진단이 아닌
교육·정보 매칭 목적임을 디스클레이머로 명시한다.
"""
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.orm import Session

from ..database.allergen_models import AllergenMaster
from ..database.connection import get_db
from ..models.prescription import (
    GRADE_DESCRIPTIONS,
    MAST_MAX_GRADE,
    MAST_MIN_GRADE,
    normalize_grade,
)
from ..services.prescription_engine import PrescriptionEngine

router = APIRouter(prefix="/public/mast", tags=["Public MAST"])

_limiter = Limiter(key_func=get_remote_address)
_engine = PrescriptionEngine()


_DISCLAIMER = (
    "본 정보는 논문 · 전문기관 출처 기반의 교육 · 정보 매칭 목적이며, "
    "의료 진단 · 처방을 대체하지 않습니다. "
    "정확한 진단과 처방은 반드시 의료진과 상담하세요."
)


class MastMatchRequest(BaseModel):
    """MAST 등급 입력 요청"""
    allergen_code: str = Field(..., description="알러젠 코드 (예: peanut, milk, d1)")
    grade: int = Field(
        ...,
        ge=MAST_MIN_GRADE,
        le=MAST_MAX_GRADE,
        description="MAST 검사 등급 (Class 0~4)",
    )


@router.get("/grades")
async def list_grades():
    """MAST Class 0~4 등급 설명 반환"""
    return {
        "standard": "MAST (Multiple Allergen Simultaneous Test)",
        "range": "0-4",
        "grades": GRADE_DESCRIPTIONS,
        "disclaimer": _DISCLAIMER,
    }


@router.post("/match")
@_limiter.limit("30/minute")
async def match_allergen_grade(
    request: Request,
    body: MastMatchRequest,
    db: Session = Depends(get_db),
):
    """병원 MAST 검사 등급 입력 → 알러젠별 정보 매칭

    응답 구조:
        - allergen: 알러젠 마스터 정보
        - grade: 등급 라벨(한·영 병기) + 색상 + 권고 행동
        - food_restriction: 식이 제한 (해당 시)
        - predicted_symptoms: 예상 증상 (논문 기반)
        - cross_reactivity_alerts: 교차반응 경고
        - emergency_guidelines: 응급 대처 가이드
        - emergency_required: Class 3+ 시 true
        - risk_level: 종합 위험도
        - has_detailed_data: 시드 콘텐츠 보유 여부 (16/119종)
        - disclaimer: 의료 면책 문구
        - citations: 논문 출처 (Phase 4에서 채움)
    """
    allergen = (
        db.query(AllergenMaster)
        .filter(AllergenMaster.code == body.allergen_code)
        .first()
    )
    if not allergen:
        raise HTTPException(
            status_code=404,
            detail=f"알러젠을 찾을 수 없습니다: {body.allergen_code}",
        )

    grade = normalize_grade(body.grade)
    grade_info = GRADE_DESCRIPTIONS[grade]

    prescription = _engine.generate_prescription(
        diagnosis_results=[{"allergen": body.allergen_code, "grade": grade}],
    )

    food_restriction = (
        prescription.food_restrictions[0].to_dict()
        if prescription.food_restrictions
        else None
    )

    has_detailed_data = bool(
        food_restriction
        or prescription.predicted_symptoms
        or prescription.cross_reactivity_alerts
    )

    return {
        "allergen": {
            "code": allergen.code,
            "name_kr": allergen.name_kr,
            "name_en": allergen.name_en,
            "category": allergen.category,
            "type": allergen.type,
        },
        "grade": {
            "value": grade,
            "level": grade_info["level"],
            "level_en": grade_info["level_en"],
            "description": grade_info["description"],
            "action": grade_info["action"],
            "color": grade_info["color"],
        },
        "is_positive": grade >= 1,
        "has_detailed_data": has_detailed_data,
        "risk_level": prescription.risk_level.value,
        "emergency_required": grade >= 3,
        "food_restriction": food_restriction,
        "predicted_symptoms": [s.to_dict() for s in prescription.predicted_symptoms],
        "cross_reactivity_alerts": [c.to_dict() for c in prescription.cross_reactivity_alerts],
        "emergency_guidelines": [e.to_dict() for e in prescription.emergency_guidelines],
        "medical_recommendation": (
            prescription.medical_recommendation.to_dict()
            if prescription.medical_recommendation
            else None
        ),
        "disclaimer": _DISCLAIMER,
        "citations": [],
    }
