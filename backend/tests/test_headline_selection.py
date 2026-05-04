"""헤드라인 선정 서비스 단위 테스트

핵심 검증:
- 1기업 1헤드라인 규칙
- MinHash 제목 유사도 ≥ 0.90 제외
- URL canonical 중복 제외
- importance_score DESC 정렬
- limit 준수
- excluded_ids 반환
"""
from __future__ import annotations

from datetime import datetime, timedelta

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.database.connection import Base
from app.database.competitor_models import CompetitorCompany, CompetitorNews
from app.services.headline_selection_service import select_top_headlines
from app.utils.dedup_helpers import (
    canonical_url,
    canonical_url_hash,
    jaccard_from_minhash,
    title_minhash,
)


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
        code=code,
        name_kr=name_kr,
        name_en=code,
        category="overseas",
        keywords=[],
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
    published_at: datetime | None = None,
) -> CompetitorNews:
    n = CompetitorNews(
        company_id=company.id,
        source="naver",
        title=title,
        url=url,
        importance_score=importance,
        published_at=published_at or datetime.utcnow(),
        is_processed=True,
        is_relevant=True,
        is_duplicate=False,
    )
    session.add(n)
    session.flush()
    return n


# ──────────────────────── dedup_helpers tests ────────────────────────


def test_canonical_url_strips_tracking():
    raw = "https://example.com/news?id=1&utm_source=naver&fbclid=abc"
    assert "utm_source" not in canonical_url(raw)
    assert "fbclid" not in canonical_url(raw)
    assert "id=1" in canonical_url(raw)


def test_canonical_url_trailing_slash():
    assert canonical_url("https://a.com/path/") == canonical_url("https://a.com/path")


def test_minhash_identical_titles():
    sig_a = title_minhash("알러지 치료제 FDA 승인")
    sig_b = title_minhash("알러지 치료제 FDA 승인")
    assert jaccard_from_minhash(sig_a, sig_b) == 1.0


def test_minhash_similar_titles():
    sig_a = title_minhash("노바티스 알러지 치료제 FDA 승인 발표")
    sig_b = title_minhash("노바티스 알러지 치료제 FDA 승인 공식 발표")
    sim = jaccard_from_minhash(sig_a, sig_b)
    assert sim >= 0.7


def test_minhash_different_titles():
    sig_a = title_minhash("노바티스 FDA 승인")
    sig_b = title_minhash("삼성바이오 분기 실적 발표")
    sim = jaccard_from_minhash(sig_a, sig_b)
    assert sim < 0.5


# ──────────────────────── headline selection tests ────────────────────────


def test_select_top_by_importance(session: Session):
    """importance_score 내림차순으로 선정."""
    c = _make_company(session, "nova", "노바티스")
    _make_news(session, c, "저중요도", "https://a.com/1", 0.3)
    _make_news(session, c, "고중요도", "https://a.com/2", 0.9)
    session.commit()

    headlines, _, _ = select_top_headlines(
        session, limit=1, one_per_company=False, days=1, fallback_days=[1]
    )
    assert len(headlines) == 1
    assert headlines[0]["title"] == "고중요도"


def test_one_per_company(session: Session):
    """1기업 1헤드라인 — 같은 기업은 최고 importance 1건만."""
    c = _make_company(session, "gsk", "GSK")
    _make_news(session, c, "GSK 뉴스 1", "https://a.com/1", 0.9)
    _make_news(session, c, "GSK 뉴스 2", "https://a.com/2", 0.8)
    session.commit()

    headlines, _, _ = select_top_headlines(
        session, limit=5, one_per_company=True, days=1, fallback_days=[1]
    )
    assert len(headlines) == 1
    assert headlines[0]["importance_score"] == 0.9


def test_multiple_companies(session: Session):
    """다른 기업은 각각 선정."""
    c1 = _make_company(session, "nova", "노바티스")
    c2 = _make_company(session, "gsk", "GSK")
    _make_news(session, c1, "노바 뉴스", "https://a.com/1", 0.9)
    _make_news(session, c2, "GSK 뉴스", "https://a.com/2", 0.8)
    session.commit()

    headlines, excluded, _ = select_top_headlines(
        session, limit=5, one_per_company=True, days=1, fallback_days=[1]
    )
    assert len(headlines) == 2
    assert len(excluded) == 2
    company_names = {h["company_name"] for h in headlines}
    assert company_names == {"노바티스", "GSK"}


def test_url_dedup(session: Session):
    """URL canonical hash 중복 → 두 번째 기사 스킵."""
    c1 = _make_company(session, "a", "A사")
    c2 = _make_company(session, "b", "B사")
    _make_news(session, c1, "동일 기사", "https://a.com/news?utm_source=x", 0.9)
    _make_news(session, c2, "동일 기사", "https://a.com/news?utm_source=y", 0.8)
    session.commit()

    headlines, _, _ = select_top_headlines(
        session, limit=5, one_per_company=True, days=1, fallback_days=[1]
    )
    assert len(headlines) == 1


def test_excluded_ids_returned(session: Session):
    """선정된 기사의 id 가 excluded_ids 에 포함."""
    c = _make_company(session, "nova", "노바")
    n = _make_news(session, c, "뉴스", "https://a.com/1", 0.9)
    session.commit()

    _, excluded, _ = select_top_headlines(
        session, limit=5, days=1, fallback_days=[1]
    )
    assert n.id in excluded


def test_limit_respected(session: Session):
    """limit 초과 선정 금지."""
    c1 = _make_company(session, "a", "A사")
    c2 = _make_company(session, "b", "B사")
    c3 = _make_company(session, "c", "C사")
    _make_news(session, c1, "뉴스1", "https://a.com/1", 0.9)
    _make_news(session, c2, "뉴스2", "https://a.com/2", 0.8)
    _make_news(session, c3, "뉴스3", "https://a.com/3", 0.7)
    session.commit()

    headlines, _, _ = select_top_headlines(
        session, limit=2, days=1, fallback_days=[1]
    )
    assert len(headlines) == 2


def test_old_articles_excluded(session: Session):
    """days 범위 밖 기사 제외 (fallback 비활성)."""
    c = _make_company(session, "a", "A사")
    _make_news(
        session, c, "오래된 뉴스", "https://a.com/1", 0.9,
        published_at=datetime.utcnow() - timedelta(days=5),
    )
    session.commit()

    headlines, _, _ = select_top_headlines(
        session, limit=5, days=1, fallback_days=[1]
    )
    assert len(headlines) == 0


def test_importance_level_mapping(session: Session):
    """importance_level 매핑: ≥0.7=고, ≥0.4=중, <0.4=저."""
    c = _make_company(session, "a", "A사")
    _make_news(session, c, "고", "https://a.com/1", 0.85)
    session.commit()

    headlines, _, _ = select_top_headlines(
        session, limit=1, one_per_company=False, days=1, fallback_days=[1]
    )
    assert headlines[0]["importance_level"] == "고"


def test_fallback_expands_when_pool_insufficient(session: Session):
    """days=1 풀이 limit 미달 시 fallback_days로 lookback 확장."""
    c1 = _make_company(session, "a", "A사")
    c2 = _make_company(session, "b", "B사")
    c3 = _make_company(session, "c", "C사")
    # 오늘은 1건, 3일 이내 총 2건, 7일 이내 총 3건
    _make_news(session, c1, "오늘 뉴스", "https://a.com/1", 0.9)
    _make_news(
        session, c2, "2일전 뉴스", "https://a.com/2", 0.8,
        published_at=datetime.utcnow() - timedelta(days=2),
    )
    _make_news(
        session, c3, "5일전 뉴스", "https://a.com/3", 0.7,
        published_at=datetime.utcnow() - timedelta(days=5),
    )
    session.commit()

    # limit=3, 1차=days=1(1건) → fallback 3일(2건) → fallback 7일(3건)
    headlines, _, effective = select_top_headlines(
        session, limit=3, days=1, fallback_days=[1, 3, 7]
    )
    assert len(headlines) == 3
    assert effective == 7


def test_fallback_stops_at_first_sufficient_window(session: Session):
    """처음으로 limit 을 충족하는 window 에서 즉시 중단."""
    c1 = _make_company(session, "a", "A사")
    c2 = _make_company(session, "b", "B사")
    # 오늘 2건 (limit=2 충족)
    _make_news(session, c1, "오늘1", "https://a.com/1", 0.9)
    _make_news(session, c2, "오늘2", "https://a.com/2", 0.8)
    # 5일전 1건 (사용 안 됨)
    _make_news(
        session, _make_company(session, "c", "C사"),
        "5일전", "https://a.com/3", 0.7,
        published_at=datetime.utcnow() - timedelta(days=5),
    )
    session.commit()

    headlines, _, effective = select_top_headlines(
        session, limit=2, days=1, fallback_days=[1, 3, 7]
    )
    assert len(headlines) == 2
    assert effective == 1  # days=1 에서 충족 → 확장 안함
    titles = {h["title"] for h in headlines}
    assert titles == {"오늘1", "오늘2"}


def test_exclude_ids_filters_out_sent_articles(session: Session):
    """exclude_ids 로 전달된 기사는 풀에서 원천 제외된다.

    NewsLetterPlatform sent_articles(최근 N일) 을 넘겨 교차일 중복 발송 차단.
    """
    c1 = _make_company(session, "nova", "노바티스")
    c2 = _make_company(session, "gsk", "GSK")
    n1 = _make_news(session, c1, "어제 발송됨", "https://a.com/1", 0.95)
    n2 = _make_news(session, c2, "오늘 신규", "https://a.com/2", 0.85)
    session.commit()

    # exclude 없이: 중요도 상위인 n1 이 선정됨
    headlines, _, _ = select_top_headlines(
        session, limit=1, one_per_company=False, days=1, fallback_days=[1]
    )
    assert [h["id"] for h in headlines] == [n1.id]

    # exclude 하면: n2 가 선정됨
    headlines_ex, _, _ = select_top_headlines(
        session, limit=1, one_per_company=False, days=1,
        fallback_days=[1], exclude_ids={n1.id},
    )
    assert [h["id"] for h in headlines_ex] == [n2.id]


def test_exclude_ids_applied_across_fallback_windows(session: Session):
    """fallback 확장 중에도 exclude_ids 는 계속 적용된다."""
    c1 = _make_company(session, "nova", "노바티스")
    c2 = _make_company(session, "gsk", "GSK")
    # 오늘 1건(제외 대상)
    n_today_excluded = _make_news(session, c1, "오늘 제외", "https://a.com/1", 0.9)
    # 5일전 1건(살아남음)
    n_old = _make_news(
        session, c2, "5일전", "https://a.com/2", 0.7,
        published_at=datetime.utcnow() - timedelta(days=5),
    )
    session.commit()

    headlines, _, effective = select_top_headlines(
        session, limit=1, one_per_company=False, days=1,
        fallback_days=[1, 7], exclude_ids={n_today_excluded.id},
    )
    assert len(headlines) == 1
    assert headlines[0]["id"] == n_old.id
    assert effective == 7  # 1일 풀이 비어 7일로 확장됨
