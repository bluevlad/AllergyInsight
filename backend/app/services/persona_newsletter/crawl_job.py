"""크롤 확장 job — Phase 2.

`expandable` 판정된 변형 요청에 대해 비동기로 외부 소스(PubMed)를 검색·인덱싱하고,
완료 시 NewsletterPlatform 으로 webhook 콜백을 발신한다. 실행은 LLMOps 로 계측한다.

status 전이: pending → collecting → ready / failed.
"""
from __future__ import annotations

import logging
import os
import uuid
from datetime import timedelta
from typing import Callable, Optional

from sqlalchemy.orm import Session

from ...database.persona_newsletter_models import CrawlExpansionJob
from ...utils.timezone import utc_now

logger = logging.getLogger(__name__)

# 크롤 완료 예상 시간 (NewsletterPlatform 안내용)
ETA_MINUTES = 30

# 크롤당 소스별 최대 논문 수
_MAX_RESULTS = 10

# LLMOps consumer 식별자
_LLMOPS_CONSUMER = "allergyinsight-newsletter-crawl"


def create_job(
    db: Session,
    *,
    request_id: Optional[str],
    tenant_id: str,
    topic: str,
    topic_hash: Optional[str],
    source: str,
    callback_url: Optional[str],
) -> CrawlExpansionJob:
    """크롤 확장 job 생성 (status=pending)."""
    job = CrawlExpansionJob(
        job_id=str(uuid.uuid4()),
        request_id=request_id,
        tenant_id=tenant_id,
        topic=(topic or "")[:500],
        topic_hash=topic_hash,
        source=source,
        status="pending",
        callback_url=callback_url,
        eta_at=utc_now() + timedelta(minutes=ETA_MINUTES),
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


def get_job_by_request(
    db: Session, request_id: Optional[str]
) -> Optional[CrawlExpansionJob]:
    """request_id 로 크롤 job 조회 (멱등 재요청용)."""
    if not request_id:
        return None
    return (
        db.query(CrawlExpansionJob)
        .filter(CrawlExpansionJob.request_id == request_id)
        .order_by(CrawlExpansionJob.id.desc())
        .first()
    )


def _execute_crawl(topic: str, source: str) -> dict:
    """실제 크롤 — PubMed 논문 검색 + 영속화 + RAG 인덱싱.

    자체 DB 세션을 사용한다. 테스트에서는 monkeypatch 로 대체한다.
    Returns: result_summary dict.
    """
    from ...database.connection import SessionLocal
    from ...services.paper_search_service import PaperSearchService
    from ...services.rag_service import get_rag_service

    db = SessionLocal()
    try:
        search = PaperSearchService()
        # db 전달 시 검색 결과가 papers 테이블에 자동 영속화된다
        result = search.search(
            query=topic,
            max_results_per_source=_MAX_RESULTS,
            sources=[source],
            db=db,
        )
        summary: dict = {
            "source": source,
            "papers_found": int(getattr(result, "total_unique", 0) or 0),
        }
        try:
            indexed = get_rag_service().index_papers_from_db(db, batch_size=100)
            summary["indexed"] = int((indexed or {}).get("indexed", 0))
        except Exception as e:  # noqa: BLE001
            logger.warning("크롤 후 RAG 인덱싱 실패 (무시): %s", e)
            summary["indexed"] = 0
        return summary
    finally:
        db.close()


def _fire_webhook(job: CrawlExpansionJob) -> None:
    """job 완료를 callback_url 로 통지 — 예외 격리 (fire-and-forget)."""
    if not job.callback_url:
        return
    payload = {
        "job_id": job.job_id,
        "request_id": job.request_id,
        "status": job.status,
        "topic": job.topic,
        "result_summary": job.result_summary,
        "error": job.error,
    }
    try:
        import httpx

        with httpx.Client(timeout=5.0) as client:
            client.post(job.callback_url, json=payload)
    except Exception as e:  # noqa: BLE001
        logger.warning("webhook 콜백 실패 (무시) %s: %s", job.callback_url, e)


def _report_llmops(job: CrawlExpansionJob, error: Optional[str]) -> None:
    """크롤 job 실행을 LLMOps 로 계측 — 미구성 시 no-op."""
    try:
        from ...observability.llmops import (
            LLMOpsClient,
            StageReport,
            flush_pending,
        )

        duration_ms = None
        if job.started_at and job.finished_at:
            duration_ms = int(
                (job.finished_at - job.started_at).total_seconds() * 1000
            )
        client = LLMOpsClient(
            _LLMOPS_CONSUMER,
            api_key=os.getenv("LLMOPS_API_KEY_CRAWL"),
        )
        client.report(
            run_id=job.job_id,
            started_at=job.started_at or job.created_at,
            ended_at=job.finished_at,
            status="success" if job.status == "ready" else "failure",
            stages=[StageReport(name="crawl_expansion", duration_ms=duration_ms)],
            metrics={"source": job.source, **(job.result_summary or {})},
            error={"message": error} if error else None,
            extra={"topic_hash": job.topic_hash},
        )
        flush_pending(2.0)
    except Exception as e:  # noqa: BLE001
        logger.debug("LLMOps 계측 생략: %s", e)


def run_expansion_job(
    job_id: str,
    *,
    crawl_fn: Optional[Callable[[str, str], dict]] = None,
    db: Optional[Session] = None,
) -> None:
    """크롤 확장 job 실행 — FastAPI BackgroundTasks 진입점.

    status 전이 pending → collecting → ready/failed. 완료 시 LLMOps 계측 + webhook.

    Args:
        crawl_fn: 크롤 함수 주입 (테스트용). 기본은 `_execute_crawl`.
        db: 세션 주입 (테스트용). 기본은 자체 SessionLocal.
    """
    own_session = db is None
    if own_session:
        from ...database.connection import SessionLocal

        db = SessionLocal()

    try:
        job = (
            db.query(CrawlExpansionJob)
            .filter(CrawlExpansionJob.job_id == job_id)
            .first()
        )
        if job is None:
            logger.warning("크롤 job 없음: %s", job_id)
            return

        job.status = "collecting"
        job.started_at = utc_now()
        db.commit()

        error: Optional[str] = None
        crawl = crawl_fn or _execute_crawl
        try:
            job.result_summary = crawl(job.topic, job.source)
            job.status = "ready"
        except Exception as e:  # noqa: BLE001
            error = str(e)[:500]
            job.status = "failed"
            job.error = error
            logger.warning("크롤 확장 job 실패 (%s): %s", job_id, e)

        job.finished_at = utc_now()
        db.commit()
        db.refresh(job)

        _report_llmops(job, error)
        _fire_webhook(job)
    except Exception as e:  # noqa: BLE001
        logger.error("크롤 job 실행 오류 (%s): %s", job_id, e)
    finally:
        if own_session:
            db.close()
