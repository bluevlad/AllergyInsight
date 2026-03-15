"""스케줄러 관리자 API"""
import logging
import threading

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from typing import Optional

from .dependencies import require_super_admin
from ..database.connection import get_db
from ..database.models import User
from ..database.scheduler_models import SchedulerExecutionLog

logger = logging.getLogger(__name__)

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


# ============================================================================
# 벌크 논문 수집
# ============================================================================

@router.post("/bulk-collect")
async def bulk_collect_papers(
    start_year: int = Query(2016, ge=2000, le=2030, description="수집 시작 연도"),
    end_year: int = Query(2026, ge=2000, le=2030, description="수집 종료 연도"),
    rebuild_rag: bool = Query(True, description="수집 후 RAG DB 재구축 여부"),
    current_user: User = Depends(require_super_admin),
):
    """연도별 논문 벌크 수집 (백그라운드 실행)

    최근 10년간 알러지 논문을 연도별로 수집하고 RAG DB를 재구축합니다.
    백그라운드에서 실행되며, 진행 상황은 /scheduler/history?job_id=bulk_paper_collect 에서 확인 가능합니다.
    """
    if start_year > end_year:
        raise HTTPException(status_code=400, detail="start_year는 end_year보다 작거나 같아야 합니다.")

    def _run_bulk():
        import time
        from datetime import datetime
        from ..database.connection import SessionLocal

        db = SessionLocal()
        log = None
        try:
            log = SchedulerExecutionLog(
                job_id="bulk_paper_collect",
                status="running",
                started_at=datetime.utcnow(),
                trigger_type="manual",
            )
            db.add(log)
            db.commit()
            db.refresh(log)

            from scripts.bulk_collect_papers import collect_year, rebuild_rag_db, ALL_ALLERGENS

            results = []
            for year in range(start_year, end_year + 1):
                try:
                    result = collect_year(year, ALL_ALLERGENS)
                    results.append(result)
                    logger.info(f"[bulk_collect] {year}: {result['total_new']}건 신규")
                except Exception as e:
                    logger.warning(f"[bulk_collect] {year} 실패: {e}")
                    results.append({"year": year, "total_found": 0, "total_new": 0, "error": str(e)})
                time.sleep(3)

            rag_result = None
            if rebuild_rag:
                rag_result = rebuild_rag_db()

            now = datetime.utcnow()
            log.status = "success"
            log.completed_at = now
            log.duration_seconds = (now - log.started_at).total_seconds()
            log.result_summary = {
                "years_processed": len(results),
                "total_found": sum(r.get("total_found", 0) for r in results),
                "total_new": sum(r.get("total_new", 0) for r in results),
                "year_details": {r["year"]: r.get("total_new", 0) for r in results},
                "rag_rebuild": rag_result,
            }
            db.commit()

        except Exception as e:
            if log:
                now = datetime.utcnow()
                log.status = "failed"
                log.completed_at = now
                log.duration_seconds = (now - log.started_at).total_seconds()
                log.error_message = str(e)
                db.commit()
            logger.error(f"[bulk_collect] 전체 실패: {e}")
        finally:
            db.close()

    thread = threading.Thread(target=_run_bulk, daemon=True)
    thread.start()

    return {
        "message": f"{start_year}~{end_year} 논문 벌크 수집이 백그라운드에서 시작되었습니다.",
        "years": list(range(start_year, end_year + 1)),
        "rebuild_rag": rebuild_rag,
        "check_progress": "/api/admin/scheduler/history?job_id=bulk_paper_collect",
    }
