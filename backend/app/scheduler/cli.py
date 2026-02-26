"""스케줄러 CLI 엔트리포인트

독립 실행: python -m app.scheduler.cli [옵션]

옵션:
    --run-once       수집 + 분석 + 발송 1회 실행 후 종료
    --collect-only   뉴스 수집만 실행
    --process-only   AI 분석만 실행
    --send-only      뉴스레터 발송만 실행
    (옵션 없음)      스케줄러 데몬 모드로 실행
"""
import argparse
import signal
import sys
import time
import logging

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("scheduler.cli")


def main():
    parser = argparse.ArgumentParser(description="AllergyInsight 뉴스 스케줄러")
    parser.add_argument("--run-once", action="store_true", help="수집+분석+발송 1회 실행")
    parser.add_argument("--collect-only", action="store_true", help="뉴스 수집만 실행")
    parser.add_argument("--process-only", action="store_true", help="AI 분석만 실행")
    parser.add_argument("--send-only", action="store_true", help="뉴스레터 발송만 실행")
    args = parser.parse_args()

    from .jobs import collect_news, process_articles, generate_and_send_reports

    if args.collect_only:
        logger.info("=== 뉴스 수집 모드 ===")
        result = collect_news()
        if result:
            logger.info(f"수집 결과: {result}")
        sys.exit(0)

    if args.process_only:
        logger.info("=== AI 분석 모드 ===")
        process_articles()
        sys.exit(0)

    if args.send_only:
        logger.info("=== 뉴스레터 발송 모드 ===")
        generate_and_send_reports()
        sys.exit(0)

    if args.run_once:
        logger.info("=== 전체 1회 실행 모드 ===")
        result = collect_news()
        if result:
            logger.info(f"수집 결과: {result}")
        process_articles()
        generate_and_send_reports()
        logger.info("=== 전체 1회 실행 완료 ===")
        sys.exit(0)

    # 데몬 모드: 스케줄러 시작 후 대기
    logger.info("=== 스케줄러 데몬 모드 시작 ===")
    from .scheduler_service import get_scheduler_service

    scheduler = get_scheduler_service()
    scheduler.start()

    # Graceful shutdown
    def signal_handler(signum, frame):
        logger.info("종료 시그널 수신, 스케줄러 중지 중...")
        scheduler.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    logger.info("스케줄러 실행 중 (Ctrl+C로 종료)")
    try:
        while True:
            time.sleep(60)
    except (KeyboardInterrupt, SystemExit):
        scheduler.stop()
        logger.info("스케줄러 종료")


if __name__ == "__main__":
    main()
