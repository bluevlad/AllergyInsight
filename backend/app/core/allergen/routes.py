"""알러젠 마스터 데이터 API

119종 알러젠 기본 정보를 DB에서 조회하는 API 엔드포인트입니다.
"""
from typing import Optional, List
from fastapi import APIRouter, Query, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ...database.connection import get_db
from ...database.allergen_models import AllergenMaster
from ...data.allergen_master import AllergenCategory, AllergenType
from ...data.allergen_prescription_db import ALLERGEN_PRESCRIPTION_DB
from . import service as allergen_service

router = APIRouter(prefix="/allergens", tags=["Allergens"])


# ============================================================================
# Schemas
# ============================================================================

class AllergenResponse(BaseModel):
    """알러젠 정보 응답"""
    code: str
    name_kr: str
    name_en: str
    category: str
    type: str
    description: Optional[str] = None
    note: Optional[str] = None
    has_prescription: bool = False


class AllergenListResponse(BaseModel):
    """알러젠 목록 응답"""
    items: List[AllergenResponse]
    total: int


class AllergenSummaryResponse(BaseModel):
    """알러젠 요약 통계"""
    total: int
    by_category: dict
    by_type: dict


class AllergenSearchResponse(BaseModel):
    """알러젠 검색 결과"""
    query: str
    results: List[AllergenResponse]
    count: int


# ============================================================================
# Helper Functions
# ============================================================================

def _has_prescription(code: str, name_en: str) -> bool:
    """처방 정보 존재 여부 확인"""
    return (
        code in ALLERGEN_PRESCRIPTION_DB or
        name_en.lower().replace(" ", "_") in ALLERGEN_PRESCRIPTION_DB
    )


def allergen_to_response(allergen: AllergenMaster) -> AllergenResponse:
    """AllergenMaster ORM 객체를 응답 모델로 변환"""
    return AllergenResponse(
        code=allergen.code,
        name_kr=allergen.name_kr,
        name_en=allergen.name_en,
        category=allergen.category,
        type=allergen.type,
        description=allergen.description,
        note=allergen.note,
        has_prescription=_has_prescription(allergen.code, allergen.name_en),
    )


# ============================================================================
# Endpoints
# ============================================================================

@router.get("/", response_model=AllergenListResponse)
async def list_allergens(
    category: Optional[str] = Query(None, description="카테고리 필터 (예: mite, tree, egg_dairy)"),
    type: Optional[str] = Query(None, description="타입 필터 (food, inhalant, contact, venom)"),
    limit: int = Query(200, ge=1, le=500, description="최대 반환 개수"),
    offset: int = Query(0, ge=0, description="건너뛸 개수"),
    db: Session = Depends(get_db),
):
    """
    알러젠 목록 조회

    119종 알러젠 기본 정보를 조회합니다.
    카테고리 또는 타입으로 필터링할 수 있습니다.
    """
    items, total = allergen_service.list_allergens(
        db, category=category, allergen_type=type, limit=limit, offset=offset,
    )

    return AllergenListResponse(
        items=[allergen_to_response(a) for a in items],
        total=total,
    )


@router.get("/summary", response_model=AllergenSummaryResponse)
async def get_summary(db: Session = Depends(get_db)):
    """
    알러젠 요약 통계

    전체 알러젠 수, 카테고리별/타입별 분포를 반환합니다.
    """
    return allergen_service.get_summary(db)


@router.get("/search", response_model=AllergenSearchResponse)
async def search(
    q: str = Query(..., min_length=1, description="검색어 (한글명, 영문명, 코드)"),
    db: Session = Depends(get_db),
):
    """
    알러젠 검색

    한글명, 영문명, 코드로 알러젠을 검색합니다.
    """
    results = allergen_service.search_allergens(db, q)
    items = [allergen_to_response(a) for a in results]

    return AllergenSearchResponse(
        query=q,
        results=items,
        count=len(items),
    )


@router.get("/codes")
async def list_codes(db: Session = Depends(get_db)):
    """
    알러젠 코드 목록

    전체 알러젠 코드 목록을 반환합니다.
    """
    codes = allergen_service.get_all_codes(db)
    return {
        "codes": codes,
        "count": len(codes),
    }


@router.get("/categories")
async def list_categories():
    """
    알러젠 카테고리 목록

    사용 가능한 카테고리와 각 카테고리의 한글명을 반환합니다.
    """
    category_names = {
        "mite": "진드기",
        "dust": "집먼지",
        "animal": "동물/비듬/상피",
        "insect": "벌독/곤충",
        "latex": "라텍스",
        "microorganism": "미생물",
        "tree": "나무",
        "grass": "목초",
        "weed": "잡초",
        "other": "기타",
        "egg_dairy": "알/유제품",
        "crustacean": "갑각류",
        "fish_shellfish": "어패류",
        "vegetable": "채소",
        "meat": "육류",
        "fruit": "과일",
        "seed_nut": "씨/견과류",
    }

    return {
        "categories": [
            {"code": cat.value, "name_kr": category_names.get(cat.value, cat.value)}
            for cat in AllergenCategory
        ]
    }


@router.get("/types")
async def list_types():
    """
    알러젠 타입 목록

    사용 가능한 타입 (식품, 흡입성, 접촉성, 독소)을 반환합니다.
    """
    type_names = {
        "food": "식품",
        "inhalant": "흡입성",
        "contact": "접촉성",
        "venom": "독소",
    }

    return {
        "types": [
            {"code": t.value, "name_kr": type_names.get(t.value, t.value)}
            for t in AllergenType
        ]
    }


@router.get("/{code}", response_model=AllergenResponse)
async def get_allergen(code: str, db: Session = Depends(get_db)):
    """
    알러젠 상세 조회

    코드로 특정 알러젠 정보를 조회합니다.
    """
    allergen = allergen_service.get_by_code(db, code)

    if not allergen:
        raise HTTPException(404, f"알러젠을 찾을 수 없습니다: {code}")

    return allergen_to_response(allergen)
