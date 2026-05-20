"""수요 분석 + 운영자 고도화 제안 — Phase 4.

newsletter_topic_requests + newsletter_engagements 를 집계해 미충족 수요를
식별하고 운영자용 EvolutionProposal 을 생성한다. 제안 본문은 LLM 으로 작성하되
LLM 미가용 시 템플릿으로 graceful degrade 한다.
"""
from __future__ import annotations

import logging
import os
from collections import Counter
from datetime import date, datetime, timedelta
from typing import Any, Callable, Optional

from sqlalchemy.orm import Session

from ...database.persona_newsletter_models import (
    EvolutionProposal,
    NewsletterEngagement,
    NewsletterTopicRequest,
)
from ...utils.timezone import utc_now

logger = logging.getLogger(__name__)

_LLMOPS_CONSUMER = "allergyinsight-evolution-proposal"
_MAX_TOKENS = 400

# 제안 생성 임계값 — 동일 주제가 기간 내 N회 이상 반복되면 신호로 본다
UNSUPPORTED_THRESHOLD = 2
EXPANDABLE_THRESHOLD = 3

_MODEL_NAME = os.environ.get("GEMINI_MODEL") or os.environ.get(
    "LLM_MODEL", "gemini-2.5-flash"
)

_PROPOSAL_TEMPLATES = {
    "new_source": (
        "미충족 주제 '{topic}' 가 최근 {count}회 요청되었습니다. 이 주제를 다룰 "
        "신규 크롤 소스/커넥터 추가를 검토하세요."
    ),
    "keyword_expansion": (
        "확장 후보 주제 '{topic}' 가 최근 {count}회 요청되었습니다. 알러젠 뉴스 "
        "키워드 레지스트리 보강 또는 우선 인덱싱을 검토하세요."
    ),
}


# ---------------------------------------------------------------------------
# 인게이지먼트 수집
# ---------------------------------------------------------------------------
def record_engagements(
    db: Session, *, tenant_id: str, events: list[dict]
) -> int:
    """오픈·클릭 이벤트 적재. 적재 건수 반환."""
    recorded = 0
    for ev in events:
        event_type = (ev.get("event") or "").strip()
        if event_type not in ("open", "click"):
            continue
        occurred_dt: Optional[datetime] = None
        raw = ev.get("occurred_at")
        if raw:
            try:
                occurred_dt = datetime.fromisoformat(
                    str(raw).replace("Z", "+00:00")
                )
            except ValueError:
                occurred_dt = None
        db.add(
            NewsletterEngagement(
                tenant_id=tenant_id or "allergy-insight",
                persona_code=(ev.get("persona_code") or None),
                section_type=(ev.get("section_type") or None),
                content_ref=(ev.get("content_ref") or None),
                event=event_type,
                occurred_at=occurred_dt,
            )
        )
        recorded += 1
    if recorded:
        try:
            db.commit()
        except Exception as e:  # noqa: BLE001
            db.rollback()
            logger.warning("인게이지먼트 적재 실패: %s", e)
            return 0
    return recorded


# ---------------------------------------------------------------------------
# 수요 분석
# ---------------------------------------------------------------------------
def analyze_demand(db: Session, since_days: int = 30) -> dict[str, Any]:
    """수요 로그·인게이지먼트 집계 → demand summary."""
    since = utc_now() - timedelta(days=since_days)
    reqs = (
        db.query(NewsletterTopicRequest)
        .filter(NewsletterTopicRequest.created_at >= since)
        .all()
    )

    def _clusters(coverage_value: str) -> list[dict]:
        by_hash: dict[str, dict] = {}
        for r in reqs:
            if r.coverage != coverage_value or not r.topic_hash:
                continue
            c = by_hash.setdefault(
                r.topic_hash, {"topic": r.topic, "count": 0}
            )
            c["count"] += 1
        return sorted(by_hash.values(), key=lambda c: -c["count"])

    engagements = (
        db.query(NewsletterEngagement)
        .filter(NewsletterEngagement.created_at >= since)
        .all()
    )

    return {
        "since_days": since_days,
        "total_requests": len(reqs),
        "coverage_counts": dict(Counter(r.coverage for r in reqs)),
        "persona_counts": dict(Counter(r.persona_code for r in reqs)),
        "unsupported_clusters": _clusters("unsupported"),
        "expandable_clusters": _clusters("expandable"),
        "engagement_counts": dict(Counter(e.event for e in engagements)),
        "engagement_by_section": dict(
            Counter(e.section_type for e in engagements if e.section_type)
        ),
    }


# ---------------------------------------------------------------------------
# 제안 생성
# ---------------------------------------------------------------------------
def _llm_proposal(prompt: str) -> Optional[str]:
    """제안 본문 LLM 생성 — 미가용 시 None. 테스트에서 monkeypatch."""
    try:
        from ...services.ollama_service import get_ollama_service

        return get_ollama_service()._chat(
            prompt, max_tokens=_MAX_TOKENS, provider="news"
        )
    except Exception as e:  # noqa: BLE001
        logger.warning("제안 LLM 생성 불가: %s", e)
        return None


def _recommended_action(
    proposal_type: str,
    cluster: dict,
    llm_fn: Optional[Callable[[str], Optional[str]]],
) -> str:
    """제안 조치 문구 — LLM 우선, 실패 시 템플릿."""
    topic = cluster.get("topic") or "(미상 주제)"
    template = _PROPOSAL_TEMPLATES[proposal_type].format(
        topic=topic, count=cluster["count"]
    )
    generate = llm_fn or _llm_proposal
    prompt = (
        f"알러지 정보 서비스의 수요 신호: 주제 '{topic}' 가 최근 "
        f"{cluster['count']}회 요청되었으나 충분히 다루지 못했다.\n"
        f"운영자가 취할 구체적 조치를 2~3문장으로 한국어로 제안하라."
    )
    try:
        text = generate(prompt)
    except Exception as e:  # noqa: BLE001
        logger.warning("제안 생성 실패 — 템플릿 사용: %s", e)
        text = None
    return (text or "").strip() or template


def generate_proposals(
    db: Session,
    since_days: int = 30,
    llm_fn: Optional[Callable[[str], Optional[str]]] = None,
) -> list[EvolutionProposal]:
    """수요 분석 → EvolutionProposal 생성. pending 중복은 제목 기준 스킵.

    Returns: 새로 생성된 제안 목록.
    """
    summary = analyze_demand(db, since_days)
    period_end = date.today()
    period_start = period_end - timedelta(days=since_days)

    candidates: list[tuple[str, dict, str]] = []
    for cluster in summary["unsupported_clusters"]:
        if cluster["count"] >= UNSUPPORTED_THRESHOLD:
            candidates.append(("new_source", cluster, "high"))
    for cluster in summary["expandable_clusters"]:
        if cluster["count"] >= EXPANDABLE_THRESHOLD:
            candidates.append(("keyword_expansion", cluster, "medium"))

    created: list[EvolutionProposal] = []
    for proposal_type, cluster, priority in candidates[:10]:
        topic = cluster.get("topic") or "(미상 주제)"
        title = f"[{proposal_type}] {topic[:120]}"
        # pending 중복 스킵
        dup = (
            db.query(EvolutionProposal)
            .filter(
                EvolutionProposal.title == title,
                EvolutionProposal.status == "pending",
            )
            .first()
        )
        if dup is not None:
            continue
        proposal = EvolutionProposal(
            period_start=period_start,
            period_end=period_end,
            proposal_type=proposal_type,
            title=title,
            recommended_action=_recommended_action(
                proposal_type, cluster, llm_fn
            ),
            evidence={
                "cluster": cluster,
                "coverage_counts": summary["coverage_counts"],
            },
            priority=priority,
            status="pending",
        )
        db.add(proposal)
        created.append(proposal)

    if created:
        try:
            db.commit()
            for p in created:
                db.refresh(p)
        except Exception as e:  # noqa: BLE001
            db.rollback()
            logger.error("제안 적재 실패: %s", e)
            return []
    return created
