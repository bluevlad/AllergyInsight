"""Strategic Intel Admin API 스키마"""
from datetime import date, datetime
from typing import Any, Optional

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


class HitRateBucket(BaseModel):
    total: int
    hit: int
    hit_rate: Optional[float] = None
    by_direction: dict[str, dict[str, Any]] = {}


class StatsResponse(BaseModel):
    period_start: Optional[date] = None
    hit_rate: dict[str, HitRateBucket] = {}
    n_hypotheses: int
    n_validated: int
    tech_pulse: dict[str, int] = {}  # {tech_id: trigger_count}


class GenerateMonthlyRequest(BaseModel):
    year: int
    month: int
