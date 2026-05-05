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


def stage_classify(
    db,
    start: date,
    end: date,
    limit: int | None = None,
    *,
    max_per_run: int | None = None,
    rpm_limit: int = 12,
    target: str = "all",
    progress_every: int = 25,
) -> dict:
    """Stage 3: papers/news 라벨링

    대상:
      - papers: published_at >= start (NULL이면 year로 fallback — start.year 이상이면 포함)
      - competitor_news: published_at >= start, 4사 (sugentech/greencross/bodytech/madx) 한정

    무료 한도 대응:
      - max_per_run    : 이번 실행에서 처리할 *총* 항목 수 상한 (Gemini 무료 RPD 1,500 대비 1,400 권장)
      - rpm_limit      : 분당 호출 상한 (free tier 15 RPM → 12로 안전 마진)
      - target         : 'papers' | 'news' | 'all' — 분리 실행 가능
      - progress_every : N개마다 진행 로그 출력
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

    # 페이싱 설정 — 분당 rpm_limit 호출 → 호출당 최소 간격
    min_interval_s = 60.0 / max(1, rpm_limit)
    last_call_at = [0.0]

    def pace():
        elapsed = time.time() - last_call_at[0]
        if elapsed < min_interval_s:
            time.sleep(min_interval_s - elapsed)
        last_call_at[0] = time.time()

    remaining = [max_per_run] if max_per_run else [None]
    aggregate = {
        "papers_processed": 0,
        "papers_labels_added": 0,
        "news_processed": 0,
        "news_labels_added": 0,
        "stopped_by_quota": False,
    }

    # ---- Papers ----
    if target in ("all", "papers") and (remaining[0] is None or remaining[0] > 0):
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
        if remaining[0] is not None:
            paper_q = paper_q.limit(remaining[0])
        papers = paper_q.all()

        paper_labels = 0
        for idx, p in enumerate(papers, 1):
            try:
                pace()
                labels = classifier.classify_and_save_paper(p)
                if labels:
                    paper_labels += len(labels)
            except Exception as e:
                logger.warning("paper classify failed (id=%s): %s", p.id, e)
            if idx % progress_every == 0:
                logger.info(
                    "[classify/papers] progress %d/%d (labels added=%d, elapsed=%.0fs)",
                    idx, len(papers), paper_labels, time.time() - t0,
                )
            if remaining[0] is not None:
                remaining[0] -= 1
                if remaining[0] <= 0:
                    aggregate["stopped_by_quota"] = True
                    logger.info("[classify/papers] daily quota reached (max_per_run=%d)", max_per_run)
                    break
        aggregate["papers_processed"] = len(papers) if not aggregate["stopped_by_quota"] else (max_per_run - max(0, remaining[0] or 0))
        aggregate["papers_labels_added"] = paper_labels
        logger.info(
            "[classify/papers] done — processed=%d labels=%d",
            aggregate["papers_processed"], paper_labels,
        )

    # ---- News (4사 한정) ----
    if (
        target in ("all", "news")
        and not aggregate["stopped_by_quota"]
        and (remaining[0] is None or remaining[0] > 0)
    ):
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
        if remaining[0] is not None:
            news_q = news_q.limit(remaining[0])
        newslist = news_q.all()

        news_labels = 0
        for idx, n in enumerate(newslist, 1):
            try:
                pace()
                labels = classifier.classify_and_save_news(n)
                if labels:
                    news_labels += len(labels)
            except Exception as e:
                logger.warning("news classify failed (id=%s): %s", n.id, e)
            if idx % progress_every == 0:
                logger.info(
                    "[classify/news] progress %d/%d (labels added=%d, elapsed=%.0fs)",
                    idx, len(newslist), news_labels, time.time() - t0,
                )
            if remaining[0] is not None:
                remaining[0] -= 1
                if remaining[0] <= 0:
                    aggregate["stopped_by_quota"] = True
                    logger.info("[classify/news] daily quota reached (max_per_run=%d)", max_per_run)
                    break
        aggregate["news_processed"] = len(newslist) if not aggregate["stopped_by_quota"] else (len(newslist) - max(0, remaining[0] or 0))
        aggregate["news_labels_added"] = news_labels
        logger.info(
            "[classify/news] done — processed=%d labels=%d",
            aggregate["news_processed"], news_labels,
        )

    return {
        "stage": "classify",
        "rpm_limit": rpm_limit,
        "max_per_run": max_per_run,
        "target": target,
        **aggregate,
        "elapsed_s": round(time.time() - t0, 2),
    }


def stage_generate(db, start: date, end: date, *, regenerate: bool = False) -> dict:
    """Stage 4: 라벨된 paper/news → 가설 생성 (4사)

    중복 가설은 자동 skip (HypothesisGenerator 내부에서 검사).
    regenerate=True 인 경우 generator_version 매칭 가설을 모두 삭제 후 재생성.
    """
    from app.database.competitor_models import CompetitorNews
    from app.database.models import Paper as PaperORM
    from app.database.strategic_intel_models import (
        HypothesisLog,
        NewsTechLink,
        PaperTechLink,
    )
    from app.services.strategic_intel.hypothesis_engine import (
        GENERATOR_VERSION,
        HypothesisGenerator,
    )

    t0 = time.time()
    gen = HypothesisGenerator(db)

    if regenerate:
        deleted = (
            db.query(HypothesisLog)
            .filter(HypothesisLog.generator_version == GENERATOR_VERSION)
            .delete(synchronize_session=False)
        )
        db.commit()
        logger.info("[generate] regenerate=True — deleted %d existing hypotheses (version=%s)", deleted, GENERATOR_VERSION)

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


def stage_disclosures(db, start: date, end: date) -> dict:
    """Stage 2.5 (Phase D): DART 공시 → competitor_news 적재 (3사)

    DART_API_KEY 가 없으면 graceful skip.
    """
    from app.services.strategic_intel.disclosure_service import DartDisclosureService

    t0 = time.time()
    svc = DartDisclosureService()
    if not svc._has_key():
        logger.warning("[disclosures] DART_API_KEY 미설정 — skip")
        return {
            "stage": "disclosures",
            "skipped": True,
            "reason": "DART_API_KEY missing",
            "elapsed_s": round(time.time() - t0, 2),
        }
    results = svc.collect_all(db, since=start, until=end)
    summary = [
        {
            "company": r.company_code,
            "fetched": r.fetched,
            "inserted": r.inserted,
            **({"error": r.error} if r.error else {}),
        }
        for r in results
    ]
    logger.info("[disclosures] %s (%.2fs)", summary, time.time() - t0)
    return {
        "stage": "disclosures",
        "results": summary,
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


def stage_qualitative(
    db,
    *,
    since: date | None = None,
    limit: int = 100,
    rpm_limit: int = 12,
) -> dict:
    """Stage 6 (Phase B): LLM 정성 보강 — 룰 결정 위에 정성 분석 레이어.

    Gemini 무료 한도(15 RPM / 1,500 RPD) 안전 마진 적용 — limit + 호출 간격.
    `qualitative_version` 가 현재 버전과 다른 가설만 처리 (idempotent).
    """
    from app.services.strategic_intel.qualitative_enhancer import (
        HypothesisQualitativeEnhancer,
    )

    t0 = time.time()
    interval = max(0, 60.0 / rpm_limit) if rpm_limit > 0 else 0
    enhancer = HypothesisQualitativeEnhancer(db)

    # 페이싱: enhance_pending 은 1회 호출에 limit 만큼 처리하므로 단일 호출.
    # rpm_limit 은 enhance_one 사이에 sleep 으로 유지.
    from app.database.strategic_intel_models import HypothesisLog
    q = db.query(HypothesisLog).filter(
        (HypothesisLog.qualitative_version.is_(None))
        | (HypothesisLog.qualitative_version != enhancer.VERSION)
    )
    if since is not None:
        q = q.filter(HypothesisLog.trigger_date >= since)
    rows = (
        q.order_by(HypothesisLog.trigger_date.desc(), HypothesisLog.id.desc())
        .limit(limit)
        .all()
    )

    updated = 0
    for i, h in enumerate(rows):
        try:
            if enhancer.enhance_one(h):
                updated += 1
        except Exception as e:
            logger.warning("enhance_one failed h=%s: %s", h.id, e)
        if interval and i + 1 < len(rows):
            time.sleep(interval)

    logger.info("[qualitative] checked=%d updated=%d (%.2fs)",
                len(rows), updated, time.time() - t0)
    return {
        "stage": "qualitative",
        "checked": len(rows),
        "updated": updated,
        "elapsed_s": round(time.time() - t0, 2),
    }


# ---------------------------------------------------------------------------
# 메인
# ---------------------------------------------------------------------------


STAGES_ORDER = ["seed", "prices", "disclosures", "classify", "generate", "validate", "qualitative"]


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
    parser.add_argument("--classify-limit", type=int, default=None, help="분류 항목 수 제한 (디버그용)")
    parser.add_argument(
        "--max-per-run", type=int, default=1400,
        help="이번 실행 총 처리 상한 (Gemini 무료 RPD 1500 → 기본 1400 안전 마진)",
    )
    parser.add_argument(
        "--rpm-limit", type=int, default=12,
        help="분당 호출 상한 (Gemini 무료 RPM 15 → 기본 12 안전 마진)",
    )
    parser.add_argument(
        "--target", choices=["all", "papers", "news"], default="all",
        help="분류 대상 — papers/news 분리 실행 가능",
    )
    parser.add_argument("--validate-limit", type=int, default=1000)
    parser.add_argument(
        "--regenerate", action="store_true",
        help="generate 단계에서 기존 가설(현재 generator_version)을 삭제 후 재생성",
    )
    parser.add_argument(
        "--qualitative-limit", type=int, default=100,
        help="qualitative 단계에서 1회 처리할 가설 수 상한 (LLM 비용 안전 마진)",
    )
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
            elif stage == "disclosures":
                summary.append(stage_disclosures(db, args.start, args.end))
            elif stage == "classify":
                summary.append(stage_classify(
                    db, args.start, args.end, args.classify_limit,
                    max_per_run=args.max_per_run,
                    rpm_limit=args.rpm_limit,
                    target=args.target,
                ))
            elif stage == "generate":
                summary.append(stage_generate(db, args.start, args.end, regenerate=args.regenerate))
            elif stage == "validate":
                summary.append(stage_validate(db, args.validate_limit))
            elif stage == "qualitative":
                summary.append(stage_qualitative(
                    db,
                    since=args.start,
                    limit=args.qualitative_limit,
                    rpm_limit=args.rpm_limit,
                ))

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
