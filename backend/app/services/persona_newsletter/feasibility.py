"""역량 진단 — Phase 1: covered / unsupported 2분기 (LLM 미사용).

- select 요청: 제시 데이터 선택 → 항상 covered.
- transform 요청: RAG 검색 score≥0.6 시 covered.
  도메인 밖 → out_of_domain, 도메인 내 미보유 → not_indexed_yet.

expandable(크롤 확장) 판정과 LLM 도메인 분류는 Phase 2에서 도입한다.
"""
from __future__ import annotations

import logging
from typing import Callable, Optional

from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

# RAG 검색 강한 매칭 임계값 — 이 이상이면 인덱스 보유로 판정
STRONG_SCORE = 0.6

# 알러지 / 체외진단 도메인 핵심어 — 키워드 휴리스틱 (LLM 미사용)
_DOMAIN_TERMS: frozenset[str] = frozenset(
    {
        "알러지", "알레르기", "allergy", "allergic", "ige", "면역글로불린",
        "아나필락시스", "anaphylaxis", "면역요법", "immunotherapy",
        "진단키트", "체외진단", "ivd", "in vitro", "알러젠", "알레르겐",
        "allergen", "감작", "sensitization", "피부단자", "skin prick",
        "아토피", "atopic", "천식", "asthma", "비염", "rhinitis",
        "식품알레르기", "식품알러지", "food allergy", "두드러기", "urticaria",
        "면역", "immuno",
    }
)


def _in_allergy_domain(topic: str, db: Session) -> bool:
    """알러지/체외진단 도메인 여부 — 키워드 휴리스틱 (LLM 미사용).

    핵심어 사전 + AllergenMaster 등록 알러젠명 부분일치.
    """
    text = topic.lower()
    if any(term in text for term in _DOMAIN_TERMS):
        return True
    try:
        from ...database.allergen_models import AllergenMaster

        rows = db.query(AllergenMaster.name_kr, AllergenMaster.name_en).all()
        for name_kr, name_en in rows:
            if name_kr and name_kr.lower() in text:
                return True
            if name_en and len(name_en) >= 3 and name_en.lower() in text:
                return True
    except Exception as e:  # noqa: BLE001
        logger.warning("도메인 판정 중 알러젠 조회 실패 (무시): %s", e)
    return False


def _default_search(query: str, n_results: int = 5) -> list[dict]:
    """기본 RAG 검색 — ChromaDB 미가용 시 빈 리스트로 graceful degrade."""
    try:
        from ...services.rag_service import get_rag_service

        return get_rag_service().search(query, n_results=n_results) or []
    except Exception as e:  # noqa: BLE001
        logger.warning("RAG 검색 불가 — 빈 결과 폴백: %s", e)
        return []


def diagnose(
    db: Session,
    *,
    topic: Optional[str],
    request_type: str,
    search_fn: Optional[Callable[[str, int], list[dict]]] = None,
) -> tuple[str, float, Optional[str]]:
    """역량 진단.

    Args:
        topic: 변형 요청 주제 (select 요청은 무시).
        request_type: 'select' | 'transform'.
        search_fn: RAG 검색 주입 (테스트용). 기본은 실 RAG.

    Returns:
        (coverage, confidence, fallback_reason)
        coverage ∈ {'covered', 'unsupported'} — Phase 1 (expandable 없음).
    """
    if request_type == "select":
        return ("covered", 1.0, None)

    # request_type == "transform"
    cleaned = (topic or "").strip()
    if not cleaned:
        return ("unsupported", 0.0, "out_of_domain")

    search = search_fn or _default_search
    try:
        hits = search(cleaned, 5) or []
    except Exception as e:  # noqa: BLE001
        logger.warning("RAG 검색 예외 — 빈 결과 처리: %s", e)
        hits = []

    strong = [h for h in hits if float(h.get("score") or 0.0) >= STRONG_SCORE]
    if strong:
        avg = sum(float(h["score"]) for h in strong) / len(strong)
        return ("covered", min(avg * 1.2, 1.0), None)

    if not _in_allergy_domain(cleaned, db):
        return ("unsupported", 0.0, "out_of_domain")

    # 도메인 내부지만 인덱스 미보유 — Phase 1 은 크롤 확장 없음
    return ("unsupported", 0.0, "not_indexed_yet")
