"""Public Analytics API - read-only aggregate statistics (no auth required)

Exposes aggregated platform statistics for public dashboards.
Never returns individual patient data or PII.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from ..database.connection import get_db
from ..database.models import User, UserDiagnosis, Paper
from ..services.analytics_service import AnalyticsService
from ..services.keyword_trend_service import KeywordTrendService
from ..services.insight_report_service import InsightReportService

router = APIRouter()

_analytics_service = AnalyticsService()
_keyword_trend_service = KeywordTrendService()
_insight_service = InsightReportService()


@router.get("/overview")
def get_analytics_overview(db: Session = Depends(get_db)):
    """Analytics overview - allergen positive rates summary (latest month)."""
    return _analytics_service.get_overview(db)


@router.get("/trend/{allergen_code}")
def get_allergen_trend(
    allergen_code: str,
    limit: int = Query(default=12, ge=1, le=60),
    db: Session = Depends(get_db),
):
    """Allergen trend data for a specific allergen code."""
    return _analytics_service.get_allergen_trend(db, allergen_code, limit=limit)


@router.get("/keywords/overview")
def get_keywords_overview(db: Session = Depends(get_db)):
    """Keyword trends overview - latest period grouped by category."""
    return _keyword_trend_service.get_overview(db)


@router.get("/keywords/trend")
def get_keyword_trend(
    keyword: str | None = Query(default=None),
    category: str | None = Query(default=None),
    limit: int = Query(default=12, ge=1, le=60),
    db: Session = Depends(get_db),
):
    """Keyword trend data, optionally filtered by keyword and/or category."""
    return _keyword_trend_service.get_keyword_trend(db, keyword, category, limit)


@router.get("/summary")
def get_platform_summary(db: Session = Depends(get_db)):
    """High-level platform summary - aggregate counts only, no PII."""
    total_users = db.query(func.count(User.id)).scalar() or 0
    total_diagnoses = db.query(func.count(UserDiagnosis.id)).scalar() or 0
    total_papers = db.query(func.count(Paper.id)).scalar() or 0

    return {
        "total_users": total_users,
        "total_diagnoses": total_diagnoses,
        "total_papers": total_papers,
    }


# --- Allergen Insight Reports ---

@router.get("/insights")
def get_insight_reports(
    allergen: str | None = Query(default=None),
    limit: int = Query(default=12, ge=1, le=60),
    db: Session = Depends(get_db),
):
    """Allergen insight reports list, optionally filtered by allergen code."""
    return _insight_service.get_reports(db, allergen_code=allergen, limit=limit)


@router.get("/insights/allergens")
def get_insight_allergens(db: Session = Depends(get_db)):
    """Available allergens with insight reports."""
    return _insight_service.get_available_allergens(db)


@router.get("/insights/{report_id}")
def get_insight_detail(report_id: int, db: Session = Depends(get_db)):
    """Allergen insight report detail."""
    report = _insight_service.get_report_detail(db, report_id)
    if not report:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Report not found")
    return report
