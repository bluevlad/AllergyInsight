"""분석 관리 API 라우터

예측 분석 시스템의 관리 엔드포인트:
- 월별 집계 실행
- 트렌드 조회
- 행동 로그 통계
"""
from datetime import date, datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func

from .dependencies import require_super_admin
from ..database.connection import get_db
from ..database.models import User
from ..database.analytics_models import AnalyticsSnapshot, KeywordTrend, PatientActivityLog
from ..services.analytics_service import AnalyticsService
from ..services.keyword_trend_service import KeywordTrendService

router = APIRouter()

_analytics_service = AnalyticsService()
_keyword_trend_service = KeywordTrendService()


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
    since = datetime.utcnow() - timedelta(days=days)

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
        PatientActivityLog.created_at >= datetime.utcnow() - timedelta(days=7)
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
