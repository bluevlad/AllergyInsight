"""Public Analytics API - read-only aggregate statistics (no auth required)

Exposes aggregated platform statistics for public dashboards.
Never returns individual patient data or PII.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta, timezone
from typing import Optional

from ..database.connection import get_db
from ..database.models import User, UserDiagnosis, Paper
from ..database.competitor_models import CompetitorNews, CompetitorCompany
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


@router.get("/papers/stats")
def get_paper_collection_stats(db: Session = Depends(get_db)):
    """Public paper collection statistics - aggregate counts only, no PII."""
    from ..database.models import PaperAllergenLink

    total = db.query(func.count(Paper.id)).scalar() or 0

    # Source breakdown
    source_rows = db.query(
        Paper.source,
        func.count(Paper.id),
    ).group_by(Paper.source).all()
    by_source = {(src or "unknown"): cnt for src, cnt in source_rows}

    # Guideline count
    guideline_count = db.query(func.count(Paper.id)).filter(
        Paper.is_guideline == True
    ).scalar() or 0

    # Year distribution
    year_rows = db.query(
        Paper.year,
        func.count(Paper.id),
    ).filter(Paper.year.isnot(None)).group_by(Paper.year).order_by(Paper.year).all()
    by_year = {str(yr): cnt for yr, cnt in year_rows}

    # Top allergen links
    allergen_rows = db.query(
        PaperAllergenLink.allergen_code,
        func.count(PaperAllergenLink.id),
    ).group_by(PaperAllergenLink.allergen_code).order_by(
        func.count(PaperAllergenLink.id).desc()
    ).limit(15).all()
    top_allergen_links = [
        {"allergen_code": code, "paper_count": cnt}
        for code, cnt in allergen_rows
    ]

    # Link type distribution
    link_type_rows = db.query(
        PaperAllergenLink.link_type,
        func.count(PaperAllergenLink.id),
    ).group_by(PaperAllergenLink.link_type).all()
    by_link_type = {lt: cnt for lt, cnt in link_type_rows}

    # Recent papers (10)
    recent = db.query(Paper).order_by(Paper.created_at.desc()).limit(10).all()
    recent_papers = [
        {
            "title": p.title,
            "source": p.source,
            "year": p.year,
            "is_guideline": p.is_guideline,
            "created_at": p.created_at.isoformat() if p.created_at else None,
        }
        for p in recent
    ]

    return {
        "total": total,
        "guideline_count": guideline_count,
        "by_source": by_source,
        "by_year": by_year,
        "top_allergen_links": top_allergen_links,
        "by_link_type": by_link_type,
        "recent_papers": recent_papers,
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


# --- Public News (전일 수집 뉴스) ---

@router.get("/news/recent")
def get_recent_news(
    days: int = Query(default=1, ge=1, le=7, description="최근 N일 뉴스"),
    category: Optional[str] = Query(default=None, description="카테고리 필터"),
    limit: int = Query(default=30, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """최근 수집된 뉴스 목록 (공개, read-only). 중복 제외, 중요도순 정렬."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)

    query = (
        db.query(CompetitorNews)
        .join(CompetitorCompany, isouter=True)
        .filter(
            CompetitorNews.is_duplicate == False,
            CompetitorNews.created_at >= cutoff,
        )
    )

    if category:
        query = query.filter(CompetitorNews.category == category)

    news_items = query.order_by(
        CompetitorNews.importance_score.desc().nullslast(),
        CompetitorNews.published_at.desc().nullslast(),
        CompetitorNews.created_at.desc(),
    ).limit(limit).all()

    items = []
    for news in news_items:
        items.append({
            "id": news.id,
            "title": news.title,
            "description": news.description,
            "url": news.url,
            "source": news.source,
            "company_code": news.company.code if news.company else None,
            "company_name": news.company.name_kr if news.company else None,
            "published_at": news.published_at.isoformat() if news.published_at else None,
            "category": news.category,
            "summary": news.summary,
            "importance_score": news.importance_score,
        })

    # 카테고리별 건수
    cat_counts_query = (
        db.query(CompetitorNews.category, func.count(CompetitorNews.id))
        .filter(
            CompetitorNews.is_duplicate == False,
            CompetitorNews.created_at >= cutoff,
        )
        .group_by(CompetitorNews.category)
        .all()
    )
    by_category = {cat: cnt for cat, cnt in cat_counts_query}

    total = sum(by_category.values())

    return {
        "items": items,
        "total": total,
        "by_category": by_category,
        "days": days,
    }
