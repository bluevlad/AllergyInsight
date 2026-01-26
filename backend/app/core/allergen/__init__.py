"""Core Allergen Module - 알러젠 데이터베이스

기존 data 모듈을 re-export합니다.
"""

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

__all__ = [
    # 데이터
    "FOOD_ALLERGENS",
    "INHALANT_ALLERGENS",
    "ALLERGEN_PRESCRIPTION_DB",
    "CROSS_REACTIVITY_MAP",
    "EMERGENCY_GUIDELINES",

    # 함수
    "get_allergen_info",
    "get_cross_reactivities",
    "get_all_allergens",
    "get_allergen_list",
]
