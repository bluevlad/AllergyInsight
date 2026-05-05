"""LLM 정성 보강기 (Phase B) — 룰 결정 위에 정성 분석 레이어

룰 엔진(`hypothesis_engine`)이 4사 가설을 1차 결정한 뒤, 본 서비스가
트리거 본문 + fit matrix context 를 LLM 에 제공해 다음을 산출:

  1) qualitative_rationale   : 보강된 한국어 rationale
  2) qualitative_score       : -1.0 ~ 1.0 정성 점수 (룰 impact_score 와 별도)
  3) qualitative_override    : 룰 방향(direction) 을 뒤집을 정황이면 True
                                — 룰과 LLM 의 drift 모니터링 KPI

룰 결정(`impact_direction`, `impact_score`) 자체는 절대 변경하지 않는다.
적중 판정·검증·통계는 모두 룰 결정 기준으로 유지 — 정성 보강은 의사결정자가
함께 참고하는 보조 정보. drift(override 비율) 가 임계 초과 시 룰 캘리브레이션
신호로 활용한다.

Strategic Intel 모듈 전용. 외부 사용자 노출 금지.
"""
from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass
from typing import Optional

from sqlalchemy.orm import Session

from ...database.competitor_models import CompetitorNews
from ...database.models import Paper as PaperORM
from ...database.strategic_intel_models import (
    CompanyTechFit,
    HypothesisLog,
    TechCategory,
)
from ..ollama_service import OllamaService
from .hypothesis_engine import ALL_COMPANIES

logger = logging.getLogger(__name__)

QUALITATIVE_VERSION = "qual-v1-2026-05"

# 트리거 본문 길이 상한 (LLM 비용/토큰 안전 마진)
TRIGGER_BODY_MAX_CHARS = 2400


@dataclass
class QualitativeResult:
    qualitative_score: float          # -1.0 ~ 1.0
    qualitative_rationale: str        # 보강된 한국어 rationale
    qualitative_override: bool        # 룰 direction 을 뒤집어야 한다고 판단되면 True


# ---------------------------------------------------------------------------
# Context 수집 헬퍼
# ---------------------------------------------------------------------------


def _load_trigger_body(db: Session, h: HypothesisLog) -> str:
    """트리거 본문 (paper.abstract / news.description) 로드 — 길이 상한 적용"""
    if h.trigger_type == "paper" and h.trigger_paper_id:
        p = db.query(PaperORM).filter(PaperORM.id == h.trigger_paper_id).first()
        if p:
            return (p.abstract_kr or p.abstract or "")[:TRIGGER_BODY_MAX_CHARS]
    if h.trigger_type == "news" and h.trigger_news_id:
        n = db.query(CompetitorNews).filter(CompetitorNews.id == h.trigger_news_id).first()
        if n:
            return (n.description or n.summary or "")[:TRIGGER_BODY_MAX_CHARS]
    return ""


def _load_fit_context(
    db: Session, h: HypothesisLog
) -> dict[str, dict[str, float]]:
    """가설 시점에 활성인 fit matrix 로드 — {company_code: {tech_id: score}}"""
    rows = (
        db.query(CompanyTechFit)
        .filter(CompanyTechFit.effective_from <= h.trigger_date)
        .filter(
            (CompanyTechFit.effective_to.is_(None))
            | (CompanyTechFit.effective_to > h.trigger_date)
        )
        .all()
    )
    matrix: dict[str, dict[str, float]] = {}
    for r in rows:
        matrix.setdefault(r.company_code, {})[r.tech_category_id] = float(r.fit_score)
    return matrix


def _tech_summary(tech_categories: list[dict], names: dict[str, str]) -> str:
    """tech_categories 스냅샷 → 사람이 읽는 줄"""
    parts = []
    for c in tech_categories or []:
        if not isinstance(c, dict):
            continue
        tid = c.get("id")
        conf = c.get("confidence")
        if tid:
            label = names.get(tid, tid)
            parts.append(f"{label} (conf={conf})")
    return ", ".join(parts) or "(미상)"


# ---------------------------------------------------------------------------
# 프롬프트
# ---------------------------------------------------------------------------


def _build_prompt(
    h: HypothesisLog,
    trigger_body: str,
    own_fit_top: list[tuple[str, float, str]],
    competitor_fit_top: list[tuple[str, str, float, str]],
    tech_summary: str,
) -> str:
    """LLM 프롬프트 — 룰 결정 + 회사/경쟁사 fit context"""
    own_fit_str = (
        "\n".join(f"  - {label} (id={tid}): {score:.2f}" for tid, score, label in own_fit_top)
        or "  (보유 영역 정보 없음)"
    )
    comp_fit_str = (
        "\n".join(
            f"  - {company}: {label} (id={tid}) {score:.2f}"
            for company, tid, score, label in competitor_fit_top
        )
        or "  (경쟁사 fit 정보 없음)"
    )
    return f"""You are an internal strategic intelligence analyst writing for executives at an allergy IVD diagnostic kit/reagent company.

A rule-based hypothesis has already been generated for this trigger. Your job is to provide a *qualitative* second-pass analysis with deeper context.

TRIGGER:
- Type   : {h.trigger_type}
- Date   : {h.trigger_date}
- Title  : {h.trigger_title or '(제목 없음)'}
- Tech   : {tech_summary}
- Body   : {trigger_body or '(본문 없음)'}

TARGET COMPANY: {h.company_code}
- Triggered tech areas — own fit:
{own_fit_str}
- Triggered tech areas — competitor max fit:
{comp_fit_str}

RULE-BASED HYPOTHESIS (do NOT alter this — only annotate):
- direction     : {h.impact_direction}
- impact_score  : {float(h.impact_score):.2f}
- fit_snapshot  : {float(h.fit_score_snapshot) if h.fit_score_snapshot is not None else 0.0:.2f}
- rule_rationale: {h.rationale}

INSTRUCTIONS:
1. Write a refined Korean rationale (2~4 sentences) that adds *qualitative* nuance the rule cannot see — e.g. clinical/regulatory implications, product-line synergy, timing relative to {h.company_code}'s recent moves.
2. Provide a qualitative_score in [-1.0, 1.0]:
   - +1.0 = strong tailwind for {h.company_code}
   -  0.0 = neutral
   - -1.0 = strong threat to {h.company_code}
3. Set override=true ONLY IF you would clearly flip the rule's direction (e.g., rule says positive but reading the body it's actually a negative for {h.company_code}). Otherwise override=false.
4. Avoid recommending stock action. Avoid causal claims about price.
5. Output STRICT JSON only:

{{"qualitative_rationale": "<한국어 본문>", "qualitative_score": <float>, "qualitative_override": <true|false>}}
"""


# ---------------------------------------------------------------------------
# 응답 파싱
# ---------------------------------------------------------------------------


def _strip_json_fences(s: str) -> str:
    s = s.strip()
    if s.startswith("```"):
        s = re.sub(r"^```(json)?\s*", "", s)
        s = re.sub(r"\s*```$", "", s)
    return s.strip()


def _parse_response(raw: str) -> Optional[QualitativeResult]:
    cleaned = _strip_json_fences(raw)
    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", cleaned, re.DOTALL)
        if not match:
            return None
        try:
            data = json.loads(match.group(0))
        except json.JSONDecodeError:
            return None
    if not isinstance(data, dict):
        return None

    rationale = data.get("qualitative_rationale")
    if not isinstance(rationale, str) or not rationale.strip():
        return None
    try:
        score = float(data.get("qualitative_score", 0))
    except (TypeError, ValueError):
        return None
    score = max(-1.0, min(1.0, score))
    override = bool(data.get("qualitative_override", False))
    return QualitativeResult(
        qualitative_score=score,
        qualitative_rationale=rationale.strip(),
        qualitative_override=override,
    )


# ---------------------------------------------------------------------------
# 보강기 본체
# ---------------------------------------------------------------------------


class HypothesisQualitativeEnhancer:
    """가설 정성 보강기 — 룰 결정 후 LLM 분석 레이어 적용"""

    VERSION = QUALITATIVE_VERSION

    def __init__(self, db: Session, llm: OllamaService | None = None):
        self.db = db
        self.llm = llm or OllamaService()
        self._tech_names: dict[str, str] | None = None

    def _tech_names_map(self) -> dict[str, str]:
        if self._tech_names is None:
            self._tech_names = {
                c.id: c.name_kr for c in self.db.query(TechCategory).all()
            }
        return self._tech_names

    def _competitor_fit_top(
        self,
        h: HypothesisLog,
        matrix: dict[str, dict[str, float]],
    ) -> list[tuple[str, str, float, str]]:
        """라벨된 카테고리에서 경쟁 회사들의 가장 높은 fit (회사당 1건, 0.4 이상)"""
        names = self._tech_names_map()
        labels = [c["id"] for c in (h.tech_categories or []) if isinstance(c, dict) and c.get("id")]
        out: list[tuple[str, str, float, str]] = []
        for other in ALL_COMPANIES:
            if other == h.company_code:
                continue
            company_fits = matrix.get(other, {})
            best_tid: str | None = None
            best_score = 0.0
            for tid in labels:
                score = company_fits.get(tid, 0.0)
                if score > best_score:
                    best_score = score
                    best_tid = tid
            if best_tid and best_score >= 0.4:
                out.append((other, best_tid, best_score, names.get(best_tid, best_tid)))
        return sorted(out, key=lambda t: -t[2])[:4]

    def _own_fit_top(
        self,
        h: HypothesisLog,
        matrix: dict[str, dict[str, float]],
    ) -> list[tuple[str, float, str]]:
        names = self._tech_names_map()
        labels = [c["id"] for c in (h.tech_categories or []) if isinstance(c, dict) and c.get("id")]
        company_fits = matrix.get(h.company_code, {})
        out: list[tuple[str, float, str]] = []
        for tid in labels:
            score = company_fits.get(tid, 0.0)
            out.append((tid, score, names.get(tid, tid)))
        return sorted(out, key=lambda t: -t[1])[:4]

    def enhance_one(self, h: HypothesisLog) -> bool:
        """단일 가설 정성 보강. 이미 현재 버전으로 보강됐다면 skip.

        Returns: True if updated.
        """
        if h.qualitative_version == self.VERSION:
            return False

        trigger_body = _load_trigger_body(self.db, h)
        matrix = _load_fit_context(self.db, h)
        own_fit = self._own_fit_top(h, matrix)
        comp_fit = self._competitor_fit_top(h, matrix)
        tech_summary = _tech_summary(h.tech_categories, self._tech_names_map())

        prompt = _build_prompt(h, trigger_body, own_fit, comp_fit, tech_summary)
        raw = self.llm._chat(prompt, max_tokens=600, provider="news")
        if not raw:
            logger.warning("LLM empty for hypothesis_id=%s", h.id)
            return False

        parsed = _parse_response(raw)
        if not parsed:
            logger.warning("Failed to parse qualitative response for h=%s: %s", h.id, raw[:200])
            return False

        from decimal import Decimal
        try:
            h.qualitative_score = Decimal(f"{parsed.qualitative_score:.2f}")
            h.qualitative_rationale = parsed.qualitative_rationale
            h.qualitative_override = parsed.qualitative_override
            h.qualitative_version = self.VERSION
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            logger.warning("qualitative commit failed h=%s: %s", h.id, e)
            return False
        return True

    def enhance_pending(
        self,
        *,
        since=None,
        limit: int = 100,
    ) -> dict[str, int]:
        """`qualitative_version` 이 현재 버전과 다른 가설을 일괄 보강."""
        q = self.db.query(HypothesisLog).filter(
            (HypothesisLog.qualitative_version.is_(None))
            | (HypothesisLog.qualitative_version != self.VERSION)
        )
        if since is not None:
            q = q.filter(HypothesisLog.trigger_date >= since)
        rows = (
            q.order_by(HypothesisLog.trigger_date.desc(), HypothesisLog.id.desc())
            .limit(limit)
            .all()
        )
        updated = 0
        for h in rows:
            try:
                if self.enhance_one(h):
                    updated += 1
            except Exception as e:
                logger.warning("enhance_one failed h=%s: %s", h.id, e)
        return {"checked": len(rows), "updated": updated}


# ---------------------------------------------------------------------------
# Drift 메트릭 (룰 vs LLM 일치율 모니터링)
# ---------------------------------------------------------------------------


def qualitative_drift(db: Session, *, since=None) -> dict:
    """정성 보강 vs 룰 결정 일치율 — drift 모니터링 KPI.

    Returns:
      {
        "n_total": <int>,           # 가설 전체
        "n_enhanced": <int>,        # 정성 보강된 가설
        "n_override": <int>,        # qualitative_override=True
        "coverage": <float|None>,   # n_enhanced / n_total
        "override_rate": <float|None>,  # n_override / n_enhanced
      }
    """
    q = db.query(HypothesisLog)
    if since is not None:
        q = q.filter(HypothesisLog.trigger_date >= since)
    rows = q.all()
    n_total = len(rows)
    n_enhanced = sum(1 for r in rows if r.qualitative_version is not None)
    n_override = sum(1 for r in rows if r.qualitative_override is True)
    return {
        "n_total": n_total,
        "n_enhanced": n_enhanced,
        "n_override": n_override,
        "coverage": round(n_enhanced / n_total, 3) if n_total else None,
        "override_rate": round(n_override / n_enhanced, 3) if n_enhanced else None,
    }
