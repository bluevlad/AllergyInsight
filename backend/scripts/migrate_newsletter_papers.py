"""AllergyNewsLetter → AllergyInsight 논문 마이그레이션 스크립트

AllergyNewsLetter SQLite DB에 축적된 PubMed 논문을
AllergyInsight PostgreSQL papers 테이블로 일회성 마이그레이션합니다.

Usage:
    cd /Users/rainend/GIT/AllergyInsight/backend
    python -m scripts.migrate_newsletter_papers
    python -m scripts.migrate_newsletter_papers --source /path/to/allergynewsletter.db
"""
import argparse
import json
import logging
import os
import sqlite3
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

# backend/ 디렉토리를 Python path에 추가
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database.connection import SessionLocal
from app.models.paper import Paper as PaperDC, PaperSource
from app.services.paper_persistence_service import PaperPersistenceService

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

# AllergyNewsLetter 기본 DB 경로
DEFAULT_SOURCE_DB = str(
    Path(__file__).resolve().parent.parent.parent.parent
    / "AllergyNewsLetter" / "data" / "allergynewsletter.db"
)

# 카테고리 → paper_type 매핑
CATEGORY_MAP = {
    "CLINICAL": "research",
    "RESEARCH": "research",
    "LIFESTYLE": "review",
    "MARKET": "research",
    "REGULATION": "guideline",
    "OTHER": "research",
}


@dataclass
class MigrationResult:
    total: int = 0
    new: int = 0
    duplicate: int = 0
    failed: int = 0


def load_source_articles(db_path: str) -> list[dict]:
    """AllergyNewsLetter SQLite에서 논문 레코드를 읽어옵니다."""
    if not os.path.exists(db_path):
        raise FileNotFoundError(f"소스 DB를 찾을 수 없습니다: {db_path}")

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        cursor = conn.execute(
            """
            SELECT pmid, doi, title, abstract, authors, journal,
                   pub_date, link, keyword, category, summary,
                   importance_score
            FROM articles
            WHERE content_type = 'PAPER' AND is_duplicate = 0
            ORDER BY pub_date DESC
            """
        )
        rows = [dict(row) for row in cursor.fetchall()]
        logger.info(f"소스 DB에서 {len(rows)}건 논문 로드 완료: {db_path}")
        return rows
    finally:
        conn.close()


def parse_authors(authors_json: str | None) -> list[str]:
    """JSON 문자열 형태의 authors를 list[str]로 변환합니다."""
    if not authors_json:
        return []
    try:
        parsed = json.loads(authors_json)
        if isinstance(parsed, list):
            return [str(a) for a in parsed if a]
        return []
    except (json.JSONDecodeError, TypeError):
        return [authors_json] if authors_json else []


def parse_year(pub_date: str | None) -> int | None:
    """pub_date 문자열에서 연도를 추출합니다."""
    if not pub_date:
        return None
    try:
        dt = datetime.fromisoformat(pub_date)
        return dt.year
    except (ValueError, TypeError):
        # "2026-01-15" 같은 단순 문자열 처리
        try:
            return int(pub_date[:4])
        except (ValueError, IndexError):
            return None


def article_to_paper_dc(article: dict) -> PaperDC:
    """AllergyNewsLetter article dict → AllergyInsight Paper dataclass"""
    keywords = []
    if article.get("keyword"):
        keywords = [article["keyword"]]

    # DB 컬럼 길이 제한에 맞춰 truncate
    journal = article.get("journal") or None
    if journal and len(journal) > 200:
        journal = journal[:200]

    return PaperDC(
        title=article["title"],
        abstract=article.get("abstract") or "",
        authors=parse_authors(article.get("authors")),
        source=PaperSource.PUBMED,
        source_id=article.get("pmid") or "",
        doi=article.get("doi"),
        year=parse_year(article.get("pub_date")),
        journal=journal,
        keywords=keywords,
    )


def migrate(source_db: str) -> MigrationResult:
    """메인 마이그레이션 로직"""
    result = MigrationResult()
    articles = load_source_articles(source_db)
    result.total = len(articles)

    if result.total == 0:
        logger.info("마이그레이션할 논문이 없습니다.")
        return result

    service = PaperPersistenceService()
    db = SessionLocal()

    try:
        for i, article in enumerate(articles, 1):
            title_short = article["title"][:60]
            try:
                paper_dc = article_to_paper_dc(article)

                # Savepoint로 개별 논문 실패 시 해당 건만 롤백
                savepoint = db.begin_nested()
                try:
                    saved = service.save_paper(paper_dc, db)

                    if saved:
                        result.new += 1
                        _apply_extra_fields(article, paper_dc, db)
                        log_level = "NEW"
                    else:
                        result.duplicate += 1
                        log_level = "DUP"

                    savepoint.commit()
                except Exception:
                    savepoint.rollback()
                    raise

                if i % 50 == 0 or i == result.total:
                    logger.info(
                        f"[{i}/{result.total}] {log_level}: {title_short}..."
                    )

            except Exception as e:
                result.failed += 1
                logger.warning(f"[{i}/{result.total}] FAIL: {title_short}... - {e}")
                continue

        db.commit()
        logger.info("DB 커밋 완료")

    except Exception as e:
        db.rollback()
        logger.error(f"마이그레이션 중 치명적 오류, 롤백 수행: {e}")
        raise
    finally:
        db.close()

    return result


def _apply_extra_fields(article: dict, paper_dc: PaperDC, db) -> None:
    """save_paper() 이후, ORM에 추가 필드(abstract_kr, paper_type, url)를 설정합니다."""
    from app.database.models import Paper as PaperORM
    from sqlalchemy import func

    # 방금 저장된 논문을 PMID로 찾기
    orm = None
    if paper_dc.source_id:
        orm = db.query(PaperORM).filter(
            PaperORM.pmid == paper_dc.source_id
        ).first()

    if not orm:
        return

    changed = False

    # AI 요약 → abstract_kr
    summary = article.get("summary")
    if summary and not orm.abstract_kr:
        orm.abstract_kr = summary
        changed = True

    # 카테고리 → paper_type 매핑 (extractor 결과보다 Newsletter 분류 우선)
    category = article.get("category")
    if category and category in CATEGORY_MAP:
        orm.paper_type = CATEGORY_MAP[category]
        changed = True

    # URL 설정
    link = article.get("link")
    if link and not orm.url:
        orm.url = link
        changed = True

    if changed:
        db.flush()


def print_report(result: MigrationResult) -> None:
    """마이그레이션 결과 리포트를 출력합니다."""
    print("\n" + "=" * 60)
    print("  AllergyNewsLetter → AllergyInsight 논문 마이그레이션 결과")
    print("=" * 60)
    print(f"  총 대상:  {result.total}건")
    print(f"  신규 저장: {result.new}건")
    print(f"  중복 스킵: {result.duplicate}건")
    print(f"  실패:     {result.failed}건")
    print("=" * 60)

    if result.failed > 0:
        print("  ⚠ 실패 건은 위 로그를 확인하세요.")
    if result.new > 0:
        print("  동일 스크립트 재실행 시 신규 0건이 됩니다 (멱등성 보장).")
    print()


def main():
    parser = argparse.ArgumentParser(
        description="AllergyNewsLetter 논문을 AllergyInsight DB로 마이그레이션"
    )
    parser.add_argument(
        "--source",
        default=DEFAULT_SOURCE_DB,
        help=f"AllergyNewsLetter SQLite DB 경로 (기본: {DEFAULT_SOURCE_DB})",
    )
    args = parser.parse_args()

    logger.info(f"마이그레이션 시작: {args.source}")
    result = migrate(args.source)
    print_report(result)


if __name__ == "__main__":
    main()
