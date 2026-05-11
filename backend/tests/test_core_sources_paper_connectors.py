"""Tests for 5 paper connectors: CORE, Semantic Scholar, Europe PMC,
OpenAlex, bioRxiv.

WBS: P1-C-003 ~ P1-C-007
"""
from __future__ import annotations

from datetime import date
from unittest.mock import MagicMock, patch

import pytest

from app.core.sources import registry
from app.core.sources.base import SourceKind, SourceSearchResult
from app.core.sources.paper.biorxiv import BiorxivConnector
from app.core.sources.paper.core import CoreConnector
from app.core.sources.paper.europe_pmc import EuropePMCConnector
from app.core.sources.paper.openalex import OpenAlexConnector
from app.core.sources.paper.semantic_scholar import SemanticScholarConnector
from app.models.paper import Paper, PaperSearchResult, PaperSource


# ───────── helper ─────────


def _make_paper(source: PaperSource, source_id: str, **overrides) -> Paper:
    base = dict(
        title="t",
        abstract="a",
        authors=["A", "B"],
        source=source,
        source_id=source_id,
        doi="10.1/x",
        year=2024,
        published_at=date(2024, 1, 1),
        journal="J",
        citation_count=10,
        pdf_url=None,
        keywords=["k1"],
    )
    base.update(overrides)
    return Paper(**base)


def _legacy_result(source: PaperSource, papers: list[Paper], **kw) -> PaperSearchResult:
    return PaperSearchResult(
        papers=papers,
        total_count=kw.get("total_count", len(papers)),
        query=kw.get("query", "q"),
        source=source,
        search_time_ms=kw.get("search_time_ms", 1.0),
    )


# ───────── 전체 등록 smoke ─────────


class TestAllConnectorsRegistered:
    def test_six_paper_connectors_in_registry(self):
        names = registry.names()
        for n in ["pubmed", "semantic_scholar", "europe_pmc", "openalex", "biorxiv", "core"]:
            assert n in names, f"{n} not registered"

    def test_all_papers_are_paper_kind(self):
        for n in ["pubmed", "semantic_scholar", "europe_pmc", "openalex", "biorxiv", "core"]:
            assert registry.get(n).kind == SourceKind.PAPER


# ═══════════════════ CoreConnector (P1-C-003) ═══════════════════


class TestCoreConnector:
    def test_registered_name(self):
        c = registry.get("core")
        assert isinstance(c, CoreConnector)
        assert c.kind == SourceKind.PAPER

    def test_is_available_when_no_key(self, monkeypatch):
        monkeypatch.delenv("CORE_API_KEY", raising=False)
        c = CoreConnector()
        assert c.is_available() is False

    def test_is_available_when_key_set(self, monkeypatch):
        monkeypatch.setenv("CORE_API_KEY", "secret")
        c = CoreConnector()
        assert c.is_available() is True

    def test_search_converts_papers(self):
        c = CoreConnector()
        legacy = _legacy_result(
            PaperSource.CORE,
            [_make_paper(PaperSource.CORE, "core:111", pdf_url="https://x/p.pdf")],
        )
        with patch.object(c._service, "search", return_value=legacy):
            r = c.search("q")

        assert r.count == 1
        assert r.source == "core"
        assert r.docs[0].source == "core"
        assert r.docs[0].source_id == "core:111"
        assert r.docs[0].pdf_url == "https://x/p.pdf"

    def test_get_pdf_url_returns_none(self):
        assert CoreConnector().get_pdf_url("core:1") is None

    def test_error_handling(self):
        c = CoreConnector()
        with patch.object(c._service, "search", side_effect=RuntimeError("api 500")):
            r = c.search("q")
        assert r.has_error
        assert "api 500" in r.meta["error"]

    def test_close_delegates(self):
        c = CoreConnector()
        c._service.close = MagicMock()
        c.close()
        c._service.close.assert_called_once()


# ═══════════════════ SemanticScholarConnector (P1-C-004) ═══════════════════


class TestSemanticScholarConnector:
    def test_registered_name(self):
        c = registry.get("semantic_scholar")
        assert isinstance(c, SemanticScholarConnector)

    def test_capability_flags(self):
        c = SemanticScholarConnector()
        assert c.SUPPORTS_YEAR_RANGE is True
        assert c.SUPPORTS_OPEN_ACCESS_FILTER is True
        assert c.SUPPORTS_PDF_URL is True

    def test_is_available_always_true(self):
        assert SemanticScholarConnector().is_available() is True

    def test_search_passes_all_kwargs(self):
        c = SemanticScholarConnector()
        legacy = _legacy_result(PaperSource.SEMANTIC_SCHOLAR, [])
        with patch.object(c._service, "search", return_value=legacy) as m:
            c.search(
                "atopy",
                max_results=5,
                year_range=(2020, 2024),
                open_access_only=True,
                fields_of_study=["Medicine"],
            )
        m.assert_called_once_with(
            "atopy",
            max_results=5,
            year_range=(2020, 2024),
            open_access_only=True,
            fields_of_study=["Medicine"],
        )

    def test_search_defaults(self):
        c = SemanticScholarConnector()
        legacy = _legacy_result(PaperSource.SEMANTIC_SCHOLAR, [])
        with patch.object(c._service, "search", return_value=legacy) as m:
            c.search("q")
        kwargs = m.call_args.kwargs
        assert kwargs["year_range"] is None
        assert kwargs["open_access_only"] is False
        assert kwargs["fields_of_study"] is None

    def test_get_pdf_url_via_paper_id(self):
        c = SemanticScholarConnector()
        paper = _make_paper(PaperSource.SEMANTIC_SCHOLAR, "S2:abc", pdf_url="https://s2/p.pdf")
        with patch.object(c._service, "get_paper_by_id", return_value=paper):
            assert c.get_pdf_url("S2:abc") == "https://s2/p.pdf"

    def test_get_pdf_url_returns_none_when_not_found(self):
        c = SemanticScholarConnector()
        with patch.object(c._service, "get_paper_by_id", return_value=None):
            assert c.get_pdf_url("S2:missing") is None

    def test_get_pdf_url_by_pmid(self):
        c = SemanticScholarConnector()
        paper = _make_paper(PaperSource.SEMANTIC_SCHOLAR, "S2:x", pdf_url="https://s2/p.pdf")
        with patch.object(c._service, "get_paper_by_pmid", return_value=paper):
            assert c.get_pdf_url_by_pmid("12345") == "https://s2/p.pdf"

    def test_get_pdf_url_by_doi(self):
        c = SemanticScholarConnector()
        paper = _make_paper(PaperSource.SEMANTIC_SCHOLAR, "S2:y", pdf_url="https://s2/p.pdf")
        with patch.object(c._service, "get_paper_by_doi", return_value=paper):
            assert c.get_pdf_url_by_doi("10.1/x") == "https://s2/p.pdf"

    def test_get_pdf_url_swallows_exceptions(self):
        c = SemanticScholarConnector()
        with patch.object(c._service, "get_paper_by_id", side_effect=RuntimeError):
            assert c.get_pdf_url("id") is None
        with patch.object(c._service, "get_paper_by_pmid", side_effect=RuntimeError):
            assert c.get_pdf_url_by_pmid("p") is None

    def test_api_key_from_env(self, monkeypatch):
        monkeypatch.setenv("SEMANTIC_SCHOLAR_API_KEY", "s2_key")
        c = SemanticScholarConnector()
        assert c._service.api_key == "s2_key"

    def test_error_handling(self):
        c = SemanticScholarConnector()
        with patch.object(c._service, "search", side_effect=RuntimeError("429")):
            r = c.search("q")
        assert r.has_error


# ═══════════════════ EuropePMCConnector (P1-C-005) ═══════════════════


class TestEuropePMCConnector:
    def test_registered_name(self):
        c = registry.get("europe_pmc")
        assert isinstance(c, EuropePMCConnector)

    def test_is_available_always_true(self):
        # 공개 API, 키 불필요
        assert EuropePMCConnector().is_available() is True

    def test_search_default_sort_is_relevance(self):
        c = EuropePMCConnector()
        legacy = _legacy_result(PaperSource.EUROPE_PMC, [])
        with patch.object(c._service, "search", return_value=legacy) as m:
            c.search("q")
        assert m.call_args.kwargs["sort"] == "RELEVANCE"

    def test_sort_kwarg_passes_through(self):
        c = EuropePMCConnector()
        legacy = _legacy_result(PaperSource.EUROPE_PMC, [])
        with patch.object(c._service, "search", return_value=legacy) as m:
            c.search("q", sort="DATE")
        assert m.call_args.kwargs["sort"] == "DATE"

    def test_search_returns_normalized(self):
        c = EuropePMCConnector()
        legacy = _legacy_result(
            PaperSource.EUROPE_PMC,
            [_make_paper(PaperSource.EUROPE_PMC, "PMC123", journal="J Allergy")],
        )
        with patch.object(c._service, "search", return_value=legacy):
            r = c.search("q")
        assert r.docs[0].source == "europe_pmc"
        assert r.docs[0].journal == "J Allergy"

    def test_get_pdf_url_returns_none(self):
        assert EuropePMCConnector().get_pdf_url("PMC123") is None

    def test_error_handling(self):
        c = EuropePMCConnector()
        with patch.object(c._service, "search", side_effect=RuntimeError("timeout")):
            r = c.search("q")
        assert r.has_error


# ═══════════════════ OpenAlexConnector (P1-C-006) ═══════════════════


class TestOpenAlexConnector:
    def test_registered_name(self):
        c = registry.get("openalex")
        assert isinstance(c, OpenAlexConnector)

    def test_is_available_always_true(self):
        assert OpenAlexConnector().is_available() is True

    def test_email_from_openalex_env(self, monkeypatch):
        monkeypatch.setenv("OPENALEX_EMAIL", "oa@example.com")
        monkeypatch.delenv("PUBMED_EMAIL", raising=False)
        c = OpenAlexConnector()
        assert c._service.email == "oa@example.com"

    def test_email_fallback_to_pubmed(self, monkeypatch):
        monkeypatch.delenv("OPENALEX_EMAIL", raising=False)
        monkeypatch.setenv("PUBMED_EMAIL", "fallback@example.com")
        c = OpenAlexConnector()
        assert c._service.email == "fallback@example.com"

    def test_default_search_uses_search_method(self):
        c = OpenAlexConnector()
        legacy = _legacy_result(PaperSource.OPENALEX, [])
        with patch.object(c._service, "search", return_value=legacy) as m_search, \
             patch.object(c._service, "search_by_concept") as m_concept:
            c.search("allergy")
        m_search.assert_called_once()
        m_concept.assert_not_called()

    def test_concept_id_kwarg_delegates_to_concept_search(self):
        c = OpenAlexConnector()
        legacy = _legacy_result(PaperSource.OPENALEX, [])
        with patch.object(c._service, "search") as m_search, \
             patch.object(c._service, "search_by_concept", return_value=legacy) as m_concept:
            r = c.search("anything", concept_id="C71924100")
        m_concept.assert_called_once_with("C71924100", max_results=20)
        m_search.assert_not_called()
        assert r.meta["concept_id"] == "C71924100"

    def test_search_returns_normalized(self):
        c = OpenAlexConnector()
        legacy = _legacy_result(
            PaperSource.OPENALEX,
            [_make_paper(PaperSource.OPENALEX, "W123", citation_count=42)],
        )
        with patch.object(c._service, "search", return_value=legacy):
            r = c.search("q")
        assert r.docs[0].source == "openalex"
        assert r.docs[0].citation_count == 42

    def test_error_handling(self):
        c = OpenAlexConnector()
        with patch.object(c._service, "search", side_effect=RuntimeError("net err")):
            r = c.search("q")
        assert r.has_error


# ═══════════════════ BiorxivConnector (P1-C-007, 미결 O2 해결) ═══════════════════


class TestBiorxivConnector:
    def test_registered_name(self):
        c = registry.get("biorxiv")
        assert isinstance(c, BiorxivConnector)

    def test_is_available_always_true(self):
        assert BiorxivConnector().is_available() is True

    def test_keyword_mode_default(self):
        """No date kwargs → 키워드 검색 (Europe PMC SRC:PPR)."""
        c = BiorxivConnector()
        legacy = _legacy_result(PaperSource.BIORXIV_MEDRXIV, [])
        with patch.object(c._service, "search", return_value=legacy) as m_search, \
             patch.object(c._service, "collect_recent") as m_collect:
            r = c.search("vaccine")
        m_search.assert_called_once_with("vaccine", max_results=20, sort="DATE")
        m_collect.assert_not_called()
        assert r.meta["mode"] == "keyword"

    def test_date_range_mode(self):
        """date_from + date_to 지정 → bioRxiv 직접 수집."""
        c = BiorxivConnector()
        legacy = _legacy_result(PaperSource.BIORXIV_MEDRXIV, [])
        with patch.object(c._service, "search") as m_search, \
             patch.object(c._service, "collect_recent", return_value=legacy) as m_collect:
            r = c.search(
                "ignored",
                date_from="2026-01-01",
                date_to="2026-01-31",
                server="biorxiv",
                max_results=30,
            )
        m_collect.assert_called_once_with(
            date_from="2026-01-01",
            date_to="2026-01-31",
            server="biorxiv",
            max_results=30,
        )
        m_search.assert_not_called()
        assert r.meta["mode"] == "date_range"

    def test_partial_date_range_uses_keyword_mode(self):
        """date_from 만 있고 date_to 없으면 키워드 모드 (둘 다 있어야 활성)."""
        c = BiorxivConnector()
        legacy = _legacy_result(PaperSource.BIORXIV_MEDRXIV, [])
        with patch.object(c._service, "search", return_value=legacy) as m_search, \
             patch.object(c._service, "collect_recent") as m_collect:
            r = c.search("q", date_from="2026-01-01")
        m_search.assert_called_once()
        m_collect.assert_not_called()
        assert r.meta["mode"] == "keyword"

    def test_sort_kwarg_passes_through(self):
        c = BiorxivConnector()
        legacy = _legacy_result(PaperSource.BIORXIV_MEDRXIV, [])
        with patch.object(c._service, "search", return_value=legacy) as m:
            c.search("q", sort="RELEVANCE")
        assert m.call_args.kwargs["sort"] == "RELEVANCE"

    def test_default_server_is_medrxiv(self):
        c = BiorxivConnector()
        legacy = _legacy_result(PaperSource.BIORXIV_MEDRXIV, [])
        with patch.object(c._service, "collect_recent", return_value=legacy) as m:
            c.search("q", date_from="2026-01-01", date_to="2026-01-31")
        assert m.call_args.kwargs["server"] == "medrxiv"

    def test_search_returns_normalized(self):
        c = BiorxivConnector()
        legacy = _legacy_result(
            PaperSource.BIORXIV_MEDRXIV,
            [_make_paper(PaperSource.BIORXIV_MEDRXIV, "doi:10.1101/2024")],
        )
        with patch.object(c._service, "search", return_value=legacy):
            r = c.search("q")
        assert r.docs[0].source == "biorxiv_medrxiv"

    def test_error_handling_keyword_mode(self):
        c = BiorxivConnector()
        with patch.object(c._service, "search", side_effect=RuntimeError("epmc err")):
            r = c.search("q")
        assert r.has_error

    def test_error_handling_date_mode(self):
        c = BiorxivConnector()
        with patch.object(c._service, "collect_recent", side_effect=RuntimeError("biorxiv err")):
            r = c.search("q", date_from="2026-01-01", date_to="2026-01-31")
        assert r.has_error
