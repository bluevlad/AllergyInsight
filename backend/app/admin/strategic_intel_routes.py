"""Strategic Intel Admin API 라우터

내부 경영진 분석용 — super_admin 전용. 외부 사용자 노출 금지.

엔드포인트:
  GET  /admin/strategic-intel/matrix          — Tech Fit Matrix
  GET  /admin/strategic-intel/hypotheses      — 가설 목록 (필터)
  GET  /admin/strategic-intel/hypotheses/{id} — 가설 상세
  GET  /admin/strategic-intel/reports         — 리포트 목록
  GET  /admin/strategic-intel/reports/{id}    — 리포트 상세 (markdown 본문 포함)
  GET  /admin/strategic-intel/stats           — 적중률/Tech Pulse 통계
  POST /admin/strategic-intel/reports/event/{hypothesis_id}    — 이벤트 리포트 수동 발행
  POST /admin/strategic-intel/reports/monthly                   — 월간 리포트 수동 발행
"""
from collections import defaultdict
from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from .dependencies import require_super_admin
from .strategic_intel_schemas import (
    FitCellItem,
    FitMatrixResponse,
    GenerateMonthlyRequest,
    HitRateBucket,
    HypothesisItem,
    HypothesisListResponse,
    ReportDetail,
    ReportItem,
    ReportListResponse,
    StatsResponse,
    TechCategoryItem,
    UnhitClustersResponse,
)
from ..database.connection import get_db
from ..database.models import User
from ..database.strategic_intel_models import (
    CompanyTechFit,
    HypothesisLog,
    StrategicIntelReport,
    TechCategory,
)
from ..services.strategic_intel.hypothesis_engine import (
    ALL_COMPANIES,
    hypothesis_hit_rate,
    unhit_clusters,
)
from ..services.strategic_intel.report_service import StrategicIntelReportService

router = APIRouter(prefix="/strategic-intel", tags=["Strategic Intel"])


# ---------------------------------------------------------------------------
# Fit Matrix
# ---------------------------------------------------------------------------


@router.get("/matrix", response_model=FitMatrixResponse)
def get_fit_matrix(
    on_date: Optional[date] = Query(None, description="기준 일자 (기본: 오늘)"),
    _: User = Depends(require_super_admin),
    db: Session = Depends(get_db),
):
    eff = on_date or date.today()
    cats = db.query(TechCategory).filter(TechCategory.is_active.is_(True)).order_by(TechCategory.sort_order).all()
    cells = (
        db.query(CompanyTechFit)
        .filter(CompanyTechFit.effective_from <= eff)
        .filter(
            (CompanyTechFit.effective_to.is_(None)) | (CompanyTechFit.effective_to > eff)
        )
        .all()
    )
    return FitMatrixResponse(
        categories=[
            TechCategoryItem(
                id=c.id, name_kr=c.name_kr, name_en=c.name_en,
                description=c.description, sort_order=c.sort_order or 0,
            )
            for c in cats
        ],
        cells=[
            FitCellItem(
                company_code=c.company_code,
                tech_category_id=c.tech_category_id,
                fit_score=float(c.fit_score),
                rationale=c.rationale,
                version=c.version or "v1",
                effective_from=c.effective_from,
            )
            for c in cells
        ],
        effective_on=eff,
    )


# ---------------------------------------------------------------------------
# Hypotheses
# ---------------------------------------------------------------------------


@router.get("/hypotheses", response_model=HypothesisListResponse)
def list_hypotheses(
    page: int = Query(1, ge=1),
    page_size: int = Query(30, ge=1, le=200),
    company: Optional[str] = None,
    direction: Optional[str] = Query(None, description="positive|neutral|negative"),
    status: Optional[str] = None,
    hit: Optional[bool] = None,
    since: Optional[date] = None,
    until: Optional[date] = None,
    _: User = Depends(require_super_admin),
    db: Session = Depends(get_db),
):
    q = db.query(HypothesisLog)
    if company:
        q = q.filter(HypothesisLog.company_code == company)
    if direction:
        q = q.filter(HypothesisLog.impact_direction == direction)
    if status:
        q = q.filter(HypothesisLog.validation_status == status)
    if hit is not None:
        q = q.filter(HypothesisLog.hit_t5d == hit)
    if since:
        q = q.filter(HypothesisLog.trigger_date >= since)
    if until:
        q = q.filter(HypothesisLog.trigger_date <= until)

    total = q.count()
    rows = (
        q.order_by(HypothesisLog.trigger_date.desc(), HypothesisLog.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return HypothesisListResponse(
        items=[_to_hypothesis_item(h) for h in rows],
        total=total, page=page, page_size=page_size,
    )


@router.get("/hypotheses/{hypothesis_id}", response_model=HypothesisItem)
def get_hypothesis(
    hypothesis_id: int,
    _: User = Depends(require_super_admin),
    db: Session = Depends(get_db),
):
    h = db.query(HypothesisLog).filter(HypothesisLog.id == hypothesis_id).first()
    if not h:
        raise HTTPException(status_code=404, detail="가설을 찾을 수 없습니다.")
    return _to_hypothesis_item(h)


def _to_hypothesis_item(h: HypothesisLog) -> HypothesisItem:
    return HypothesisItem(
        id=h.id,
        trigger_type=h.trigger_type,
        trigger_paper_id=h.trigger_paper_id,
        trigger_news_id=h.trigger_news_id,
        trigger_date=h.trigger_date,
        trigger_title=h.trigger_title,
        tech_categories=h.tech_categories or [],
        company_code=h.company_code,
        impact_direction=h.impact_direction,
        impact_score=float(h.impact_score) if h.impact_score is not None else 0.0,
        fit_score_snapshot=float(h.fit_score_snapshot) if h.fit_score_snapshot is not None else None,
        rationale=h.rationale,
        abnormal_t1d=float(h.abnormal_t1d) if h.abnormal_t1d is not None else None,
        abnormal_t5d=float(h.abnormal_t5d) if h.abnormal_t5d is not None else None,
        abnormal_t30d=float(h.abnormal_t30d) if h.abnormal_t30d is not None else None,
        market_t5d_return=float(h.market_t5d_return) if h.market_t5d_return is not None else None,
        validation_t5d_return=float(h.validation_t5d_return) if h.validation_t5d_return is not None else None,
        hit_t5d=h.hit_t5d,
        validation_status=h.validation_status,
        validated_at=h.validated_at,
        benchmark_ticker=h.benchmark_ticker,
        volume_zscore_t1d=float(h.volume_zscore_t1d) if h.volume_zscore_t1d is not None else None,
        market_cap_change_t5d=float(h.market_cap_change_t5d) if h.market_cap_change_t5d is not None else None,
    )


# ---------------------------------------------------------------------------
# Reports
# ---------------------------------------------------------------------------


@router.get("/reports", response_model=ReportListResponse)
def list_reports(
    report_type: Optional[str] = Query(None, description="event|monthly"),
    page: int = Query(1, ge=1),
    page_size: int = Query(30, ge=1, le=100),
    _: User = Depends(require_super_admin),
    db: Session = Depends(get_db),
):
    q = db.query(StrategicIntelReport)
    if report_type:
        q = q.filter(StrategicIntelReport.report_type == report_type)
    total = q.count()
    rows = (
        q.order_by(StrategicIntelReport.generated_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return ReportListResponse(
        items=[
            ReportItem(
                id=r.id, report_type=r.report_type,
                period_start=r.period_start, period_end=r.period_end,
                title=r.title, summary=r.summary,
                trigger_hypothesis_id=r.trigger_hypothesis_id,
                metrics=r.metrics, generated_at=r.generated_at,
            )
            for r in rows
        ],
        total=total,
    )


@router.get("/reports/{report_id}", response_model=ReportDetail)
def get_report(
    report_id: int,
    _: User = Depends(require_super_admin),
    db: Session = Depends(get_db),
):
    r = db.query(StrategicIntelReport).filter(StrategicIntelReport.id == report_id).first()
    if not r:
        raise HTTPException(status_code=404, detail="리포트를 찾을 수 없습니다.")
    return ReportDetail(
        id=r.id, report_type=r.report_type,
        period_start=r.period_start, period_end=r.period_end,
        title=r.title, summary=r.summary,
        content=r.content,
        trigger_hypothesis_id=r.trigger_hypothesis_id,
        hypothesis_ids=r.hypothesis_ids or [],
        metrics=r.metrics, generated_at=r.generated_at,
    )


@router.post("/reports/event/{hypothesis_id}", response_model=ReportDetail)
def generate_event_report(
    hypothesis_id: int,
    _: User = Depends(require_super_admin),
    db: Session = Depends(get_db),
):
    h = db.query(HypothesisLog).filter(HypothesisLog.id == hypothesis_id).first()
    if not h:
        raise HTTPException(status_code=404, detail="가설을 찾을 수 없습니다.")
    svc = StrategicIntelReportService(db)
    r = svc.generate_event_report(h)
    if r is None:
        raise HTTPException(status_code=500, detail="리포트 생성 실패")
    return ReportDetail(
        id=r.id, report_type=r.report_type,
        period_start=r.period_start, period_end=r.period_end,
        title=r.title, summary=r.summary,
        content=r.content,
        trigger_hypothesis_id=r.trigger_hypothesis_id,
        hypothesis_ids=r.hypothesis_ids or [],
        metrics=r.metrics, generated_at=r.generated_at,
    )


@router.post("/reports/monthly", response_model=ReportDetail)
def generate_monthly_report(
    body: GenerateMonthlyRequest,
    _: User = Depends(require_super_admin),
    db: Session = Depends(get_db),
):
    svc = StrategicIntelReportService(db)
    r = svc.generate_monthly_report(body.year, body.month)
    if r is None:
        raise HTTPException(status_code=400, detail="해당 월에 가설 데이터가 없습니다.")
    return ReportDetail(
        id=r.id, report_type=r.report_type,
        period_start=r.period_start, period_end=r.period_end,
        title=r.title, summary=r.summary,
        content=r.content,
        trigger_hypothesis_id=r.trigger_hypothesis_id,
        hypothesis_ids=r.hypothesis_ids or [],
        metrics=r.metrics, generated_at=r.generated_at,
    )


# ---------------------------------------------------------------------------
# Stats
# ---------------------------------------------------------------------------


@router.get("/stats", response_model=StatsResponse)
def get_stats(
    since: Optional[date] = None,
    _: User = Depends(require_super_admin),
    db: Session = Depends(get_db),
):
    hr_raw = hypothesis_hit_rate(db, since=since)
    hr = {k: HitRateBucket(**v) for k, v in hr_raw.items()}

    q = db.query(HypothesisLog)
    if since:
        q = q.filter(HypothesisLog.trigger_date >= since)
    hypos = q.all()

    n_validated = sum(1 for h in hypos if h.hit_t5d is not None)
    tech_pulse: dict[str, int] = defaultdict(int)
    for h in hypos:
        for c in (h.tech_categories or []):
            if isinstance(c, dict) and c.get("id"):
                tech_pulse[c["id"]] += 1

    return StatsResponse(
        period_start=since,
        hit_rate=hr,
        n_hypotheses=len(hypos),
        n_validated=n_validated,
        tech_pulse=dict(tech_pulse),
    )


@router.get("/unhit-clusters", response_model=UnhitClustersResponse)
def get_unhit_clusters(
    since: Optional[date] = None,
    min_n: int = Query(5, ge=1, le=100, description="그룹 최소 표본"),
    top_k: int = Query(5, ge=1, le=20, description="각 축당 표시 그룹 수"),
    _: User = Depends(require_super_admin),
    db: Session = Depends(get_db),
):
    """미적중 클러스터 — 룰 캘리브레이션 후보 (Phase A-4).

    n>=min_n, hit_rate <= 0.5 인 그룹을 hit_rate 오름차순 top_k 반환.
    축: tech_category / company × direction.
    """
    return UnhitClustersResponse(**unhit_clusters(db, since=since, min_n=min_n, top_k=top_k))
