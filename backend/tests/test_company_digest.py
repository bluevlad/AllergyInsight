"""기업 동향 집계 서비스 단위 테스트

핵심 검증:
- exclude_ids 로 헤드라인 선정분 disjoint
- 기업별 기사 수 집계
- 대표 기사 = importance_score 최고
- 카테고리 수집
- days 범위 필터
"""
from __future__ import annotations

from datetime import datetime, timedelta

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.database.connection import Base
from app.database.competitor_models import CompetitorCompany, CompetitorNews
from app.services.company_digest_service import build_company_digest


@pytest.fixture
def session():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    _Session = sessionmaker(bind=engine)
    sess = _Session()
    yield sess
    sess.close()


def _make_company(session: Session, code: str, name_kr: str) -> CompetitorCompany:
    c = CompetitorCompany(
        code=code, name_kr=name_kr, name_en=code,
        category="overseas", keywords=[],
    )
    session.add(c)
    session.flush()
    return c


def _make_news(
    session: Session,
    company: CompetitorCompany,
    title: str,
    url: str,
    importance: float,
    category: str = "general",
    published_at: datetime | None = None,
) -> CompetitorNews:
    n = CompetitorNews(
        company_id=company.id,
        source="naver",
        title=title,
        url=url,
        importance_score=importance,
        category=category,
        published_at=published_at or datetime.utcnow(),
        is_processed=True,
        is_relevant=True,
        is_duplicate=False,
    )
    session.add(n)
    session.flush()
    return n


def test_basic_digest(session: Session):
    """기업별 기사 수 + 대표 기사."""
    c = _make_company(session, "gsk", "GSK")
    _make_news(session, c, "GSK 뉴스 1", "https://a.com/1", 0.5, "regulatory")
    _make_news(session, c, "GSK 뉴스 2", "https://a.com/2", 0.9, "product")
    session.commit()

    digest = build_company_digest(session, days=7)
    assert len(digest) == 1
    assert digest[0]["company_name"] == "GSK"
    assert digest[0]["count_7d"] == 2
    assert digest[0]["representative"]["title"] == "GSK 뉴스 2"  # 최고 importance
    assert "regulatory" in digest[0]["categories"]
    assert "product" in digest[0]["categories"]


def test_exclude_ids_disjoint(session: Session):
    """exclude_ids 로 헤드라인 선정분 제외."""
    c = _make_company(session, "gsk", "GSK")
    n1 = _make_news(session, c, "헤드라인 기사", "https://a.com/1", 0.9)
    n2 = _make_news(session, c, "일반 기사", "https://a.com/2", 0.5)
    session.commit()

    digest = build_company_digest(session, days=7, exclude_ids={n1.id})
    assert len(digest) == 1
    assert digest[0]["count_7d"] == 1
    assert digest[0]["representative"]["title"] == "일반 기사"


def test_exclude_all_removes_company(session: Session):
    """기업의 모든 기사가 exclude 되면 해당 기업 미노출."""
    c = _make_company(session, "gsk", "GSK")
    n1 = _make_news(session, c, "기사1", "https://a.com/1", 0.9)
    session.commit()

    digest = build_company_digest(session, days=7, exclude_ids={n1.id})
    assert len(digest) == 0


def test_multiple_companies_sorted_by_count(session: Session):
    """기사 수가 많은 기업 우선."""
    c1 = _make_company(session, "a", "A사")
    c2 = _make_company(session, "b", "B사")
    _make_news(session, c1, "A1", "https://a.com/1", 0.5)
    _make_news(session, c2, "B1", "https://b.com/1", 0.5)
    _make_news(session, c2, "B2", "https://b.com/2", 0.6)
    _make_news(session, c2, "B3", "https://b.com/3", 0.7)
    session.commit()

    digest = build_company_digest(session, days=7)
    assert len(digest) == 2
    assert digest[0]["company_name"] == "B사"
    assert digest[0]["count_7d"] == 3
    assert digest[1]["company_name"] == "A사"


def test_days_filter(session: Session):
    """days 범위 밖 기사 미포함."""
    c = _make_company(session, "a", "A사")
    _make_news(
        session, c, "오래된 기사", "https://a.com/1", 0.9,
        published_at=datetime.utcnow() - timedelta(days=10),
    )
    _make_news(session, c, "최근 기사", "https://a.com/2", 0.5)
    session.commit()

    digest = build_company_digest(session, days=7)
    assert len(digest) == 1
    assert digest[0]["count_7d"] == 1
    assert digest[0]["representative"]["title"] == "최근 기사"


def test_avg_importance(session: Session):
    """중요도 평균 계산."""
    c = _make_company(session, "a", "A사")
    _make_news(session, c, "A1", "https://a.com/1", 0.4)
    _make_news(session, c, "A2", "https://a.com/2", 0.8)
    session.commit()

    digest = build_company_digest(session, days=7)
    assert digest[0]["avg_importance"] == 0.6


def test_max_companies_limit(session: Session):
    """max_companies 제한."""
    for i in range(5):
        c = _make_company(session, f"c{i}", f"회사{i}")
        _make_news(session, c, f"뉴스{i}", f"https://a.com/{i}", 0.5)
    session.commit()

    digest = build_company_digest(session, days=7, max_companies=3)
    assert len(digest) == 3
