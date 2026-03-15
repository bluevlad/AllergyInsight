"""Core Allergen Module - 알러젠 데이터베이스

데이터 소스:
1. allergen_master 테이블 (DB): 119종 알러젠 기본 정보 → service.py로 조회
2. allergen_prescription_db (dict): 상세 처방 정보 (36종)
3. AllergenCategory/AllergenType Enum: 유효값 검증용
"""

# SGTi-Allergy Screen PLUS 기본 16종 한글 이름 매핑 (공통 참조용)
ALLERGEN_NAMES_KR: dict[str, str] = {
    "peanut": "땅콩", "milk": "우유", "egg": "계란",
    "wheat": "밀", "soy": "대두", "fish": "생선",
    "shellfish": "갑각류", "tree_nuts": "견과류", "sesame": "참깨",
    "dust_mite": "집먼지진드기", "pollen": "꽃가루",
    "mold": "곰팡이", "pet_dander": "반려동물",
    "cockroach": "바퀴벌레", "latex": "라텍스", "bee_venom": "벌독",
}

# 상세 처방 정보 (기존 dict 유지)
from ...data.allergen_prescription_db import (
    FOOD_ALLERGENS,
    INHALANT_ALLERGENS,
    ALLERGEN_PRESCRIPTION_DB,
    CROSS_REACTIVITY_MAP,
    EMERGENCY_GUIDELINES,
    get_allergen_info,
    get_cross_reactivities,
    get_all_allergens,
    get_allergen_list,
)

# Enum 및 코드 매핑 (유효값 검증 + prescription 연동)
from ...data.allergen_master import (
    AllergenCategory,
    AllergenType,
    LEGACY_CODE_MAPPING,
    get_legacy_code,
    get_new_code,
    get_prescription_code,
    get_all_prescription_codes,
)

# DB 기반 서비스
from . import service

__all__ = [
    # 공통 한글 이름 매핑
    "ALLERGEN_NAMES_KR",
    # 상세 처방 데이터 (36종)
    "FOOD_ALLERGENS",
    "INHALANT_ALLERGENS",
    "ALLERGEN_PRESCRIPTION_DB",
    "CROSS_REACTIVITY_MAP",
    "EMERGENCY_GUIDELINES",
    "get_allergen_info",
    "get_cross_reactivities",
    "get_all_allergens",
    "get_allergen_list",
    # Enum (유효값 검증용)
    "AllergenCategory",
    "AllergenType",
    # 코드 매핑
    "LEGACY_CODE_MAPPING",
    "get_legacy_code",
    "get_new_code",
    "get_prescription_code",
    "get_all_prescription_codes",
    # DB 서비스
    "service",
]
