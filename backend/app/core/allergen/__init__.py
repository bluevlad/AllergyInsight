"""Core Allergen Module - 알러젠 데이터베이스

두 가지 데이터 소스를 제공합니다:

1. allergen_master: 120종 알러젠 기본 정보 (SGTi-Allergy Screen PLUS)
2. allergen_prescription_db: 상세 처방 정보 (16종)
"""

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
