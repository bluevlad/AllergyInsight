"""Database Connection"""
import logging
import os
from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:allergyinsight2024@localhost:5432/allergyinsight"
)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database tables"""
    from . import models  # Import models to register them
    from . import competitor_models  # 경쟁사 뉴스 모델
    from . import analytics_models  # 예측 분석 모델
    from . import clinical_models  # 임상 문서 모델
    from . import organization_models  # 조직 모델
    Base.metadata.create_all(bind=engine)
    run_migrations()


def _column_exists(conn, table_name: str, column_name: str) -> bool:
    """information_schema로 컬럼 존재 여부 확인"""
    result = conn.execute(
        text(
            "SELECT 1 FROM information_schema.columns "
            "WHERE table_name = :table AND column_name = :col"
        ),
        {"table": table_name, "col": column_name},
    )
    return result.fetchone() is not None


def _table_exists(conn, table_name: str) -> bool:
    """information_schema로 테이블 존재 여부 확인"""
    result = conn.execute(
        text(
            "SELECT 1 FROM information_schema.tables "
            "WHERE table_name = :table"
        ),
        {"table": table_name},
    )
    return result.fetchone() is not None


def run_migrations():
    """기존 테이블에 새 컬럼을 추가하는 멱등성 마이그레이션

    create_all()은 이미 존재하는 테이블에 컬럼을 추가하지 않으므로
    ALTER TABLE로 직접 추가합니다.
    """
    # papers 테이블에 추가할 컬럼 목록: (column_name, column_def)
    papers_new_columns = [
        ("source", "VARCHAR(30)"),
        ("source_id", "VARCHAR(100)"),
        ("semantic_scholar_id", "VARCHAR(100)"),
        ("citation_count", "INTEGER"),
        ("keywords", "JSONB"),
        ("last_synced_at", "TIMESTAMP"),
    ]

    with engine.begin() as conn:
        # papers 테이블 마이그레이션
        if _table_exists(conn, "papers"):
            for col_name, col_def in papers_new_columns:
                if not _column_exists(conn, "papers", col_name):
                    stmt = f"ALTER TABLE papers ADD COLUMN {col_name} {col_def}"
                    conn.execute(text(stmt))
                    logger.info(f"Migration: papers.{col_name} 컬럼 추가")

            # 인덱스 추가 (이미 있으면 무시)
            for idx_name, idx_def in [
                ("idx_papers_source", "CREATE INDEX IF NOT EXISTS idx_papers_source ON papers (source)"),
                ("idx_papers_source_id", "CREATE INDEX IF NOT EXISTS idx_papers_source_id ON papers (source_id)"),
            ]:
                conn.execute(text(idx_def))

    logger.info("Database migration completed")
