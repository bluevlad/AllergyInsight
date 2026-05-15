"""Tests for CompetitorNewsService.collect_allergen_news + sentinel handling.

allergen-trend-followup-plan §2.
"""
from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

from app.core.sources.base import NormalizedDoc, SourceSearchResult
from app.database.analytics_models import NewsAllergenLink
from app.database.competitor_models import CompetitorCompany, CompetitorNews
from app.services.competitor_news_service import (
    ALLERGEN_SENTINEL_CODE,
    AllergenNewsResult,
    CompetitorNewsService,
)


def _doc(source: str, url: str, title: str = "t", desc: str = "d") -> NormalizedDoc:
    return NormalizedDoc(
        source=source,
        source_id=url,
        title=title,
        abstract=desc,
        url=url,
        metadata={},
    )


def _result(source: str, docs: list[NormalizedDoc]) -> SourceSearchResult:
    return SourceSearchResult(
        docs=docs, source=source, query="q",
        meta={"total_count": len(docs)},
    )


def _patch_keyword_map(keyword_map: dict[str, list[str]]):
    return patch(
        "app.services.competitor_news_service.build_allergen_search_keywords",
        return_value=keyword_map,
    )


class TestSentinelCreation:
    def test_creates_inactive_sentinel(self, test_db):
        svc = CompetitorNewsService()
        sentinel = svc._ensure_allergen_sentinel(test_db)
        assert sentinel.code == ALLERGEN_SENTINEL_CODE
        assert sentinel.is_active is False

    def test_idempotent(self, test_db):
        svc = CompetitorNewsService()
        a = svc._ensure_allergen_sentinel(test_db)
        b = svc._ensure_allergen_sentinel(test_db)
        assert a.id == b.id
        # 단 1개만 존재
        count = (
            test_db.query(CompetitorCompany)
            .filter(CompetitorCompany.code == ALLERGEN_SENTINEL_CODE)
            .count()
        )
        assert count == 1


class TestSearchAllergenNews:
    def test_empty_keywords_returns_empty(self):
        svc = CompetitorNewsService()
        result = svc.search_allergen_news("peanut", [])
        assert isinstance(result, AllergenNewsResult)
        assert result.articles == []
        assert result.total_count == 0

    def test_attaches_sentinel_company_and_keyword(self):
        svc = CompetitorNewsService()
        for c in svc._connectors.values():
            c.is_available = MagicMock(return_value=True)
            c.search = MagicMock(return_value=_result(
                c.name, [_doc(c.name, f"https://{c.name}/1", title=c.name)],
            ))

        result = svc.search_allergen_news("peanut", ["땅콩 알레르기"])
        assert result.total_count >= 1
        for article in result.articles:
            assert article.company == ALLERGEN_SENTINEL_CODE
            assert article.search_keyword == "땅콩 알레르기"


class TestCollectAllergenNews:
    def test_creates_competitor_news_and_link(self, test_db):
        svc = CompetitorNewsService()
        for c in svc._connectors.values():
            c.is_available = MagicMock(return_value=True)
            c.search = MagicMock(return_value=_result(
                c.name, [_doc(c.name, f"https://{c.name}/1")],
            ))

        with _patch_keyword_map({"peanut": ["땅콩 알레르기"]}):
            result = svc.collect_allergen_news(test_db, max_results_per_allergen=5)

        assert result["total_new"] >= 1
        assert result["total_links"] >= 1

        # 저장된 CompetitorNews 가 sentinel 에 매핑
        sentinel = test_db.query(CompetitorCompany).filter(
            CompetitorCompany.code == ALLERGEN_SENTINEL_CODE
        ).first()
        assert sentinel is not None

        news_rows = test_db.query(CompetitorNews).filter(
            CompetitorNews.company_id == sentinel.id
        ).all()
        assert len(news_rows) >= 1

        # NewsAllergenLink 가 deterministic 으로 peanut 으로 생성
        links = test_db.query(NewsAllergenLink).filter(
            NewsAllergenLink.allergen_code == "peanut"
        ).all()
        assert len(links) >= 1
        # 검색 시점에 결정된 link 라 content_category 는 None
        assert all(l.content_category is None for l in links)

    def test_duplicate_url_creates_link_only(self, test_db):
        """기존 CompetitorNews(url) 가 있으면 새 행 만들지 않고 link 만 추가."""
        # 사전에 동일 URL 의 뉴스를 한 회사 밑에 미리 생성
        company = CompetitorCompany(
            code="acme",
            name_kr="아크미",
            name_en="Acme",
            category="industry",
            keywords=["acme"],
            is_active=True,
        )
        test_db.add(company)
        test_db.commit()

        existing_news = CompetitorNews(
            company_id=company.id,
            source="naver",
            title="기존",
            description="",
            url="https://dup/1",
            published_at=datetime.now(timezone.utc),
            search_keyword="acme",
        )
        test_db.add(existing_news)
        test_db.commit()
        existing_id = existing_news.id

        svc = CompetitorNewsService()
        for c in svc._connectors.values():
            c.is_available = MagicMock(return_value=True)
            c.search = MagicMock(return_value=_result(
                c.name, [_doc(c.name, "https://dup/1")],
            ))

        with _patch_keyword_map({"milk": ["우유 알레르기"]}):
            result = svc.collect_allergen_news(test_db, max_results_per_allergen=5)

        # 새 CompetitorNews 는 추가되지 않음
        assert result["total_new"] == 0
        assert result["total_duplicate"] >= 1
        # link 는 기존 뉴스에 milk 로 연결
        links = test_db.query(NewsAllergenLink).filter(
            NewsAllergenLink.news_id == existing_id,
            NewsAllergenLink.allergen_code == "milk",
        ).all()
        assert len(links) == 1

    def test_link_uniqueness_per_allergen(self, test_db):
        """같은 뉴스에 동일 allergen_code 2번 호출해도 link 는 1개."""
        svc = CompetitorNewsService()
        for c in svc._connectors.values():
            c.is_available = MagicMock(return_value=True)
            c.search = MagicMock(return_value=_result(
                c.name, [_doc(c.name, "https://same/1")],
            ))

        with _patch_keyword_map({"peanut": ["땅콩 알레르기"]}):
            svc.collect_allergen_news(test_db, max_results_per_allergen=5)
            # 두번째 호출에선 새 link 가 더 추가되지 않아야 함
            second = svc.collect_allergen_news(test_db, max_results_per_allergen=5)

        assert second["total_links"] == 0

    def test_empty_keyword_map_skips(self, test_db):
        svc = CompetitorNewsService()
        with _patch_keyword_map({}):
            result = svc.collect_allergen_news(test_db)
        assert result == {
            "total_new": 0,
            "total_duplicate": 0,
            "total_links": 0,
            "allergen_stats": {},
        }
