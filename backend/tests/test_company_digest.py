"""기업 동향 집계 서비스 단위 테스트

핵심 검증:
- exclude_ids 로 헤드라인 선정분 disjoint
- 기업별 기사 수 집계
- 대표 기사 = importance_score 최고
- 카테고리 수집
- days 범위 필터
- (B1) exclude_companies / category_mix / since_date / event_class
"""
from __future__ import annotations

from datetime import date, datetime, timedelta

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


# ────────────────────────────────────────────────────────────────────
# B1: exclude_companies / category_mix / since_date / event_class
# ────────────────────────────────────────────────────────────────────


def test_exclude_companies_filters_by_name_kr(session: Session):
    """exclude_companies (name_kr 매칭) 로 풀 단계 차단."""
    a = _make_company(session, "a", "A사")
    b = _make_company(session, "b", "B사")
    _make_news(session, a, "A뉴스", "https://a.com/1", 0.7)
    _make_news(session, b, "B뉴스", "https://b.com/1", 0.5)
    session.commit()

    digest = build_company_digest(
        session, days=7, exclude_companies={"A사"}
    )
    names = [c["company_name"] for c in digest]
    assert "A사" not in names
    assert "B사" in names


def test_exclude_companies_strip_whitespace(session: Session):
    """exclude_companies 는 strip 후 매칭 (공백 토큰 무시)."""
    a = _make_company(session, "a", "A사")
    _make_news(session, a, "A뉴스", "https://a.com/1", 0.5)
    session.commit()

    # 빈/공백 토큰은 무시되어야 함 (정상 회사 차단되지 않음)
    digest = build_company_digest(
        session, days=7, exclude_companies={"", "  ", "  A사  "}.union({"A사"})
    )
    # "A사" 가 명시되어 있어 차단됨
    assert digest == []


def test_category_mix_caps_per_event_class(session: Session):
    """category_mix=True 면 같은 event_class 가 max_per_category 한도."""
    cats = ["regulatory"] * 4 + ["product"] * 2
    for i, cat in enumerate(cats):
        c = _make_company(session, f"c{i}", f"회사{i}")
        _make_news(session, c, f"뉴스{i}", f"https://a.com/{i}", 0.5, category=cat)
    session.commit()

    # 다양성 OFF (기본): regulatory 4 + product 2 = 6 모두 노출
    digest_off = build_company_digest(session, days=7)
    assert len(digest_off) == 6

    # 다양성 ON, max_per_category=2: regulatory 2 + product 2 = 4
    digest_on = build_company_digest(
        session, days=7, category_mix=True, max_per_category=2
    )
    classes = [c["event_class"] for c in digest_on]
    assert classes.count("regulatory") == 2
    assert classes.count("product") == 2
    assert len(digest_on) == 4


def test_since_date_filters_pool_and_marks_is_new_company(session: Session):
    """since_date: 풀 필터 + is_new_company 플래그.

    A사: since_date 이전에 처리완료 기사 1건 (= 신규 아님)
    B사: since_date 이후에만 처리완료 기사 (= 신규)
    """
    a = _make_company(session, "a", "A사")
    b = _make_company(session, "b", "B사")
    boundary = datetime.utcnow() - timedelta(days=3)
    pre = boundary - timedelta(days=5)
    post_a = boundary + timedelta(days=1)
    post_b = boundary + timedelta(days=2)

    _make_news(session, a, "A예전", "https://a.com/0", 0.5, published_at=pre)
    _make_news(session, a, "A최근", "https://a.com/1", 0.6, published_at=post_a)
    _make_news(session, b, "B최근", "https://b.com/1", 0.7, published_at=post_b)
    session.commit()

    digest = build_company_digest(session, since_date=boundary.date())
    by_name = {c["company_name"]: c for c in digest}
    # 풀에는 since_date 이후 기사만 → A사 1건 / B사 1건
    assert by_name["A사"]["count_7d"] == 1
    assert by_name["B사"]["count_7d"] == 1
    # since_date 이전 기록 유무로 신규 판정
    assert by_name["A사"]["is_new_company"] is False
    assert by_name["B사"]["is_new_company"] is True


def test_event_class_falls_back_chain(session: Session):
    """대표 기사 category → categories[0] → 'general' 폴백."""
    a = _make_company(session, "a", "A사")
    # category=None (DB 기본은 'general' 이지만 명시적 None 케이스 검증)
    n = _make_news(session, a, "A뉴스", "https://a.com/1", 0.5, category="general")
    n.category = None
    session.flush()
    session.commit()

    digest = build_company_digest(session, days=7)
    # rep.category=None, bucket categories empty (None 은 categories set 에 안 담김)
    assert digest[0]["event_class"] == "general"

    # 두 기사가 다른 category — 대표 = importance 높은 쪽
    b = _make_company(session, "b", "B사")
    _make_news(session, b, "낮음", "https://b.com/1", 0.4, category="financial")
    _make_news(session, b, "높음", "https://b.com/2", 0.9, category="product")
    session.commit()
    digest2 = build_company_digest(session, days=7)
    by_name = {c["company_name"]: c for c in digest2}
    assert by_name["B사"]["event_class"] == "product"


def test_is_new_company_only_when_since_date_provided(session: Session):
    """since_date 미제공 시 is_new_company 는 항상 False."""
    a = _make_company(session, "a", "A사")
    _make_news(session, a, "A뉴스", "https://a.com/1", 0.5)
    session.commit()

    digest = build_company_digest(session, days=7)
    assert digest[0]["is_new_company"] is False


def test_representative_includes_id_and_category(session: Session):
    """대표 기사 dict 에 id, category 포함 (B1 응답 확장)."""
    a = _make_company(session, "a", "A사")
    n = _make_news(session, a, "A뉴스", "https://a.com/1", 0.5, category="regulatory")
    session.commit()
    digest = build_company_digest(session, days=7)
    rep = digest[0]["representative"]
    assert rep["id"] == n.id
    assert rep["category"] == "regulatory"
