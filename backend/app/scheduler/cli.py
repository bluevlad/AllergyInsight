"""스케줄러 CLI 엔트리포인트

독립 실행: python -m app.scheduler.cli [옵션]

옵션:
    --run-once         수집 + 분석 1회 실행 후 종료
    --collect-only     뉴스 수집만 실행
    --process-only     AI 분석만 실행
    --ingest-drugs     약물 정보 수집 1회 실행 후 종료
                       (옵션: --source openfda|mfds_eyakeunyo, --limit N)
    (옵션 없음)        스케줄러 데몬 모드로 실행
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
    datefmt="%Y-%m-%d %H:%M:%S %Z",
)
logger = logging.getLogger("scheduler.cli")


def main():
    parser = argparse.ArgumentParser(description="AllergyInsight 뉴스 스케줄러")
    parser.add_argument("--run-once", action="store_true", help="수집+분석 1회 실행")
    parser.add_argument("--collect-only", action="store_true", help="뉴스 수집만 실행")
    parser.add_argument("--process-only", action="store_true", help="AI 분석만 실행")
    parser.add_argument(
        "--ingest-drugs", action="store_true", help="약물 정보 수집 1회 실행"
    )
    parser.add_argument(
        "--source", default=None, help="특정 소스만 수집 (예: openfda, mfds_eyakeunyo)"
    )
    parser.add_argument(
        "--limit", type=int, default=None, help="수집 건수 제한"
    )
    args = parser.parse_args()

    from .jobs import collect_news, process_articles, ingest_drugs

    if args.ingest_drugs:
        logger.info("=== 약물 수집 모드 ===")
        results = ingest_drugs(source=args.source, limit=args.limit)
        if results:
            for r in results:
                logger.info(
                    f"[{r.source}] ok={r.ok} success={r.success_count} "
                    f"failed={len(r.failed_items)} fatal={r.fatal_error}"
                )
        sys.exit(0)

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

    if args.run_once:
        logger.info("=== 전체 1회 실행 모드 ===")
        result = collect_news()
        if result:
            logger.info(f"수집 결과: {result}")
        process_articles()
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
