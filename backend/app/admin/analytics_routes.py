"""분석 관리 API 라우터

예측 분석 시스템의 관리 엔드포인트:
- 월별 집계 실행
- 트렌드 조회
- 행동 로그 통계
"""
from datetime import date, datetime
from typing import Optional

from ..utils.timezone import utc_now

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func

from .dependencies import require_super_admin
from ..database.connection import get_db
from ..database.models import User
from ..database.analytics_models import AnalyticsSnapshot, KeywordTrend, PatientActivityLog
from ..services.analytics_service import AnalyticsService
from ..services.keyword_trend_service import KeywordTrendService
from ..services.allergen_trend_service import AllergenTrendService
from ..services.treatment_extraction_service import TreatmentExtractionService

router = APIRouter()

_analytics_service = AnalyticsService()
_keyword_trend_service = KeywordTrendService()
_allergen_trend_service = AllergenTrendService()
_treatment_service = TreatmentExtractionService()


# ============================================================================
# 임상 트렌드 분석 (Module A)
# ============================================================================

@router.post("/analytics/aggregate")
async def run_aggregation(
    year: Optional[int] = Query(None, description="집계 연도 (미지정 시 전체)"),
    month: Optional[int] = Query(None, ge=1, le=12, description="집계 월"),
    current_user: User = Depends(require_super_admin),
    db: Session = Depends(get_db),
):
    """월별 알러젠 양성률 집계 실행"""
    if year and month:
        result = _analytics_service.aggregate_monthly(db, year, month)
        return {"success": True, "results": [result]}
    else:
        results = _analytics_service.aggregate_all_months(db)
        return {"success": True, "results": results}


@router.get("/analytics/overview")
async def get_analytics_overview(
    current_user: User = Depends(require_super_admin),
    db: Session = Depends(get_db),
):
    """최근 월별 집계 개요"""
    return _analytics_service.get_overview(db)


@router.get("/analytics/trend/{allergen_code}")
async def get_allergen_trend(
    allergen_code: str,
    limit: int = Query(12, ge=1, le=60, description="조회 개월 수"),
    current_user: User = Depends(require_super_admin),
    db: Session = Depends(get_db),
):
    """특정 알러젠의 양성률 트렌드 조회"""
    trend = _analytics_service.get_allergen_trend(db, allergen_code, limit=limit)
    return {"allergen_code": allergen_code, "trend": trend}


# ============================================================================
# 키워드 트렌드 (Module B)
# ============================================================================

@router.post("/analytics/keywords/extract")
async def run_keyword_extraction(
    year: Optional[int] = Query(None, description="추출 연도 (미지정 시 전체)"),
    month: Optional[int] = Query(None, ge=1, le=12, description="추출 월"),
    current_user: User = Depends(require_super_admin),
    db: Session = Depends(get_db),
):
    """뉴스 키워드 트렌드 추출 실행"""
    if year and month:
        result = _keyword_trend_service.extract_monthly(db, year, month)
        return {"success": True, "results": [result]}
    else:
        results = _keyword_trend_service.extract_all_months(db)
        return {"success": True, "results": results}


@router.get("/analytics/keywords/overview")
async def get_keyword_overview(
    current_user: User = Depends(require_super_admin),
    db: Session = Depends(get_db),
):
    """최근 키워드 트렌드 개요"""
    return _keyword_trend_service.get_overview(db)


@router.get("/analytics/keywords/trend")
async def get_keyword_trend(
    keyword: Optional[str] = Query(None, description="특정 키워드"),
    category: Optional[str] = Query(None, description="카테고리 필터"),
    limit: int = Query(12, ge=1, le=60),
    current_user: User = Depends(require_super_admin),
    db: Session = Depends(get_db),
):
    """키워드 트렌드 조회"""
    trend = _keyword_trend_service.get_keyword_trend(db, keyword, category, limit)
    return {"trend": trend}


# ============================================================================
# 논문 알러젠 트렌드 (Module D)
# ============================================================================

@router.post("/analytics/paper-trend/aggregate")
async def run_paper_trend_aggregation(
    year: Optional[int] = Query(None, description="집계 연도 (미지정 시 전체)"),
    current_user: User = Depends(require_super_admin),
    db: Session = Depends(get_db),
):
    """논문 알러젠 언급률 트렌드 집계 실행"""
    if year:
        result = _allergen_trend_service.aggregate_yearly(db, year)
        return {"success": True, "results": [result]}
    else:
        results = _allergen_trend_service.aggregate_all_years(db)
        return {"success": True, "results": results}


@router.get("/analytics/paper-trend/overview")
async def get_paper_trend_overview(
    current_user: User = Depends(require_super_admin),
    db: Session = Depends(get_db),
):
    """논문 알러젠 트렌드 개요"""
    return _allergen_trend_service.get_overview(db)


@router.get("/analytics/paper-trend/{allergen_code}")
async def get_paper_trend_detail(
    allergen_code: str,
    period: str = Query("yearly", regex="^(yearly|quarterly)$"),
    limit: int = Query(20, ge=1, le=50),
    current_user: User = Depends(require_super_admin),
    db: Session = Depends(get_db),
):
    """특정 알러젠의 논문 언급률 트렌드"""
    return _allergen_trend_service.get_allergen_paper_trend(
        db, allergen_code, period_type=period, limit=limit
    )


# ============================================================================
# 치료법 추출 및 트렌드 (Module E)
# ============================================================================

@router.post("/analytics/treatments/extract")
async def run_treatment_extraction(
    limit: int = Query(100, ge=1, le=500, description="처리할 논문 수"),
    current_user: User = Depends(require_super_admin),
    db: Session = Depends(get_db),
):
    """논문에서 치료법 엔티티 배치 추출"""
    return _treatment_service.extract_from_papers(db, limit=limit)


@router.post("/analytics/treatments/aggregate")
async def run_treatment_trend_aggregation(
    current_user: User = Depends(require_super_admin),
    db: Session = Depends(get_db),
):
    """치료법 트렌드 집계 실행"""
    return _treatment_service.aggregate_trends(db)


@router.get("/analytics/treatments/overview")
async def get_treatment_overview(
    current_user: User = Depends(require_super_admin),
    db: Session = Depends(get_db),
):
    """치료법 트렌드 개요"""
    return _treatment_service.get_overview(db)


# ============================================================================
# 환자 행동 통계 (Module C)
# ============================================================================

@router.get("/analytics/activity/stats")
async def get_activity_stats(
    days: int = Query(30, ge=1, le=365, description="조회 기간 (일)"),
    current_user: User = Depends(require_super_admin),
    db: Session = Depends(get_db),
):
    """환자 행동 로그 통계"""
    from datetime import timedelta
    since = utc_now() - timedelta(days=days)

    # 총 로그 수
    total = db.query(func.count(PatientActivityLog.id)).filter(
        PatientActivityLog.created_at >= since
    ).scalar()

    # 행동 유형별 집계
    by_action = db.query(
        PatientActivityLog.action_type,
        func.count(PatientActivityLog.id),
    ).filter(
        PatientActivityLog.created_at >= since
    ).group_by(PatientActivityLog.action_type).all()

    # 리소스 유형별 집계
    by_resource = db.query(
        PatientActivityLog.resource_type,
        func.count(PatientActivityLog.id),
    ).filter(
        PatientActivityLog.created_at >= since,
        PatientActivityLog.resource_type.isnot(None),
    ).group_by(PatientActivityLog.resource_type).all()

    # 고유 사용자 수
    unique_users = db.query(
        func.count(func.distinct(PatientActivityLog.user_id))
    ).filter(
        PatientActivityLog.created_at >= since,
        PatientActivityLog.user_id.isnot(None),
    ).scalar()

    # 일별 활동 추이 (최근 7일)
    daily_counts = db.query(
        func.date(PatientActivityLog.created_at).label("day"),
        func.count(PatientActivityLog.id),
    ).filter(
        PatientActivityLog.created_at >= utc_now() - timedelta(days=7)
    ).group_by("day").order_by("day").all()

    return {
        "period_days": days,
        "total_logs": total,
        "unique_users": unique_users,
        "by_action": {action: count for action, count in by_action},
        "by_resource": {resource: count for resource, count in by_resource},
        "daily_trend": [
            {"date": str(day), "count": count}
            for day, count in daily_counts
        ],
    }
