"""Database Connection"""
import logging
import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker

logger = logging.getLogger(__name__)

# .env 파일 지원 (로컬 개발 환경)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL 환경변수가 설정되지 않았습니다.")

# Connection pooling 설정
_pool_kwargs = {}
if DATABASE_URL.startswith("postgresql"):
    _pool_kwargs = {
        "pool_size": int(os.environ.get("DB_POOL_SIZE", "20")),
        "max_overflow": int(os.environ.get("DB_MAX_OVERFLOW", "40")),
        "pool_pre_ping": True,
        "pool_recycle": 1800,
    }
elif DATABASE_URL.startswith("sqlite"):
    _pool_kwargs = {
        "pool_pre_ping": True,
    }

engine = create_engine(DATABASE_URL, **_pool_kwargs)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


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
    from . import newsletter_models  # 뉴스레터 발송 이력
    from . import subscriber_models  # 구독자 모델
    from ..services.diagnosis_repository import StoredDiagnosisModel, StoredPrescriptionModel  # noqa: F401
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
        # users 테이블 마이그레이션: password_hash 컬럼 추가
        if _table_exists(conn, "users"):
            if not _column_exists(conn, "users", "password_hash"):
                conn.execute(text("ALTER TABLE users ADD COLUMN password_hash VARCHAR(255)"))
                logger.info("Migration: users.password_hash 컬럼 추가")

        # papers 테이블 마이그레이션
        if _table_exists(conn, "papers"):
            for col_name, col_def in papers_new_columns:
                if not _column_exists(conn, "papers", col_name):
                    stmt = f"ALTER TABLE papers ADD COLUMN {col_name} {col_def}"
                    conn.execute(text(stmt))
                    logger.info(f"Migration: papers.{col_name} 컬럼 추가")

            # abstract/abstract_kr 컬럼 VARCHAR→TEXT 변환 (긴 초록 지원)
            for col_name in ("abstract", "abstract_kr"):
                result = conn.execute(text(
                    "SELECT data_type FROM information_schema.columns "
                    "WHERE table_name = 'papers' AND column_name = :col"
                ), {"col": col_name})
                row = result.fetchone()
                if row and row[0] == "character varying":
                    conn.execute(text(f"ALTER TABLE papers ALTER COLUMN {col_name} TYPE TEXT"))
                    logger.info(f"Migration: papers.{col_name} VARCHAR→TEXT 변환")

            # 인덱스 추가 (이미 있으면 무시)
            for idx_name, idx_def in [
                ("idx_papers_source", "CREATE INDEX IF NOT EXISTS idx_papers_source ON papers (source)"),
                ("idx_papers_source_id", "CREATE INDEX IF NOT EXISTS idx_papers_source_id ON papers (source_id)"),
            ]:
                conn.execute(text(idx_def))

    logger.info("Database migration completed")
