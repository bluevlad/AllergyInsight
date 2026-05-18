"""스케줄러 Job 함수 모듈

5개의 스케줄된 Job:
- job_daily_paper_search: 매일 02:00 KST 알레르겐 로테이션 논문 검색
- job_newsletter_sync: 매일 03:00 KST AllergyNewsLetter DB 증분 동기화
- job_korean_translation: 매일 04:00 KST 미번역 논문 한국어 번역
- job_analytics_aggregation: 매일 05:00 KST 분석 집계 (알러젠 양성률 + 키워드 트렌드)
- job_news_pipeline: 매일 07:00 KST 뉴스 수집 파이프라인 (수집→중복제거→AI분석)
"""
import logging
import os
import sqlite3
import time
from datetime import datetime, timezone
from typing import Optional

from ..config import settings
from ..observability.llmops import LLMOpsClient, StageReport
from ..utils.timezone import utc_now
from ..database.connection import SessionLocal
from ..database.scheduler_models import SchedulerExecutionLog

logger = logging.getLogger(__name__)

# LLMOps 보고 — paper translate 잡 전용. LLMOPS_API_KEY_TRANSLATE 부재 시 no-op.
_LLMOPS_TRANSLATE = LLMOpsClient(
    consumer_id="allergyinsight-paper-translate",
    api_key=os.environ.get("LLMOPS_API_KEY_TRANSLATE", ""),
)
_LLM_MODEL_NAME = os.environ.get(
    "LLM_MODEL", "mlx-community/EXAONE-3.5-7.8B-Instruct-4bit"
)

# DB 컬럼이 DateTime(naive)이라 fetch 시 tz 정보가 사라진다. utc_now()(aware)와
# 빼기 연산하려면 보정 필요 — 컬럼 마이그레이션을 미루기 위한 클라이언트 보정.
_EPOCH = datetime(2024, 1, 1, tzinfo=timezone.utc)


def _as_utc(dt: datetime) -> datetime:
    """naive datetime 을 UTC aware 로 간주해서 반환 (이미 aware 면 그대로)."""
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)

# ============================================================================
# 알레르겐 로테이션 전략
# ============================================================================

# Legacy 폴백 (Phase 1.G-007) — DomainPack 미로딩 시 사용.
# Phase 1.F 에서 DomainPack 정착 후 제거 예정.
_ALLERGEN_TIERS_FALLBACK = {
    2: ["peanut", "tree_nut", "shellfish", "milk", "egg"],           # Tier 1: 매 2일
    3: ["wheat", "soy", "fish", "sesame"],                           # Tier 2: 매 3일
    4: [                                                              # Tier 3: 매 4일
        "dust_mite", "cat", "dog", "pollen", "mold",
        "latex", "insect", "drug",
    ],
}

# Backward-compat alias — 기존 import 호환
ALLERGEN_TIERS = _ALLERGEN_TIERS_FALLBACK


def get_allergens_for_day(day_number: int) -> list[str]:
    """주어진 일자에 검색할 알레르겐 목록을 반환 (결정적 로테이션).

    1차: DomainPack 의 sources.rotation.tiers (Phase 1.G-007).
    2차: legacy ``_ALLERGEN_TIERS_FALLBACK`` (pack 미로딩 시).

    Args:
        day_number: 에포크 기준 일수 또는 연중 일수 등 정수값

    Returns:
        해당일 검색 대상 알레르겐 코드 리스트
    """
    try:
        from ..core.domains import get_pack
        pack = get_pack("allergy")
    except Exception:
        pack = None

    if pack is not None:
        return pack.get_allergens_for_day(day_number)

    # Legacy fallback
    result: list[str] = []
    for interval, allergens in _ALLERGEN_TIERS_FALLBACK.items():
        for i, allergen in enumerate(allergens):
            if (day_number + i) % interval == 0:
                result.append(allergen)
    return result


def _log_start(db, job_id: str, trigger_type: str = "scheduled") -> SchedulerExecutionLog:
    """실행 로그 시작 기록"""
    log = SchedulerExecutionLog(
        job_id=job_id,
        status="running",
        started_at=utc_now(),
        trigger_type=trigger_type,
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return log


def _log_complete(db, log: SchedulerExecutionLog, result_summary: dict) -> None:
    """실행 로그 성공 기록"""
    now = utc_now()
    log.status = "success"
    log.completed_at = now
    log.duration_seconds = (now - _as_utc(log.started_at)).total_seconds()
    log.result_summary = result_summary
    db.commit()


def _log_fail(db, log: SchedulerExecutionLog, error: str) -> None:
    """실행 로그 실패 기록"""
    now = utc_now()
    log.status = "failed"
    log.completed_at = now
    log.duration_seconds = (now - _as_utc(log.started_at)).total_seconds()
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
        day_number = (utc_now() - _EPOCH).days
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

    # LLMOps 보고용 식별자 (잡 1회 = batch_run 1건)
    llmops_started_at = datetime.now(timezone.utc)
    llmops_run_id = f"{llmops_started_at.isoformat()}-{os.getpid()}-translate"
    t0 = time.monotonic()

    try:
        from .ollama_service import check_ollama_available, ollama_translate
        from ..database.models import Paper as PaperORM

        if not check_ollama_available():
            _log_fail(db, log, "Ollama 서버 접근 불가 또는 모델 미설치")
            logger.warning("[korean_translation] Ollama 사용 불가")
            _LLMOPS_TRANSLATE.report(
                run_id=llmops_run_id,
                started_at=llmops_started_at,
                ended_at=datetime.now(timezone.utc),
                status="failure",
                error={"type": "OllamaUnavailable", "message": "endpoint 접근 불가 또는 모델 미설치"},
                extra={"trigger_type": trigger_type},
            )
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
            _LLMOPS_TRANSLATE.report(
                run_id=llmops_run_id,
                started_at=llmops_started_at,
                ended_at=datetime.now(timezone.utc),
                status="success",
                metrics={"target_count": 0, "translated": 0, "failed": 0},
                extra={"trigger_type": trigger_type, "note": "no targets"},
            )
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
        duration_ms = int((time.monotonic() - t0) * 1000)
        _LLMOPS_TRANSLATE.report(
            run_id=llmops_run_id,
            started_at=llmops_started_at,
            ended_at=datetime.now(timezone.utc),
            status="success" if failed_count == 0 else "partial",
            stages=[StageReport(
                name="translate", model=_LLM_MODEL_NAME, duration_ms=duration_ms,
            )],
            metrics={
                "target_count": len(papers),
                "translated": translated_count,
                "failed": failed_count,
            },
            extra={"trigger_type": trigger_type},
        )

    except Exception as e:
        _log_fail(db, log, str(e))
        logger.error(f"[korean_translation] 실패: {e}")
        _LLMOPS_TRANSLATE.report(
            run_id=llmops_run_id,
            started_at=llmops_started_at,
            ended_at=datetime.now(timezone.utc),
            status="failure",
            error={"type": type(e).__name__, "message": str(e)[:500]},
            extra={"trigger_type": trigger_type},
        )
    finally:
        db.close()
        # 짧게 끝나는 잡(no-targets / Ollama-unavailable) 의 fire-and-forget 보장.
        # 정기 cron 의 상주 프로세스에서도 안전 (no-op).
        _LLMOPS_TRANSLATE.flush(timeout=2.0)


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

def job_analytics_aggregation(trigger_type: str = "scheduled") -> None:
    """월별 알러젠 양성률 집계 + 키워드 트렌드 추출

    AnalyticsService.aggregate_all_months()로 미집계 월을 집계하고,
    KeywordTrendService.extract_all_months()로 키워드를 추출합니다.
    """
    db = SessionLocal()
    log = _log_start(db, "analytics_aggregation", trigger_type)

    try:
        from .analytics_service import AnalyticsService
        from .keyword_trend_service import KeywordTrendService

        analytics_svc = AnalyticsService()
        keyword_svc = KeywordTrendService()

        # 1) 알러젠 양성률 집계
        agg_results = analytics_svc.aggregate_all_months(db)
        logger.info(f"[analytics_aggregation] 알러젠 집계: {len(agg_results)}개월 처리")

        # 2) 키워드 트렌드 추출
        kw_results = keyword_svc.extract_all_months(db)
        logger.info(f"[analytics_aggregation] 키워드 추출: {len(kw_results)}개월 처리")

        summary = {
            "allergen_months_processed": len(agg_results),
            "keyword_months_processed": len(kw_results),
            "allergen_details": agg_results[:5] if agg_results else [],
            "keyword_details": kw_results[:5] if kw_results else [],
        }
        _log_complete(db, log, summary)
        logger.info(
            f"[analytics_aggregation] 완료: 알러젠 {len(agg_results)}개월, "
            f"키워드 {len(kw_results)}개월"
        )

    except Exception as e:
        _log_fail(db, log, str(e))
        logger.error(f"[analytics_aggregation] 실패: {e}")
    finally:
        db.close()


# ============================================================================
# Job 6: RAG 인덱싱 + Unpaywall PDF 보강
# ============================================================================

def job_rag_and_enrich(trigger_type: str = "scheduled") -> None:
    """신규 논문 RAG 인덱싱 + Unpaywall PDF URL 보강

    1) 미인덱싱 논문을 ChromaDB에 배치 인덱싱
    2) pdf_url이 없는 논문에 Unpaywall로 PDF URL 보강
    """
    db = SessionLocal()
    log = _log_start(db, "rag_and_enrich", trigger_type)

    try:
        rag_result = {"indexed": 0, "skipped": 0, "total_chunks": 0}
        unpaywall_result = {"checked": 0, "enriched": 0, "failed": 0}

        # 1) RAG 인덱싱
        try:
            from .rag_service import get_rag_service

            rag = get_rag_service()
            if rag.is_available:
                rag_result = rag.index_papers_from_db(db, batch_size=200)
                logger.info(
                    f"[rag_and_enrich] RAG: {rag_result['indexed']}건 인덱싱, "
                    f"{rag_result['total_chunks']}개 청크"
                )
            else:
                logger.warning("[rag_and_enrich] ChromaDB 미가용, RAG 인덱싱 건너뜀")
        except Exception as e:
            logger.warning(f"[rag_and_enrich] RAG 인덱싱 실패: {e}")

        # 2) Unpaywall PDF URL 보강
        try:
            from .unpaywall_service import UnpaywallService

            unpaywall = UnpaywallService()
            try:
                unpaywall_result = unpaywall.enrich_papers(db, batch_size=50)
                logger.info(
                    f"[rag_and_enrich] Unpaywall: {unpaywall_result['enriched']}/"
                    f"{unpaywall_result['checked']}건 PDF URL 확보"
                )
            finally:
                unpaywall.close()
        except Exception as e:
            logger.warning(f"[rag_and_enrich] Unpaywall 보강 실패: {e}")

        # 3) CORE Full-text RAG 보강 (API 키 설정 시에만)
        fulltext_result = {"enriched": 0, "failed": 0}
        try:
            from .rag_service import get_rag_service

            rag = get_rag_service()
            if rag.is_available:
                fulltext_result = rag.enrich_with_fulltext(db, batch_size=10)
                logger.info(
                    f"[rag_and_enrich] Full-text: {fulltext_result['enriched']}건 보강"
                )
        except Exception as e:
            logger.warning(f"[rag_and_enrich] Full-text 보강 실패: {e}")

        summary = {
            "rag_indexed": rag_result.get("indexed", 0),
            "rag_chunks": rag_result.get("total_chunks", 0),
            "unpaywall_checked": unpaywall_result.get("checked", 0),
            "unpaywall_enriched": unpaywall_result.get("enriched", 0),
            "fulltext_enriched": fulltext_result.get("enriched", 0),
        }
        _log_complete(db, log, summary)
        logger.info(f"[rag_and_enrich] 완료: {summary}")

    except Exception as e:
        _log_fail(db, log, str(e))
        logger.error(f"[rag_and_enrich] 실패: {e}")
    finally:
        db.close()


# ============================================================================
# Job 7: 프리프린트 수집 + 임상시험 검색
# ============================================================================

def job_preprint_and_trials(trigger_type: str = "scheduled") -> None:
    """최신 프리프린트 수집 + 알러젠별 임상시험 검색

    1) bioRxiv/medRxiv에서 최근 7일간 프리프린트 수집
    2) ClinicalTrials.gov에서 주요 알러젠 임상시험 검색
    """
    db = SessionLocal()
    log = _log_start(db, "preprint_and_trials", trigger_type)

    try:
        preprint_count = 0
        trial_count = 0

        # 1) 프리프린트 수집 (최근 7일)
        try:
            from .biorxiv_service import BiorxivService
            from .paper_persistence_service import PaperPersistenceService
            from datetime import timedelta

            biorxiv = BiorxivService()
            persistence = PaperPersistenceService()
            today = utc_now()
            week_ago = today - timedelta(days=7)

            try:
                result = biorxiv.collect_recent(
                    date_from=week_ago.strftime("%Y-%m-%d"),
                    date_to=today.strftime("%Y-%m-%d"),
                    server="medrxiv",
                    max_results=50,
                )
                for paper in result.papers:
                    # 알러지 관련 키워드 필터
                    text = f"{paper.title} {paper.abstract}".lower()
                    if any(kw in text for kw in ["allergy", "allergen", "anaphylaxis", "immunotherapy", "ige"]):
                        saved = persistence.save_paper(paper, db)
                        if saved:
                            preprint_count += 1
            finally:
                biorxiv.close()

            logger.info(f"[preprint_and_trials] 프리프린트: {preprint_count}건 신규 저장")
        except Exception as e:
            logger.warning(f"[preprint_and_trials] 프리프린트 수집 실패: {e}")

        # 2) 임상시험 검색 (주요 알러젠 3종 로테이션)
        try:
            from .clinicaltrials_service import ClinicalTrialsService
            from .paper_persistence_service import PaperPersistenceService

            ct = ClinicalTrialsService()
            persistence = PaperPersistenceService()

            # 요일 기반 로테이션 (7요일 × 3알러젠)
            allergen_groups = [
                ["peanut", "milk", "egg"],
                ["wheat", "soy", "shellfish"],
                ["tree_nut", "fish", "sesame"],
                ["dust_mite", "cat", "dog"],
                ["peanut", "milk", "egg"],
                ["wheat", "soy", "shellfish"],
                ["tree_nut", "fish", "sesame"],
            ]
            day_of_week = utc_now().weekday()
            target_allergens = allergen_groups[day_of_week]

            try:
                for allergen in target_allergens:
                    result = ct.search_allergy(allergen, max_results=5)
                    for paper in result.papers:
                        saved = persistence.save_paper(paper, db)
                        if saved:
                            trial_count += 1
                    time.sleep(0.5)
            finally:
                ct.close()

            logger.info(f"[preprint_and_trials] 임상시험: {trial_count}건 신규 ({target_allergens})")
        except Exception as e:
            logger.warning(f"[preprint_and_trials] 임상시험 검색 실패: {e}")

        db.commit()

        summary = {
            "preprints_saved": preprint_count,
            "trials_saved": trial_count,
        }
        _log_complete(db, log, summary)
        logger.info(f"[preprint_and_trials] 완료: {summary}")

    except Exception as e:
        _log_fail(db, log, str(e))
        logger.error(f"[preprint_and_trials] 실패: {e}")
    finally:
        db.close()



# ============================================================================
# Job: 알러젠 직접 뉴스 수집 (followup-plan §2) — 주1회
# ============================================================================

def job_allergen_news_collection(trigger_type: str = "scheduled") -> None:
    """AllergenMaster 키워드로 직접 뉴스 검색 → CompetitorNews + NewsAllergenLink 저장.

    경쟁사 뉴스에 알러젠 태깅이 약해 종합 트렌드의 뉴스 섹션이 비어있던 문제 해결.
    검색 시점에 allergen_code 가 결정되므로 LLM 추정 없이 deterministic 태깅.
    """
    db = SessionLocal()
    log = _log_start(db, "allergen_news_collection", trigger_type)

    try:
        from .competitor_news_service import CompetitorNewsService

        max_results = settings.SCHEDULER_NEWS_MAX_RESULTS
        service = CompetitorNewsService()
        try:
            result = service.collect_allergen_news(
                db=db,
                allergen_codes=None,  # KNOWN_ALLERGENS 전체
                max_results_per_allergen=max_results,
            )
        finally:
            service.close()

        summary = {
            "total_new": result.get("total_new", 0),
            "total_duplicate": result.get("total_duplicate", 0),
            "total_links": result.get("total_links", 0),
            "allergens_searched": len(result.get("allergen_stats", {})),
        }
        _log_complete(db, log, summary)
        logger.info(
            f"[allergen_news_collection] 완료: 신규 {summary['total_new']}건, "
            f"링크 {summary['total_links']}건 ({summary['allergens_searched']}종)"
        )

    except Exception as e:
        _log_fail(db, log, str(e))
        logger.error(f"[allergen_news_collection] 실패: {e}")
    finally:
        db.close()


# ============================================================================
# Job: 임상 함의(clinical_implication) 일일 백필 — B2a-cron
# ============================================================================

def job_clinical_implication_backfill(trigger_type: str = "scheduled") -> None:
    """매일 새벽 미처리 논문에 clinical_implication LLM 추출.

    무료 티어 Gemini RPD 한도(Flash-Lite 1,000/일) 안에서 점진적 누적.
    - 매 호출 사이 throttle 로 RPM 한도 회피
    - 연속 실패/빈 응답 누적 시 early-stop 으로 호출 낭비 차단
    - skip_extracted=True 로 멱등 — 매일 호출 시 새 논문만 처리

    환경변수 오버라이드:
      CLINICAL_IMPLICATION_BATCH_LIMIT (default: 300)
      CLINICAL_IMPLICATION_INTERVAL_MS (default: 7000)
      CLINICAL_IMPLICATION_EARLY_STOP  (default: 5)
    """
    db = SessionLocal()
    log = _log_start(db, "clinical_implication_backfill", trigger_type)

    try:
        from .clinical_implication_service import (
            get_clinical_implication_service,
        )

        service = get_clinical_implication_service()
        limit = int(os.getenv("CLINICAL_IMPLICATION_BATCH_LIMIT", "300"))
        interval_ms = int(os.getenv("CLINICAL_IMPLICATION_INTERVAL_MS", "7000"))
        early_stop = int(os.getenv("CLINICAL_IMPLICATION_EARLY_STOP", "5"))

        result = service.extract_from_papers(
            db,
            limit=limit,
            skip_extracted=True,
            interval_ms=interval_ms,
            early_stop_after_failures=early_stop,
        )
        summary = {
            "limit": limit,
            "interval_ms": interval_ms,
            "early_stop_after_failures": early_stop,
            **result,
        }
        _log_complete(db, log, summary)
        logger.info(f"[clinical_implication_backfill] 완료: {summary}")

    except Exception as e:
        _log_fail(db, log, str(e))
        logger.error(f"[clinical_implication_backfill] 실패: {e}")
    finally:
        db.close()
