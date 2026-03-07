"""스케줄러 관리자 API"""
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from typing import Optional

from .dependencies import require_super_admin
from ..database.connection import get_db
from ..database.models import User
from ..database.scheduler_models import SchedulerExecutionLog

router = APIRouter(prefix="/scheduler", tags=["Scheduler Admin"])


def _get_scheduler():
    """현재 스케줄러 서비스 인스턴스 반환"""
    from ..services.scheduler_service import get_scheduler_service
    service = get_scheduler_service()
    if service is None:
        raise HTTPException(status_code=503, detail="스케줄러가 비활성화되어 있습니다.")
    return service


# ============================================================================
# 스케줄러 상태
# ============================================================================

@router.get("/status")
async def get_scheduler_status(
    current_user: User = Depends(require_super_admin),
):
    """스케줄러 전체 상태"""
    scheduler = _get_scheduler()
    status = scheduler.get_status()
    jobs = scheduler.get_jobs()
    return {
        **status,
        "jobs": jobs,
    }


@router.get("/jobs")
async def get_scheduler_jobs(
    current_user: User = Depends(require_super_admin),
):
    """등록된 Job 목록 + 다음 실행시각"""
    scheduler = _get_scheduler()
    return {"jobs": scheduler.get_jobs()}


# ============================================================================
# Job 제어
# ============================================================================

@router.post("/jobs/{job_id}/trigger")
async def trigger_job(
    job_id: str,
    current_user: User = Depends(require_super_admin),
):
    """Job 수동 즉시 실행"""
    scheduler = _get_scheduler()
    success = scheduler.trigger_job(job_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Job '{job_id}'을(를) 찾을 수 없습니다.")
    return {"message": f"Job '{job_id}' 수동 실행이 시작되었습니다."}


@router.post("/jobs/{job_id}/pause")
async def pause_job(
    job_id: str,
    current_user: User = Depends(require_super_admin),
):
    """Job 일시중지"""
    scheduler = _get_scheduler()
    success = scheduler.pause_job(job_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Job '{job_id}'을(를) 찾을 수 없습니다.")
    return {"message": f"Job '{job_id}'이(가) 일시중지되었습니다."}


@router.post("/jobs/{job_id}/resume")
async def resume_job(
    job_id: str,
    current_user: User = Depends(require_super_admin),
):
    """Job 재개"""
    scheduler = _get_scheduler()
    success = scheduler.resume_job(job_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Job '{job_id}'을(를) 찾을 수 없습니다.")
    return {"message": f"Job '{job_id}'이(가) 재개되었습니다."}


# ============================================================================
# 실행 이력
# ============================================================================

@router.get("/history")
async def get_scheduler_history(
    job_id: Optional[str] = Query(None, description="Job ID 필터"),
    status: Optional[str] = Query(None, description="상태 필터 (success, failed, running)"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(require_super_admin),
    db: Session = Depends(get_db),
):
    """실행 이력 조회 (페이징, 필터)"""
    query = db.query(SchedulerExecutionLog)

    if job_id:
        query = query.filter(SchedulerExecutionLog.job_id == job_id)
    if status:
        query = query.filter(SchedulerExecutionLog.status == status)

    total = query.count()
    offset = (page - 1) * page_size
    logs = (
        query.order_by(SchedulerExecutionLog.started_at.desc())
        .offset(offset)
        .limit(page_size)
        .all()
    )

    items = [
        {
            "id": log.id,
            "job_id": log.job_id,
            "status": log.status,
            "started_at": log.started_at.isoformat() if log.started_at else None,
            "completed_at": log.completed_at.isoformat() if log.completed_at else None,
            "duration_seconds": log.duration_seconds,
            "result_summary": log.result_summary,
            "error_message": log.error_message,
            "trigger_type": log.trigger_type,
        }
        for log in logs
    ]

    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get("/history/{job_id}/latest")
async def get_latest_execution(
    job_id: str,
    current_user: User = Depends(require_super_admin),
    db: Session = Depends(get_db),
):
    """특정 Job의 최근 실행 기록"""
    log = (
        db.query(SchedulerExecutionLog)
        .filter(SchedulerExecutionLog.job_id == job_id)
        .order_by(SchedulerExecutionLog.started_at.desc())
        .first()
    )

    if not log:
        raise HTTPException(status_code=404, detail=f"Job '{job_id}'의 실행 기록이 없습니다.")

    return {
        "id": log.id,
        "job_id": log.job_id,
        "status": log.status,
        "started_at": log.started_at.isoformat() if log.started_at else None,
        "completed_at": log.completed_at.isoformat() if log.completed_at else None,
        "duration_seconds": log.duration_seconds,
        "result_summary": log.result_summary,
        "error_message": log.error_message,
        "trigger_type": log.trigger_type,
    }
