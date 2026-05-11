"""Tests for app.core.sources — ABC, registry, errors.

Covers WBS P1-A-002 ~ A-006 and P1-B-001 ~ B-002.
"""
from __future__ import annotations

import pytest

from app.core.sources import registry
from app.core.sources.base import (
    NormalizedDoc,
    SourceConnector,
    SourceKind,
    SourceSearchResult,
)
from app.core.sources.errors import (
    RateLimitError,
    SourceAuthError,
    SourceError,
    SourceTimeoutError,
    SourceUnavailableError,
)
from app.core.sources.news.base import NewsSourceConnector
from app.core.sources.paper.base import PaperSourceConnector


# ───────────────── NormalizedDoc ─────────────────


class TestNormalizedDoc:
    def test_minimal_fields(self):
        doc = NormalizedDoc(source="pubmed", source_id="123", title="t")
        assert doc.source == "pubmed"
        assert doc.source_id == "123"
        assert doc.title == "t"
        assert doc.authors == ()
        assert doc.keywords == ()
        assert doc.metadata == {}
        assert doc.abstract is None
        assert doc.year is None

    def test_to_paper_dict(self):
        doc = NormalizedDoc(
            source="pubmed",
            source_id="123",
            title="t",
            authors=("A", "B"),
            doi="10.1",
            year=2024,
            keywords=("k1", "k2"),
        )
        d = doc.to_paper_dict()
        assert d["authors"] == ["A", "B"]
        assert d["doi"] == "10.1"
        assert d["year"] == 2024
        assert d["keywords"] == ["k1", "k2"]

    def test_frozen(self):
        doc = NormalizedDoc(source="x", source_id="1", title="t")
        with pytest.raises(Exception):  # FrozenInstanceError
            doc.title = "u"  # type: ignore[misc]

    def test_metadata_independent_per_instance(self):
        """default_factory=dict 가 인스턴스마다 독립 dict 를 만드는지."""
        a = NormalizedDoc(source="x", source_id="1", title="t")
        b = NormalizedDoc(source="x", source_id="2", title="u")
        a.metadata["k"] = 1
        assert b.metadata == {}


# ───────────────── SourceSearchResult ─────────────────


class TestSourceSearchResult:
    def test_count(self):
        r = SourceSearchResult(
            docs=[NormalizedDoc(source="x", source_id="1", title="a")],
            source="x",
            query="q",
        )
        assert r.count == 1
        assert not r.has_error

    def test_empty_no_error(self):
        r = SourceSearchResult.empty("pubmed", "q")
        assert r.count == 0
        assert not r.has_error
        assert r.source == "pubmed"
        assert r.query == "q"

    def test_empty_with_error(self):
        r = SourceSearchResult.empty("pubmed", "q", error="timeout")
        assert r.count == 0
        assert r.has_error
        assert r.meta["error"] == "timeout"

    def test_default_fetched_at_is_utc(self):
        r = SourceSearchResult(docs=[], source="x", query="q")
        assert r.fetched_at.tzinfo is not None


# ───────────────── Registry ─────────────────


@pytest.fixture
def clean_registry():
    """각 테스트마다 registry 격리. 기존 등록은 보존 후 복원."""
    snapshot = dict(registry._REGISTRY)
    registry.clear()
    yield
    registry.clear()
    registry._REGISTRY.update(snapshot)


class _DummyConnector(SourceConnector):
    """ABC 의 abstract method 를 채운 테스트용 더미."""

    def search(self, query, max_results=20, **kwargs):
        return SourceSearchResult(
            docs=[
                NormalizedDoc(source=self.name, source_id="1", title=query)
            ],
            source=self.name,
            query=query,
        )

    def is_available(self):
        return True


class TestRegistry:
    def test_register_sets_name_attribute(self, clean_registry):
        @registry.register("dummy")
        class C(_DummyConnector):
            kind = SourceKind.PAPER

        assert C.name == "dummy"
        instance = registry.get("dummy")
        assert instance.name == "dummy"

    def test_duplicate_name_raises(self, clean_registry):
        @registry.register("dup")
        class A(_DummyConnector):
            pass

        with pytest.raises(ValueError, match="already registered"):

            @registry.register("dup")
            class B(_DummyConnector):
                pass

    def test_unknown_name_raises(self, clean_registry):
        with pytest.raises(KeyError, match="not registered"):
            registry.get("ghost")

    def test_all_of_kind_filters(self, clean_registry):
        @registry.register("p1")
        class P(_DummyConnector):
            kind = SourceKind.PAPER

        @registry.register("n1")
        class N(_DummyConnector):
            kind = SourceKind.NEWS

        papers = registry.all_of_kind(SourceKind.PAPER)
        news = registry.all_of_kind(SourceKind.NEWS)
        assert {c.name for c in papers} == {"p1"}
        assert {c.name for c in news} == {"n1"}

    def test_names_sorted(self, clean_registry):
        for n in ["zeta", "alpha", "mike"]:
            @registry.register(n)
            class _C(_DummyConnector):
                pass

        assert registry.names() == ["alpha", "mike", "zeta"]

    def test_unregister(self, clean_registry):
        @registry.register("temp")
        class T(_DummyConnector):
            pass

        assert "temp" in registry.names()
        registry.unregister("temp")
        assert "temp" not in registry.names()

    def test_unregister_unknown_is_silent(self, clean_registry):
        registry.unregister("ghost")  # no raise


# ───────────────── End-to-end (Echo + 부분 실패) ─────────────────


class TestEchoEndToEnd:
    def test_echo_via_registry(self, clean_registry):
        @registry.register("echo")
        class EchoSource(_DummyConnector):
            kind = SourceKind.PAPER

        c = registry.get("echo")
        result = c.search("hello", max_results=3)
        assert result.source == "echo"
        assert result.count == 1
        assert result.docs[0].title == "hello"
        assert not result.has_error

    def test_error_propagation_via_meta(self, clean_registry):
        @registry.register("erroring")
        class E(_DummyConnector):
            def search(self, query, max_results=20, **kwargs):
                return SourceSearchResult.empty(
                    self.name, query, error="boom"
                )

        result = registry.get("erroring").search("q")
        assert result.has_error
        assert result.meta["error"] == "boom"

    def test_context_manager_close_called(self, clean_registry):
        closed = {"v": False}

        @registry.register("cm")
        class CM(_DummyConnector):
            def close(self):
                closed["v"] = True

        with registry.get("cm") as c:
            assert c.search("q").count == 1
        assert closed["v"] is True


# ───────────────── Paper / News 분기 ─────────────────


class TestPaperSourceConnector:
    def test_kind_is_paper(self, clean_registry):
        @registry.register("paper_test")
        class P(PaperSourceConnector):
            SUPPORTS_PDF_URL = True

            def search(self, query, max_results=20, **kwargs):
                return SourceSearchResult.empty(self.name, query)

            def is_available(self):
                return True

            def get_pdf_url(self, source_id):
                return f"https://example.com/{source_id}.pdf"

        c = registry.get("paper_test")
        assert c.kind == SourceKind.PAPER
        assert c.get_pdf_url("abc") == "https://example.com/abc.pdf"
        assert c.SUPPORTS_PDF_URL is True

    def test_paper_without_get_pdf_cannot_instantiate(self, clean_registry):
        class Broken(PaperSourceConnector):
            def search(self, query, max_results=20, **kwargs):
                return SourceSearchResult.empty(self.name, query)

            def is_available(self):
                return True

            # get_pdf_url 미구현 → TypeError 예상

        with pytest.raises(TypeError):
            Broken()


class TestNewsSourceConnector:
    def test_kind_is_news(self, clean_registry):
        @registry.register("news_test")
        class N(NewsSourceConnector):
            def search(self, query, max_results=20, **kwargs):
                return SourceSearchResult.empty(self.name, query)

            def is_available(self):
                return True

        c = registry.get("news_test")
        assert c.kind == SourceKind.NEWS


# ───────────────── Errors ─────────────────


class TestErrors:
    def test_hierarchy(self):
        assert issubclass(SourceUnavailableError, SourceError)
        assert issubclass(RateLimitError, SourceError)
        assert issubclass(SourceTimeoutError, SourceError)
        assert issubclass(SourceAuthError, SourceError)

    def test_raise_and_catch(self):
        with pytest.raises(SourceError):
            raise RateLimitError("429")
