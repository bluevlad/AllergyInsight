"""연도별 논문 벌크 수집 스크립트

최근 10년(2016~2026) 알러지 논문을 연도별 × 알레르겐별로 수집하고,
수집 완료 후 RAG DB를 재구축합니다.

사용법:
    # 전체 수집 (2016~2026)
    python -m scripts.bulk_collect_papers

    # 특정 연도 범위
    python -m scripts.bulk_collect_papers --start-year 2020 --end-year 2024

    # RAG 재구축만
    python -m scripts.bulk_collect_papers --rag-only

    # 수집만 (RAG 재구축 없이)
    python -m scripts.bulk_collect_papers --no-rag
"""
import argparse
import logging
import os
import sys
import time
from datetime import datetime

# 프로젝트 루트를 sys.path에 추가
_backend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.insert(0, _backend_dir)

# .env 로드 (Docker 환경에서는 환경변수가 이미 설정됨)
try:
    from dotenv import load_dotenv

    for env_path in [
        os.path.join(_backend_dir, "..", ".env"),
        os.path.join(_backend_dir, ".env"),
    ]:
        if os.path.exists(env_path):
            load_dotenv(env_path, override=False)
            break
except ImportError:
    pass

from app.config import settings
from app.database.connection import SessionLocal
from app.database.scheduler_models import SchedulerExecutionLog

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# 전체 알레르겐 목록 (17종)
ALL_ALLERGENS = [
    "peanut", "tree_nut", "shellfish", "milk", "egg",
    "wheat", "soy", "fish", "sesame",
    "dust_mite", "cat", "dog", "pollen", "mold",
    "latex", "insect", "drug",
]

# 소스당 최대 결과 수 (벌크 수집이므로 넉넉하게)
MAX_RESULTS_PER_SOURCE = 50


def _save_paper_safe(persistence, paper, db, allergen_code=None):
    """논문 저장 (savepoint로 격리, 개별 실패가 전체에 영향 없음)"""
    savepoint = db.begin_nested()
    try:
        saved = persistence.save_paper(paper, db, allergen_code=allergen_code)
        savepoint.commit()
        return saved
    except Exception:
        savepoint.rollback()
        return False


def collect_year(year: int, allergens: list[str], dry_run: bool = False) -> dict:
    """특정 연도의 논문 수집

    Args:
        year: 수집 대상 연도
        allergens: 수집할 알레르겐 목록
        dry_run: True이면 실제 DB 저장 안함

    Returns:
        {"year": int, "total_found": int, "total_new": int, "details": dict}
    """
    from app.services.pubmed_service import PubMedService
    from app.services.europe_pmc_service import EuropePMCService
    from app.services.openalex_service import OpenAlexService
    from app.services.paper_persistence_service import PaperPersistenceService

    db = SessionLocal()
    persistence = PaperPersistenceService()

    pubmed = PubMedService(
        api_key=settings.PUBMED_API_KEY,
        email=settings.PUBMED_EMAIL,
    )
    epmc = EuropePMCService()
    openalex = OpenAlexService(email=settings.PUBMED_EMAIL)

    min_date = f"{year}/01/01"
    max_date = f"{year}/12/31"

    total_found = 0
    total_new = 0
    details = {}

    try:
        for allergen in allergens:
            allergen_found = 0
            allergen_new = 0

            # --- PubMed (연도 필터 지원) ---
            try:
                query = (
                    f'("{allergen}"[Title/Abstract]) AND '
                    f'(allergy[Title/Abstract] OR allergic[Title/Abstract] '
                    f'OR hypersensitivity[Title/Abstract])'
                )
                result = pubmed.search(
                    query=query,
                    max_results=MAX_RESULTS_PER_SOURCE,
                    sort="relevance",
                    min_date=min_date,
                    max_date=max_date,
                )
                for paper in result.papers:
                    if _save_paper_safe(persistence, paper, db, allergen_code=allergen):
                        allergen_new += 1
                allergen_found += len(result.papers)
            except Exception as e:
                logger.warning(f"  PubMed 실패 ({allergen}, {year}): {e}")

            time.sleep(0.5)

            # --- Europe PMC (연도 필터 쿼리 구성) ---
            try:
                epmc_query = f'{allergen} allergy PUB_YEAR:{year}'
                result = epmc.search(epmc_query, max_results=MAX_RESULTS_PER_SOURCE)
                for paper in result.papers:
                    if _save_paper_safe(persistence, paper, db, allergen_code=allergen):
                        allergen_new += 1
                allergen_found += len(result.papers)
            except Exception as e:
                logger.warning(f"  Europe PMC 실패 ({allergen}, {year}): {e}")

            time.sleep(0.5)

            # --- OpenAlex (클라이언트 사이드 연도 필터) ---
            try:
                oa_query = f"{allergen} allergy"
                result = openalex.search(oa_query, max_results=MAX_RESULTS_PER_SOURCE)
                for paper in result.papers:
                    if paper.year and paper.year == year:
                        if _save_paper_safe(persistence, paper, db, allergen_code=allergen):
                            allergen_new += 1
                        allergen_found += 1
            except Exception as e:
                logger.warning(f"  OpenAlex 실패 ({allergen}, {year}): {e}")

            # Rate limit 준수 (알레르겐 사이 2초 간격)
            time.sleep(2)

            total_found += allergen_found
            total_new += allergen_new
            details[allergen] = {"found": allergen_found, "new": allergen_new}

            logger.info(
                f"  {allergen}: {allergen_found}건 발견, {allergen_new}건 신규"
            )

        db.commit()

    except Exception as e:
        db.rollback()
        logger.error(f"연도 {year} 수집 중 오류: {e}")
        raise
    finally:
        epmc.close()
        openalex.close()
        db.close()

    return {
        "year": year,
        "total_found": total_found,
        "total_new": total_new,
        "details": details,
    }


def rebuild_rag_db() -> dict:
    """RAG DB 재구축 (기존 인덱스 삭제 → 전체 재인덱싱)"""
    from app.services.rag_service import get_rag_service

    logger.info("=" * 60)
    logger.info("RAG DB 재구축 시작")
    logger.info("=" * 60)

    rag = get_rag_service()
    if not rag.is_available:
        logger.error("ChromaDB를 사용할 수 없습니다.")
        return {"error": "ChromaDB unavailable"}

    # 1) 기존 컬렉션 삭제 후 재생성
    try:
        if rag._client:
            rag._client.delete_collection("allergy_papers")
            logger.info("기존 RAG 컬렉션 삭제 완료")
            rag._collection = None
            rag._available = None
    except Exception as e:
        logger.warning(f"기존 컬렉션 삭제 중 오류 (무시): {e}")

    # 2) 전체 논문 배치 인덱싱
    db = SessionLocal()
    try:
        from app.database.models import Paper as PaperORM

        total_papers = (
            db.query(PaperORM)
            .filter(PaperORM.abstract.isnot(None))
            .filter(PaperORM.abstract != "")
            .count()
        )
        logger.info(f"인덱싱 대상 논문 수: {total_papers}건")

        batch_size = 500
        total_indexed = 0
        total_chunks = 0

        while True:
            result = rag.index_papers_from_db(db, batch_size=batch_size)
            indexed = result.get("indexed", 0)
            chunks = result.get("total_chunks", 0)

            if indexed == 0:
                break

            total_indexed += indexed
            total_chunks += chunks

            logger.info(
                f"  배치 인덱싱: +{indexed}건 ({total_indexed}/{total_papers}), "
                f"+{chunks}개 청크"
            )

        logger.info(
            f"RAG 재구축 완료: {total_indexed}건 인덱싱, "
            f"{total_chunks}개 청크 생성"
        )

        return {
            "total_papers": total_papers,
            "indexed": total_indexed,
            "total_chunks": total_chunks,
        }

    finally:
        db.close()


def log_bulk_execution(start_time: float, results: list[dict], rag_result: dict | None) -> None:
    """벌크 수집 실행 로그를 스케줄러 로그에 기록"""
    db = SessionLocal()
    try:
        duration = time.time() - start_time
        total_found = sum(r["total_found"] for r in results)
        total_new = sum(r["total_new"] for r in results)

        log = SchedulerExecutionLog(
            job_id="bulk_paper_collect",
            status="success",
            started_at=datetime.utcfromtimestamp(start_time),
            completed_at=datetime.utcnow(),
            duration_seconds=duration,
            trigger_type="manual",
            result_summary={
                "years_processed": len(results),
                "total_found": total_found,
                "total_new": total_new,
                "year_details": {r["year"]: r["total_new"] for r in results},
                "rag_rebuild": rag_result,
            },
        )
        db.add(log)
        db.commit()
        logger.info(f"실행 로그 저장 완료 (duration={duration:.1f}s)")
    except Exception as e:
        logger.warning(f"실행 로그 저장 실패: {e}")
    finally:
        db.close()


def main():
    parser = argparse.ArgumentParser(description="AllergyInsight 논문 벌크 수집")
    parser.add_argument(
        "--start-year", type=int, default=2016,
        help="수집 시작 연도 (기본: 2016)",
    )
    parser.add_argument(
        "--end-year", type=int, default=2026,
        help="수집 종료 연도 (기본: 2026)",
    )
    parser.add_argument(
        "--allergens", nargs="*", default=None,
        help="수집할 알레르겐 (기본: 전체 17종)",
    )
    parser.add_argument(
        "--rag-only", action="store_true",
        help="RAG DB 재구축만 실행",
    )
    parser.add_argument(
        "--no-rag", action="store_true",
        help="RAG DB 재구축 건너뛰기",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="실제 DB 저장 없이 시뮬레이션",
    )

    args = parser.parse_args()
    allergens = args.allergens or ALL_ALLERGENS
    start_time = time.time()

    logger.info("=" * 60)
    logger.info("AllergyInsight 논문 벌크 수집 시작")
    logger.info(f"  연도 범위: {args.start_year} ~ {args.end_year}")
    logger.info(f"  알레르겐: {len(allergens)}종")
    logger.info(f"  소스당 최대: {MAX_RESULTS_PER_SOURCE}건")
    logger.info("=" * 60)

    results = []
    rag_result = None

    # 1) 논문 수집 (연도 순서)
    if not args.rag_only:
        for year in range(args.start_year, args.end_year + 1):
            logger.info(f"\n{'='*40}")
            logger.info(f"[{year}] 수집 시작 ({year - args.start_year + 1}/{args.end_year - args.start_year + 1})")
            logger.info(f"{'='*40}")

            try:
                result = collect_year(year, allergens, dry_run=args.dry_run)
                results.append(result)

                logger.info(
                    f"[{year}] 완료: {result['total_found']}건 발견, "
                    f"{result['total_new']}건 신규 저장"
                )
            except Exception as e:
                logger.error(f"[{year}] 수집 실패: {e}")
                results.append({
                    "year": year,
                    "total_found": 0,
                    "total_new": 0,
                    "details": {},
                    "error": str(e),
                })

            # 연도 간 대기 (API 부하 방지)
            time.sleep(3)

    # 2) RAG DB 재구축
    if not args.no_rag:
        rag_result = rebuild_rag_db()

    # 3) 결과 요약
    elapsed = time.time() - start_time
    total_found = sum(r["total_found"] for r in results)
    total_new = sum(r["total_new"] for r in results)

    logger.info("\n" + "=" * 60)
    logger.info("벌크 수집 최종 요약")
    logger.info("=" * 60)
    logger.info(f"  소요 시간: {elapsed:.1f}초 ({elapsed/60:.1f}분)")
    logger.info(f"  처리 연도: {len(results)}개")
    logger.info(f"  전체 발견: {total_found}건")
    logger.info(f"  신규 저장: {total_new}건")

    if rag_result:
        logger.info(f"  RAG 인덱싱: {rag_result.get('indexed', 0)}건, "
                     f"{rag_result.get('total_chunks', 0)}개 청크")

    logger.info("\n연도별 상세:")
    for r in results:
        status = "ERROR" if r.get("error") else "OK"
        logger.info(
            f"  {r['year']}: {r['total_found']}건 발견, "
            f"{r['total_new']}건 신규 [{status}]"
        )

    # 4) 실행 로그 기록
    if results and not args.dry_run:
        log_bulk_execution(start_time, results, rag_result)

    logger.info("\n완료!")


if __name__ == "__main__":
    main()
