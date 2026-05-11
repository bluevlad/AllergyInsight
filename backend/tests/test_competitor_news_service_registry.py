"""Tests for the registry-based CompetitorNewsService refactor.

WBS: P1-E-003
"""
from __future__ import annotations

from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from app.core.sources.base import NormalizedDoc, SourceSearchResult
from app.models.competitor_news import NewsArticle
from app.services.competitor_news_service import (
    CompanyNewsResult,
    CompetitorNewsService,
)


# ───────── 헬퍼 ─────────


def _doc(source: str, source_id: str, **kw) -> NormalizedDoc:
    return NormalizedDoc(
        source=source,
        source_id=source_id,
        title=kw.get("title", "t"),
        abstract=kw.get("description", "d"),
        url=source_id,
        metadata=kw.get("metadata", {}),
    )


def _result(source: str, docs: list[NormalizedDoc]) -> SourceSearchResult:
    return SourceSearchResult(
        docs=docs, source=source, query="q",
        meta={"total_count": len(docs)},
    )


# ───────── CompanyNewsResult ─────────


class TestCompanyNewsResultShape:
    def test_errors_field_default(self):
        r = CompanyNewsResult(
            company_code="x", company_name="X",
            naver_articles=[], google_articles=[],
            total_count=0, search_time_ms=0.0,
        )
        assert r.errors == {}


# ───────── Source 별칭 / 필터링 ─────────


class TestSourceAlias:
    def test_uses_both_news_connectors_by_default(self):
        svc = CompetitorNewsService()
        names = set(svc._connectors.keys())
        assert "naver_news" in names
        assert "google_news_rss" in names

    def test_short_alias_naver(self):
        svc = CompetitorNewsService()
        for c in svc._connectors.values():
            c.is_available = MagicMock(return_value=True)
        selected = svc._resolve_sources(["naver"])
        assert {c.name for c in selected} == {"naver_news"}

    def test_short_alias_google(self):
        svc = CompetitorNewsService()
        for c in svc._connectors.values():
            c.is_available = MagicMock(return_value=True)
        selected = svc._resolve_sources(["google"])
        assert {c.name for c in selected} == {"google_news_rss"}

    def test_full_registry_name_accepted(self):
        svc = CompetitorNewsService()
        for c in svc._connectors.values():
            c.is_available = MagicMock(return_value=True)
        selected = svc._resolve_sources(["naver_news", "google_news_rss"])
        assert {c.name for c in selected} == {"naver_news", "google_news_rss"}

    def test_none_means_all_available(self):
        svc = CompetitorNewsService()
        for c in svc._connectors.values():
            c.is_available = MagicMock(return_value=True)
        selected = svc._resolve_sources(None)
        assert len(selected) == 2

    def test_unavailable_connector_skipped(self):
        svc = CompetitorNewsService()
        svc._connectors["naver_news"].is_available = MagicMock(return_value=False)
        svc._connectors["google_news_rss"].is_available = MagicMock(return_value=True)
        selected = svc._resolve_sources(None)
        assert {c.name for c in selected} == {"google_news_rss"}


# ───────── search_company_news ─────────


def _patch_keywords(svc, keywords):
    """업체 키워드 조회를 mock 으로 강제."""
    svc._get_company_keywords = MagicMock(return_value=keywords)


class TestSearchCompanyNews:
    def test_empty_keywords_returns_empty(self):
        svc = CompetitorNewsService()
        _patch_keywords(svc, [])
        result = svc.search_company_news("nokeyword")
        assert result.naver_articles == []
        assert result.google_articles == []
        assert result.total_count == 0

    def test_keyword_x_source_fanout(self):
        svc = CompetitorNewsService()
        _patch_keywords(svc, ["kw1", "kw2"])
        for c in svc._connectors.values():
            c.is_available = MagicMock(return_value=True)
            c.search = MagicMock(return_value=_result(c.name, []))

        svc.search_company_news("acme", max_results=5)

        # 키워드 2 × source 2 = 4번 호출 분포
        assert svc._connectors["naver_news"].search.call_count == 2
        assert svc._connectors["google_news_rss"].search.call_count == 2

    def test_articles_distributed_by_legacy_alias(self):
        svc = CompetitorNewsService()
        _patch_keywords(svc, ["kw"])
        for c in svc._connectors.values():
            c.is_available = MagicMock(return_value=True)

        svc._connectors["naver_news"].search = MagicMock(return_value=_result(
            "naver_news",
            [_doc("naver_news", "https://n/1", title="N1")],
        ))
        svc._connectors["google_news_rss"].search = MagicMock(return_value=_result(
            "google_news_rss",
            [_doc("google_news_rss", "https://g/1", title="G1")],
        ))

        result = svc.search_company_news("acme")

        assert len(result.naver_articles) == 1
        assert result.naver_articles[0].title == "N1"
        assert result.naver_articles[0].source == "naver"  # legacy alias 복원

        assert len(result.google_articles) == 1
        assert result.google_articles[0].title == "G1"
        assert result.google_articles[0].source == "google"

    def test_url_deduplication_across_sources(self):
        """동일 URL 이 양 source 에서 나오면 1개만 유지."""
        svc = CompetitorNewsService()
        _patch_keywords(svc, ["kw"])
        for c in svc._connectors.values():
            c.is_available = MagicMock(return_value=True)

        dup_url = "https://dup/1"
        svc._connectors["naver_news"].search = MagicMock(return_value=_result(
            "naver_news",
            [_doc("naver_news", dup_url, title="from naver")],
        ))
        svc._connectors["google_news_rss"].search = MagicMock(return_value=_result(
            "google_news_rss",
            [_doc("google_news_rss", dup_url, title="from google")],
        ))

        result = svc.search_company_news("acme")
        total = len(result.naver_articles) + len(result.google_articles)
        assert total == 1

    def test_company_and_keyword_injected(self):
        svc = CompetitorNewsService()
        _patch_keywords(svc, ["kw"])
        for c in svc._connectors.values():
            c.is_available = MagicMock(return_value=True)
            c.search = MagicMock(return_value=_result(
                c.name, [_doc(c.name, f"https://{c.name}/1")],
            ))

        result = svc.search_company_news("acme")
        for article in result.naver_articles + result.google_articles:
            assert article.company == "acme"
            assert article.search_keyword == "kw"

    def test_partial_failure_recorded_in_errors(self):
        svc = CompetitorNewsService()
        _patch_keywords(svc, ["kw"])
        for c in svc._connectors.values():
            c.is_available = MagicMock(return_value=True)

        svc._connectors["naver_news"].search = MagicMock(
            side_effect=RuntimeError("naver 500")
        )
        svc._connectors["google_news_rss"].search = MagicMock(
            return_value=_result("google_news_rss", [])
        )

        result = svc.search_company_news("acme")

        assert any("naver" in k for k in result.errors)
        assert any("naver 500" in v for v in result.errors.values())

    def test_connector_internal_error_captured(self):
        svc = CompetitorNewsService()
        _patch_keywords(svc, ["kw"])
        for c in svc._connectors.values():
            c.is_available = MagicMock(return_value=True)

        # naver 가 부분 실패 (connector 내부 catch)
        svc._connectors["naver_news"].search = MagicMock(
            return_value=SourceSearchResult.empty(
                "naver_news", "kw", error="rate limit",
            )
        )
        svc._connectors["google_news_rss"].search = MagicMock(
            return_value=_result("google_news_rss", [])
        )

        result = svc.search_company_news("acme")
        assert any("naver_news" in k for k in result.errors)


# ───────── close ─────────


class TestClose:
    def test_close_closes_all_connectors(self):
        svc = CompetitorNewsService()
        for c in svc._connectors.values():
            c.close = MagicMock()
        svc.close()
        for c in svc._connectors.values():
            c.close.assert_called_once()
