"""스케줄러 작업 함수

스케줄러에서 호출하는 작업 함수들입니다.
각 함수는 SessionLocal로 직접 DB 세션을 생성합니다.
"""
import logging
from datetime import datetime

from ..database.connection import SessionLocal
from ..services.competitor_news_service import CompetitorNewsService

logger = logging.getLogger(__name__)


def collect_news():
    """뉴스 수집 작업

    파이프라인 서비스를 통해 수집 + 중복 제거 + AI 분석을 수행합니다.
    """
    logger.info(f"[{datetime.now().isoformat()}] 뉴스 수집 시작")
    db = SessionLocal()
    try:
        from ..services.news_pipeline_service import NewsPipelineService

        pipeline = NewsPipelineService()
        result = pipeline.run_collection_pipeline(
            db=db,
            max_results_per_company=10,
            auto_analyze=True,
        )
        logger.info(
            f"뉴스 수집 완료: 신규 {result['collected']}건, "
            f"중복 {result['duplicates']}건, 분석 {result['analyzed']}건"
        )
        pipeline.close()
        return result
    except Exception as e:
        logger.error(f"뉴스 수집 실패: {e}", exc_info=True)
        return None
    finally:
        db.close()


def process_articles():
    """미분석 기사 AI 처리"""
    logger.info(f"[{datetime.now().isoformat()}] 기사 분석 시작")
    db = SessionLocal()
    try:
        from ..services.news_pipeline_service import NewsPipelineService

        pipeline = NewsPipelineService()
        analyzed = pipeline.process_unanalyzed_articles(db, limit=50)
        logger.info(f"기사 분석 완료: {analyzed}건")
        pipeline.close()
    except Exception as e:
        logger.error(f"기사 분석 실패: {e}", exc_info=True)
    finally:
        db.close()


def aggregate_paper_allergen_trends():
    """논문 알러젠 트렌드 집계 작업

    전체 연도에 대해 논문-알러젠 언급률을 재집계합니다.
    """
    logger.info(f"[{datetime.now().isoformat()}] 논문 알러젠 트렌드 집계 시작")
    db = SessionLocal()
    try:
        from ..services.allergen_trend_service import AllergenTrendService

        service = AllergenTrendService()
        results = service.aggregate_all_years(db)
        total_allergens = sum(r["allergens_processed"] for r in results)
        logger.info(
            f"논문 알러젠 트렌드 집계 완료: {len(results)}개 연도, "
            f"총 {total_allergens}건 알러젠 처리"
        )
        return results
    except Exception as e:
        logger.error(f"논문 알러젠 트렌드 집계 실패: {e}", exc_info=True)
        return None
    finally:
        db.close()


def extract_and_aggregate_treatments():
    """치료법 추출 + 트렌드 집계 작업

    미처리 논문에서 치료법을 추출하고 연도별 트렌드를 집계합니다.
    """
    logger.info(f"[{datetime.now().isoformat()}] 치료법 추출 시작")
    db = SessionLocal()
    try:
        from ..services.treatment_extraction_service import TreatmentExtractionService

        service = TreatmentExtractionService()

        # 1단계: 미처리 논문에서 치료법 추출 (100건 배치)
        extract_result = service.extract_from_papers(db, limit=100)
        logger.info(
            f"치료법 추출: 처리={extract_result['processed']}, "
            f"추출={extract_result['extracted']}, 스킵={extract_result['skipped']}"
        )

        # 2단계: 트렌드 집계
        trend_result = service.aggregate_trends(db)
        logger.info(f"치료법 트렌드 집계: {trend_result['trends_created']}건")

        return {
            "extraction": extract_result,
            "aggregation": trend_result,
        }
    except Exception as e:
        logger.error(f"치료법 추출 실패: {e}", exc_info=True)
        return None
    finally:
        db.close()


def ingest_drugs(source: str | None = None, limit: int | None = None):
    """약물 정보 증분 수집 작업.

    파이프라인(DrugIngestPipeline)으로 openFDA · MFDS 어댑터를 순차 실행한다.
    source=None 이면 등록된 모든 소스, 지정하면 단일 소스만 실행.
    """
    logger.info(
        f"[{datetime.now().isoformat()}] 약물 수집 시작 source={source or 'all'} limit={limit}"
    )
    db = SessionLocal()
    try:
        from ..services.drug_ingest.factory import build_default_pipeline

        pipeline = build_default_pipeline()
        if source:
            results = [pipeline.run_source(db, source, limit=limit)]
        else:
            results = pipeline.run_all(db, limit=limit)

        for r in results:
            status = "ok" if r.ok else f"FATAL:{r.fatal_error}"
            logger.info(
                f"약물 수집[{r.source}] {status} "
                f"success={r.success_count} failed={len(r.failed_items)}"
            )
        return results
    except Exception as e:
        logger.error(f"약물 수집 실패: {e}", exc_info=True)
        return None
    finally:
        db.close()


def tag_and_generate_insights():
    """뉴스 알러젠 태깅 + 월별 인사이트 리포트 생성

    매월 1회 실행: 미태깅 뉴스 태깅 후 전월 인사이트 리포트를 생성합니다.
    """
    logger.info(f"[{datetime.now().isoformat()}] 인사이트 리포트 생성 시작")
    db = SessionLocal()
    try:
        from ..services.insight_report_service import InsightReportService

        service = InsightReportService()

        # 1단계: 미태깅 뉴스 알러젠 태깅
        tagged = service.tag_untagged_news(db, limit=200)
        logger.info(f"뉴스 알러젠 태깅: {tagged}건")

        # 2단계: 전월 인사이트 리포트 생성
        now = datetime.now()
        if now.month == 1:
            target_year, target_month = now.year - 1, 12
        else:
            target_year, target_month = now.year, now.month - 1

        reports = service.generate_monthly_report(db, target_year, target_month)
        logger.info(f"인사이트 리포트 생성 완료: {len(reports)}건")
    except Exception as e:
        logger.error(f"인사이트 리포트 생성 실패: {e}", exc_info=True)
    finally:
        db.close()


# ============================================================================
# Strategic Intel — 4사 알러지 IVD 추적 (super_admin 전용 모듈)
# ============================================================================

def strategic_intel_daily(
    *,
    classify_window_days: int = 30,
    classify_max_per_run: int = 400,
    classify_rpm_limit: int = 12,
    qualitative_limit: int = 80,
):
    """매일 장마감 후 — 시세 갱신 + 신규 분류 + 가설 생성 + LLM 정성 보강.

    범위:
      - prices       : 최근 4일 (휴장/지연 흡수)
      - classify     : 최근 classify_window_days (기본 30일) 내 미분류 항목
      - generate     : 같은 윈도우의 라벨된 트리거 → 가설
      - qualitative  : qualitative_version 미설정 가설 최대 qualitative_limit 건

    Gemini 무료 티어 한도 (15 RPM / 1,500 RPD) 분배 — classify 400 + qualitative 80
    + 여유분.
    상세: docs/admin/STRATEGIC_INTEL_RUNBOOK.md
    """
    from datetime import date, timedelta
    from scripts.backfill_strategic_intel import (
        stage_prices,
        stage_disclosures,
        stage_classify,
        stage_generate,
        stage_qualitative,
    )

    today = date.today()
    logger.info(f"[{datetime.now().isoformat()}] strategic_intel_daily 시작")
    db = SessionLocal()
    try:
        prices_window_start = today - timedelta(days=4)
        classify_window_start = today - timedelta(days=classify_window_days)
        disclosures_window_start = today - timedelta(days=7)  # DART 1주 윈도우

        prices_result = stage_prices(db, prices_window_start, today)
        logger.info(f"strategic_intel_daily prices: {prices_result}")

        # Phase D — DART 공시 (분류기 픽업 전 적재)
        disclosures_result = stage_disclosures(db, disclosures_window_start, today)
        logger.info(f"strategic_intel_daily disclosures: {disclosures_result}")

        classify_result = stage_classify(
            db,
            classify_window_start,
            today,
            max_per_run=classify_max_per_run,
            rpm_limit=classify_rpm_limit,
            target="all",
        )
        logger.info(f"strategic_intel_daily classify: {classify_result}")

        generate_result = stage_generate(db, classify_window_start, today)
        logger.info(f"strategic_intel_daily generate: {generate_result}")

        qualitative_result = stage_qualitative(
            db,
            since=classify_window_start,
            limit=qualitative_limit,
            rpm_limit=classify_rpm_limit,
        )
        logger.info(f"strategic_intel_daily qualitative: {qualitative_result}")

        return {
            "prices": prices_result,
            "disclosures": disclosures_result,
            "classify": classify_result,
            "generate": generate_result,
            "qualitative": qualitative_result,
        }
    except Exception as e:
        logger.error(f"strategic_intel_daily 실패: {e}", exc_info=True)
        return None
    finally:
        db.close()


def strategic_intel_validate(*, batch_limit: int = 500):
    """매일 오전 — pending/partial 가설 시장 검증 (T+1d/5d/30d abnormal return)."""
    from scripts.backfill_strategic_intel import stage_validate

    logger.info(f"[{datetime.now().isoformat()}] strategic_intel_validate 시작 limit={batch_limit}")
    db = SessionLocal()
    try:
        result = stage_validate(db, batch_limit)
        logger.info(f"strategic_intel_validate: {result}")
        return result
    except Exception as e:
        logger.error(f"strategic_intel_validate 실패: {e}", exc_info=True)
        return None
    finally:
        db.close()


def strategic_intel_event_scan():
    """매일 — 검증 완료 가설 중 |abnormal_t5d|>=5% 인 후보 → 이벤트 리포트 자동 발행.

    중복 방지: trigger_hypothesis_id 매칭으로 이미 발행된 가설은 skip.
    """
    from datetime import date, timedelta
    from ..services.strategic_intel.report_service import StrategicIntelReportService

    logger.info(f"[{datetime.now().isoformat()}] strategic_intel_event_scan 시작")
    db = SessionLocal()
    try:
        svc = StrategicIntelReportService(db)
        # 최근 60일 내 검증 완료 가설만 스캔 (오래된 가설 재발행 방지)
        candidates = svc.find_event_candidates(since=date.today() - timedelta(days=60))
        published = 0
        failed = 0
        for h in candidates:
            try:
                if svc.generate_event_report(h):
                    published += 1
            except Exception as inner:
                failed += 1
                logger.warning(f"event report 발행 실패 hypothesis_id={h.id}: {inner}")
        logger.info(
            f"strategic_intel_event_scan: candidates={len(candidates)} published={published} failed={failed}"
        )
        return {"candidates": len(candidates), "published": published, "failed": failed}
    except Exception as e:
        logger.error(f"strategic_intel_event_scan 실패: {e}", exc_info=True)
        return None
    finally:
        db.close()


def strategic_intel_monthly():
    """매월 1일 — 전월 종합 리포트 자동 발행."""
    from datetime import date
    from ..services.strategic_intel.report_service import StrategicIntelReportService

    today = date.today()
    if today.month == 1:
        target_year, target_month = today.year - 1, 12
    else:
        target_year, target_month = today.year, today.month - 1

    logger.info(
        f"[{datetime.now().isoformat()}] strategic_intel_monthly 시작 — {target_year}년 {target_month:02d}월"
    )
    db = SessionLocal()
    try:
        svc = StrategicIntelReportService(db)
        report = svc.generate_monthly_report(target_year, target_month)
        if report:
            logger.info(f"월간 리포트 생성: id={report.id} {report.title}")
            return {"report_id": report.id, "title": report.title}
        logger.info("월간 리포트: 가설 데이터 없음 — skip")
        return {"report_id": None, "skipped": True}
    except Exception as e:
        logger.error(f"strategic_intel_monthly 실패: {e}", exc_info=True)
        return None
    finally:
        db.close()
