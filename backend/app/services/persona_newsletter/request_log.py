"""뉴스레터 주제 요청 로깅 — 수요 신호 적재.

모든 topic-request 는 결과(coverage)와 함께 newsletter_topic_requests 에
기록된다. 이 로그가 Phase 4 운영자 제안의 학습 신호이자 멱등성의 근거다.
"""
from __future__ import annotations

import hashlib
import logging
from typing import Optional

from sqlalchemy.orm import Session

from ...database.persona_newsletter_models import NewsletterTopicRequest

logger = logging.getLogger(__name__)


def topic_hash(topic: Optional[str]) -> Optional[str]:
    """주제 정규화(strip+lower) 후 SHA-256 해시 — dedup·캐싱 키."""
    if not topic or not topic.strip():
        return None
    return hashlib.sha256(topic.strip().lower().encode("utf-8")).hexdigest()


def get_logged(db: Session, request_id: str) -> Optional[NewsletterTopicRequest]:
    """멱등성 — 동일 request_id 의 기존 로그 조회."""
    try:
        return (
            db.query(NewsletterTopicRequest)
            .filter(NewsletterTopicRequest.request_id == request_id)
            .first()
        )
    except Exception as e:  # noqa: BLE001
        logger.warning("토픽 요청 조회 실패: %s", e)
        return None


def log_request(
    db: Session,
    *,
    request_id: str,
    tenant_id: str,
    persona_code: str,
    request_type: str,
    topic: Optional[str],
    intent: Optional[dict],
    coverage: str,
    confidence: Optional[float],
    served: bool,
    fallback_reason: Optional[str],
    elapsed_ms: Optional[int],
) -> None:
    """요청·결과를 적재. 로깅 실패가 API 응답을 막지 않도록 예외 격리."""
    try:
        db.add(
            NewsletterTopicRequest(
                request_id=request_id,
                tenant_id=tenant_id,
                persona_code=persona_code,
                request_type=request_type,
                topic=(topic or None),
                topic_hash=topic_hash(topic),
                intent=intent,
                coverage=coverage,
                confidence=confidence,
                served=served,
                fallback_reason=fallback_reason,
                elapsed_ms=elapsed_ms,
            )
        )
        db.commit()
    except Exception as e:  # noqa: BLE001
        db.rollback()
        logger.warning("토픽 요청 로깅 실패 (무시): %s", e)
