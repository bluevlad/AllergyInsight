"""Strategic Intel 백필 오케스트레이션 스크립트

5단계를 순차 실행 (각 단계 idempotent — 재실행 안전):

  1) Seed       : tech_categories + company_tech_fits 시드 (v1)
  2) Prices     : KOSDAQ 3사 + KOSDAQ 종합 일별 시세 백필
  3) Classify   : papers/news → tech 카테고리 라벨링 (LLM)
  4) Generate   : 라벨된 트리거 → 회사별 가설 생성 (4사)
  5) Validate   : 가설 → T+1d/T+5d/T+30d abnormal return 계산 + hit 판정

사용법:
    # 전체 (기본 — 2025-12-01부터 오늘까지)
    python -m scripts.backfill_strategic_intel

    # 시작일 지정
    python -m scripts.backfill_strategic_intel --start 2025-12-01 --end 2026-04-30

    # 특정 단계만
    python -m scripts.backfill_strategic_intel --only seed
    python -m scripts.backfill_strategic_intel --only prices
    python -m scripts.backfill_strategic_intel --only classify
    python -m scripts.backfill_strategic_intel --only generate
    python -m scripts.backfill_strategic_intel --only validate

    # 단계 스킵
    python -m scripts.backfill_strategic_intel --skip seed prices

    # Dry-run (DB write 없음, 카운트만)
    python -m scripts.backfill_strategic_intel --dry-run

    # 분류 대상 제한 (디버그)
    python -m scripts.backfill_strategic_intel --classify-limit 50
"""
from __future__ import annotations

import argparse
import logging
import os
import sys
import time
from datetime import date, datetime, timedelta

# 프로젝트 루트를 sys.path에 추가
_backend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.insert(0, _backend_dir)

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


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [strategic-intel-backfill] %(message)s",
)
logger = logging.getLogger(__name__)


DEFAULT_START = date(2025, 12, 1)


# ---------------------------------------------------------------------------
# Stage 함수
# ---------------------------------------------------------------------------


def stage_seed(db) -> dict:
    """Stage 1: Tech taxonomy + Fit matrix v1 시드"""
    from app.database.seed_strategic_intel import seed_all

    t0 = time.time()
    result = seed_all(db)
    logger.info(
        "[seed] tech=%d fit=%d (%.2fs)",
        result["tech_categories_inserted"],
        result["fit_cells_inserted"],
        time.time() - t0,
    )
    return {"stage": "seed", **result}


def stage_prices(db, start: date, end: date) -> dict:
    """Stage 2: 일별 시세 백필"""
    from app.services.strategic_intel import stock_price_service as price_svc

    t0 = time.time()
    result = price_svc.collect_all(db, start, end)
    logger.info("[prices] %s (%.2fs)", result, time.time() - t0)
    return {"stage": "prices", "rows_per_ticker": result, "elapsed_s": round(time.time() - t0, 2)}


def stage_classify(db, start: date, end: date, limit: int | None = None) -> dict:
    """Stage 3: papers/news 라벨링

    대상:
      - papers: published_at >= start (NULL이면 year로 fallback — start.year 이상이면 포함)
      - competitor_news: published_at >= start, 4사 (sugentech/greencross/bodytech/madx) 한정
    """
    from app.database.competitor_models import CompetitorCompany, CompetitorNews
    from app.database.models import Paper as PaperORM
    from app.database.strategic_intel_models import NewsTechLink, PaperTechLink
    from app.services.strategic_intel.tech_classifier import (
        TechClassifier,
        ALL_COMPANIES_FOR_NEWS_FILTER,
    )

    t0 = time.time()
    classifier = TechClassifier(db)

    # ---- Papers ----
    paper_q = (
        db.query(PaperORM)
        .outerjoin(
            PaperTechLink,
            (PaperTechLink.paper_id == PaperORM.id)
            & (PaperTechLink.classifier_version == classifier.CLASSIFIER_VERSION_USED),
        )
        .filter(PaperTechLink.id.is_(None))  # 미분류만
        .filter(
            (PaperORM.published_at >= start)
            | ((PaperORM.published_at.is_(None)) & (PaperORM.year >= start.year))
        )
    )
    if end:
        paper_q = paper_q.filter(
            (PaperORM.published_at <= end)
            | ((PaperORM.published_at.is_(None)) & (PaperORM.year <= end.year))
        )
    paper_q = paper_q.order_by(PaperORM.id.asc())
    if limit:
        paper_q = paper_q.limit(limit)
    papers = paper_q.all()

    paper_labels = 0
    paper_skipped = 0
    for p in papers:
        try:
            labels = classifier.classify_and_save_paper(p)
            if labels:
                paper_labels += len(labels)
            else:
                paper_skipped += 1
        except Exception as e:
            logger.warning("paper classify failed (id=%s): %s", p.id, e)
            paper_skipped += 1
    logger.info(
        "[classify/papers] processed=%d labeled=%d skipped=%d",
        len(papers),
        len(papers) - paper_skipped,
        paper_skipped,
    )

    # ---- News (4사 한정) ----
    target_codes = list(ALL_COMPANIES_FOR_NEWS_FILTER)
    target_company_ids = [
        cid for (cid,) in db.query(CompetitorCompany.id)
        .filter(CompetitorCompany.code.in_(target_codes)).all()
    ]
    news_q = (
        db.query(CompetitorNews)
        .outerjoin(
            NewsTechLink,
            (NewsTechLink.news_id == CompetitorNews.id)
            & (NewsTechLink.classifier_version == classifier.CLASSIFIER_VERSION_USED),
        )
        .filter(NewsTechLink.id.is_(None))
        .filter(CompetitorNews.company_id.in_(target_company_ids))
        .filter(CompetitorNews.published_at >= datetime.combine(start, datetime.min.time()))
    )
    if end:
        news_q = news_q.filter(
            CompetitorNews.published_at <= datetime.combine(end, datetime.max.time())
        )
    news_q = news_q.order_by(CompetitorNews.id.asc())
    if limit:
        news_q = news_q.limit(limit)
    newslist = news_q.all()

    news_labels = 0
    news_skipped = 0
    for n in newslist:
        try:
            labels = classifier.classify_and_save_news(n)
            if labels:
                news_labels += len(labels)
            else:
                news_skipped += 1
        except Exception as e:
            logger.warning("news classify failed (id=%s): %s", n.id, e)
            news_skipped += 1

    logger.info(
        "[classify/news] processed=%d labeled=%d skipped=%d",
        len(newslist),
        len(newslist) - news_skipped,
        news_skipped,
    )

    return {
        "stage": "classify",
        "papers_processed": len(papers),
        "papers_labels_added": paper_labels,
        "news_processed": len(newslist),
        "news_labels_added": news_labels,
        "elapsed_s": round(time.time() - t0, 2),
    }


def stage_generate(db, start: date, end: date) -> dict:
    """Stage 4: 라벨된 paper/news → 가설 생성 (4사)

    중복 가설은 자동 skip (HypothesisGenerator 내부에서 검사).
    """
    from app.database.competitor_models import CompetitorNews
    from app.database.models import Paper as PaperORM
    from app.database.strategic_intel_models import NewsTechLink, PaperTechLink
    from app.services.strategic_intel.hypothesis_engine import HypothesisGenerator

    t0 = time.time()
    gen = HypothesisGenerator(db)

    # ---- Paper trigger ----
    labeled_paper_ids = (
        db.query(PaperTechLink.paper_id).distinct().subquery()
    )
    paper_q = (
        db.query(PaperORM)
        .filter(PaperORM.id.in_(labeled_paper_ids))
        .filter(
            (PaperORM.published_at >= start)
            | ((PaperORM.published_at.is_(None)) & (PaperORM.year >= start.year))
        )
    )
    if end:
        paper_q = paper_q.filter(
            (PaperORM.published_at <= end)
            | ((PaperORM.published_at.is_(None)) & (PaperORM.year <= end.year))
        )
    papers = paper_q.all()

    paper_hypos = 0
    for p in papers:
        try:
            hypos = gen.generate_for_paper(p)
            paper_hypos += len(hypos)
        except Exception as e:
            logger.warning("paper hypothesis gen failed (id=%s): %s", p.id, e)
    logger.info("[generate/papers] %d papers → %d hypotheses", len(papers), paper_hypos)

    # ---- News trigger ----
    labeled_news_ids = (
        db.query(NewsTechLink.news_id).distinct().subquery()
    )
    news_q = (
        db.query(CompetitorNews)
        .filter(CompetitorNews.id.in_(labeled_news_ids))
        .filter(CompetitorNews.published_at >= datetime.combine(start, datetime.min.time()))
    )
    if end:
        news_q = news_q.filter(
            CompetitorNews.published_at <= datetime.combine(end, datetime.max.time())
        )
    newslist = news_q.all()

    news_hypos = 0
    for n in newslist:
        try:
            hypos = gen.generate_for_news(n)
            news_hypos += len(hypos)
        except Exception as e:
            logger.warning("news hypothesis gen failed (id=%s): %s", n.id, e)
    logger.info("[generate/news] %d news → %d hypotheses", len(newslist), news_hypos)

    return {
        "stage": "generate",
        "paper_triggers": len(papers),
        "paper_hypotheses": paper_hypos,
        "news_triggers": len(newslist),
        "news_hypotheses": news_hypos,
        "elapsed_s": round(time.time() - t0, 2),
    }


def stage_validate(db, batch_limit: int = 1000) -> dict:
    """Stage 5: 가설 검증 (T+1d/T+5d/T+30d abnormal return + hit 판정)"""
    from app.services.strategic_intel.hypothesis_engine import HypothesisValidator

    t0 = time.time()
    validator = HypothesisValidator(db)
    result = validator.validate_pending(limit=batch_limit)
    logger.info("[validate] checked=%d updated=%d", result["checked"], result["updated"])
    return {"stage": "validate", **result, "elapsed_s": round(time.time() - t0, 2)}


# ---------------------------------------------------------------------------
# 메인
# ---------------------------------------------------------------------------


STAGES_ORDER = ["seed", "prices", "classify", "generate", "validate"]


def parse_date(s: str) -> date:
    return datetime.strptime(s, "%Y-%m-%d").date()


def main():
    parser = argparse.ArgumentParser(description="Strategic Intel 백필")
    parser.add_argument("--start", type=parse_date, default=DEFAULT_START)
    parser.add_argument("--end", type=parse_date, default=date.today())
    parser.add_argument("--only", choices=STAGES_ORDER, help="단일 단계만 실행")
    parser.add_argument(
        "--skip", nargs="+", choices=STAGES_ORDER, default=[], help="스킵할 단계"
    )
    parser.add_argument("--classify-limit", type=int, default=None, help="분류 처리 제한")
    parser.add_argument("--validate-limit", type=int, default=1000)
    parser.add_argument("--dry-run", action="store_true", help="DB 커밋 없이 카운트만")
    args = parser.parse_args()

    if args.start > args.end:
        logger.error("start (%s) > end (%s)", args.start, args.end)
        sys.exit(2)

    selected = [args.only] if args.only else [s for s in STAGES_ORDER if s not in args.skip]

    logger.info(
        "Backfill 시작: start=%s end=%s stages=%s dry_run=%s",
        args.start, args.end, selected, args.dry_run,
    )

    from app.database.connection import SessionLocal, init_db

    # 테이블 보장 + 마이그레이션
    init_db()

    db = SessionLocal()
    summary = []
    try:
        for stage in selected:
            if stage == "seed":
                summary.append(stage_seed(db))
            elif stage == "prices":
                summary.append(stage_prices(db, args.start, args.end))
            elif stage == "classify":
                summary.append(stage_classify(db, args.start, args.end, args.classify_limit))
            elif stage == "generate":
                summary.append(stage_generate(db, args.start, args.end))
            elif stage == "validate":
                summary.append(stage_validate(db, args.validate_limit))

            if args.dry_run:
                db.rollback()
                logger.info("[dry-run] rollback after stage=%s", stage)
            else:
                db.commit()
    except Exception:
        db.rollback()
        logger.exception("백필 중단 — rollback 수행")
        raise
    finally:
        db.close()

    logger.info("=" * 70)
    logger.info("Backfill 완료")
    for entry in summary:
        logger.info("  %s", entry)
    logger.info("=" * 70)


if __name__ == "__main__":
    main()
