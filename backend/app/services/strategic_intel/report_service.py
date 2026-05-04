"""Strategic Intel 리포트 에이전트

두 가지 리포트 발행:
  1) 이벤트 리포트 (event)
     - 트리거: 검증된 가설 중 |abnormal_t5d| >= EVENT_ABNORMAL_THRESHOLD
     - 또는 단일 트리거(논문/뉴스)에서 다수 회사가 동일 방향 가설을 받은 경우
  2) 월간 종합 리포트 (monthly)
     - 매월 말 발행
     - 섹션: Tech Pulse / Hypothesis Verdict / Competitive Map Shift / Whitespace / Hit Rate

내부 경영진 보조용 — 외부 노출 금지. 투자 자문 아님 (필수 면책 포함).
"""
from __future__ import annotations

import json
import logging
from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Optional

from sqlalchemy.orm import Session

from ...database.strategic_intel_models import (
    CompanyTechFit,
    HypothesisLog,
    StrategicIntelReport,
    TechCategory,
)
from ..ollama_service import OllamaService
from .hypothesis_engine import (
    ALL_COMPANIES,
    VALIDATED_COMPANIES,
    hypothesis_hit_rate,
)

logger = logging.getLogger(__name__)

GENERATOR_VERSION = "report-v1-2026-05"

# 이벤트 리포트 트리거 임계값
EVENT_ABNORMAL_THRESHOLD = 0.05   # |abnormal_t5d| >= 5%
EVENT_HIGH_IMPACT_SCORE = 0.55    # impact_score 절대값
DISCLAIMER = (
    "본 리포트는 내부 경영 의사결정 보조 목적으로 자동 생성된 분석 자료이며, "
    "투자 자문이나 매매 추천이 아닙니다. 가설은 사후 주가 흐름과의 동시 발생을 1차 검증한 결과로, "
    "인과관계를 단정하지 않습니다."
)


# ---------------------------------------------------------------------------
# 데이터 수집 헬퍼
# ---------------------------------------------------------------------------


def _hypothesis_brief(h: HypothesisLog) -> dict:
    return {
        "id": h.id,
        "company": h.company_code,
        "trigger_type": h.trigger_type,
        "trigger_date": h.trigger_date.isoformat() if h.trigger_date else None,
        "trigger_title": h.trigger_title,
        "tech_categories": h.tech_categories,
        "impact_direction": h.impact_direction,
        "impact_score": float(h.impact_score) if h.impact_score is not None else None,
        "fit_score_snapshot": float(h.fit_score_snapshot) if h.fit_score_snapshot is not None else None,
        "rationale": h.rationale,
        "abnormal_t1d": _to_float(h.abnormal_t1d),
        "abnormal_t5d": _to_float(h.abnormal_t5d),
        "abnormal_t30d": _to_float(h.abnormal_t30d),
        "hit_t5d": h.hit_t5d,
        "validation_status": h.validation_status,
    }


def _to_float(v) -> Optional[float]:
    if v is None:
        return None
    return float(v)


# ---------------------------------------------------------------------------
# Event Report
# ---------------------------------------------------------------------------


class StrategicIntelReportService:
    """Strategic Intel 리포트 생성 서비스"""

    def __init__(self, db: Session, llm: OllamaService | None = None):
        self.db = db
        self.llm = llm or OllamaService()

    # ------------------------------------------------------------------
    # 이벤트 리포트
    # ------------------------------------------------------------------

    def find_event_candidates(self, since: date | None = None) -> list[HypothesisLog]:
        """이벤트 리포트 발행 후보 조회

        조건:
          - validation_status in ('validated', 'closed')
          - hypothesis 가 회사 검증 대상 (한국 3사)
          - |abnormal_t5d| >= EVENT_ABNORMAL_THRESHOLD
          - 아직 이 가설을 trigger로 한 이벤트 리포트 없음
        """
        q = (
            self.db.query(HypothesisLog)
            .filter(HypothesisLog.validation_status.in_(["validated", "closed"]))
            .filter(HypothesisLog.company_code.in_(VALIDATED_COMPANIES))
            .filter(HypothesisLog.abnormal_t5d.isnot(None))
        )
        if since:
            q = q.filter(HypothesisLog.trigger_date >= since)
        candidates = q.all()

        # 임계값 + 중복 제거
        out: list[HypothesisLog] = []
        for h in candidates:
            if h.abnormal_t5d is None:
                continue
            if abs(float(h.abnormal_t5d)) < EVENT_ABNORMAL_THRESHOLD:
                continue
            existing = (
                self.db.query(StrategicIntelReport.id)
                .filter(StrategicIntelReport.trigger_hypothesis_id == h.id)
                .first()
            )
            if existing:
                continue
            out.append(h)
        return out

    def generate_event_report(self, primary: HypothesisLog) -> StrategicIntelReport | None:
        """단일 가설을 중심으로 이벤트 리포트 생성

        같은 trigger의 다른 회사 가설들도 함께 묶어서 분석.
        """
        # 같은 트리거의 모든 회사 가설 묶기
        sibling_q = self.db.query(HypothesisLog).filter(
            HypothesisLog.trigger_type == primary.trigger_type,
            HypothesisLog.trigger_date == primary.trigger_date,
        )
        if primary.trigger_paper_id:
            sibling_q = sibling_q.filter(HypothesisLog.trigger_paper_id == primary.trigger_paper_id)
        elif primary.trigger_news_id:
            sibling_q = sibling_q.filter(HypothesisLog.trigger_news_id == primary.trigger_news_id)
        siblings = sibling_q.all()

        briefs = [_hypothesis_brief(h) for h in siblings]
        tech_names = self._tech_names_for_labels(primary.tech_categories or [])

        prompt = self._build_event_prompt(primary, briefs, tech_names)
        narrative = self.llm._chat(prompt, max_tokens=900, provider="news") or ""
        narrative = narrative.strip() or "(LLM 응답 실패 — 데이터 요약만 표시)"

        title = (
            f"[Strategic Intel · 이벤트] "
            f"{primary.company_code} | {primary.trigger_date} | "
            f"{primary.trigger_title[:80] if primary.trigger_title else '(제목 없음)'}"
        )
        summary = self._event_summary(primary, briefs)

        # 본문 마크다운 조립
        content = self._compose_event_markdown(primary, briefs, tech_names, narrative)

        report = StrategicIntelReport(
            report_type="event",
            period_start=primary.trigger_date,
            period_end=primary.trigger_date + timedelta(days=30),
            title=title,
            summary=summary,
            content=content,
            trigger_hypothesis_id=primary.id,
            hypothesis_ids=[h.id for h in siblings],
            metrics={
                "primary_company": primary.company_code,
                "primary_abnormal_t5d": _to_float(primary.abnormal_t5d),
                "n_companies": len(siblings),
                "tech_labels": [c["id"] for c in (primary.tech_categories or [])],
            },
            generator_version=GENERATOR_VERSION,
        )
        self.db.add(report)
        self.db.commit()
        return report

    def _build_event_prompt(
        self,
        primary: HypothesisLog,
        briefs: list[dict],
        tech_names: list[str],
    ) -> str:
        return f"""You are an internal corporate intelligence analyst writing for executives at an allergy IVD diagnostic kit/reagent company.

Generate a concise Korean executive briefing (250~400 words) on the following event.

EVENT TRIGGER:
- Type     : {primary.trigger_type}
- Date     : {primary.trigger_date}
- Title    : {primary.trigger_title}
- Tech     : {", ".join(tech_names) or "(미상)"}

COMPANIES & HYPOTHESES (4사 — 수젠텍/녹십자MS/바디텍메드/MADx):
{json.dumps(briefs, ensure_ascii=False, indent=2)}

INSTRUCTIONS:
1. Open with what happened (2-3 sentences) — the technology disclosed and why it matters in allergy IVD kits/reagents.
2. Per-company implication: state how each of the 4 companies is positioned vs this technology.
   Use the impact_direction and abnormal_t5d to weave in market reaction (was the prior hypothesis confirmed by short-term price?).
3. Strategic recommendation: 2-3 bullet items on what management should monitor / consider.
4. NEVER recommend buying/selling stock. NEVER claim causation between the event and price.
   Use phrases like "동시 발생", "관찰됨", "정합성 확인" (not "원인", "예측", "결과").
5. Output Korean markdown. NO preface, NO meta commentary. Start with "## 무슨 일이 일어났나".
"""

    def _compose_event_markdown(
        self,
        primary: HypothesisLog,
        briefs: list[dict],
        tech_names: list[str],
        narrative: str,
    ) -> str:
        lines = [
            f"# 이벤트 리포트 — {primary.trigger_date}",
            "",
            f"**트리거**: {primary.trigger_type.upper()} | {primary.trigger_title}",
            f"**기술 카테고리**: {', '.join(tech_names) or '(미상)'}",
            "",
            narrative,
            "",
            "---",
            "## 가설 / 검증 데이터 (T+5d)",
            "",
            "| 회사 | 영향 | impact | fit | T+1d | T+5d | T+30d | 적중(T+5d) |",
            "|---|---|---|---|---|---|---|---|",
        ]
        for b in briefs:
            lines.append(
                "| {company} | {direction} | {impact} | {fit} | {t1d} | {t5d} | {t30d} | {hit} |".format(
                    company=b["company"],
                    direction=b["impact_direction"],
                    impact=_pct(b["impact_score"], 2),
                    fit=_pct(b["fit_score_snapshot"], 2),
                    t1d=_pct(b["abnormal_t1d"]),
                    t5d=_pct(b["abnormal_t5d"]),
                    t30d=_pct(b["abnormal_t30d"]),
                    hit=("적중" if b["hit_t5d"] else "—" if b["hit_t5d"] is None else "미적중"),
                )
            )
        lines += ["", "---", "", f"> {DISCLAIMER}"]
        return "\n".join(lines)

    def _event_summary(self, primary: HypothesisLog, briefs: list[dict]) -> str:
        moves = [b for b in briefs if b["abnormal_t5d"] is not None]
        if not moves:
            return f"{primary.company_code}: 시장 검증 데이터 미확보"
        biggest = max(moves, key=lambda b: abs(b["abnormal_t5d"] or 0))
        return (
            f"{biggest['company']} T+5d abnormal {_pct(biggest['abnormal_t5d'])} "
            f"(가설 방향: {biggest['impact_direction']}, "
            f"{'적중' if biggest['hit_t5d'] else '미적중' if biggest['hit_t5d'] is False else '판정전'})"
        )

    # ------------------------------------------------------------------
    # 월간 리포트
    # ------------------------------------------------------------------

    def generate_monthly_report(self, year: int, month: int) -> StrategicIntelReport | None:
        period_start = date(year, month, 1)
        next_month = date(year + (1 if month == 12 else 0), 1 if month == 12 else month + 1, 1)
        period_end = next_month - timedelta(days=1)

        # 중복 방지
        existing = (
            self.db.query(StrategicIntelReport)
            .filter(
                StrategicIntelReport.report_type == "monthly",
                StrategicIntelReport.period_start == period_start,
            )
            .first()
        )
        if existing:
            logger.info("월간 리포트 이미 존재: %s", period_start)
            return existing

        # 해당 월 데이터 집계
        hypos = (
            self.db.query(HypothesisLog)
            .filter(HypothesisLog.trigger_date >= period_start)
            .filter(HypothesisLog.trigger_date <= period_end)
            .all()
        )
        if not hypos:
            logger.info("월간 리포트: 가설 없음 (%s)", period_start)
            return None

        hit_rate = hypothesis_hit_rate(self.db, since=period_start)

        # Tech pulse — 트리거 빈도
        tech_freq: dict[str, int] = defaultdict(int)
        for h in hypos:
            for c in (h.tech_categories or []):
                tech_freq[c["id"]] += 1

        # Whitespace — fit 낮은 카테고리에 트리거가 집중되는 경우
        fit_matrix = self._load_active_fit_matrix(period_end)
        whitespace = []
        for tid, freq in sorted(tech_freq.items(), key=lambda kv: -kv[1])[:5]:
            avg_fit = sum(fit_matrix.get(c, {}).get(tid, 0.0) for c in ALL_COMPANIES) / max(
                1, len(ALL_COMPANIES)
            )
            if avg_fit <= 0.45:
                whitespace.append({"tech_id": tid, "freq": freq, "avg_fit": round(avg_fit, 2)})

        # Top events
        top_events = sorted(
            [h for h in hypos if h.abnormal_t5d is not None],
            key=lambda h: -abs(float(h.abnormal_t5d)),
        )[:5]

        tech_names_map = {c.id: c.name_kr for c in self.db.query(TechCategory).all()}
        prompt = self._build_monthly_prompt(
            period_start,
            period_end,
            hypos,
            hit_rate,
            [(tid, freq, tech_names_map.get(tid, tid)) for tid, freq in tech_freq.items()],
            whitespace,
            [_hypothesis_brief(h) for h in top_events],
        )
        narrative = self.llm._chat(prompt, max_tokens=1500, provider="news") or ""
        narrative = narrative.strip() or "(LLM 응답 실패)"

        content = self._compose_monthly_markdown(
            period_start,
            period_end,
            hypos,
            hit_rate,
            tech_freq,
            tech_names_map,
            whitespace,
            top_events,
            narrative,
        )

        title = f"[Strategic Intel · 월간] {year}년 {month:02d}월 종합"
        summary = self._monthly_summary(hypos, hit_rate)

        report = StrategicIntelReport(
            report_type="monthly",
            period_start=period_start,
            period_end=period_end,
            title=title,
            summary=summary,
            content=content,
            hypothesis_ids=[h.id for h in hypos],
            metrics={
                "n_hypotheses": len(hypos),
                "hit_rate": hit_rate,
                "tech_pulse": dict(tech_freq),
                "whitespace": whitespace,
            },
            generator_version=GENERATOR_VERSION,
        )
        self.db.add(report)
        self.db.commit()
        return report

    def _build_monthly_prompt(
        self,
        period_start: date,
        period_end: date,
        hypos: list[HypothesisLog],
        hit_rate: dict,
        tech_freq: list[tuple[str, int, str]],
        whitespace: list[dict],
        top_events: list[dict],
    ) -> str:
        return f"""You are an internal strategic intelligence analyst preparing a monthly executive briefing
on allergy IVD diagnostic kit/reagent technology trends and competitive positioning.

Period      : {period_start} ~ {period_end}
Total hypotheses : {len(hypos)}
Hit rate (T+5d)  : {json.dumps(hit_rate, ensure_ascii=False)}
Tech volume      : {[(name, freq) for _, freq, name in sorted(tech_freq, key=lambda x: -x[1])[:8]]}
Whitespace flags : {whitespace}
Top abnormal moves (|T+5d|): {json.dumps(top_events, ensure_ascii=False)[:3500]}

Write a Korean markdown executive briefing with 4 sections (1500자 내외):

## 1. Tech Pulse
이번 달 알러지 진단 키트/시약 분야의 주요 기술 흐름 3가지. 각 흐름이 4개 추적사 (수젠텍/녹십자MS/바디텍메드/MADx) 중 누구의 강점/약점에 닿는지 요약.

## 2. Hypothesis & Verdict
회사별 적중률(hit rate) 해석. 어느 회사·어느 방향 가설이 시장과 정합도가 높았는지. 단정적 인과 표현 금지.

## 3. Competitive Map Shift
한 달간의 트렌드가 4사 경쟁구도에 시사하는 점. 약점/강점 변화 신호.

## 4. Whitespace
4사가 모두 약하지만 트리거 발생량이 큰 카테고리. 진입 가능성 / 위협 시그널 평가.

규칙:
- "투자", "매수", "매도", "예측", "원인" 단어 금지.
- "동시 발생", "관찰됨", "정합도", "신호" 같은 보조 표현 권장.
- 본문만 출력. 헤더 외 타 메타 텍스트 금지.
"""

    def _compose_monthly_markdown(
        self,
        period_start: date,
        period_end: date,
        hypos: list[HypothesisLog],
        hit_rate: dict,
        tech_freq: dict[str, int],
        tech_names_map: dict[str, str],
        whitespace: list[dict],
        top_events: list[HypothesisLog],
        narrative: str,
    ) -> str:
        lines = [
            f"# Strategic Intel 월간 리포트 — {period_start} ~ {period_end}",
            "",
            "**대상**: 수젠텍 (KOSDAQ 253840) · 녹십자엠에스 (142280) · 바디텍메드 (206640) · MADx (비상장)",
            f"**총 가설**: {len(hypos)}건 | **벤치마크 지수**: KOSDAQ 종합",
            "",
            "---",
            "",
            narrative,
            "",
            "---",
            "## 데이터 — 회사별 T+5d 적중률",
            "",
            "| 회사 | 가설 수 | 적중 | 적중률 |",
            "|---|---|---|---|",
        ]
        for code, b in hit_rate.items():
            lines.append(
                f"| {code} | {b['total']} | {b['hit']} | {_pct(b['hit_rate'])} |"
            )
        lines += [
            "",
            "## 데이터 — Tech Pulse (트리거 빈도 상위)",
            "",
            "| 카테고리 | 빈도 |",
            "|---|---|",
        ]
        for tid, freq in sorted(tech_freq.items(), key=lambda kv: -kv[1])[:8]:
            lines.append(f"| {tech_names_map.get(tid, tid)} | {freq} |")

        if whitespace:
            lines += [
                "",
                "## 데이터 — Whitespace 플래그",
                "",
                "| 카테고리 | 빈도 | 4사 평균 fit |",
                "|---|---|---|",
            ]
            for w in whitespace:
                lines.append(
                    f"| {tech_names_map.get(w['tech_id'], w['tech_id'])} | {w['freq']} | {w['avg_fit']:.2f} |"
                )

        if top_events:
            lines += [
                "",
                "## 데이터 — 주요 이벤트 (|T+5d| 상위)",
                "",
                "| 일자 | 회사 | 방향 | T+5d | 트리거 |",
                "|---|---|---|---|---|",
            ]
            for h in top_events:
                lines.append(
                    f"| {h.trigger_date} | {h.company_code} | {h.impact_direction} | "
                    f"{_pct(_to_float(h.abnormal_t5d))} | {(h.trigger_title or '')[:60]} |"
                )

        lines += ["", "---", "", f"> {DISCLAIMER}"]
        return "\n".join(lines)

    def _monthly_summary(self, hypos: list[HypothesisLog], hit_rate: dict) -> str:
        n = len(hypos)
        validated = sum(1 for h in hypos if h.hit_t5d is not None)
        if not hit_rate:
            return f"가설 {n}건 / 검증 {validated}건 (T+5d 데이터 부족)"
        avg = (
            sum(b.get("hit_rate") or 0 for b in hit_rate.values()) / len(hit_rate)
            if hit_rate
            else None
        )
        avg_str = f"{avg*100:.1f}%" if avg is not None else "—"
        return f"가설 {n}건 / 검증 {validated}건 / 평균 적중률 {avg_str}"

    # ------------------------------------------------------------------
    # 유틸
    # ------------------------------------------------------------------

    def _tech_names_for_labels(self, labels: list[dict]) -> list[str]:
        ids = [l["id"] for l in labels if isinstance(l, dict) and l.get("id")]
        if not ids:
            return []
        rows = (
            self.db.query(TechCategory.id, TechCategory.name_kr)
            .filter(TechCategory.id.in_(ids))
            .all()
        )
        name_map = {r[0]: r[1] for r in rows}
        return [name_map.get(i, i) for i in ids]

    def _load_active_fit_matrix(self, on_date: date) -> dict[str, dict[str, float]]:
        rows = (
            self.db.query(CompanyTechFit)
            .filter(CompanyTechFit.effective_from <= on_date)
            .filter(
                (CompanyTechFit.effective_to.is_(None))
                | (CompanyTechFit.effective_to > on_date)
            )
            .all()
        )
        matrix: dict[str, dict[str, float]] = {}
        for r in rows:
            matrix.setdefault(r.company_code, {})[r.tech_category_id] = float(r.fit_score)
        return matrix


def _pct(v: Optional[float], precision: int = 2) -> str:
    """소수 → 백분율 문자열 (None → '—')"""
    if v is None:
        return "—"
    return f"{v*100:+.{precision}f}%"
