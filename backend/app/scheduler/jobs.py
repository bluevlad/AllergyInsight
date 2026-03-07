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


def generate_and_send_reports():
    """뉴스레터 생성 및 발송

    인증된 구독자에게 키워드 매칭 기반 뉴스레터를 발송합니다.
    """
    logger.info(f"[{datetime.now().isoformat()}] 뉴스레터 발송 시작")
    db = SessionLocal()
    try:
        from ..services.newsletter_service import NewsletterService

        service = NewsletterService()
        result = service.send_to_subscribers(db=db, days=1)
        logger.info(f"뉴스레터 발송 완료: {result['message']}")
    except Exception as e:
        logger.error(f"뉴스레터 발송 실패: {e}", exc_info=True)
    finally:
        db.close()
