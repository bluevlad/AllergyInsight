"""Core Allergen Module - 알러젠 데이터베이스

두 가지 데이터 소스를 제공합니다:

1. allergen_master: 120종 알러젠 기본 정보 (SGTi-Allergy Screen PLUS)
2. allergen_prescription_db: 상세 처방 정보 (16종)
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

# 상세 처방 정보 (기존)
from ...data.allergen_prescription_db import (
    # 알러젠 데이터
    FOOD_ALLERGENS,
    INHALANT_ALLERGENS,
    ALLERGEN_PRESCRIPTION_DB,
    CROSS_REACTIVITY_MAP,
    EMERGENCY_GUIDELINES,

    # 유틸리티 함수
    get_allergen_info,
    get_cross_reactivities,
    get_all_allergens,
    get_allergen_list,
)

# 119종 마스터 데이터
from ...data.allergen_master import (
    ALLERGEN_MASTER_DB,
    AllergenCategory,
    AllergenType,
    get_allergen_by_code,
    get_allergens_by_category,
    get_allergens_by_type,
    get_food_allergens as get_food_allergens_master,
    get_inhalant_allergens as get_inhalant_allergens_master,
    get_all_allergen_codes,
    get_allergen_count,
    search_allergens,
    get_allergen_summary,
    LEGACY_CODE_MAPPING,
    get_legacy_code,
    get_new_code,
    get_prescription_code,
    get_all_prescription_codes,
)

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

    # 119종 마스터 데이터
    "ALLERGEN_MASTER_DB",
    "AllergenCategory",
    "AllergenType",
    "get_allergen_by_code",
    "get_allergens_by_category",
    "get_allergens_by_type",
    "get_food_allergens_master",
    "get_inhalant_allergens_master",
    "get_all_allergen_codes",
    "get_allergen_count",
    "search_allergens",
    "get_allergen_summary",
    # 코드 매핑
    "LEGACY_CODE_MAPPING",
    "get_legacy_code",
    "get_new_code",
    "get_prescription_code",
    "get_all_prescription_codes",
]
