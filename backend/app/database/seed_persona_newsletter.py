"""페르소나 적응형 뉴스레터 — 페르소나 카탈로그 시드 v1 (6종).

idempotent — code 기준 upsert. 앱 startup 또는 수동 실행으로 호출.
페르소나 정의 근거: persona-adaptive-newsletter-phase1-design.md §4.3
"""
from __future__ import annotations

import logging

from sqlalchemy.orm import Session

from .persona_newsletter_models import NewsletterPersona

logger = logging.getLogger(__name__)


# 페르소나 v1 — 역할 × 깊이 × 콘텐츠 가중치 행렬
PERSONAS_V1: list[dict] = [
    {
        "code": "clinician",
        "label": "임상의(의사)",
        "description": "가이드라인 변경·근거 논문·진단 알고리즘 중심. 간결·근거 인용.",
        "default_depth": "expert",
        "guardrail_profile": "professional",
        "display_order": 1,
        "section_weights": {
            "sections": [
                {"key": "guideline", "weight": 1.0, "max_items": 5},
                {"key": "papers", "weight": 0.9, "max_items": 8},
                {"key": "headlines", "weight": 0.6, "max_items": 5},
                {"key": "industry", "weight": 0.3, "max_items": 3},
            ],
            "category_boost": {
                "regulation": 0.30,
                "diagnosis_method": 0.25,
                "treatment": 0.20,
                "research": 0.15,
            },
            "exclude_categories": [],
        },
    },
    {
        "code": "lab",
        "label": "검사실(임상병리사)",
        "description": "진단키트 신기술·검사법·규제 승인 중심. 실무·QC 관점.",
        "default_depth": "practical",
        "guardrail_profile": "professional",
        "display_order": 2,
        "section_weights": {
            "sections": [
                {"key": "diagnosis_news", "weight": 1.0, "max_items": 6},
                {"key": "regulation_news", "weight": 0.9, "max_items": 5},
                {"key": "headlines", "weight": 0.6, "max_items": 5},
                {"key": "papers", "weight": 0.5, "max_items": 5},
                {"key": "industry", "weight": 0.4, "max_items": 3},
            ],
            "category_boost": {
                "diagnosis_method": 0.40,
                "regulatory": 0.30,
                "regulation": 0.30,
                "product": 0.20,
            },
            "exclude_categories": [],
        },
    },
    {
        "code": "hospital_admin",
        "label": "병원 관리자",
        "description": "시장·수가·경쟁 동향 중심. 경영 브리핑 관점.",
        "default_depth": "practical",
        "guardrail_profile": "professional",
        "display_order": 3,
        "section_weights": {
            "sections": [
                {"key": "industry", "weight": 1.0, "max_items": 6},
                {"key": "regulation_news", "weight": 0.6, "max_items": 4},
                {"key": "headlines", "weight": 0.5, "max_items": 5},
                {"key": "papers", "weight": 0.3, "max_items": 3},
            ],
            "category_boost": {
                "market": 0.35,
                "financial": 0.30,
                "regulatory": 0.20,
                "regulation": 0.20,
            },
            "exclude_categories": [],
        },
    },
    {
        "code": "patient",
        "label": "일반 환자·보호자",
        "description": "생활관리·알러젠 회피·역학 중심. 쉬운 언어·강한 면책.",
        "default_depth": "general",
        "guardrail_profile": "consumer",
        "display_order": 4,
        "section_weights": {
            "sections": [
                {"key": "treatment_news", "weight": 1.0, "max_items": 6},
                {"key": "headlines", "weight": 0.5, "max_items": 5},
                {"key": "papers", "weight": 0.4, "max_items": 4},
            ],
            "category_boost": {"treatment": 0.40, "epidemiology": 0.30},
            "exclude_categories": ["financial", "partnership", "competitor"],
        },
    },
    {
        "code": "researcher",
        "label": "연구자",
        "description": "메타분석·preprint·최신 트렌드 중심. 깊이·레퍼런스.",
        "default_depth": "expert",
        "guardrail_profile": "professional",
        "display_order": 5,
        "section_weights": {
            "sections": [
                {"key": "papers", "weight": 1.0, "max_items": 12},
                {"key": "headlines", "weight": 0.3, "max_items": 4},
                {"key": "industry", "weight": 0.2, "max_items": 2},
            ],
            "category_boost": {"research": 0.40, "technology": 0.20},
            "exclude_categories": [],
        },
    },
    {
        "code": "industry",
        "label": "기업 IR·투자자",
        "description": "M&A·투자·파트너십 중심. 동향 브리핑.",
        "default_depth": "practical",
        "guardrail_profile": "professional",
        "display_order": 6,
        "section_weights": {
            "sections": [
                {"key": "industry", "weight": 1.0, "max_items": 8},
                {"key": "headlines", "weight": 0.5, "max_items": 5},
                {"key": "regulation_news", "weight": 0.5, "max_items": 4},
            ],
            "category_boost": {
                "financial": 0.40,
                "partnership": 0.35,
                "market": 0.30,
            },
            "exclude_categories": [],
        },
    },
]

# upsert 시 갱신 대상 필드 (code 는 키이므로 제외)
_UPDATABLE_FIELDS = (
    "label",
    "description",
    "default_depth",
    "guardrail_profile",
    "section_weights",
    "display_order",
)


def seed_persona_newsletter(db: Session | None = None) -> int:
    """페르소나 카탈로그 시드 (idempotent upsert).

    Returns:
        upsert 처리된 페르소나 수 (실패 시 0).
    """
    should_close = False
    if db is None:
        from .connection import SessionLocal

        db = SessionLocal()
        should_close = True

    count = 0
    try:
        for spec in PERSONAS_V1:
            existing = (
                db.query(NewsletterPersona)
                .filter(NewsletterPersona.code == spec["code"])
                .first()
            )
            if existing:
                for field in _UPDATABLE_FIELDS:
                    setattr(existing, field, spec[field])
                existing.is_active = True
            else:
                db.add(NewsletterPersona(is_active=True, **spec))
            count += 1
        db.commit()
        logger.info("뉴스레터 페르소나 시드 완료: %d종", count)
    except Exception as e:  # noqa: BLE001
        db.rollback()
        logger.error("뉴스레터 페르소나 시드 실패: %s", e)
        count = 0
    finally:
        if should_close:
            db.close()
    return count
