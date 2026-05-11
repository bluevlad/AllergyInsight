"""Tests for news connectors (Naver, Google News RSS) + base helpers.

WBS: P1-E-001, P1-E-002
"""
from __future__ import annotations

from datetime import date, datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

from app.core.sources import registry
from app.core.sources.base import NormalizedDoc, SourceKind, SourceSearchResult
from app.core.sources.news.base import (
    NewsSourceConnector,
    news_article_to_normalized,
    normalized_to_news_article,
)
from app.core.sources.news.google_news_rss import GoogleNewsRssConnector
from app.core.sources.news.naver_news import NaverNewsConnector
from app.models.competitor_news import NewsArticle, NewsSearchResult


# ───────── 변환 헬퍼 ─────────


class TestNewsArticleConversion:
    def test_article_to_normalized_basic(self):
        a = NewsArticle(
            title="t",
            url="https://news.example/1",
            source="naver",
            company="acme",
            description="desc",
            published_at=datetime(2026, 5, 11, 9, 0, tzinfo=timezone.utc),
            search_keyword="alpha",
        )
        d = news_article_to_normalized(a)
        assert d.source == "naver"
        assert d.source_id == "https://news.example/1"
        assert d.title == "t"
        assert d.abstract == "desc"
        assert d.published_at == date(2026, 5, 11)
        assert d.metadata["company"] == "acme"
        assert d.metadata["search_keyword"] == "alpha"
        assert "2026-05-11" in d.metadata["published_datetime"]

    def test_article_to_normalized_with_source_override(self):
        a = NewsArticle(title="t", url="u", source="naver", company="",
                        description="", search_keyword="")
        d = news_article_to_normalized(a, source_name="naver_news")
        assert d.source == "naver_news"

    def test_round_trip(self):
        original = NewsArticle(
            title="round trip",
            url="https://x/1",
            source="naver_news",
            company="acme",
            description="abc",
            published_at=datetime(2026, 1, 2, 3, 4, 5),
            search_keyword="kw",
        )
        doc = news_article_to_normalized(original)
        recovered = normalized_to_news_article(doc)
        assert recovered.title == "round trip"
        assert recovered.url == "https://x/1"
        assert recovered.source == "naver_news"
        assert recovered.company == "acme"
        assert recovered.description == "abc"
        assert recovered.search_keyword == "kw"
        assert recovered.published_at == datetime(2026, 1, 2, 3, 4, 5)

    def test_no_published_at(self):
        a = NewsArticle(title="t", url="u", source="naver", company="",
                        description="", search_keyword="")
        d = news_article_to_normalized(a)
        assert d.published_at is None
        assert "published_datetime" not in d.metadata

    def test_no_optional_fields_in_metadata_when_empty(self):
        a = NewsArticle(title="t", url="u", source="naver", company="",
                        description="", search_keyword="")
        d = news_article_to_normalized(a)
        assert "company" not in d.metadata
        assert "search_keyword" not in d.metadata


# ───────── Naver News Connector ─────────


def _naver_legacy(articles: list[NewsArticle]) -> NewsSearchResult:
    return NewsSearchResult(
        articles=articles, total_count=len(articles),
        source="naver", search_time_ms=1.0,
    )


class TestNaverNewsConnector:
    def test_registered_name(self):
        c = registry.get("naver_news")
        assert isinstance(c, NaverNewsConnector)
        assert c.kind == SourceKind.NEWS

    def test_is_available_requires_both_keys(self, monkeypatch):
        monkeypatch.delenv("NAVER_CLIENT_ID", raising=False)
        monkeypatch.delenv("NAVER_CLIENT_SECRET", raising=False)
        assert NaverNewsConnector().is_available() is False

        monkeypatch.setenv("NAVER_CLIENT_ID", "id")
        monkeypatch.setenv("NAVER_CLIENT_SECRET", "sec")
        assert NaverNewsConnector().is_available() is True

    def test_is_available_false_with_only_id(self, monkeypatch):
        monkeypatch.setenv("NAVER_CLIENT_ID", "id")
        monkeypatch.delenv("NAVER_CLIENT_SECRET", raising=False)
        assert NaverNewsConnector().is_available() is False

    def test_search_returns_normalized(self):
        c = NaverNewsConnector()
        legacy = _naver_legacy([
            NewsArticle(title="t1", url="https://n/1", source="naver",
                        company="", description="d1", search_keyword="q"),
            NewsArticle(title="t2", url="https://n/2", source="naver",
                        company="", description="d2", search_keyword="q"),
        ])
        with patch.object(c._service, "search", return_value=legacy):
            r = c.search("q", max_results=5)

        assert r.source == "naver_news"
        assert r.count == 2
        assert r.docs[0].source == "naver_news"  # override 적용
        assert r.docs[0].source_id == "https://n/1"
        assert r.meta["total_count"] == 2

    def test_search_passes_kwargs(self):
        c = NaverNewsConnector()
        with patch.object(c._service, "search", return_value=_naver_legacy([])) as m:
            c.search("q", max_results=50, sort="sim", start=20)
        m.assert_called_once_with("q", display=50, start=20, sort="sim")

    def test_default_sort_is_date(self):
        c = NaverNewsConnector()
        with patch.object(c._service, "search", return_value=_naver_legacy([])) as m:
            c.search("q")
        kwargs = m.call_args.kwargs
        assert kwargs["sort"] == "date"
        assert kwargs["start"] == 1

    def test_error_handling(self):
        c = NaverNewsConnector()
        with patch.object(c._service, "search", side_effect=RuntimeError("500")):
            r = c.search("q")
        assert r.has_error
        assert "500" in r.meta["error"]

    def test_supports_since_flag(self):
        assert NaverNewsConnector.SUPPORTS_SINCE is False


# ───────── Google News RSS Connector ─────────


def _google_legacy(articles: list[NewsArticle]) -> NewsSearchResult:
    return NewsSearchResult(
        articles=articles, total_count=len(articles),
        source="google", search_time_ms=2.0,
    )


class TestGoogleNewsRssConnector:
    def test_registered_name(self):
        c = registry.get("google_news_rss")
        assert isinstance(c, GoogleNewsRssConnector)

    def test_is_available_always_true(self):
        assert GoogleNewsRssConnector().is_available() is True

    def test_supports_since_flag(self):
        assert GoogleNewsRssConnector.SUPPORTS_SINCE is True

    def test_search_default_kwargs(self):
        c = GoogleNewsRssConnector()
        with patch.object(c._service, "search", return_value=_google_legacy([])) as m:
            c.search("q", max_results=10)
        m.assert_called_once_with(
            "q", lang="ko", country="KR", when="7d", max_results=10
        )

    def test_search_custom_kwargs(self):
        c = GoogleNewsRssConnector()
        with patch.object(c._service, "search", return_value=_google_legacy([])) as m:
            c.search("q", lang="en", country="US", when="1d")
        kwargs = m.call_args.kwargs
        assert kwargs["lang"] == "en"
        assert kwargs["country"] == "US"
        assert kwargs["when"] == "1d"

    def test_search_returns_normalized(self):
        c = GoogleNewsRssConnector()
        legacy = _google_legacy([
            NewsArticle(title="t1", url="https://g/1", source="google",
                        company="", description="d1", search_keyword="q"),
        ])
        with patch.object(c._service, "search", return_value=legacy):
            r = c.search("q")
        assert r.source == "google_news_rss"
        assert r.docs[0].source == "google_news_rss"
        assert r.meta["since_filtered"] is False

    def test_since_filter_excludes_old_articles(self):
        c = GoogleNewsRssConnector()
        legacy = _google_legacy([
            NewsArticle(
                title="recent",
                url="https://g/recent",
                source="google",
                company="",
                description="",
                published_at=datetime(2026, 5, 10),
                search_keyword="",
            ),
            NewsArticle(
                title="old",
                url="https://g/old",
                source="google",
                company="",
                description="",
                published_at=datetime(2025, 1, 1),
                search_keyword="",
            ),
        ])
        with patch.object(c._service, "search", return_value=legacy):
            r = c.search("q", since=datetime(2026, 1, 1))
        assert r.count == 1
        assert r.docs[0].title == "recent"
        assert r.meta["since_filtered"] is True
        assert r.meta["raw_count"] == 2

    def test_since_filter_keeps_articles_with_unknown_date(self):
        """발행일 미상 기사는 보수적으로 포함 (false positive 허용)."""
        c = GoogleNewsRssConnector()
        legacy = _google_legacy([
            NewsArticle(
                title="unknown date",
                url="https://g/u",
                source="google",
                company="",
                description="",
                published_at=None,
                search_keyword="",
            ),
        ])
        with patch.object(c._service, "search", return_value=legacy):
            r = c.search("q", since=datetime(2026, 1, 1))
        assert r.count == 1

    def test_no_since_kwarg_no_filtering(self):
        c = GoogleNewsRssConnector()
        legacy = _google_legacy([
            NewsArticle(
                title="old",
                url="https://g/old",
                source="google",
                company="",
                description="",
                published_at=datetime(2020, 1, 1),
                search_keyword="",
            ),
        ])
        with patch.object(c._service, "search", return_value=legacy):
            r = c.search("q")
        assert r.count == 1  # since 없으면 필터 안 함
        assert r.meta["since_filtered"] is False

    def test_error_handling(self):
        c = GoogleNewsRssConnector()
        with patch.object(c._service, "search", side_effect=RuntimeError("rss err")):
            r = c.search("q")
        assert r.has_error


# ───────── 등록 smoke ─────────


class TestAllNewsConnectorsRegistered:
    def test_both_news_connectors_in_registry(self):
        names = registry.names()
        assert "naver_news" in names
        assert "google_news_rss" in names

    def test_news_kind(self):
        for n in ["naver_news", "google_news_rss"]:
            assert registry.get(n).kind == SourceKind.NEWS

    def test_all_of_kind_returns_two_news(self):
        news_conns = registry.all_of_kind(SourceKind.NEWS)
        names = {c.name for c in news_conns}
        assert "naver_news" in names
        assert "google_news_rss" in names
