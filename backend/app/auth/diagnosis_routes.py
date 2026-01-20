"""Diagnosis Routes - User diagnosis history"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database.connection import get_db
from ..database.models import User, UserDiagnosis, DiagnosisKit
from .dependencies import require_auth
from .schemas import UserDiagnosisResponse, UserDiagnosisSummary

router = APIRouter(prefix="/diagnosis", tags=["Diagnosis"])


def get_risk_levels(results: dict) -> tuple:
    """Get high risk and moderate risk allergens"""
    high_risk = []
    moderate_risk = []

    # Allergen Korean names mapping
    allergen_names = {
        "peanut": "땅콩", "milk": "우유", "egg": "계란",
        "wheat": "밀", "soy": "대두", "fish": "생선",
        "shellfish": "갑각류", "tree_nuts": "견과류", "sesame": "참깨",
        "dust_mite": "집먼지진드기", "pollen": "꽃가루",
        "mold": "곰팡이", "pet_dander": "반려동물",
        "cockroach": "바퀴벌레", "latex": "라텍스", "bee_venom": "벌독"
    }

    for allergen, grade in results.items():
        name = allergen_names.get(allergen, allergen)
        if grade >= 4:
            high_risk.append(name)
        elif grade >= 2:
            moderate_risk.append(name)

    return high_risk, moderate_risk


@router.get("/my", response_model=List[UserDiagnosisResponse])
async def get_my_diagnoses(
    user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Get all diagnoses for current user"""
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

        result.append(UserDiagnosisResponse(
            id=diag.id,
            results=diag.results,
            diagnosis_date=diag.diagnosis_date,
            prescription=diag.prescription,
            created_at=diag.created_at,
            kit_serial=kit_serial
        ))

    return result


@router.get("/my/latest", response_model=UserDiagnosisSummary)
async def get_latest_diagnosis(
    user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Get latest diagnosis summary (for mobile/quick view)"""
    diagnosis = db.query(UserDiagnosis).filter(
        UserDiagnosis.user_id == user.id
    ).order_by(UserDiagnosis.diagnosis_date.desc()).first()

    if not diagnosis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No diagnosis found"
        )

    high_risk, moderate_risk = get_risk_levels(diagnosis.results)
    total_positive = sum(1 for g in diagnosis.results.values() if g > 0)

    return UserDiagnosisSummary(
        id=diagnosis.id,
        diagnosis_date=diagnosis.diagnosis_date,
        high_risk=high_risk,
        moderate_risk=moderate_risk,
        total_positive=total_positive
    )


@router.get("/my/{diagnosis_id}", response_model=UserDiagnosisResponse)
async def get_diagnosis_detail(
    diagnosis_id: int,
    user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Get specific diagnosis detail"""
    diagnosis = db.query(UserDiagnosis).filter(
        UserDiagnosis.id == diagnosis_id,
        UserDiagnosis.user_id == user.id
    ).first()

    if not diagnosis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Diagnosis not found"
        )

    kit_serial = None
    if diagnosis.kit_id:
        kit = db.query(DiagnosisKit).filter(DiagnosisKit.id == diagnosis.kit_id).first()
        if kit:
            kit_serial = kit.serial_number

    return UserDiagnosisResponse(
        id=diagnosis.id,
        results=diagnosis.results,
        diagnosis_date=diagnosis.diagnosis_date,
        prescription=diagnosis.prescription,
        created_at=diagnosis.created_at,
        kit_serial=kit_serial
    )


@router.get("/allergen-info")
async def get_allergen_info():
    """Get allergen information for display"""
    return {
        "food": [
            {"code": "peanut", "name_kr": "땅콩", "name_en": "Peanut"},
            {"code": "milk", "name_kr": "우유", "name_en": "Milk"},
            {"code": "egg", "name_kr": "계란", "name_en": "Egg"},
            {"code": "wheat", "name_kr": "밀", "name_en": "Wheat"},
            {"code": "soy", "name_kr": "대두", "name_en": "Soy"},
            {"code": "fish", "name_kr": "생선", "name_en": "Fish"},
            {"code": "shellfish", "name_kr": "갑각류", "name_en": "Shellfish"},
            {"code": "tree_nuts", "name_kr": "견과류", "name_en": "Tree Nuts"},
            {"code": "sesame", "name_kr": "참깨", "name_en": "Sesame"},
        ],
        "inhalant": [
            {"code": "dust_mite", "name_kr": "집먼지진드기", "name_en": "Dust Mite"},
            {"code": "pollen", "name_kr": "꽃가루", "name_en": "Pollen"},
            {"code": "mold", "name_kr": "곰팡이", "name_en": "Mold"},
            {"code": "pet_dander", "name_kr": "반려동물", "name_en": "Pet Dander"},
            {"code": "cockroach", "name_kr": "바퀴벌레", "name_en": "Cockroach"},
            {"code": "latex", "name_kr": "라텍스", "name_en": "Latex"},
            {"code": "bee_venom", "name_kr": "벌독", "name_en": "Bee Venom"},
        ],
        "grades": {
            0: {"label": "음성", "color": "#4CAF50"},
            1: {"label": "약양성", "color": "#8BC34A"},
            2: {"label": "양성", "color": "#FFEB3B"},
            3: {"label": "양성", "color": "#FFC107"},
            4: {"label": "강양성", "color": "#FF9800"},
            5: {"label": "강양성", "color": "#F44336"},
            6: {"label": "최강양성", "color": "#B71C1C"},
        }
    }
