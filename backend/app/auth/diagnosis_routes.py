"""Diagnosis Routes - User diagnosis history"""
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database.connection import get_db
from ..database.models import User, UserDiagnosis, DiagnosisKit, Paper, PaperAllergenLink
from .dependencies import require_auth
from .schemas import UserDiagnosisResponse, UserDiagnosisSummary
from ..data.allergen_prescription_db import (
    get_allergen_info as get_allergen_prescription,
    EMERGENCY_GUIDELINES
)

router = APIRouter(prefix="/diagnosis", tags=["Diagnosis"])


def get_citations_for_allergens(
    db: Session,
    allergen_codes: List[str],
    link_types: List[str] = None,
    limit_per_allergen: int = 3
) -> Dict[str, List[Dict[str, Any]]]:
    """Get citations for multiple allergens grouped by allergen code"""
    citations = {}

    for allergen_code in allergen_codes:
        query = db.query(Paper).join(PaperAllergenLink).filter(
            PaperAllergenLink.allergen_code == allergen_code,
            Paper.is_verified == True
        )

        if link_types:
            query = query.filter(PaperAllergenLink.link_type.in_(link_types))

        papers = query.order_by(
            PaperAllergenLink.relevance_score.desc(),
            Paper.year.desc()
        ).limit(limit_per_allergen).all()

        if papers:
            citations[allergen_code] = [
                {
                    "id": p.id,
                    "pmid": p.pmid,
                    "doi": p.doi,
                    "title": p.title,
                    "title_kr": p.title_kr,
                    "authors": p.authors,
                    "journal": p.journal,
                    "year": p.year,
                    "url": p.url,
                    "paper_type": p.paper_type,
                }
                for p in papers
            ]

    return citations


def get_citations_by_link_type(
    db: Session,
    allergen_codes: List[str],
    link_type: str,
    limit: int = 5
) -> List[Dict[str, Any]]:
    """Get citations for a specific link type across allergens"""
    from sqlalchemy import func, distinct

    # Subquery to get distinct paper IDs with max relevance score
    subq = db.query(
        PaperAllergenLink.paper_id,
        func.max(PaperAllergenLink.relevance_score).label('max_score')
    ).filter(
        PaperAllergenLink.allergen_code.in_(allergen_codes),
        PaperAllergenLink.link_type == link_type
    ).group_by(PaperAllergenLink.paper_id).subquery()

    papers = db.query(Paper).join(
        subq, Paper.id == subq.c.paper_id
    ).filter(
        Paper.is_verified == True
    ).order_by(
        subq.c.max_score.desc(),
        Paper.year.desc()
    ).limit(limit).all()

    return [
        {
            "id": p.id,
            "pmid": p.pmid,
            "doi": p.doi,
            "title": p.title,
            "title_kr": p.title_kr,
            "authors": p.authors,
            "journal": p.journal,
            "year": p.year,
            "url": p.url,
            "paper_type": p.paper_type,
        }
        for p in papers
    ]


def get_citations_by_specific_item(
    db: Session,
    allergen_code: str,
    specific_item: str,
    link_type: str = None,
    limit: int = 2
) -> List[Dict[str, Any]]:
    """Get citations for a specific item (symptom, food, etc.)"""
    query = db.query(Paper).join(PaperAllergenLink).filter(
        PaperAllergenLink.allergen_code == allergen_code,
        PaperAllergenLink.specific_item == specific_item,
        Paper.is_verified == True
    )

    if link_type:
        query = query.filter(PaperAllergenLink.link_type == link_type)

    papers = query.order_by(
        PaperAllergenLink.relevance_score.desc(),
        Paper.year.desc()
    ).limit(limit).all()

    return [
        {
            "id": p.id,
            "pmid": p.pmid,
            "title": p.title,
            "title_kr": p.title_kr,
            "authors": p.authors,
            "year": p.year,
            "url": p.url,
            "paper_type": p.paper_type,
        }
        for p in papers
    ]


def get_item_citations_batch(
    db: Session,
    items: List[Dict[str, str]],  # [{"allergen_code": ..., "specific_item": ..., "link_type": ...}]
    limit_per_item: int = 1
) -> Dict[str, List[Dict[str, Any]]]:
    """여러 항목에 대한 출처를 일괄 조회"""
    result = {}

    for item in items:
        key = f"{item['allergen_code']}:{item['specific_item']}"
        citations = get_citations_by_specific_item(
            db,
            allergen_code=item["allergen_code"],
            specific_item=item["specific_item"],
            link_type=item.get("link_type"),
            limit=limit_per_item
        )
        if citations:
            result[key] = citations

    return result


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
            # 증상별 출처 조회
            symptoms_with_citations = []
            for symptom in symptoms_data.get("symptoms", []):
                symptom_name = symptom.get("name", "") if isinstance(symptom, dict) else symptom
                symptom_citations = get_citations_by_specific_item(
                    db, allergen_code, symptom_name, "symptom", limit=1
                )
                symptom_entry = symptom.copy() if isinstance(symptom, dict) else {"name": symptom}
                symptom_entry["citations"] = symptom_citations
                symptoms_with_citations.append(symptom_entry)

            symptoms_risk[risk_level].append({
                "allergen": allergen_name,
                "allergen_code": allergen_code,
                "grade": grade,
                "severity": symptoms_data.get("severity", "unknown"),
                "symptoms": symptoms_with_citations,
            })

        # Collect dietary info (for food allergens)
        if allergen_info.get("category") == "food":
            if allergen_info.get("avoid_foods"):
                # 회피식품별 출처 조회
                foods_with_citations = []
                for food in allergen_info["avoid_foods"][:8]:
                    food_citations = get_citations_by_specific_item(
                        db, allergen_code, food, "dietary", limit=1
                    )
                    foods_with_citations.append({
                        "name": food,
                        "citations": food_citations
                    })
                dietary_management["avoid_foods"].append({
                    "allergen": allergen_name,
                    "allergen_code": allergen_code,
                    "foods": foods_with_citations,
                })

            if allergen_info.get("hidden_sources"):
                dietary_management["hidden_sources"].append({
                    "allergen": allergen_name,
                    "allergen_code": allergen_code,
                    "sources": allergen_info["hidden_sources"][:6],
                })

            if allergen_info.get("cross_reactivity"):
                for cross in allergen_info["cross_reactivity"]:
                    # 교차반응 출처 조회
                    cross_citations = get_citations_by_specific_item(
                        db, allergen_code, "교차반응", "cross_reactivity", limit=1
                    )
                    dietary_management["cross_reactivity"].append({
                        "from_allergen": allergen_name,
                        "from_allergen_code": allergen_code,
                        "to_allergen": cross.get("allergen_kr", ""),
                        "probability": cross.get("probability", ""),
                        "related_foods": cross.get("related_foods", [])[:5],
                        "citations": cross_citations,
                    })

            if allergen_info.get("substitutes"):
                for sub in allergen_info["substitutes"][:3]:
                    # 대체식품 출처 조회
                    sub_citations = get_citations_by_specific_item(
                        db, allergen_code, sub.get("original", ""), "substitute", limit=1
                    )
                    dietary_management["substitutes"].append({
                        "allergen": allergen_name,
                        "allergen_code": allergen_code,
                        "original": sub.get("original", ""),
                        "alternatives": sub.get("alternatives", []),
                        "notes": sub.get("notes", ""),
                        "citations": sub_citations,
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

    # Collect positive allergen codes for citation lookup
    positive_allergens = [code for code, grade in results.items() if grade > 0]

    # Get citations grouped by category
    citations = {
        "symptoms": get_citations_by_link_type(db, positive_allergens, "symptom", limit=5),
        "dietary": get_citations_by_link_type(db, positive_allergens, "dietary", limit=5),
        "cross_reactivity": get_citations_by_link_type(db, positive_allergens, "cross_reactivity", limit=3),
        "emergency": get_citations_by_link_type(db, positive_allergens, "emergency", limit=3),
        "by_allergen": get_citations_for_allergens(db, positive_allergens, limit_per_allergen=2),
    }

    # Count total citations
    total_citations = (
        len(citations["symptoms"]) +
        len(citations["dietary"]) +
        len(citations["cross_reactivity"]) +
        len(citations["emergency"])
    )

    return {
        "diagnosis_id": diagnosis_id,
        "diagnosis_date": diagnosis.diagnosis_date.isoformat(),
        "symptoms_risk": symptoms_risk,
        "dietary_management": dietary_management,
        "emergency_medical": emergency_medical,
        "citations": citations,
        "total_citations": total_citations,
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
