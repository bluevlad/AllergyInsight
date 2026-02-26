"""Consumer My Diagnosis Routes - 내 진단 결과 조회 API

사용자가 자신의 알러지 검사 결과를 조회하는 API입니다.
"""
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime

from ...database.connection import get_db
from ...database.models import User, UserDiagnosis, DiagnosisKit, Paper, PaperAllergenLink
from ...core.auth import require_consumer
from ...core.allergen import (
    get_allergen_info as get_allergen_prescription,
    EMERGENCY_GUIDELINES,
    ALLERGEN_NAMES_KR,
)

router = APIRouter(prefix="/my", tags=["Consumer - My Diagnosis"])


# ============================================================================
# Schemas
# ============================================================================

class DiagnosisSummary(BaseModel):
    """진단 요약"""
    id: int
    diagnosis_date: datetime
    high_risk: List[str]
    moderate_risk: List[str]
    total_positive: int

class DiagnosisDetail(BaseModel):
    """진단 상세"""
    id: int
    results: Dict[str, int]
    diagnosis_date: datetime
    prescription: Optional[Dict[str, Any]]
    kit_serial: Optional[str]
    created_at: datetime


# ============================================================================
# Helper Functions
# ============================================================================

def get_risk_levels(results: dict) -> tuple:
    """고위험/중위험 알러젠 분류"""
    high_risk = []
    moderate_risk = []

    for allergen, grade in results.items():
        name = ALLERGEN_NAMES_KR.get(allergen, allergen)
        if grade >= 4:
            high_risk.append(name)
        elif grade >= 2:
            moderate_risk.append(name)

    return high_risk, moderate_risk


def get_citations_for_item(
    db: Session, allergen_code: str, item_name: str, link_type: str, limit: int = 2
) -> List[Dict[str, Any]]:
    """특정 항목에 대한 출처 논문 조회"""
    import re
    main_name = re.split(r'\s*[\(\(]', item_name)[0].strip()

    papers = db.query(Paper).join(PaperAllergenLink).filter(
        PaperAllergenLink.allergen_code == allergen_code,
        PaperAllergenLink.specific_item.ilike(f"%{main_name}%"),
        Paper.is_verified == True
    ).order_by(
        PaperAllergenLink.relevance_score.desc()
    ).limit(limit).all()

    return [
        {
            "id": p.id,
            "title": p.title,
            "title_kr": p.title_kr,
            "year": p.year,
            "url": p.url,
        }
        for p in papers
    ]


# ============================================================================
# Endpoints
# ============================================================================

@router.get("/diagnoses")
async def get_my_diagnoses(
    user: User = Depends(require_consumer),
    db: Session = Depends(get_db)
):
    """내 진단 목록 조회"""
    diagnoses = db.query(UserDiagnosis).filter(
        UserDiagnosis.user_id == user.id
    ).order_by(UserDiagnosis.diagnosis_date.desc()).all()

    result = []
    for diag in diagnoses:
        kit_serial = None
        if diag.kit_id:
            kit = db.query(DiagnosisKit).filter(DiagnosisKit.id == diag.kit_id).first()
            if kit:
                kit_serial = kit.serial_number

        high_risk, moderate_risk = get_risk_levels(diag.results)
        total_positive = sum(1 for g in diag.results.values() if g > 0)

        result.append({
            "id": diag.id,
            "diagnosis_date": diag.diagnosis_date,
            "high_risk": high_risk,
            "moderate_risk": moderate_risk,
            "total_positive": total_positive,
            "kit_serial": kit_serial,
        })

    return {"items": result, "total": len(result)}


@router.get("/diagnoses/latest", response_model=DiagnosisSummary)
async def get_latest_diagnosis(
    user: User = Depends(require_consumer),
    db: Session = Depends(get_db)
):
    """최신 진단 요약 조회"""
    diagnosis = db.query(UserDiagnosis).filter(
        UserDiagnosis.user_id == user.id
    ).order_by(UserDiagnosis.diagnosis_date.desc()).first()

    if not diagnosis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="진단 결과가 없습니다"
        )

    high_risk, moderate_risk = get_risk_levels(diagnosis.results)
    total_positive = sum(1 for g in diagnosis.results.values() if g > 0)

    return DiagnosisSummary(
        id=diagnosis.id,
        diagnosis_date=diagnosis.diagnosis_date,
        high_risk=high_risk,
        moderate_risk=moderate_risk,
        total_positive=total_positive
    )


@router.get("/diagnoses/{diagnosis_id}")
async def get_diagnosis_detail(
    diagnosis_id: int,
    user: User = Depends(require_consumer),
    db: Session = Depends(get_db)
):
    """진단 상세 조회"""
    diagnosis = db.query(UserDiagnosis).filter(
        UserDiagnosis.id == diagnosis_id,
        UserDiagnosis.user_id == user.id
    ).first()

    if not diagnosis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="진단 결과를 찾을 수 없습니다"
        )

    kit_serial = None
    if diagnosis.kit_id:
        kit = db.query(DiagnosisKit).filter(DiagnosisKit.id == diagnosis.kit_id).first()
        if kit:
            kit_serial = kit.serial_number

    high_risk, moderate_risk = get_risk_levels(diagnosis.results)

    return {
        "id": diagnosis.id,
        "results": diagnosis.results,
        "diagnosis_date": diagnosis.diagnosis_date,
        "prescription": diagnosis.prescription,
        "kit_serial": kit_serial,
        "created_at": diagnosis.created_at,
        "summary": {
            "high_risk": high_risk,
            "moderate_risk": moderate_risk,
            "total_positive": sum(1 for g in diagnosis.results.values() if g > 0),
        }
    }


@router.get("/diagnoses/{diagnosis_id}/guide")
async def get_patient_guide(
    diagnosis_id: int,
    user: User = Depends(require_consumer),
    db: Session = Depends(get_db)
):
    """환자 맞춤형 가이드 조회"""
    diagnosis = db.query(UserDiagnosis).filter(
        UserDiagnosis.id == diagnosis_id,
        UserDiagnosis.user_id == user.id
    ).first()

    if not diagnosis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="진단 결과를 찾을 수 없습니다"
        )

    results = diagnosis.results

    # 증상/위험도
    symptoms_risk = {"high_risk": [], "moderate_risk": [], "low_risk": []}

    # 식이 관리
    dietary_management = {
        "avoid_foods": [],
        "hidden_sources": [],
        "cross_reactivity": [],
        "substitutes": [],
    }

    # 응급/의료
    emergency_medical = {
        "has_severe_allergy": False,
        "emergency_guidelines": EMERGENCY_GUIDELINES,
        "management_tips": [],
    }

    for allergen_code, grade in results.items():
        if grade == 0:
            continue

        allergen_info = get_allergen_prescription(allergen_code)
        if not allergen_info:
            continue

        allergen_name = ALLERGEN_NAMES_KR.get(allergen_code, allergen_code)

        # 위험도 분류
        if grade >= 4:
            risk_level = "high_risk"
            emergency_medical["has_severe_allergy"] = True
        elif grade >= 2:
            risk_level = "moderate_risk"
        else:
            risk_level = "low_risk"

        # 증상 정보
        if grade >= 5:
            grade_range = "5-6"
        elif grade >= 3:
            grade_range = "3-4"
        else:
            grade_range = "1-2"

        symptoms_data = allergen_info.get("symptoms_by_grade", {}).get(grade_range, {})
        if symptoms_data:
            symptoms_risk[risk_level].append({
                "allergen": allergen_name,
                "allergen_code": allergen_code,
                "grade": grade,
                "severity": symptoms_data.get("severity", "unknown"),
                "symptoms": symptoms_data.get("symptoms", []),
            })

        # 식품 알러젠 정보
        if allergen_info.get("category") == "food":
            if allergen_info.get("avoid_foods"):
                dietary_management["avoid_foods"].append({
                    "allergen": allergen_name,
                    "allergen_code": allergen_code,
                    "foods": allergen_info["avoid_foods"][:8],
                })

            if allergen_info.get("hidden_sources"):
                dietary_management["hidden_sources"].append({
                    "allergen": allergen_name,
                    "allergen_code": allergen_code,
                    "sources": allergen_info["hidden_sources"][:6],
                })

            if allergen_info.get("cross_reactivity"):
                for cross in allergen_info["cross_reactivity"]:
                    dietary_management["cross_reactivity"].append({
                        "from_allergen": allergen_name,
                        "to_allergen": cross.get("allergen_kr", ""),
                        "probability": cross.get("probability", ""),
                        "related_foods": cross.get("related_foods", [])[:5],
                    })

            if allergen_info.get("substitutes"):
                for sub in allergen_info["substitutes"][:3]:
                    dietary_management["substitutes"].append({
                        "allergen": allergen_name,
                        "original": sub.get("original", ""),
                        "alternatives": sub.get("alternatives", []),
                        "notes": sub.get("notes", ""),
                    })

        # 흡입 알러젠 관리 팁
        if allergen_info.get("category") == "inhalant":
            if allergen_info.get("management_tips"):
                emergency_medical["management_tips"].append({
                    "allergen": allergen_name,
                    "tips": allergen_info["management_tips"][:6],
                })

    return {
        "diagnosis_id": diagnosis_id,
        "diagnosis_date": diagnosis.diagnosis_date.isoformat(),
        "symptoms_risk": symptoms_risk,
        "dietary_management": dietary_management,
        "emergency_medical": emergency_medical,
    }
