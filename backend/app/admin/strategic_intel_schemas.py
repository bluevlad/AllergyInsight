"""Strategic Intel Admin API 스키마"""
from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel


class TechCategoryItem(BaseModel):
    id: str
    name_kr: str
    name_en: str
    description: Optional[str] = None
    sort_order: int = 0


class FitCellItem(BaseModel):
    company_code: str
    tech_category_id: str
    fit_score: float
    rationale: Optional[str] = None
    version: str
    effective_from: date


class FitMatrixResponse(BaseModel):
    categories: list[TechCategoryItem]
    cells: list[FitCellItem]
    effective_on: date


class HypothesisItem(BaseModel):
    id: int
    trigger_type: str
    trigger_paper_id: Optional[int] = None
    trigger_news_id: Optional[int] = None
    trigger_date: date
    trigger_title: Optional[str] = None
    tech_categories: list[dict] = []
    company_code: str
    impact_direction: str
    impact_score: float
    fit_score_snapshot: Optional[float] = None
    rationale: str
    abnormal_t1d: Optional[float] = None
    abnormal_t5d: Optional[float] = None
    abnormal_t30d: Optional[float] = None
    market_t5d_return: Optional[float] = None
    validation_t5d_return: Optional[float] = None
    hit_t5d: Optional[bool] = None
    validation_status: str
    validated_at: Optional[datetime] = None
    benchmark_ticker: Optional[str] = None
    # Phase A-3 보조 시그널
    volume_zscore_t1d: Optional[float] = None
    market_cap_change_t5d: Optional[float] = None
    # Phase B — LLM 정성 보강
    qualitative_score: Optional[float] = None
    qualitative_rationale: Optional[str] = None
    qualitative_override: Optional[bool] = None
    qualitative_version: Optional[str] = None


class UnhitTechItem(BaseModel):
    tech_id: str
    total: int
    hit: int
    hit_rate: Optional[float] = None
    ci_low: Optional[float] = None
    ci_high: Optional[float] = None


class UnhitCompanyDirectionItem(BaseModel):
    company: str
    direction: str
    total: int
    hit: int
    hit_rate: Optional[float] = None
    ci_low: Optional[float] = None
    ci_high: Optional[float] = None


class UnhitClustersResponse(BaseModel):
    by_tech: list[UnhitTechItem] = []
    by_company_direction: list[UnhitCompanyDirectionItem] = []


class HypothesisListResponse(BaseModel):
    items: list[HypothesisItem]
    total: int
    page: int
    page_size: int


class ReportItem(BaseModel):
    id: int
    report_type: str
    period_start: date
    period_end: date
    title: str
    summary: Optional[str] = None
    trigger_hypothesis_id: Optional[int] = None
    metrics: Optional[dict] = None
    generated_at: datetime


class ReportDetail(ReportItem):
    content: str
    hypothesis_ids: list[int] = []


class ReportListResponse(BaseModel):
    items: list[ReportItem]
    total: int


class DirectionStats(BaseModel):
    """방향별 적중률 + 통계적 유의성"""
    total: int
    hit: int
    hit_rate: Optional[float] = None
    ci_low: Optional[float] = None         # Wilson 95% CI 하한
    ci_high: Optional[float] = None        # Wilson 95% CI 상한
    p_value: Optional[float] = None        # 양측 이항검정 p-value (H0: p=0.5)
    is_significant: Optional[bool] = None  # p < 0.05 AND n >= 30
    insufficient_n: bool = False           # n < 30 — 판단 보류


class HitRateBucket(DirectionStats):
    """회사별 종합 적중률 — DirectionStats + 방향별 분해"""
    by_direction: dict[str, DirectionStats] = {}


class QualitativeDrift(BaseModel):
    """LLM 정성 보강 vs 룰 결정 drift KPI (Phase B)"""
    n_total: int = 0
    n_enhanced: int = 0
    n_override: int = 0
    coverage: Optional[float] = None         # n_enhanced / n_total
    override_rate: Optional[float] = None    # n_override / n_enhanced


class StatsResponse(BaseModel):
    period_start: Optional[date] = None
    hit_rate: dict[str, HitRateBucket] = {}
    n_hypotheses: int
    n_validated: int
    tech_pulse: dict[str, int] = {}  # {tech_id: trigger_count}
    qualitative_drift: Optional[QualitativeDrift] = None


class GenerateMonthlyRequest(BaseModel):
    year: int
    month: int
