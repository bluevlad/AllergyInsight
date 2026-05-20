"""페르소나 적응형 뉴스레터 공개 API — Phase 1 + Phase 2.

수신자의 역할·목적(페르소나)에 따라 콘텐츠를 선택·구성하고, 미보유 주제는
비동기 크롤로 확장한다. NewsletterPlatform 의 뉴스레터 Agent 가 호출한다.

- GET  /api/public/newsletter/personas             — 페르소나 카탈로그
- POST /api/public/newsletter/topic-request        — 역량 진단 + 콘텐츠 서빙
- GET  /api/public/newsletter/topic-request/{job}  — 크롤 확장 job 상태 조회

인증: 헤더 X-Newsletter-Key (env NEWSLETTER_API_KEY).
정본 API 계약: persona-adaptive-newsletter-plan.md §3.2.
"""
from __future__ import annotations

import logging
import time
from typing import Any, Literal, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, Header, HTTPException
from pydantic import BaseModel, Field, model_validator
from sqlalchemy.orm import Session

from ..config import settings
from ..database.connection import get_db
from ..database.persona_newsletter_models import CrawlExpansionJob, NewsletterPersona
from ..services.persona_newsletter import composer, crawl_job, feasibility
from ..services.persona_newsletter.request_log import (
    get_logged,
    log_request,
    topic_hash,
)

logger = logging.getLogger(__name__)

router = APIRouter()

DEFAULT_PERSONA_CODE = "patient"


# ---------------------------------------------------------------------------
# 인증
# ---------------------------------------------------------------------------
def require_newsletter_key(
    x_newsletter_key: Optional[str] = Header(default=None),
) -> bool:
    """X-Newsletter-Key 헤더 검증.

    env NEWSLETTER_API_KEY 미설정 시 503 — 무인증 노출 금지.
    """
    expected = getattr(settings, "NEWSLETTER_API_KEY", None)
    if not expected:
        raise HTTPException(
            status_code=503, detail="Newsletter API 인증이 구성되지 않았습니다"
        )
    if not x_newsletter_key or x_newsletter_key != expected:
        raise HTTPException(
            status_code=401, detail="유효하지 않은 X-Newsletter-Key"
        )
    return True


# ---------------------------------------------------------------------------
# 스키마
# ---------------------------------------------------------------------------
class SubscriberRef(BaseModel):
    """요청 시점 수신자 페르소나 컨텍스트 (구독자 정본은 NewsletterPlatform)."""

    persona_code: str = Field(min_length=1, max_length=30)
    depth: Optional[str] = None
    interests: list[str] = Field(default_factory=list)


class Intent(BaseModel):
    depth: Optional[str] = None
    language: Optional[str] = "ko"
    framing: Optional[str] = None


class TopicContext(BaseModel):
    current_content_ids: list[int] = Field(default_factory=list)
    section: Optional[str] = None
    # expandable 크롤 완료 시 역호출할 NewsletterPlatform webhook URL
    callback_url: Optional[str] = Field(default=None, max_length=1000)


class TopicRequestBody(BaseModel):
    """POST /topic-request 요청 본문."""

    request_id: str = Field(min_length=1, max_length=64)
    tenant_id: str = "allergy-insight"
    subscriber_ref: SubscriberRef
    request_type: Literal["select", "transform"]
    topic: Optional[str] = Field(default=None, max_length=500)
    intent: Optional[Intent] = None
    context: Optional[TopicContext] = None

    @model_validator(mode="after")
    def _require_topic_for_transform(self) -> "TopicRequestBody":
        if self.request_type == "transform" and not (
            self.topic and self.topic.strip()
        ):
            raise ValueError("transform 요청에는 topic 이 필요합니다")
        return self


# ---------------------------------------------------------------------------
# 헬퍼
# ---------------------------------------------------------------------------
def _resolve_persona(
    db: Session, code: str
) -> tuple[Optional[NewsletterPersona], bool]:
    """페르소나 조회. 미등록 시 기본 페르소나(patient)로 폴백.

    Returns:
        (persona, persona_fallback) — 폴백되었으면 True.
    """
    persona = (
        db.query(NewsletterPersona)
        .filter(
            NewsletterPersona.code == code,
            NewsletterPersona.is_active.is_(True),
        )
        .first()
    )
    if persona:
        return persona, False
    fallback = (
        db.query(NewsletterPersona)
        .filter(
            NewsletterPersona.code == DEFAULT_PERSONA_CODE,
            NewsletterPersona.is_active.is_(True),
        )
        .first()
    )
    return fallback, True


_FALLBACK_MESSAGES = {
    "out_of_domain": "요청하신 주제는 알러지·체외진단 도메인 범위를 벗어납니다.",
}


def _fallback_message(reason: Optional[str]) -> str:
    return _FALLBACK_MESSAGES.get(reason or "", "요청을 처리할 수 없습니다.")


def _expansion_block(job: CrawlExpansionJob) -> dict[str, Any]:
    """expandable 응답의 expansion 블록."""
    return {
        "feasible": True,
        "source": job.source,
        "job_id": job.job_id,
        "status": job.status,
        "eta_minutes": crawl_job.ETA_MINUTES,
    }


# ---------------------------------------------------------------------------
# 엔드포인트
# ---------------------------------------------------------------------------
@router.get("/personas")
def get_personas(
    db: Session = Depends(get_db),
    _auth: bool = Depends(require_newsletter_key),
) -> dict[str, Any]:
    """페르소나 카탈로그. NewsletterPlatform UI 의 역할·목적 선택지 구성용."""
    rows = (
        db.query(NewsletterPersona)
        .filter(NewsletterPersona.is_active.is_(True))
        .order_by(NewsletterPersona.display_order)
        .all()
    )
    personas: list[dict[str, Any]] = []
    for p in rows:
        weights = p.section_weights or {}
        recommended = [
            s.get("key")
            for s in sorted(
                weights.get("sections", []) or [],
                key=lambda s: -float(s.get("weight", 0) or 0),
            )
            if s.get("key")
        ]
        personas.append(
            {
                "code": p.code,
                "label": p.label,
                "description": p.description,
                "default_depth": p.default_depth,
                "recommended_sections": recommended,
            }
        )
    return {
        "data": {"personas": personas},
        "meta": {"version": "v1", "count": len(personas)},
    }


@router.post("/topic-request")
def post_topic_request(
    body: TopicRequestBody,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    _auth: bool = Depends(require_newsletter_key),
) -> dict[str, Any]:
    """역량 진단 + 콘텐츠 서빙 — covered / expandable / unsupported 3분기.

    - covered:     페르소나 가중치 기반 콘텐츠 즉시 반환.
    - expandable:  비동기 크롤 job 생성 후 expansion 블록 반환.
    - unsupported: fallback(대체 주제) 반환.

    멱등성: 동일 request_id 재요청 시 최초 진단·job 을 재사용한다.
    """
    started = time.monotonic()

    existing = get_logged(db, body.request_id)
    persona, persona_fallback = _resolve_persona(
        db, body.subscriber_ref.persona_code
    )
    if persona is None:
        raise HTTPException(
            status_code=503, detail="페르소나 카탈로그가 구성되지 않았습니다"
        )

    if existing is not None:
        # 멱등 — 재진단 금지, 최초 결과 재사용
        coverage = existing.coverage
        confidence = existing.confidence
        fallback_reason = existing.fallback_reason
        source: Optional[str] = None
    else:
        coverage, confidence, fallback_reason, source = feasibility.diagnose(
            db, topic=body.topic, request_type=body.request_type
        )

    response: dict[str, Any] = {
        "request_id": body.request_id,
        "coverage": coverage,
        "confidence": round(float(confidence or 0.0), 3),
    }
    served = False

    if coverage == "covered":
        sections = composer.compose(
            db, persona=persona, interests=body.subscriber_ref.interests
        )
        response["data"] = {"sections": sections}
        served = bool(sections)

    elif coverage == "expandable":
        # 멱등 — 기존 job 재사용, 없으면 생성 후 백그라운드 크롤 예약
        job = crawl_job.get_job_by_request(db, body.request_id)
        if job is None:
            callback_url = body.context.callback_url if body.context else None
            job = crawl_job.create_job(
                db,
                request_id=body.request_id,
                tenant_id=body.tenant_id,
                topic=body.topic or "",
                topic_hash=topic_hash(body.topic),
                source=source or feasibility.DEFAULT_EXPANSION_SOURCE,
                callback_url=callback_url,
            )
            background_tasks.add_task(crawl_job.run_expansion_job, job.job_id)
        response["expansion"] = _expansion_block(job)

    else:  # unsupported
        response["fallback"] = {
            "reason": fallback_reason,
            "message": _fallback_message(fallback_reason),
            "alternatives": composer.suggest_alternatives(db),
        }

    elapsed_ms = int((time.monotonic() - started) * 1000)
    meta: dict[str, Any] = {"elapsed_ms": elapsed_ms, "phase": "2"}
    if persona_fallback:
        meta["persona_fallback"] = True
    response["meta"] = meta

    if existing is None:
        log_request(
            db,
            request_id=body.request_id,
            tenant_id=body.tenant_id,
            persona_code=persona.code,
            request_type=body.request_type,
            topic=body.topic,
            intent=(body.intent.model_dump() if body.intent else None),
            coverage=coverage,
            confidence=confidence,
            served=served,
            fallback_reason=fallback_reason,
            elapsed_ms=elapsed_ms,
        )

    return response


@router.get("/topic-request/{job_id}")
def get_topic_request_job(
    job_id: str,
    db: Session = Depends(get_db),
    _auth: bool = Depends(require_newsletter_key),
) -> dict[str, Any]:
    """크롤 확장 job 상태 조회 — expandable 비동기 결과 폴링용."""
    job = (
        db.query(CrawlExpansionJob)
        .filter(CrawlExpansionJob.job_id == job_id)
        .first()
    )
    if job is None:
        raise HTTPException(status_code=404, detail="크롤 job 을 찾을 수 없습니다")
    return {
        "job_id": job.job_id,
        "request_id": job.request_id,
        "status": job.status,
        "topic": job.topic,
        "source": job.source,
        "result_summary": job.result_summary,
        "error": job.error,
        "eta_at": job.eta_at.isoformat() if job.eta_at else None,
        "finished_at": job.finished_at.isoformat() if job.finished_at else None,
    }
