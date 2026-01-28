"""알러지 처방 데이터 모듈

이 모듈은 두 가지 알러젠 데이터를 제공합니다:

1. allergen_master: 120종 알러젠 기본 정보 (코드, 이름, 카테고리)
   - SGTi-Allergy Screen PLUS 진단키트 기준
   - 진단 결과 저장/조회에 사용

2. allergen_prescription_db: 상세 처방 정보 (16종)
   - 회피 식품, 대체 식품, 증상, 교차반응 등
   - 환자 가이드 생성에 사용
"""
from .allergen_prescription_db import (
    ALLERGEN_PRESCRIPTION_DB,
    FOOD_ALLERGENS,
    INHALANT_ALLERGENS,
    CROSS_REACTIVITY_MAP,
    EMERGENCY_GUIDELINES,
    get_allergen_info,
    get_cross_reactivities,
)

from .allergen_master import (
    ALLERGEN_MASTER_DB,
    AllergenCategory,
    AllergenType,
    get_allergen_by_code,
    get_allergens_by_category,
    get_allergens_by_type,
    get_food_allergens,
    get_inhalant_allergens,
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
    # Prescription DB (상세 처방 정보 - 36종)
    "ALLERGEN_PRESCRIPTION_DB",
    "FOOD_ALLERGENS",
    "INHALANT_ALLERGENS",
    "CROSS_REACTIVITY_MAP",
    "EMERGENCY_GUIDELINES",
    "get_allergen_info",
    "get_cross_reactivities",
    # Master DB (119종 기본 정보)
    "ALLERGEN_MASTER_DB",
    "AllergenCategory",
    "AllergenType",
    "get_allergen_by_code",
    "get_allergens_by_category",
    "get_allergens_by_type",
    "get_food_allergens",
    "get_inhalant_allergens",
    "get_all_allergen_codes",
    "get_allergen_count",
    "search_allergens",
    "get_allergen_summary",
    # 코드 매핑 (Master ↔ Prescription)
    "LEGACY_CODE_MAPPING",
    "get_legacy_code",
    "get_new_code",
    "get_prescription_code",
    "get_all_prescription_codes",
]
