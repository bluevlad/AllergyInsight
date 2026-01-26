"""Consumer Guide Routes - 식품/생활 가이드 API

알러지 관리를 위한 가이드 정보를 제공합니다.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel

from ...database.connection import get_db
from ...database.models import User
from ...core.auth import require_consumer
from ...core.allergen import ALLERGEN_PRESCRIPTION_DB, get_allergen_info

router = APIRouter(prefix="/guide", tags=["Consumer - Guide"])


# ============================================================================
# Schemas
# ============================================================================

class FoodInfo(BaseModel):
    """식품 정보"""
    name: str
    category: str
    allergens: List[str]
    safe_alternatives: Optional[List[str]] = None

class SymptomInfo(BaseModel):
    """증상 정보"""
    name: str
    severity: str
    description: str
    action: str

class LifestyleTip(BaseModel):
    """생활 팁"""
    category: str
    title: str
    tips: List[str]


# ============================================================================
# Endpoints
# ============================================================================

@router.get("/foods")
async def get_food_guide(
    allergen_codes: Optional[str] = Query(None, description="콤마로 구분된 알러젠 코드"),
    user: User = Depends(require_consumer),
    db: Session = Depends(get_db)
):
    """회피 식품 및 대체 식품 가이드

    사용자의 양성 알러젠에 대한 식품 가이드를 제공합니다.
    """
    codes = allergen_codes.split(",") if allergen_codes else []

    avoid_foods = []
    substitutes = []
    hidden_sources = []

    # 코드가 없으면 모든 식품 알러젠 정보 반환
    if not codes:
        codes = ["peanut", "milk", "egg", "wheat", "soy", "fish", "shellfish", "tree_nuts", "sesame"]

    allergen_names = {
        "peanut": "땅콩", "milk": "우유", "egg": "계란",
        "wheat": "밀", "soy": "대두", "fish": "생선",
        "shellfish": "갑각류", "tree_nuts": "견과류", "sesame": "참깨",
    }

    for code in codes:
        info = get_allergen_info(code)
        if not info or info.get("category") != "food":
            continue

        name = allergen_names.get(code, code)

        if info.get("avoid_foods"):
            avoid_foods.append({
                "allergen": name,
                "allergen_code": code,
                "foods": info["avoid_foods"],
            })

        if info.get("substitutes"):
            for sub in info["substitutes"]:
                substitutes.append({
                    "allergen": name,
                    "allergen_code": code,
                    "original": sub.get("original", ""),
                    "alternatives": sub.get("alternatives", []),
                    "notes": sub.get("notes", ""),
                })

        if info.get("hidden_sources"):
            hidden_sources.append({
                "allergen": name,
                "allergen_code": code,
                "sources": info["hidden_sources"],
            })

    return {
        "avoid_foods": avoid_foods,
        "substitutes": substitutes,
        "hidden_sources": hidden_sources,
        "total_allergens": len(codes),
    }


@router.get("/symptoms")
async def get_symptoms_guide(
    allergen_codes: Optional[str] = Query(None, description="콤마로 구분된 알러젠 코드"),
    user: User = Depends(require_consumer),
    db: Session = Depends(get_db)
):
    """알러지 증상 정보 가이드"""
    codes = allergen_codes.split(",") if allergen_codes else []

    symptoms_by_severity = {
        "mild": [],
        "moderate": [],
        "severe": [],
    }

    allergen_names = {
        "peanut": "땅콩", "milk": "우유", "egg": "계란",
        "wheat": "밀", "soy": "대두", "fish": "생선",
        "shellfish": "갑각류", "tree_nuts": "견과류", "sesame": "참깨",
        "dust_mite": "집먼지진드기", "pollen": "꽃가루",
        "mold": "곰팡이", "pet_dander": "반려동물",
        "cockroach": "바퀴벌레", "latex": "라텍스", "bee_venom": "벌독"
    }

    if not codes:
        codes = list(allergen_names.keys())

    for code in codes:
        info = get_allergen_info(code)
        if not info:
            continue

        name = allergen_names.get(code, code)

        for grade_range, data in info.get("symptoms_by_grade", {}).items():
            severity = data.get("severity", "mild")
            if severity not in symptoms_by_severity:
                severity = "mild"

            symptoms_by_severity[severity].append({
                "allergen": name,
                "allergen_code": code,
                "grade_range": grade_range,
                "symptoms": data.get("symptoms", []),
            })

    return {
        "mild": symptoms_by_severity["mild"],
        "moderate": symptoms_by_severity["moderate"],
        "severe": symptoms_by_severity["severe"],
    }


@router.get("/lifestyle")
async def get_lifestyle_tips(
    allergen_codes: Optional[str] = Query(None, description="콤마로 구분된 알러젠 코드"),
    user: User = Depends(require_consumer),
    db: Session = Depends(get_db)
):
    """일상 생활 관리 팁"""
    codes = allergen_codes.split(",") if allergen_codes else []

    tips = []

    allergen_names = {
        "dust_mite": "집먼지진드기", "pollen": "꽃가루",
        "mold": "곰팡이", "pet_dander": "반려동물",
        "cockroach": "바퀴벌레",
    }

    # 흡입 알러젠이 없으면 모든 흡입 알러젠 팁 제공
    inhalant_codes = [c for c in codes if c in allergen_names]
    if not inhalant_codes:
        inhalant_codes = list(allergen_names.keys())

    for code in inhalant_codes:
        info = get_allergen_info(code)
        if not info or info.get("category") != "inhalant":
            continue

        name = allergen_names.get(code, code)

        if info.get("management_tips"):
            tips.append({
                "allergen": name,
                "allergen_code": code,
                "tips": info["management_tips"],
            })

    # 공통 생활 팁 추가
    common_tips = [
        {
            "category": "실내 환경",
            "title": "실내 공기 관리",
            "tips": [
                "정기적으로 환기하되 꽃가루 시즌에는 주의",
                "공기청정기 사용 (HEPA 필터 권장)",
                "습도 40-50% 유지",
                "카펫보다 마루 바닥 선호",
            ]
        },
        {
            "category": "청소",
            "title": "청소 습관",
            "tips": [
                "물걸레 청소 권장",
                "진공청소기는 HEPA 필터 장착",
                "침구류 주 1회 이상 55℃ 이상에서 세탁",
                "먼지가 쌓이기 쉬운 곳 정기 청소",
            ]
        },
        {
            "category": "외출",
            "title": "외출 시 주의사항",
            "tips": [
                "마스크 착용 (KF94 권장)",
                "꽃가루 시즌에는 외출 후 샤워",
                "외출복은 침실에 두지 않기",
                "응급약 항상 휴대",
            ]
        },
    ]

    return {
        "allergen_specific": tips,
        "common_tips": common_tips,
    }


@router.get("/cross-reactivity")
async def get_cross_reactivity_info(
    allergen_code: str = Query(..., description="알러젠 코드"),
    user: User = Depends(require_consumer),
    db: Session = Depends(get_db)
):
    """교차반응 정보 조회"""
    info = get_allergen_info(allergen_code)
    if not info:
        return {"cross_reactivity": [], "message": "알러젠 정보를 찾을 수 없습니다"}

    allergen_names = {
        "peanut": "땅콩", "milk": "우유", "egg": "계란",
        "wheat": "밀", "soy": "대두", "fish": "생선",
        "shellfish": "갑각류", "tree_nuts": "견과류", "sesame": "참깨",
    }

    cross_reactions = []
    for cross in info.get("cross_reactivity", []):
        cross_reactions.append({
            "from_allergen": allergen_names.get(allergen_code, allergen_code),
            "to_allergen": cross.get("allergen_kr", ""),
            "to_allergen_en": cross.get("allergen", ""),
            "probability": cross.get("probability", ""),
            "related_foods": cross.get("related_foods", []),
            "notes": cross.get("notes", ""),
        })

    return {
        "allergen_code": allergen_code,
        "allergen_name": allergen_names.get(allergen_code, allergen_code),
        "cross_reactivity": cross_reactions,
    }
