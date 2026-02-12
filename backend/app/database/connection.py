"""Database Connection"""
import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

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
    Base.metadata.create_all(bind=engine)
