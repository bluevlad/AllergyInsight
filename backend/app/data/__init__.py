"""알러지 처방 데이터 모듈

이 모듈은 두 가지 알러젠 데이터를 제공합니다:

1. allergen_master: 119종 알러젠 기본 정보 (코드, 이름, 카테고리)
   - 런타임 조회: DB 테이블 (allergen_master) → core.allergen.service
   - 시드 데이터 원본: ALLERGEN_MASTER_DB dict (seed_allergens.py에서 사용)
   - Enum/코드 매핑: AllergenCategory, AllergenType, LEGACY_CODE_MAPPING

2. allergen_prescription_db: 상세 처방 정보 (36종)
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
    ALLERGEN_MASTER_DB,  # 시드 데이터 원본 (런타임 조회는 DB 사용)
    AllergenCategory,
    AllergenType,
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
    # Master DB (시드 원본 + Enum + 코드 매핑)
    "ALLERGEN_MASTER_DB",
    "AllergenCategory",
    "AllergenType",
    "LEGACY_CODE_MAPPING",
    "get_legacy_code",
    "get_new_code",
    "get_prescription_code",
    "get_all_prescription_codes",
]
