"""APScheduler 기반 통합 스케줄러 서비스

BackgroundScheduler를 래핑하여 6개 Job을 관리합니다.
- AllergyInsight 기존 3개: 논문 검색, 뉴스레터 동기화, 한국어 번역
- HealthPulse 통합 2개: 뉴스 수집 파이프라인, 뉴스레터 발송
- 분석 집계 1개: 알러젠 양성률 + 키워드 트렌드
"""
import logging
import os
from datetime import datetime
from typing import Optional

from apscheduler.executors.pool import ThreadPoolExecutor
from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.schedulers.background import BackgroundScheduler

from .scheduler_jobs import (
    job_daily_paper_search,
    job_newsletter_sync,
    job_korean_translation,
    job_news_pipeline,
    job_newsletter_send,
    job_analytics_aggregation,
)

logger = logging.getLogger(__name__)


class SchedulerService:
    """APScheduler BackgroundScheduler 래퍼"""

    def __init__(self):
        self._scheduler = BackgroundScheduler(
            jobstores={"default": MemoryJobStore()},
            executors={"default": ThreadPoolExecutor(3)},
            job_defaults={
                "coalesce": True,
                "max_instances": 1,
                "misfire_grace_time": 3600,
            },
            timezone="Asia/Seoul",
        )
        self._register_jobs()

    def _register_jobs(self) -> None:
        """6개 Job 등록 (CronTrigger)"""
        # Job 1: 일일 논문 검색 (02:00 KST)
        self._scheduler.add_job(
            job_daily_paper_search,
            "cron",
            hour=2, minute=0,
            id="daily_paper_search",
            name="일일 논문 검색",
            replace_existing=True,
        )
        # Job 2: 뉴스레터 DB 증분 동기화 (03:00 KST)
        self._scheduler.add_job(
            job_newsletter_sync,
            "cron",
            hour=3, minute=0,
            id="newsletter_sync",
            name="뉴스레터 동기화",
            replace_existing=True,
        )
        # Job 3: 한국어 번역 (04:00 KST)
        self._scheduler.add_job(
            job_korean_translation,
            "cron",
            hour=4, minute=0,
            id="korean_translation",
            name="한국어 번역",
            replace_existing=True,
        )
        # Job 4: 뉴스 수집 파이프라인 (환경변수 CRAWL_HOUR/CRAWL_MINUTE, 기본 07:00 KST)
        crawl_hour = int(os.getenv("CRAWL_HOUR", "7"))
        crawl_minute = int(os.getenv("CRAWL_MINUTE", "0"))
        self._scheduler.add_job(
            job_news_pipeline,
            "cron",
            hour=crawl_hour, minute=crawl_minute,
            id="news_pipeline",
            name="뉴스 수집 파이프라인",
            replace_existing=True,
        )
        # Job 5: 분석 집계 (05:00 KST - 뉴스 수집 후, 뉴스레터 발송 전)
        self._scheduler.add_job(
            job_analytics_aggregation,
            "cron",
            hour=5, minute=0,
            id="analytics_aggregation",
            name="분석 집계 (알러젠+키워드)",
            replace_existing=True,
        )
        # Job 6: 뉴스레터 발송 (환경변수 SEND_HOUR/SEND_MINUTE, 기본 08:00 KST)
        send_hour = int(os.getenv("SEND_HOUR", "8"))
        send_minute = int(os.getenv("SEND_MINUTE", "0"))
        self._scheduler.add_job(
            job_newsletter_send,
            "cron",
            hour=send_hour, minute=send_minute,
            id="newsletter_send",
            name="뉴스레터 발송",
            replace_existing=True,
        )

    def start(self) -> None:
        """스케줄러 시작"""
        if not self._scheduler.running:
            self._scheduler.start()
            logger.info("통합 스케줄러 시작됨 (6개 Job)")

    def shutdown(self) -> None:
        """스케줄러 종료"""
        if self._scheduler.running:
            self._scheduler.shutdown(wait=False)
            logger.info("통합 스케줄러 종료됨")

    def get_status(self) -> dict:
        """스케줄러 상태 조회"""
        return {
            "running": self._scheduler.running,
            "job_count": len(self._scheduler.get_jobs()),
            "timezone": str(self._scheduler.timezone),
        }

    def get_jobs(self) -> list[dict]:
        """등록된 Job 목록"""
        jobs = []
        for job in self._scheduler.get_jobs():
            next_run = getattr(job, "next_run_time", None)
            jobs.append({
                "id": job.id,
                "name": job.name,
                "next_run_time": next_run.isoformat() if next_run else None,
                "paused": next_run is None,
            })
        return jobs

    def trigger_job(self, job_id: str) -> bool:
        """수동 즉시 실행"""
        job = self._scheduler.get_job(job_id)
        if not job:
            return False

        from concurrent.futures import ThreadPoolExecutor as TPE
        executor = TPE(max_workers=1)
        executor.submit(job.func, "manual")
        executor.shutdown(wait=False)
        return True

    def pause_job(self, job_id: str) -> bool:
        """Job 일시중지"""
        try:
            self._scheduler.pause_job(job_id)
            return True
        except Exception:
            return False

    def resume_job(self, job_id: str) -> bool:
        """Job 재개"""
        try:
            self._scheduler.resume_job(job_id)
            return True
        except Exception:
            return False


# ============================================================================
# 싱글톤 접근자
# ============================================================================

_scheduler_service: Optional[SchedulerService] = None


def get_scheduler_service() -> SchedulerService:
    """SchedulerService 싱글톤 인스턴스 반환"""
    global _scheduler_service
    if _scheduler_service is None:
        _scheduler_service = SchedulerService()
    return _scheduler_service
