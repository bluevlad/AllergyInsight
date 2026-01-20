"""Diagnosis Routes - User diagnosis history"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database.connection import get_db
from ..database.models import User, UserDiagnosis, DiagnosisKit
from .dependencies import require_auth
from .schemas import UserDiagnosisResponse, UserDiagnosisSummary
from ..data.allergen_prescription_db import (
    get_allergen_info as get_allergen_prescription,
    EMERGENCY_GUIDELINES
)

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


@router.get("/my/{diagnosis_id}/patient-guide")
async def get_patient_guide(
    diagnosis_id: int,
    user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Get patient-focused guide based on diagnosis results"""
    diagnosis = db.query(UserDiagnosis).filter(
        UserDiagnosis.id == diagnosis_id,
        UserDiagnosis.user_id == user.id
    ).first()

    if not diagnosis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Diagnosis not found"
        )

    results = diagnosis.results

    # 1. 증상 및 위험도 (Symptoms & Risk)
    symptoms_risk = {
        "high_risk": [],  # 등급 4 이상
        "moderate_risk": [],  # 등급 2-3
        "low_risk": [],  # 등급 1
    }

    # 2. 식이 관리 (Dietary Management)
    dietary_management = {
        "avoid_foods": [],
        "hidden_sources": [],
        "cross_reactivity": [],
        "substitutes": [],
        "restaurant_cautions": [],
    }

    # 3. 응급 및 의료 (Emergency & Medical)
    emergency_medical = {
        "has_severe_allergy": False,
        "emergency_guidelines": EMERGENCY_GUIDELINES,
        "management_tips": [],
    }

    allergen_names = {
        "peanut": "땅콩", "milk": "우유", "egg": "계란",
        "wheat": "밀", "soy": "대두", "fish": "생선",
        "shellfish": "갑각류", "tree_nuts": "견과류", "sesame": "참깨",
        "dust_mite": "집먼지진드기", "pollen": "꽃가루",
        "mold": "곰팡이", "pet_dander": "반려동물",
        "cockroach": "바퀴벌레", "latex": "라텍스", "bee_venom": "벌독"
    }

    for allergen_code, grade in results.items():
        if grade == 0:
            continue

        allergen_info = get_allergen_prescription(allergen_code)
        if not allergen_info:
            continue

        allergen_name = allergen_names.get(allergen_code, allergen_code)

        # Determine severity grade range
        if grade >= 5:
            grade_range = "5-6"
            risk_level = "high_risk"
            emergency_medical["has_severe_allergy"] = True
        elif grade >= 3:
            grade_range = "3-4"
            risk_level = "moderate_risk" if grade == 3 else "high_risk"
            if grade >= 4:
                emergency_medical["has_severe_allergy"] = True
        else:
            grade_range = "1-2"
            risk_level = "low_risk" if grade == 1 else "moderate_risk"

        # Get symptoms for this grade
        symptoms_data = allergen_info.get("symptoms_by_grade", {}).get(grade_range, {})
        if symptoms_data:
            symptoms_risk[risk_level].append({
                "allergen": allergen_name,
                "allergen_code": allergen_code,
                "grade": grade,
                "severity": symptoms_data.get("severity", "unknown"),
                "symptoms": symptoms_data.get("symptoms", []),
            })

        # Collect dietary info (for food allergens)
        if allergen_info.get("category") == "food":
            if allergen_info.get("avoid_foods"):
                dietary_management["avoid_foods"].append({
                    "allergen": allergen_name,
                    "foods": allergen_info["avoid_foods"][:8],  # Top 8
                })

            if allergen_info.get("hidden_sources"):
                dietary_management["hidden_sources"].append({
                    "allergen": allergen_name,
                    "sources": allergen_info["hidden_sources"][:6],  # Top 6
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

            if allergen_info.get("restaurant_cautions"):
                dietary_management["restaurant_cautions"].extend([
                    f"({allergen_name}) {caution}"
                    for caution in allergen_info["restaurant_cautions"][:4]
                ])

        # Collect management tips (for inhalant allergens)
        if allergen_info.get("category") == "inhalant":
            if allergen_info.get("management_tips"):
                emergency_medical["management_tips"].append({
                    "allergen": allergen_name,
                    "tips": allergen_info["management_tips"][:6],
                })

    # Remove duplicates from restaurant cautions
    dietary_management["restaurant_cautions"] = list(
        dict.fromkeys(dietary_management["restaurant_cautions"])
    )[:10]

    return {
        "diagnosis_id": diagnosis_id,
        "diagnosis_date": diagnosis.diagnosis_date.isoformat(),
        "symptoms_risk": symptoms_risk,
        "dietary_management": dietary_management,
        "emergency_medical": emergency_medical,
    }


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
