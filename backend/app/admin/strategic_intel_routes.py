"""Strategic Intel Admin API 라우터

내부 경영진 분석용 — super_admin 전용. 외부 사용자 노출 금지.

엔드포인트:
  GET  /admin/strategic-intel/matrix          — Tech Fit Matrix (현재 시점)
  GET  /admin/strategic-intel/matrix/history  — Fit Matrix 변경 이력 (Phase E)
  GET  /admin/strategic-intel/hypotheses      — 가설 목록 (필터)
  GET  /admin/strategic-intel/hypotheses/{id} — 가설 상세
  GET  /admin/strategic-intel/reports         — 리포트 목록
  GET  /admin/strategic-intel/reports/{id}    — 리포트 상세 (markdown 본문 + 워터마크)
  GET  /admin/strategic-intel/stats           — 적중률/Tech Pulse/Drift/Audit 요약
  GET  /admin/strategic-intel/unhit-clusters  — 룰 캘리브레이션 후보
  GET  /admin/strategic-intel/audit-logs      — 접근 audit 조회 (Phase E)
  POST /admin/strategic-intel/reports/event/{hypothesis_id}    — 이벤트 리포트 수동 발행
  POST /admin/strategic-intel/reports/monthly                   — 월간 리포트 수동 발행

Phase E 거버넌스:
  - 모든 조회·발행 액션은 audit_service.record() 로 기록
  - 리포트 본문은 열람 시 super_admin email + 시각 워터마크 prepend
"""
from collections import defaultdict
from datetime import date, datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session

from .dependencies import require_super_admin
from .strategic_intel_schemas import (
    AuditLogItem,
    AuditLogListResponse,
    FitCellItem,
    FitMatrixHistoryResponse,
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
from ..services.strategic_intel import audit_service
from ..services.strategic_intel.hypothesis_engine import (
    ALL_COMPANIES,
    hypothesis_hit_rate,
    unhit_clusters,
)
from ..services.strategic_intel.qualitative_enhancer import qualitative_drift
from ..services.strategic_intel.report_service import StrategicIntelReportService

router = APIRouter(prefix="/strategic-intel", tags=["Strategic Intel"])


def _watermark(content: str, user: User) -> str:
    """리포트 본문 상단에 열람자/시각 워터마크 prepend (Phase E)"""
    ts = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    email = getattr(user, "email", "(unknown)")
    header = (
        f"<!-- Strategic Intel · 내부 자료 — 외부 노출 금지 -->\n"
        f"> 🔒 **열람**: {email} · {ts}\n"
        f"> 본 리포트는 내부 경영 의사결정 보조용이며, 외부 공유·인용·투자 자문이 아닙니다.\n\n"
    )
    return header + (content or "")


# ---------------------------------------------------------------------------
# Fit Matrix
# ---------------------------------------------------------------------------


@router.get("/matrix", response_model=FitMatrixResponse)
def get_fit_matrix(
    request: Request,
    on_date: Optional[date] = Query(None, description="기준 일자 (기본: 오늘)"),
    user: User = Depends(require_super_admin),
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
    audit_service.record(
        db, user, "view_matrix",
        resource_type="matrix", metadata={"on_date": eff.isoformat()}, request=request,
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
                effective_to=c.effective_to,
            )
            for c in cells
        ],
        effective_on=eff,
    )


@router.get("/matrix/history", response_model=FitMatrixHistoryResponse)
def get_fit_matrix_history(
    request: Request,
    company: Optional[str] = Query(None, description="회사 코드로 필터"),
    user: User = Depends(require_super_admin),
    db: Session = Depends(get_db),
):
    """Fit Matrix 시점성 변경 이력 — effective_from / effective_to 활용 (Phase E)"""
    q = db.query(CompanyTechFit).order_by(
        CompanyTechFit.company_code.asc(),
        CompanyTechFit.tech_category_id.asc(),
        CompanyTechFit.effective_from.asc(),
    )
    if company:
        q = q.filter(CompanyTechFit.company_code == company)
    rows = q.all()
    audit_service.record(
        db, user, "view_matrix_history",
        resource_type="matrix",
        metadata={"company": company} if company else None,
        request=request,
    )
    return FitMatrixHistoryResponse(
        cells=[
            FitCellItem(
                company_code=c.company_code,
                tech_category_id=c.tech_category_id,
                fit_score=float(c.fit_score),
                rationale=c.rationale,
                version=c.version or "v1",
                effective_from=c.effective_from,
                effective_to=c.effective_to,
            )
            for c in rows
        ],
    )


# ---------------------------------------------------------------------------
# Hypotheses
# ---------------------------------------------------------------------------


@router.get("/hypotheses", response_model=HypothesisListResponse)
def list_hypotheses(
    request: Request,
    page: int = Query(1, ge=1),
    page_size: int = Query(30, ge=1, le=200),
    company: Optional[str] = None,
    direction: Optional[str] = Query(None, description="positive|neutral|negative"),
    status: Optional[str] = None,
    hit: Optional[bool] = None,
    since: Optional[date] = None,
    until: Optional[date] = None,
    user: User = Depends(require_super_admin),
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
    audit_service.record(
        db, user, "list_hypotheses",
        resource_type="hypothesis",
        metadata={
            "page": page, "page_size": page_size,
            "company": company, "direction": direction,
            "status": status, "hit": hit,
            "since": since.isoformat() if since else None,
            "until": until.isoformat() if until else None,
            "total": total,
        },
        request=request,
    )
    return HypothesisListResponse(
        items=[_to_hypothesis_item(h) for h in rows],
        total=total, page=page, page_size=page_size,
    )


@router.get("/hypotheses/{hypothesis_id}", response_model=HypothesisItem)
def get_hypothesis(
    hypothesis_id: int,
    request: Request,
    user: User = Depends(require_super_admin),
    db: Session = Depends(get_db),
):
    h = db.query(HypothesisLog).filter(HypothesisLog.id == hypothesis_id).first()
    if not h:
        raise HTTPException(status_code=404, detail="가설을 찾을 수 없습니다.")
    audit_service.record(
        db, user, "view_hypothesis",
        resource_type="hypothesis", resource_id=hypothesis_id, request=request,
    )
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
        qualitative_score=float(h.qualitative_score) if h.qualitative_score is not None else None,
        qualitative_rationale=h.qualitative_rationale,
        qualitative_override=h.qualitative_override,
        qualitative_version=h.qualitative_version,
    )


# ---------------------------------------------------------------------------
# Reports
# ---------------------------------------------------------------------------


@router.get("/reports", response_model=ReportListResponse)
def list_reports(
    request: Request,
    report_type: Optional[str] = Query(None, description="event|monthly"),
    page: int = Query(1, ge=1),
    page_size: int = Query(30, ge=1, le=100),
    user: User = Depends(require_super_admin),
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
    audit_service.record(
        db, user, "list_reports",
        resource_type="report",
        metadata={"report_type": report_type, "page": page, "total": total},
        request=request,
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
    request: Request,
    user: User = Depends(require_super_admin),
    db: Session = Depends(get_db),
):
    r = db.query(StrategicIntelReport).filter(StrategicIntelReport.id == report_id).first()
    if not r:
        raise HTTPException(status_code=404, detail="리포트를 찾을 수 없습니다.")
    audit_service.record(
        db, user, "view_report",
        resource_type="report", resource_id=report_id,
        metadata={"report_type": r.report_type, "title": r.title},
        request=request,
    )
    return ReportDetail(
        id=r.id, report_type=r.report_type,
        period_start=r.period_start, period_end=r.period_end,
        title=r.title, summary=r.summary,
        content=_watermark(r.content, user),
        trigger_hypothesis_id=r.trigger_hypothesis_id,
        hypothesis_ids=r.hypothesis_ids or [],
        metrics=r.metrics, generated_at=r.generated_at,
    )


@router.post("/reports/event/{hypothesis_id}", response_model=ReportDetail)
def generate_event_report(
    hypothesis_id: int,
    request: Request,
    user: User = Depends(require_super_admin),
    db: Session = Depends(get_db),
):
    h = db.query(HypothesisLog).filter(HypothesisLog.id == hypothesis_id).first()
    if not h:
        raise HTTPException(status_code=404, detail="가설을 찾을 수 없습니다.")
    svc = StrategicIntelReportService(db)
    r = svc.generate_event_report(h)
    if r is None:
        raise HTTPException(status_code=500, detail="리포트 생성 실패")
    audit_service.record(
        db, user, "generate_event_report",
        resource_type="report", resource_id=r.id,
        metadata={"hypothesis_id": hypothesis_id, "company": h.company_code},
        request=request,
    )
    return ReportDetail(
        id=r.id, report_type=r.report_type,
        period_start=r.period_start, period_end=r.period_end,
        title=r.title, summary=r.summary,
        content=_watermark(r.content, user),
        trigger_hypothesis_id=r.trigger_hypothesis_id,
        hypothesis_ids=r.hypothesis_ids or [],
        metrics=r.metrics, generated_at=r.generated_at,
    )


@router.post("/reports/monthly", response_model=ReportDetail)
def generate_monthly_report(
    body: GenerateMonthlyRequest,
    request: Request,
    user: User = Depends(require_super_admin),
    db: Session = Depends(get_db),
):
    svc = StrategicIntelReportService(db)
    r = svc.generate_monthly_report(body.year, body.month)
    if r is None:
        raise HTTPException(status_code=400, detail="해당 월에 가설 데이터가 없습니다.")
    audit_service.record(
        db, user, "generate_monthly_report",
        resource_type="report", resource_id=r.id,
        metadata={"year": body.year, "month": body.month},
        request=request,
    )
    return ReportDetail(
        id=r.id, report_type=r.report_type,
        period_start=r.period_start, period_end=r.period_end,
        title=r.title, summary=r.summary,
        content=_watermark(r.content, user),
        trigger_hypothesis_id=r.trigger_hypothesis_id,
        hypothesis_ids=r.hypothesis_ids or [],
        metrics=r.metrics, generated_at=r.generated_at,
    )


# ---------------------------------------------------------------------------
# Stats
# ---------------------------------------------------------------------------


@router.get("/stats", response_model=StatsResponse)
def get_stats(
    request: Request,
    since: Optional[date] = None,
    user: User = Depends(require_super_admin),
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

    audit_summary = audit_service.recent_summary(db, hours=24)
    audit_service.record(
        db, user, "view_stats",
        resource_type="stats",
        metadata={"since": since.isoformat() if since else None},
        request=request,
    )
    return StatsResponse(
        period_start=since,
        hit_rate=hr,
        n_hypotheses=len(hypos),
        n_validated=n_validated,
        tech_pulse=dict(tech_pulse),
        qualitative_drift=qualitative_drift(db, since=since),
        audit_summary=audit_summary,
    )


@router.get("/unhit-clusters", response_model=UnhitClustersResponse)
def get_unhit_clusters(
    request: Request,
    since: Optional[date] = None,
    min_n: int = Query(5, ge=1, le=100, description="그룹 최소 표본"),
    top_k: int = Query(5, ge=1, le=20, description="각 축당 표시 그룹 수"),
    user: User = Depends(require_super_admin),
    db: Session = Depends(get_db),
):
    """미적중 클러스터 — 룰 캘리브레이션 후보 (Phase A-4).

    n>=min_n, hit_rate <= 0.5 인 그룹을 hit_rate 오름차순 top_k 반환.
    축: tech_category / company × direction.
    """
    audit_service.record(
        db, user, "view_unhit_clusters",
        resource_type="unhit_clusters",
        metadata={"min_n": min_n, "top_k": top_k}, request=request,
    )
    return UnhitClustersResponse(**unhit_clusters(db, since=since, min_n=min_n, top_k=top_k))


# ---------------------------------------------------------------------------
# Audit Logs (Phase E)
# ---------------------------------------------------------------------------


@router.get("/audit-logs", response_model=AuditLogListResponse)
def list_audit_logs(
    request: Request,
    user_email: Optional[str] = Query(None, description="특정 사용자만"),
    action_type: Optional[str] = Query(None, description="특정 액션만"),
    since: Optional[datetime] = Query(None, description="UTC ISO 시작 시각"),
    until: Optional[datetime] = Query(None, description="UTC ISO 종료 시각"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    user: User = Depends(require_super_admin),
    db: Session = Depends(get_db),
):
    """Strategic Intel 접근 audit 로그 (Phase E)"""
    rows, total = audit_service.list_logs(
        db,
        user_email=user_email,
        action_type=action_type,
        since=since,
        until=until,
        limit=page_size,
        offset=(page - 1) * page_size,
    )
    # audit-logs 조회 자체는 audit 하지 않음 (재귀 회피)
    return AuditLogListResponse(
        items=[
            AuditLogItem(
                id=r.id,
                user_email=r.user_email,
                action_type=r.action_type,
                resource_type=r.resource_type,
                resource_id=r.resource_id,
                metadata_json=r.metadata_json,
                ip_hash=r.ip_hash,
                accessed_at=r.accessed_at,
            )
            for r in rows
        ],
        total=total,
        page=page,
        page_size=page_size,
    )
