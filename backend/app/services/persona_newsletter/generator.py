"""페르소나 조건부 콘텐츠 생성 — Phase 3.

페르소나별 시스템 프롬프트 + 역할별 가드레일로 LLM 이 섹션 편집 요약(editorial)을
생성한다. 결과는 newsletter_content_blocks 에 (페르소나 × 일자) 단위로 1회 캐시한다
— 세그먼트 단위 생성 (수신자 1인 단위 LLM 호출 금지).

LLM 미가용 시 graceful degrade (editorial=None — 섹션만 제공).
"""
from __future__ import annotations

import logging
import os
import time
from datetime import date
from typing import Any, Callable, Optional

from sqlalchemy.orm import Session

from ...database.persona_newsletter_models import NewsletterContentBlock
from ...utils.timezone import utc_now

logger = logging.getLogger(__name__)

_LLMOPS_CONSUMER = "allergyinsight-persona-compose"
_MAX_TOKENS = 600
_MAX_CONTEXT_ITEMS = 12

# 역할별 가드레일 — 생성 프롬프트에 주입
_GUARDRAILS = {
    "consumer": (
        "독자는 일반 환자·보호자다. 쉬운 일상 언어로 쓰고, 의학적 진단이나 약물 "
        "추천을 하지 말 것. 단정적 표현을 피하라. 마지막 문장에 '본 내용은 참고용이며 "
        "정확한 진단·치료는 의료진과 상담하세요.' 를 포함하라."
    ),
    "professional": (
        "독자는 의료·검사·산업 전문가다. 간결하고 근거 중심으로 쓰되, 제시된 항목 "
        "범위를 벗어난 단정은 하지 말 것."
    ),
}

_MODEL_NAME = os.environ.get("GEMINI_MODEL") or os.environ.get(
    "LLM_MODEL", "gemini-2.5-flash"
)


def _llm_generate(prompt: str) -> Optional[str]:
    """LLM 텍스트 생성 — 미가용 시 None. 테스트에서 monkeypatch."""
    try:
        from ...services.ollama_service import get_ollama_service

        return get_ollama_service()._chat(
            prompt, max_tokens=_MAX_TOKENS, provider="news"
        )
    except Exception as e:  # noqa: BLE001
        logger.warning("LLM 생성 불가: %s", e)
        return None


def _build_prompt(persona: Any, sections: list[dict]) -> str:
    """페르소나 조건부 생성 프롬프트 — 가드레일·깊이·섹션 항목 그라운딩."""
    guardrail = _GUARDRAILS.get(
        getattr(persona, "guardrail_profile", "professional"),
        _GUARDRAILS["professional"],
    )
    depth = getattr(persona, "default_depth", "practical")
    lines: list[str] = []
    for sec in sections:
        for item in (sec.get("items") or [])[:4]:
            title = item.get("title")
            if title:
                lines.append(f"- [{sec.get('title')}] {title}")
    context = "\n".join(lines[:_MAX_CONTEXT_ITEMS]) or "(항목 없음)"
    return (
        f"당신은 '{getattr(persona, 'label', '독자')}' 대상 알러지 뉴스레터의 "
        f"편집자다.\n"
        f"아래 이번 호 항목들을 바탕으로 {depth} 수준 독자를 위한 2~3문장 분량의 "
        f"'이번 호 핵심' 편집 요약을 한국어로 작성하라.\n"
        f"{guardrail}\n"
        f"제시된 항목 범위 안에서만 작성하고, 없는 사실을 지어내지 말 것.\n\n"
        f"[이번 호 항목]\n{context}\n\n[이번 호 핵심]"
    )


def _grounding_score(text: str, sections: list[dict]) -> float:
    """생성문이 섹션 항목 어휘에 얼마나 근거하는지 간이 측정 (0~1)."""
    if not text:
        return 0.0
    terms: set[str] = set()
    for sec in sections:
        for item in sec.get("items") or []:
            for tok in str(item.get("title") or "").split():
                if len(tok) >= 2:
                    terms.add(tok)
    if not terms:
        return 0.0
    hit = sum(1 for t in terms if t in text)
    return round(min(hit / len(terms) * 3.0, 1.0), 3)


def _cache_block(
    db: Session,
    persona_code: str,
    period_key: str,
    payload: dict,
    score: float,
) -> None:
    """생성 결과를 newsletter_content_blocks 에 적재 — 실패해도 응답을 막지 않는다."""
    try:
        db.add(
            NewsletterContentBlock(
                persona_code=persona_code,
                block_type="editorial",
                period_key=period_key,
                payload=payload,
                model=payload.get("model"),
                grounding_score=score,
            )
        )
        db.commit()
    except Exception as e:  # noqa: BLE001
        db.rollback()
        logger.warning("editorial 캐시 저장 실패 (무시): %s", e)


def _report_llmops(
    persona_code: str, duration_ms: int, score: float, ok: bool
) -> None:
    """페르소나 생성을 LLMOps 로 계측 — 미구성 시 no-op."""
    try:
        from ...observability.llmops import (
            LLMOpsClient,
            StageReport,
            flush_pending,
        )

        client = LLMOpsClient(
            _LLMOPS_CONSUMER, api_key=os.getenv("LLMOPS_API_KEY_COMPOSE")
        )
        client.report(
            run_id=f"{utc_now().isoformat()}-{persona_code}-compose",
            started_at=utc_now(),
            status="success" if ok else "failure",
            stages=[
                StageReport(
                    name="persona_editorial",
                    model=_MODEL_NAME,
                    duration_ms=duration_ms,
                )
            ],
            metrics={"persona": persona_code, "grounding_score": score},
        )
        flush_pending(2.0)
    except Exception as e:  # noqa: BLE001
        logger.debug("LLMOps 계측 생략: %s", e)


def get_or_generate_editorial(
    db: Session,
    *,
    persona: Any,
    sections: list[dict],
    generate_fn: Optional[Callable[[str], Optional[str]]] = None,
) -> Optional[dict]:
    """페르소나 editorial 조회/생성 — 당일 캐시 (세그먼트 단위 1회 생성).

    Returns:
        {text, model, grounding_score, cached} 또는 None
        (섹션 없음 / LLM 미가용 시 graceful degrade).
    """
    if not sections:
        return None

    period_key = date.today().isoformat()
    cached = (
        db.query(NewsletterContentBlock)
        .filter(
            NewsletterContentBlock.persona_code == persona.code,
            NewsletterContentBlock.block_type == "editorial",
            NewsletterContentBlock.period_key == period_key,
        )
        .first()
    )
    if cached is not None:
        payload = dict(cached.payload or {})
        payload["cached"] = True
        return payload

    # 캐시 미스 — 생성
    generate = generate_fn or _llm_generate
    prompt = _build_prompt(persona, sections)
    started = time.monotonic()
    text: Optional[str] = None
    try:
        text = generate(prompt)
    except Exception as e:  # noqa: BLE001
        logger.warning("editorial 생성 실패: %s", e)
    duration_ms = int((time.monotonic() - started) * 1000)

    if not text or not text.strip():
        return None  # LLM 미가용 — 섹션만 제공

    text = text.strip()
    score = _grounding_score(text, sections)
    payload = {"text": text, "model": _MODEL_NAME, "grounding_score": score}
    _cache_block(db, persona.code, period_key, payload, score)
    _report_llmops(persona.code, duration_ms, score, ok=True)

    out = dict(payload)
    out["cached"] = False
    return out
