"""알러젠 뉴스 검색 키워드 빌더.

`AllergenMaster.name_kr` / `name_en` 을 활용해 NewsAllergenLink 의 semantic
allergen_code (예: ``peanut``, ``dust_mite``) 단위로 뉴스 검색용 키워드 묶음을
조립한다.

`allergen-trend-followup-plan.md` §2 — "알러젠 전용 뉴스 검색 키워드 세트 구성"
구현 진입점.
"""
from __future__ import annotations

import logging
from typing import Optional

from sqlalchemy.orm import Session

from ..data.allergen_master import LEGACY_CODE_MAPPING
from ..database.allergen_models import AllergenMaster
from .ollama_service import OllamaService

logger = logging.getLogger(__name__)


# 활성 알러젠 마스터가 없을 때 사용할 폴백 키워드 (semantic_code → keywords).
# OllamaService._keyword_allergen_extract 와 동일한 매핑을 검색용으로 재사용.
_FALLBACK_KEYWORDS: dict[str, list[str]] = {
    "peanut": ["땅콩 알레르기", "peanut allergy"],
    "milk": ["우유 알레르기", "milk allergy"],
    "egg": ["계란 알레르기", "egg allergy"],
    "wheat": ["밀 알레르기", "wheat allergy", "글루텐"],
    "soy": ["대두 알레르기", "soy allergy"],
    "fish": ["생선 알레르기", "fish allergy"],
    "shrimp": ["새우 알레르기", "shrimp allergy"],
    "crab": ["게 알레르기", "crab allergy"],
    "peach": ["복숭아 알레르기", "peach allergy"],
    "walnut": ["호두 알레르기", "walnut allergy"],
    "sesame": ["참깨 알레르기", "sesame allergy"],
    "buckwheat": ["메밀 알레르기", "buckwheat allergy"],
    "dust_mite": ["집먼지진드기", "house dust mite allergy"],
    "cat": ["고양이 알레르기", "cat allergy"],
    "dog": ["개 알레르기", "dog allergy"],
    "mold": ["곰팡이 알레르기", "mold allergy"],
    "cedar": ["삼나무 알레르기", "cedar pollen allergy"],
    "birch": ["자작나무 알레르기", "birch pollen allergy"],
    "ragweed": ["돼지풀 알레르기", "ragweed allergy"],
}


def _semantic_code_to_immunocap(semantic_code: str) -> Optional[str]:
    """semantic code → AllergenMaster.code (ImmunoCAP) 매핑.

    LEGACY_CODE_MAPPING 은 ``"peanut": "f13"`` 형태이므로 직접 lookup.
    """
    return LEGACY_CODE_MAPPING.get(semantic_code)


def _format_search_keywords(name_kr: str, name_en: str) -> list[str]:
    """알러젠 이름에서 뉴스 검색에 쓸 키워드 변형 생성.

    예: ``("땅콩", "Peanut") → ["땅콩 알레르기", "peanut allergy"]``

    name_kr 에 괄호 (예: ``"집먼지진드기(Dp)"``) 가 있으면 base 만 사용.
    """
    base_kr = name_kr.split("(")[0].strip()
    base_en = name_en.split(",")[0].strip()  # 대표 영문명만

    keywords: list[str] = []
    if base_kr:
        keywords.append(f"{base_kr} 알레르기")
    if base_en:
        keywords.append(f"{base_en.lower()} allergy")
    return keywords


def build_allergen_search_keywords(
    db: Optional[Session] = None,
    allergen_codes: Optional[list[str]] = None,
) -> dict[str, list[str]]:
    """semantic allergen_code → 뉴스 검색 키워드 리스트.

    Args:
        db: DB 세션. None 이면 AllergenMaster 조회 없이 폴백만 사용.
        allergen_codes: 대상 semantic code 리스트.
            None 이면 ``OllamaService.KNOWN_ALLERGENS`` 전체.

    Returns:
        ``{"peanut": ["땅콩 알레르기", "peanut allergy"], ...}``
    """
    targets = allergen_codes or list(OllamaService.KNOWN_ALLERGENS)
    result: dict[str, list[str]] = {}

    master_by_code: dict[str, AllergenMaster] = {}
    if db is not None:
        immunocap_codes = [
            _semantic_code_to_immunocap(c) for c in targets
        ]
        immunocap_codes = [c for c in immunocap_codes if c]
        if immunocap_codes:
            rows = (
                db.query(AllergenMaster)
                .filter(
                    AllergenMaster.code.in_(immunocap_codes),
                    AllergenMaster.is_active == True,
                )
                .all()
            )
            master_by_code = {row.code: row for row in rows}

    for semantic_code in targets:
        keywords: list[str] = []
        immunocap = _semantic_code_to_immunocap(semantic_code)
        if immunocap and immunocap in master_by_code:
            row = master_by_code[immunocap]
            keywords = _format_search_keywords(row.name_kr, row.name_en)

        if not keywords:
            keywords = list(_FALLBACK_KEYWORDS.get(semantic_code, []))

        if keywords:
            result[semantic_code] = keywords
        else:
            logger.debug(
                "%s: 검색 키워드 없음 (AllergenMaster/폴백 모두 미매칭)",
                semantic_code,
            )

    return result
