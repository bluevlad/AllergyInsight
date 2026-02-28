"""스케줄러 Job 함수 모듈

5개의 스케줄된 Job:
- job_daily_paper_search: 매일 02:00 KST 알레르겐 로테이션 논문 검색
- job_newsletter_sync: 매일 03:00 KST AllergyNewsLetter DB 증분 동기화
- job_korean_translation: 매일 04:00 KST 미번역 논문 한국어 번역
- job_news_pipeline: 매일 07:00 KST 뉴스 수집 파이프라인 (수집→중복제거→AI분석)
- job_newsletter_send: 매일 08:00 KST 구독자 뉴스레터 발송
"""
import logging
import os
import sqlite3
import time
from datetime import datetime
from typing import Optional

from ..config import settings
from ..database.connection import SessionLocal
from ..database.scheduler_models import SchedulerExecutionLog

logger = logging.getLogger(__name__)

# ============================================================================
# 알레르겐 로테이션 전략
# ============================================================================

ALLERGEN_TIERS = {
    2: ["peanut", "tree_nut", "shellfish", "milk", "egg"],           # Tier 1: 매 2일
    3: ["wheat", "soy", "fish", "sesame"],                           # Tier 2: 매 3일
    4: [                                                              # Tier 3: 매 4일
        "dust_mite", "cat", "dog", "pollen", "mold",
        "latex", "insect", "drug",
    ],
}


def get_allergens_for_day(day_number: int) -> list[str]:
    """주어진 일자에 검색할 알레르겐 목록을 반환 (결정적 로테이션)

    Args:
        day_number: 에포크 기준 일수 또는 연중 일수 등 정수값

    Returns:
        해당일 검색 대상 알레르겐 코드 리스트
    """
    result = []
    for interval, allergens in ALLERGEN_TIERS.items():
        for i, allergen in enumerate(allergens):
            if (day_number + i) % interval == 0:
                result.append(allergen)
    return result


def _log_start(db, job_id: str, trigger_type: str = "scheduled") -> SchedulerExecutionLog:
    """실행 로그 시작 기록"""
    log = SchedulerExecutionLog(
        job_id=job_id,
        status="running",
        started_at=datetime.utcnow(),
        trigger_type=trigger_type,
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return log


def _log_complete(db, log: SchedulerExecutionLog, result_summary: dict) -> None:
    """실행 로그 성공 기록"""
    now = datetime.utcnow()
    log.status = "success"
    log.completed_at = now
    log.duration_seconds = (now - log.started_at).total_seconds()
    log.result_summary = result_summary
    db.commit()


def _log_fail(db, log: SchedulerExecutionLog, error: str) -> None:
    """실행 로그 실패 기록"""
    now = datetime.utcnow()
    log.status = "failed"
    log.completed_at = now
    log.duration_seconds = (now - log.started_at).total_seconds()
    log.error_message = error
    db.commit()


# ============================================================================
# Job 1: 일일 논문 검색
# ============================================================================

def job_daily_paper_search(trigger_type: str = "scheduled") -> None:
    """알레르겐 로테이션으로 매일 4~6종 검색

    PaperSearchService.search_allergy()를 재사용하며,
    2초 간격으로 rate limit을 준수합니다.
    """
    db = SessionLocal()
    log = _log_start(db, "daily_paper_search", trigger_type)

    try:
        from .paper_search_service import PaperSearchService

        service = PaperSearchService()
        day_number = (datetime.utcnow() - datetime(2024, 1, 1)).days
        allergens = get_allergens_for_day(day_number)

        logger.info(f"[daily_paper_search] 대상 알레르겐: {allergens}")

        total_papers = 0
        total_new = 0
        allergen_results = {}

        try:
            for allergen in allergens:
                try:
                    result = service.search_allergy(
                        allergen=allergen,
                        include_cross_reactivity=True,
                        max_results_per_source=settings.SCHEDULER_PAPER_MAX_RESULTS,
                        db=db,
                    )
                    found = result.total_unique
                    total_papers += found
                    allergen_results[allergen] = found
                    logger.info(f"  {allergen}: {found}건 검색")

                    # Rate limit: 2초 간격
                    time.sleep(2)

                except Exception as e:
                    logger.warning(f"  {allergen} 검색 실패: {e}")
                    allergen_results[allergen] = f"error: {str(e)[:100]}"
        finally:
            service.close()

        summary = {
            "allergens_searched": len(allergens),
            "allergen_list": allergens,
            "total_papers_found": total_papers,
            "details": allergen_results,
        }
        _log_complete(db, log, summary)
        logger.info(f"[daily_paper_search] 완료: {len(allergens)}종, {total_papers}건")

    except Exception as e:
        _log_fail(db, log, str(e))
        logger.error(f"[daily_paper_search] 실패: {e}")
    finally:
        db.close()


# ============================================================================
# Job 2: 뉴스레터 증분 동기화
# ============================================================================

def job_newsletter_sync(trigger_type: str = "scheduled") -> None:
    """AllergyNewsLetter SQLite에서 증분 동기화

    마지막 성공 시각 이후 신규 article만 가져와서
    papers / competitor_news 테이블에 저장합니다.
    """
    db = SessionLocal()
    log = _log_start(db, "newsletter_sync", trigger_type)

    try:
        from scripts.migrate_newsletter_papers import (
            article_to_paper_dc,
            _apply_extra_fields,
            CATEGORY_MAP,
        )
        from .paper_persistence_service import PaperPersistenceService

        # Newsletter DB 경로 확인
        db_path = os.path.expanduser(settings.NEWSLETTER_DB_PATH)
        if not os.path.exists(db_path):
            _log_fail(db, log, f"Newsletter DB not found: {db_path}")
            logger.warning(f"[newsletter_sync] DB 파일 없음: {db_path}")
            return

        # 마지막 성공 시각 조회
        last_success = (
            db.query(SchedulerExecutionLog)
            .filter(
                SchedulerExecutionLog.job_id == "newsletter_sync",
                SchedulerExecutionLog.status == "success",
            )
            .order_by(SchedulerExecutionLog.completed_at.desc())
            .first()
        )
        last_sync_time = last_success.completed_at.isoformat() if last_success else "2000-01-01"

        # SQLite에서 증분 로드
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        try:
            cursor = conn.execute(
                """
                SELECT pmid, doi, title, abstract, authors, journal,
                       pub_date, link, keyword, category, summary,
                       importance_score, content_type, collected_at
                FROM articles
                WHERE is_duplicate = 0
                  AND collected_at > ?
                ORDER BY collected_at ASC
                """,
                (last_sync_time,),
            )
            articles = [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()

        if not articles:
            _log_complete(db, log, {"message": "신규 데이터 없음", "checked_since": last_sync_time})
            logger.info("[newsletter_sync] 신규 데이터 없음")
            return

        logger.info(f"[newsletter_sync] {len(articles)}건 증분 동기화 시작")

        service = PaperPersistenceService()
        new_papers = 0
        dup_papers = 0
        new_news = 0
        failed = 0

        for article in articles:
            content_type = article.get("content_type", "PAPER")
            try:
                if content_type == "PAPER":
                    paper_dc = article_to_paper_dc(article)
                    savepoint = db.begin_nested()
                    try:
                        saved = service.save_paper(paper_dc, db)
                        if saved:
                            new_papers += 1
                            _apply_extra_fields(article, paper_dc, db)
                        else:
                            dup_papers += 1
                        savepoint.commit()
                    except Exception:
                        savepoint.rollback()
                        raise
                elif content_type == "NEWS":
                    # 뉴스는 competitor_news 테이블에 저장
                    from ..database.competitor_models import CompetitorNews
                    existing = db.query(CompetitorNews).filter(
                        CompetitorNews.url == article.get("link")
                    ).first()
                    if not existing and article.get("link"):
                        news = CompetitorNews(
                            company_id=None,
                            source="newsletter",
                            title=article.get("title", ""),
                            description=article.get("summary", ""),
                            url=article["link"],
                            published_at=_parse_datetime(article.get("pub_date")),
                            search_keyword=article.get("keyword", ""),
                        )
                        db.add(news)
                        new_news += 1
            except Exception as e:
                failed += 1
                logger.warning(f"  동기화 실패: {article.get('title', '')[:50]}... - {e}")

        db.commit()

        summary = {
            "total_articles": len(articles),
            "new_papers": new_papers,
            "duplicate_papers": dup_papers,
            "new_news": new_news,
            "failed": failed,
            "sync_since": last_sync_time,
        }
        _log_complete(db, log, summary)
        logger.info(f"[newsletter_sync] 완료: 논문 {new_papers}건, 뉴스 {new_news}건 신규")

    except Exception as e:
        _log_fail(db, log, str(e))
        logger.error(f"[newsletter_sync] 실패: {e}")
    finally:
        db.close()


def _parse_datetime(value: Optional[str]) -> Optional[datetime]:
    """날짜 문자열을 datetime으로 변환"""
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except (ValueError, TypeError):
        return None


# ============================================================================
# Job 3: 한국어 번역
# ============================================================================

def job_korean_translation(trigger_type: str = "scheduled") -> None:
    """title_kr IS NULL인 논문 최대 N건을 Ollama로 한국어 번역"""
    db = SessionLocal()
    log = _log_start(db, "korean_translation", trigger_type)

    try:
        from .ollama_service import check_ollama_available, ollama_translate
        from ..database.models import Paper as PaperORM

        if not check_ollama_available():
            _log_fail(db, log, "Ollama 서버 접근 불가 또는 모델 미설치")
            logger.warning("[korean_translation] Ollama 사용 불가")
            return

        # 미번역 논문 조회
        batch_size = settings.SCHEDULER_TRANSLATION_BATCH_SIZE
        papers = (
            db.query(PaperORM)
            .filter(PaperORM.title_kr.is_(None))
            .filter(PaperORM.title.isnot(None))
            .order_by(PaperORM.created_at.desc())
            .limit(batch_size)
            .all()
        )

        if not papers:
            _log_complete(db, log, {"message": "번역 대상 없음"})
            logger.info("[korean_translation] 번역 대상 없음")
            return

        logger.info(f"[korean_translation] {len(papers)}건 번역 시작")

        translated_count = 0
        failed_count = 0

        for paper in papers:
            # 제목 번역
            title_kr = ollama_translate(paper.title)
            if title_kr:
                paper.title_kr = title_kr
                translated_count += 1
            else:
                failed_count += 1

            # 초록 번역 (미번역 + 초록 존재 시)
            if not paper.abstract_kr and paper.abstract:
                abstract_kr = ollama_translate(paper.abstract)
                if abstract_kr:
                    paper.abstract_kr = abstract_kr

        db.commit()

        summary = {
            "target_count": len(papers),
            "translated": translated_count,
            "failed": failed_count,
        }
        _log_complete(db, log, summary)
        logger.info(f"[korean_translation] 완료: {translated_count}/{len(papers)}건 번역")

    except Exception as e:
        _log_fail(db, log, str(e))
        logger.error(f"[korean_translation] 실패: {e}")
    finally:
        db.close()


# ============================================================================
# Job 4: 뉴스 수집 파이프라인 (HealthPulse 통합)
# ============================================================================

def job_news_pipeline(trigger_type: str = "scheduled") -> None:
    """뉴스 수집 파이프라인: 수집 → 중복제거 → AI 분석

    NewsPipelineService를 사용하여 경쟁사 뉴스를 수집하고
    중복 제거 후 AI 분석까지 수행합니다.
    """
    db = SessionLocal()
    log = _log_start(db, "news_pipeline", trigger_type)

    try:
        from .news_pipeline_service import NewsPipelineService

        pipeline = NewsPipelineService()
        try:
            result = pipeline.run_collection_pipeline(
                db=db,
                max_results_per_company=settings.SCHEDULER_NEWS_MAX_RESULTS,
                auto_analyze=True,
            )
        finally:
            pipeline.close()

        summary = {
            "collected": result.get("collected", 0),
            "duplicates": result.get("duplicates", 0),
            "analyzed": result.get("analyzed", 0),
        }
        _log_complete(db, log, summary)
        logger.info(
            f"[news_pipeline] 완료: 신규 {summary['collected']}건, "
            f"중복 {summary['duplicates']}건, 분석 {summary['analyzed']}건"
        )

    except Exception as e:
        _log_fail(db, log, str(e))
        logger.error(f"[news_pipeline] 실패: {e}")
    finally:
        db.close()


# ============================================================================
# Job 5: 뉴스레터 발송 (HealthPulse 통합)
# ============================================================================

def job_newsletter_send(trigger_type: str = "scheduled") -> None:
    """인증된 구독자에게 키워드 매칭 기반 뉴스레터 발송

    NewsletterService를 사용하여 최근 1일간 수집된
    뉴스를 구독자에게 이메일로 발송합니다.
    """
    db = SessionLocal()
    log = _log_start(db, "newsletter_send", trigger_type)

    try:
        from .newsletter_service import NewsletterService

        service = NewsletterService()
        result = service.send_to_subscribers(db=db, days=1)

        summary = {
            "message": result.get("message", ""),
            "sent_count": result.get("sent_count", 0),
            "failed_count": result.get("failed_count", 0),
        }
        _log_complete(db, log, summary)
        logger.info(f"[newsletter_send] 완료: {summary['message']}")

    except Exception as e:
        _log_fail(db, log, str(e))
        logger.error(f"[newsletter_send] 실패: {e}")
    finally:
        db.close()
