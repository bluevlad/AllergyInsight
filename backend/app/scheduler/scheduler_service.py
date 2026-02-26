"""뉴스 스케줄러 서비스

APScheduler BackgroundScheduler를 래핑하여
뉴스 수집/발송 작업을 스케줄링합니다.
"""
import os
import logging
from typing import Optional

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

logger = logging.getLogger(__name__)


class NewsSchedulerService:
    """뉴스 수집/발송 스케줄러"""

    def __init__(self):
        self._scheduler = BackgroundScheduler(
            job_defaults={
                "coalesce": True,
                "max_instances": 1,
                "misfire_grace_time": 300,
            }
        )
        self._running = False

    @property
    def is_running(self) -> bool:
        return self._running

    def start(self):
        """스케줄러 시작"""
        if self._running:
            logger.warning("스케줄러가 이미 실행 중입니다")
            return

        crawl_hour = int(os.getenv("CRAWL_HOUR", "7"))
        crawl_minute = int(os.getenv("CRAWL_MINUTE", "0"))
        send_hour = int(os.getenv("SEND_HOUR", "8"))
        send_minute = int(os.getenv("SEND_MINUTE", "0"))

        self.add_crawl_job(crawl_hour, crawl_minute)
        self.add_send_job(send_hour, send_minute)

        self._scheduler.start()
        self._running = True
        logger.info(
            f"스케줄러 시작: 수집={crawl_hour:02d}:{crawl_minute:02d}, "
            f"발송={send_hour:02d}:{send_minute:02d}"
        )

    def stop(self):
        """스케줄러 종료"""
        if not self._running:
            return

        self._scheduler.shutdown(wait=False)
        self._running = False
        logger.info("스케줄러 종료")

    def add_crawl_job(self, hour: int = 7, minute: int = 0):
        """뉴스 수집 작업 추가"""
        from .jobs import collect_news

        # 기존 작업이 있으면 제거
        if self._scheduler.get_job("news_crawl"):
            self._scheduler.remove_job("news_crawl")

        self._scheduler.add_job(
            collect_news,
            trigger=CronTrigger(hour=hour, minute=minute),
            id="news_crawl",
            name="뉴스 수집",
            replace_existing=True,
        )
        logger.info(f"뉴스 수집 작업 등록: {hour:02d}:{minute:02d}")

    def add_send_job(self, hour: int = 8, minute: int = 0):
        """뉴스레터 발송 작업 추가"""
        from .jobs import generate_and_send_reports

        if self._scheduler.get_job("news_send"):
            self._scheduler.remove_job("news_send")

        self._scheduler.add_job(
            generate_and_send_reports,
            trigger=CronTrigger(hour=hour, minute=minute),
            id="news_send",
            name="뉴스레터 발송",
            replace_existing=True,
        )
        logger.info(f"뉴스레터 발송 작업 등록: {hour:02d}:{minute:02d}")

    def run_crawl_once(self):
        """뉴스 수집 즉시 실행"""
        from .jobs import collect_news
        collect_news()

    def run_send_once(self):
        """뉴스레터 발송 즉시 실행"""
        from .jobs import generate_and_send_reports
        generate_and_send_reports()

    def get_job_status(self) -> dict:
        """스케줄러 작업 상태 조회"""
        jobs = []
        for job in self._scheduler.get_jobs():
            next_run = job.next_run_time
            jobs.append({
                "id": job.id,
                "name": job.name,
                "next_run": next_run.isoformat() if next_run else None,
                "trigger": str(job.trigger),
            })

        return {
            "is_running": self._running,
            "jobs": jobs,
        }

    def update_config(self, crawl_hour: Optional[int] = None, crawl_minute: Optional[int] = None,
                       send_hour: Optional[int] = None, send_minute: Optional[int] = None):
        """스케줄 설정 변경"""
        if crawl_hour is not None or crawl_minute is not None:
            ch = crawl_hour if crawl_hour is not None else int(os.getenv("CRAWL_HOUR", "7"))
            cm = crawl_minute if crawl_minute is not None else int(os.getenv("CRAWL_MINUTE", "0"))
            self.add_crawl_job(ch, cm)

        if send_hour is not None or send_minute is not None:
            sh = send_hour if send_hour is not None else int(os.getenv("SEND_HOUR", "8"))
            sm = send_minute if send_minute is not None else int(os.getenv("SEND_MINUTE", "0"))
            self.add_send_job(sh, sm)


# 싱글톤 인스턴스
_scheduler_service: Optional[NewsSchedulerService] = None


def get_scheduler_service() -> NewsSchedulerService:
    """스케줄러 서비스 싱글톤"""
    global _scheduler_service
    if _scheduler_service is None:
        _scheduler_service = NewsSchedulerService()
    return _scheduler_service
