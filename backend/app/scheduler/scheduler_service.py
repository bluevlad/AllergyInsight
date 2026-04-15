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
    """통합 스케줄러 (뉴스 + 논문 수집)"""

    KST = "Asia/Seoul"

    def __init__(self):
        self._scheduler = BackgroundScheduler(
            job_defaults={
                "coalesce": True,
                "max_instances": 1,
                "misfire_grace_time": 3600,
            },
            timezone=self.KST,
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
        self.add_paper_search_job()
        self.add_korean_translation_job()
        self.add_rag_enrich_job()
        self.add_preprint_trials_job()
        self.add_crawl_job(crawl_hour, crawl_minute)
        self.add_insight_job()
        self.add_paper_trend_job()
        self.add_treatment_extraction_job()
        self.add_drug_ingest_job()

        self._scheduler.start()
        self._running = True
        logger.info(
            f"스케줄러 시작: 논문=02:00, 번역=04:00, RAG/보강=05:00, "
            f"뉴스={crawl_hour:02d}:{crawl_minute:02d}, 인사이트=매월 1일 03:00, "
            f"논문트렌드=매월 1일 04:00, 치료법추출=매주 일 05:00"
        )

    def stop(self):
        """스케줄러 종료"""
        if not self._running:
            return

        self._scheduler.shutdown(wait=False)
        self._running = False
        logger.info("스케줄러 종료")

    def add_paper_search_job(self, hour: int = 2, minute: int = 0):
        """논문 검색 작업 추가 (매일 02:00 KST)"""
        from ..services.scheduler_jobs import job_daily_paper_search

        if self._scheduler.get_job("daily_paper_search"):
            self._scheduler.remove_job("daily_paper_search")

        self._scheduler.add_job(
            job_daily_paper_search,
            trigger=CronTrigger(hour=hour, minute=minute, timezone=self.KST),
            id="daily_paper_search",
            name="일일 논문 검색",
            replace_existing=True,
        )
        logger.info(f"논문 검색 작업 등록: {hour:02d}:{minute:02d}")

    def add_korean_translation_job(self, hour: int = 4, minute: int = 0):
        """한국어 번역 작업 추가 (매일 04:00 KST)"""
        from ..services.scheduler_jobs import job_korean_translation

        if self._scheduler.get_job("korean_translation"):
            self._scheduler.remove_job("korean_translation")

        self._scheduler.add_job(
            job_korean_translation,
            trigger=CronTrigger(hour=hour, minute=minute, timezone=self.KST),
            id="korean_translation",
            name="한국어 번역",
            replace_existing=True,
        )
        logger.info(f"한국어 번역 작업 등록: {hour:02d}:{minute:02d}")

    def add_rag_enrich_job(self, hour: int = 5, minute: int = 0):
        """RAG 인덱싱 + Unpaywall 보강 작업 추가 (매일 05:00 KST)"""
        from ..services.scheduler_jobs import job_rag_and_enrich

        if self._scheduler.get_job("rag_and_enrich"):
            self._scheduler.remove_job("rag_and_enrich")

        self._scheduler.add_job(
            job_rag_and_enrich,
            trigger=CronTrigger(hour=hour, minute=minute, timezone=self.KST),
            id="rag_and_enrich",
            name="RAG 인덱싱 + PDF 보강",
            replace_existing=True,
        )
        logger.info(f"RAG/보강 작업 등록: {hour:02d}:{minute:02d}")

    def add_preprint_trials_job(self, hour: int = 6, minute: int = 0):
        """프리프린트 수집 + 임상시험 검색 작업 추가 (매일 06:00 KST)"""
        from ..services.scheduler_jobs import job_preprint_and_trials

        if self._scheduler.get_job("preprint_and_trials"):
            self._scheduler.remove_job("preprint_and_trials")

        self._scheduler.add_job(
            job_preprint_and_trials,
            trigger=CronTrigger(hour=hour, minute=minute, timezone=self.KST),
            id="preprint_and_trials",
            name="프리프린트 + 임상시험 수집",
            replace_existing=True,
        )
        logger.info(f"프리프린트/임상시험 작업 등록: {hour:02d}:{minute:02d}")

    def add_crawl_job(self, hour: int = 7, minute: int = 0):
        """뉴스 수집 작업 추가"""
        from .jobs import collect_news

        # 기존 작업이 있으면 제거
        if self._scheduler.get_job("news_crawl"):
            self._scheduler.remove_job("news_crawl")

        self._scheduler.add_job(
            collect_news,
            trigger=CronTrigger(hour=hour, minute=minute, timezone=self.KST),
            id="news_crawl",
            name="뉴스 수집",
            replace_existing=True,
        )
        logger.info(f"뉴스 수집 작업 등록: {hour:02d}:{minute:02d}")

    def add_insight_job(self):
        """인사이트 리포트 생성 작업 추가 (매월 1일 03:00)"""
        from .jobs import tag_and_generate_insights

        if self._scheduler.get_job("insight_report"):
            self._scheduler.remove_job("insight_report")

        self._scheduler.add_job(
            tag_and_generate_insights,
            trigger=CronTrigger(day=1, hour=3, minute=0, timezone=self.KST),
            id="insight_report",
            name="인사이트 리포트 생성",
            replace_existing=True,
        )
        logger.info("인사이트 리포트 작업 등록: 매월 1일 03:00")

    def add_paper_trend_job(self):
        """논문 알러젠 트렌드 집계 작업 추가 (매월 1일 04:00)"""
        from .jobs import aggregate_paper_allergen_trends

        if self._scheduler.get_job("paper_trend_aggregation"):
            self._scheduler.remove_job("paper_trend_aggregation")

        self._scheduler.add_job(
            aggregate_paper_allergen_trends,
            trigger=CronTrigger(day=1, hour=4, minute=0, timezone=self.KST),
            id="paper_trend_aggregation",
            name="논문 알러젠 트렌드 집계",
            replace_existing=True,
        )
        logger.info("논문 알러젠 트렌드 집계 작업 등록: 매월 1일 04:00")

    def run_paper_trend_once(self):
        """논문 알러젠 트렌드 집계 즉시 실행"""
        from .jobs import aggregate_paper_allergen_trends
        aggregate_paper_allergen_trends()

    def add_treatment_extraction_job(self):
        """치료법 추출 + 트렌드 집계 작업 추가 (매주 일요일 05:00)"""
        from .jobs import extract_and_aggregate_treatments

        if self._scheduler.get_job("treatment_extraction"):
            self._scheduler.remove_job("treatment_extraction")

        self._scheduler.add_job(
            extract_and_aggregate_treatments,
            trigger=CronTrigger(day_of_week="sun", hour=5, minute=0, timezone=self.KST),
            id="treatment_extraction",
            name="치료법 추출 + 트렌드 집계",
            replace_existing=True,
        )
        logger.info("치료법 추출 작업 등록: 매주 일요일 05:00")

    def run_treatment_extraction_once(self):
        """치료법 추출 즉시 실행"""
        from .jobs import extract_and_aggregate_treatments
        extract_and_aggregate_treatments()

    def add_drug_ingest_job(self, hour: int = 1, minute: int = 0):
        """약물 정보 수집 작업 추가 (매일 01:00 KST).

        openFDA · MFDS 어댑터를 증분 수집한다. 외부 API 부하를 피해
        다른 작업보다 이른 시간대 배치.
        """
        from .jobs import ingest_drugs

        if self._scheduler.get_job("drug_ingest"):
            self._scheduler.remove_job("drug_ingest")

        self._scheduler.add_job(
            ingest_drugs,
            trigger=CronTrigger(hour=hour, minute=minute, timezone=self.KST),
            id="drug_ingest",
            name="약물 정보 수집",
            replace_existing=True,
        )
        logger.info(f"약물 수집 작업 등록: {hour:02d}:{minute:02d}")

    def run_drug_ingest_once(self, source: str | None = None, limit: int | None = None):
        """약물 수집 즉시 실행"""
        from .jobs import ingest_drugs
        return ingest_drugs(source=source, limit=limit)

    def run_paper_search_once(self):
        """논문 검색 즉시 실행"""
        from ..services.scheduler_jobs import job_daily_paper_search
        job_daily_paper_search("manual")

    def run_korean_translation_once(self):
        """한국어 번역 즉시 실행"""
        from ..services.scheduler_jobs import job_korean_translation
        job_korean_translation("manual")

    def run_insight_once(self):
        """인사이트 리포트 즉시 실행"""
        from .jobs import tag_and_generate_insights
        tag_and_generate_insights()

    def run_rag_enrich_once(self):
        """RAG 인덱싱 + PDF 보강 즉시 실행"""
        from ..services.scheduler_jobs import job_rag_and_enrich
        job_rag_and_enrich("manual")

    def run_preprint_trials_once(self):
        """프리프린트 + 임상시험 즉시 실행"""
        from ..services.scheduler_jobs import job_preprint_and_trials
        job_preprint_and_trials("manual")

    def run_crawl_once(self):
        """뉴스 수집 즉시 실행"""
        from .jobs import collect_news
        collect_news()

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

    def update_config(self, crawl_hour: Optional[int] = None, crawl_minute: Optional[int] = None):
        """스케줄 설정 변경"""
        if crawl_hour is not None or crawl_minute is not None:
            ch = crawl_hour if crawl_hour is not None else int(os.getenv("CRAWL_HOUR", "7"))
            cm = crawl_minute if crawl_minute is not None else int(os.getenv("CRAWL_MINUTE", "0"))
            self.add_crawl_job(ch, cm)


# 싱글톤 인스턴스
_scheduler_service: Optional[NewsSchedulerService] = None


def get_scheduler_service() -> NewsSchedulerService:
    """스케줄러 서비스 싱글톤"""
    global _scheduler_service
    if _scheduler_service is None:
        _scheduler_service = NewsSchedulerService()
    return _scheduler_service
