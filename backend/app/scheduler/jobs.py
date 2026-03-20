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


