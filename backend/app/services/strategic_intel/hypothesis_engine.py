"""가설 생성 + T+5d 검증 엔진

워크플로우:
  1) 트리거 (분류된 paper/news) → 회사별 영향 가설 자동 생성 → hypothesis_logs 적재
  2) trigger_date + N영업일 경과 시 daily_prices 조회 → abnormal return 계산 → hit 판정

Strategic Intel 모듈 전용. 외부 사용자 노출 금지.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import Iterable

from sqlalchemy.orm import Session

from ...database.strategic_intel_models import (
    CompanyTechFit,
    HypothesisLog,
    NewsTechLink,
    PaperTechLink,
    TechCategory,
)
from . import stock_price_service as price_svc

logger = logging.getLogger(__name__)

GENERATOR_VERSION = "v1-rule-2026-05"

# 가설 생성·검증 임계값
TRIGGER_MIN_CONFIDENCE = 0.50  # tech 라벨 신뢰도 이 미만이면 가설 생성 안 함
HIGH_FIT_THRESHOLD = 0.60      # 회사 핵심 영역 판정선
LOW_FIT_THRESHOLD = 0.30       # 회사 미보유 판정선 (이 이하면 위협/무관)
COMPETITOR_THREAT_FIT = 0.70   # 경쟁사가 이 이상 fit이면 위협으로 간주
NEUTRAL_BAND = (-0.15, 0.15)   # impact_score 이 범위 내면 neutral 처리
MIN_RELEVANCE_FOR_THREAT = 0.15  # 회사가 이 미만 fit이면 negative 트리거 안 함 (완전 무관)
                                # 예: MADx poc_lateral_flow=0.00 → 한국 POC 회사 진보가 위협 아님

# 검증 대상 회사 (주가 검증 가능한 한국 3사)
VALIDATED_COMPANIES = {"sugentech", "greencross", "bodytech"}
ALL_COMPANIES = {"sugentech", "greencross", "bodytech", "madx"}

# 검증 윈도우 (영업일)
T_PLUS_DAYS = {"t1d": 1, "t5d": 5, "t30d": 30}


@dataclass
class TriggerInput:
    trigger_type: str           # 'paper' | 'news'
    trigger_id: int             # papers.id or competitor_news.id
    trigger_date: date
    title: str
    tech_labels: list[tuple[str, float]]  # [(tech_id, confidence), ...]
    classifier_version: str | None = None


# ---------------------------------------------------------------------------
# Fit Matrix 조회 헬퍼
# ---------------------------------------------------------------------------


def _load_fit_matrix(db: Session, on_date: date) -> dict[str, dict[str, float]]:
    """on_date 기준 유효한 fit matrix 로드: {company_code: {tech_id: score}}"""
    rows = (
        db.query(CompanyTechFit)
        .filter(CompanyTechFit.effective_from <= on_date)
        .filter(
            (CompanyTechFit.effective_to.is_(None)) | (CompanyTechFit.effective_to > on_date)
        )
        .all()
    )
    matrix: dict[str, dict[str, float]] = {}
    for r in rows:
        matrix.setdefault(r.company_code, {})[r.tech_category_id] = float(r.fit_score)
    return matrix


# ---------------------------------------------------------------------------
# 가설 생성
# ---------------------------------------------------------------------------


@dataclass
class CompanyImpact:
    company_code: str
    impact_direction: str  # 'positive' | 'neutral' | 'negative'
    impact_score: float    # -1.0 ~ 1.0
    fit_score: float
    rationale: str


def _aggregate_fit_for_labels(
    company_code: str,
    matrix: dict[str, dict[str, float]],
    labels: list[tuple[str, float]],
) -> tuple[float, dict[str, float]]:
    """라벨된 카테고리들에서 회사의 가중 fit (max) 추출"""
    company_fits = matrix.get(company_code, {})
    contributions: dict[str, float] = {}
    for tech_id, conf in labels:
        fit = company_fits.get(tech_id, 0.0)
        contributions[tech_id] = fit * conf
    if not contributions:
        return 0.0, {}
    return max(contributions.values()), contributions


def _max_competitor_fit(
    company_code: str,
    matrix: dict[str, dict[str, float]],
    labels: list[tuple[str, float]],
) -> tuple[float, str | None]:
    """라벨된 카테고리들에서 다른 회사들의 가중 fit 최대값 + 해당 회사"""
    best = 0.0
    best_company: str | None = None
    for other_code in ALL_COMPANIES:
        if other_code == company_code:
            continue
        weighted, _ = _aggregate_fit_for_labels(other_code, matrix, labels)
        if weighted > best:
            best = weighted
            best_company = other_code
    return best, best_company


def _build_company_impact(
    company_code: str,
    matrix: dict[str, dict[str, float]],
    labels: list[tuple[str, float]],
    tech_categories: dict[str, TechCategory],
) -> CompanyImpact | None:
    """회사 1개 + 라벨 1세트 → impact 가설 1건"""
    own_weighted, own_contrib = _aggregate_fit_for_labels(company_code, matrix, labels)

    competitor_weighted, competitor_code = _max_competitor_fit(company_code, matrix, labels)

    # 핵심 라벨명 (가장 기여도 큰 것)
    top_tech_id = (
        max(own_contrib.items(), key=lambda kv: kv[1])[0]
        if own_contrib
        else (labels[0][0] if labels else None)
    )
    top_tech_name = tech_categories.get(top_tech_id).name_kr if top_tech_id else "(미상)"

    # impact 스코어 결정
    # +) 회사 핵심 영역 (own_weighted 높음) → 긍정
    # -) 회사는 약하지만 경쟁사가 강한 영역 → 위협
    own_fit_raw = matrix.get(company_code, {}).get(top_tech_id, 0.0) if top_tech_id else 0.0

    if own_weighted >= HIGH_FIT_THRESHOLD:
        impact_score = own_weighted
        direction = "positive"
        rationale = (
            f"신규 발표 기술이 {company_code}의 핵심 영역({top_tech_name}, fit={own_fit_raw:.2f})과 "
            f"직접 연관 — 자사 제품 강화·신뢰도 상승 기회로 평가."
        )
    elif (
        own_fit_raw >= MIN_RELEVANCE_FOR_THREAT  # 회사가 최소한 인접 비즈니스 보유
        and own_weighted <= LOW_FIT_THRESHOLD
        and competitor_weighted >= COMPETITOR_THREAT_FIT
        and competitor_code is not None
    ):
        impact_score = -(competitor_weighted - own_weighted)
        direction = "negative"
        rationale = (
            f"기술 발표가 경쟁사 {competitor_code}의 핵심 영역({top_tech_name}, "
            f"competitor fit={competitor_weighted:.2f})에 집중 — {company_code} 제품 라인의 "
            f"경쟁 위협 신호로 평가 (own fit={own_fit_raw:.2f})."
        )
    else:
        impact_score = own_weighted - competitor_weighted * 0.3  # 약한 시그널
        direction = "neutral"
        rationale = (
            f"{top_tech_name} 영역이 {company_code} 제품과 부분 연관(own fit={own_fit_raw:.2f}); "
            f"경쟁사 영향({competitor_weighted:.2f})도 제한적 — 중립."
        )

    # neutral band 정규화
    if NEUTRAL_BAND[0] < impact_score < NEUTRAL_BAND[1]:
        direction = "neutral"

    return CompanyImpact(
        company_code=company_code,
        impact_direction=direction,
        impact_score=round(max(-1.0, min(1.0, impact_score)), 3),
        fit_score=round(own_fit_raw, 3),
        rationale=rationale,
    )


class HypothesisGenerator:
    """가설 생성기 — fit matrix 기반 룰. (LLM 정성 보강은 v2에서 추가)"""

    def __init__(self, db: Session):
        self.db = db

    def generate_for_trigger(self, trigger: TriggerInput) -> list[HypothesisLog]:
        """단일 트리거 → 4사 가설 생성·저장 (이미 존재하면 skip)"""
        # 신뢰도 필터
        confident_labels = [
            (tid, conf) for tid, conf in trigger.tech_labels if conf >= TRIGGER_MIN_CONFIDENCE
        ]
        if not confident_labels:
            logger.debug("No confident labels for trigger %s/%d", trigger.trigger_type, trigger.trigger_id)
            return []

        matrix = _load_fit_matrix(self.db, trigger.trigger_date)
        tech_categories = {c.id: c for c in self.db.query(TechCategory).all()}

        out: list[HypothesisLog] = []
        for company_code in ALL_COMPANIES:
            impact = _build_company_impact(
                company_code, matrix, confident_labels, tech_categories
            )
            if impact is None:
                continue

            # 중복 방지: 동일 trigger + company 가설 이미 있으면 skip
            existing = self.db.query(HypothesisLog).filter(
                HypothesisLog.trigger_type == trigger.trigger_type,
                HypothesisLog.company_code == company_code,
                (
                    (HypothesisLog.trigger_paper_id == trigger.trigger_id)
                    if trigger.trigger_type == "paper"
                    else (HypothesisLog.trigger_news_id == trigger.trigger_id)
                ),
            ).first()
            if existing:
                continue

            log = HypothesisLog(
                trigger_type=trigger.trigger_type,
                trigger_paper_id=trigger.trigger_id if trigger.trigger_type == "paper" else None,
                trigger_news_id=trigger.trigger_id if trigger.trigger_type == "news" else None,
                trigger_date=trigger.trigger_date,
                trigger_title=(trigger.title or "")[:500],
                tech_categories=[
                    {"id": tid, "confidence": round(conf, 3)} for tid, conf in confident_labels
                ],
                company_code=company_code,
                impact_direction=impact.impact_direction,
                impact_score=Decimal(str(impact.impact_score)),
                fit_score_snapshot=Decimal(str(impact.fit_score)),
                rationale=impact.rationale,
                benchmark_ticker="KOSDAQ",
                validation_status="pending" if company_code in VALIDATED_COMPANIES else "no_data",
                classifier_version=trigger.classifier_version,
                generator_version=GENERATOR_VERSION,
            )
            self.db.add(log)
            out.append(log)

        self.db.commit()
        return out

    def generate_for_paper(self, paper) -> list[HypothesisLog]:
        """Paper 객체 + 기존 paper_tech_links → 가설 생성"""
        links = self.db.query(PaperTechLink).filter(PaperTechLink.paper_id == paper.id).all()
        if not links:
            return []
        trigger_date = self._infer_paper_date(paper)
        return self.generate_for_trigger(
            TriggerInput(
                trigger_type="paper",
                trigger_id=paper.id,
                trigger_date=trigger_date,
                title=paper.title or "",
                tech_labels=[(l.tech_category_id, float(l.confidence)) for l in links],
                classifier_version=links[0].classifier_version if links else None,
            )
        )

    def generate_for_news(self, news) -> list[HypothesisLog]:
        """CompetitorNews 객체 + 기존 news_tech_links → 가설 생성"""
        links = self.db.query(NewsTechLink).filter(NewsTechLink.news_id == news.id).all()
        if not links:
            return []
        published = news.published_at or news.created_at
        trigger_date = published.date() if isinstance(published, datetime) else published
        if trigger_date is None:
            return []
        return self.generate_for_trigger(
            TriggerInput(
                trigger_type="news",
                trigger_id=news.id,
                trigger_date=trigger_date,
                title=news.title or "",
                tech_labels=[(l.tech_category_id, float(l.confidence)) for l in links],
                classifier_version=links[0].classifier_version if links else None,
            )
        )

    @staticmethod
    def _infer_paper_date(paper) -> date:
        """Paper의 정확한 발행일 산출 (우선순위 적용)

        우선순위:
          1. paper.published_at (PubMed Article Date / S2 publicationDate에서 적재)
          2. paper.year (보수적 — 1월 1일)
          3. paper.created_at (수집 시점 fallback)
        """
        from datetime import date as _date
        if getattr(paper, "published_at", None):
            return paper.published_at
        if paper.year:
            try:
                return _date(int(paper.year), 1, 1)
            except (TypeError, ValueError):
                pass
        if hasattr(paper, "created_at") and paper.created_at:
            return paper.created_at.date()
        return date.today()


# ---------------------------------------------------------------------------
# 검증 (T+1d / T+5d / T+30d abnormal return)
# ---------------------------------------------------------------------------


class HypothesisValidator:
    """가설 검증 — daily_prices 기반 abnormal return 계산"""

    def __init__(self, db: Session):
        self.db = db

    def validate_one(self, h: HypothesisLog) -> bool:
        """단일 가설 검증. T+5d 데이터 확보되면 status='validated' 처리.

        벤치마크(KOSDAQ 종합) 가용 시 abnormal return 사용, 미가용 시 종목 자체 수익률(raw)
        기준으로 hit 판정. 어느 경우든 validation_{t1d/t5d/t30d}_return 은 항상 적재.

        Returns: True if any update happened
        """
        if h.company_code not in VALIDATED_COMPANIES:
            return False
        if h.validation_status == "closed":
            return False

        ticker = price_svc.COMPANY_TICKER_MAP.get(h.company_code)
        if not ticker:
            return False

        anchor = h.trigger_date
        anchor_close = price_svc.next_trading_day_close(self.db, ticker, anchor)
        if not anchor_close:
            return False
        anchor_date, p0 = anchor_close
        if p0 <= 0:
            return False

        # 벤치마크는 옵션 — 없어도 진행
        market_close = price_svc.next_trading_day_close(self.db, "KOSDAQ", anchor)
        m0_date = market_close[0] if market_close else None
        m0 = market_close[1] if market_close else None
        has_benchmark = m0 is not None and m0 > 0

        updated = False
        for label, offset in T_PLUS_DAYS.items():
            stock_target = price_svc.trading_day_offset_close(self.db, ticker, anchor_date, offset)
            if not stock_target:
                continue
            _, p_n = stock_target
            stock_ret = (p_n - p0) / p0
            setattr(h, f"validation_{label}_return", Decimal(f"{stock_ret:.5f}"))

            if has_benchmark:
                market_target = price_svc.trading_day_offset_close(
                    self.db, "KOSDAQ", m0_date, offset
                )
                if market_target:
                    _, m_n = market_target
                    market_ret = (m_n - m0) / m0
                    abnormal = stock_ret - market_ret
                    setattr(h, f"market_{label}_return", Decimal(f"{market_ret:.5f}"))
                    setattr(h, f"abnormal_{label}", Decimal(f"{abnormal:.5f}"))
            updated = True

        # 적중 판정 (메인 KPI: T+5d) — abnormal 우선, 없으면 raw return
        signal_t5d = h.abnormal_t5d if h.abnormal_t5d is not None else h.validation_t5d_return
        if signal_t5d is not None:
            if h.impact_direction == "neutral":
                # neutral → |signal| < 1% 면 적중
                h.hit_t5d = abs(float(signal_t5d)) < 0.01
            else:
                expected_sign = 1 if h.impact_direction == "positive" else -1
                actual_sign = 1 if float(signal_t5d) > 0 else -1
                h.hit_t5d = expected_sign == actual_sign
            h.validation_status = "validated"
            h.validated_at = datetime.utcnow()
            updated = True
        elif (
            (h.abnormal_t1d is not None or h.validation_t1d_return is not None)
            and h.validation_status == "pending"
        ):
            h.validation_status = "partial"
            updated = True

        # 30d 데이터 확보 시 closed 처리
        signal_t30d = h.abnormal_t30d if h.abnormal_t30d is not None else h.validation_t30d_return
        if signal_t30d is not None:
            h.validation_status = "closed"
            updated = True

        if updated:
            self.db.commit()
        return updated

    def validate_pending(self, limit: int = 200) -> dict[str, int]:
        """status가 pending/partial인 가설들을 일괄 검증"""
        pending = (
            self.db.query(HypothesisLog)
            .filter(HypothesisLog.validation_status.in_(["pending", "partial", "validated"]))
            .filter(HypothesisLog.company_code.in_(VALIDATED_COMPANIES))
            .order_by(HypothesisLog.trigger_date.asc())
            .limit(limit)
            .all()
        )
        n_updated = 0
        for h in pending:
            if self.validate_one(h):
                n_updated += 1
        return {"checked": len(pending), "updated": n_updated}


# ---------------------------------------------------------------------------
# 적중률 통계
# ---------------------------------------------------------------------------

# 통계적 유의성 판정 — n 이 작으면 신뢰 구간이 넓어 의미 없음
MIN_N_FOR_SIGNIFICANCE = 30
WILSON_Z_95 = 1.959963984540054  # 95% CI z-score
SIGNIFICANCE_ALPHA = 0.05


def _wilson_ci(k: int, n: int, z: float = WILSON_Z_95) -> tuple[float, float] | tuple[None, None]:
    """Wilson score interval — 표본 작을 때 정규근사 CI 보다 robust.

    Returns: (lower, upper) clipped to [0, 1], n=0 시 (None, None)
    """
    import math

    if n == 0:
        return None, None
    p = k / n
    z2 = z * z
    denom = 1 + z2 / n
    center = (p + z2 / (2 * n)) / denom
    margin = (z * math.sqrt((p * (1 - p) + z2 / (4 * n)) / n)) / denom
    return max(0.0, center - margin), min(1.0, center + margin)


def _binomial_two_sided_pvalue(k: int, n: int, p0: float = 0.5) -> float | None:
    """양측 이항검정 — H0: 적중률 = p0 (기본 0.5, "동전던지기").

    n 이 큰 경우(>~500) 누적이 느려질 수 있으나 실제 가설 수는 회사당 수백건 수준.
    Returns: p-value ∈ [0, 1], n=0 시 None.
    """
    from math import comb

    if n == 0:
        return None
    expected = n * p0
    if k >= expected:
        tail = sum(comb(n, i) * (p0 ** i) * ((1 - p0) ** (n - i)) for i in range(k, n + 1))
    else:
        tail = sum(comb(n, i) * (p0 ** i) * ((1 - p0) ** (n - i)) for i in range(0, k + 1))
    return min(1.0, 2 * tail)


def _bucket_with_stats(total: int, hit: int) -> dict:
    """공통 통계 계산 — total/hit → hit_rate + CI + p-value + 충분성 판정"""
    if total == 0:
        return {
            "total": 0,
            "hit": 0,
            "hit_rate": None,
            "ci_low": None,
            "ci_high": None,
            "p_value": None,
            "is_significant": None,
            "insufficient_n": True,
        }
    hit_rate = hit / total
    ci_low, ci_high = _wilson_ci(hit, total)
    p_value = _binomial_two_sided_pvalue(hit, total)
    insufficient = total < MIN_N_FOR_SIGNIFICANCE
    is_significant = (
        None
        if insufficient or p_value is None
        else p_value < SIGNIFICANCE_ALPHA
    )
    return {
        "total": total,
        "hit": hit,
        "hit_rate": round(hit_rate, 3),
        "ci_low": round(ci_low, 3) if ci_low is not None else None,
        "ci_high": round(ci_high, 3) if ci_high is not None else None,
        "p_value": round(p_value, 4) if p_value is not None else None,
        "is_significant": is_significant,
        "insufficient_n": insufficient,
    }


def hypothesis_hit_rate(db: Session, *, since: date | None = None) -> dict[str, dict]:
    """회사별 / 방향별 적중률 통계 (T+5d 기준).

    각 버킷에 Wilson 95% CI + 양측 이항검정 p-value 포함.
    n < MIN_N_FOR_SIGNIFICANCE (=30) 인 경우 insufficient_n=True 로 표시 → UI 에서 "판단 보류".
    """
    q = db.query(HypothesisLog).filter(HypothesisLog.hit_t5d.isnot(None))
    if since:
        q = q.filter(HypothesisLog.trigger_date >= since)
    rows = q.all()

    # 1차 집계: total/hit 만
    raw: dict[str, dict] = {}
    for r in rows:
        bucket = raw.setdefault(r.company_code, {"total": 0, "hit": 0, "by_direction": {}})
        bucket["total"] += 1
        bucket["hit"] += 1 if r.hit_t5d else 0
        d_bucket = bucket["by_direction"].setdefault(
            r.impact_direction, {"total": 0, "hit": 0}
        )
        d_bucket["total"] += 1
        d_bucket["hit"] += 1 if r.hit_t5d else 0

    # 2차 보강: 통계 지표 부여
    summary: dict[str, dict] = {}
    for code, b in raw.items():
        company_stats = _bucket_with_stats(b["total"], b["hit"])
        company_stats["by_direction"] = {
            direction: _bucket_with_stats(d["total"], d["hit"])
            for direction, d in b["by_direction"].items()
        }
        summary[code] = company_stats

    return summary
