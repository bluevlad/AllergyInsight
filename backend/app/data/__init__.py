"""알러지 처방 데이터 모듈"""
from .allergen_prescription_db import (
    ALLERGEN_PRESCRIPTION_DB,
    FOOD_ALLERGENS,
    INHALANT_ALLERGENS,
    CROSS_REACTIVITY_MAP,
    EMERGENCY_GUIDELINES,
    get_allergen_info,
    get_cross_reactivities,
)

__all__ = [
    "ALLERGEN_PRESCRIPTION_DB",
    "FOOD_ALLERGENS",
    "INHALANT_ALLERGENS",
    "CROSS_REACTIVITY_MAP",
    "EMERGENCY_GUIDELINES",
    "get_allergen_info",
    "get_cross_reactivities",
]
