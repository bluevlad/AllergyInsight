"""Tests for app.core.sources.paper.pubmed.PubMedConnector.

WBS: P1-C-001
"""
from __future__ import annotations

from datetime import date
from unittest.mock import patch, MagicMock

import pytest

from app.core.sources import registry
from app.core.sources.base import SourceKind, SourceSearchResult
from app.core.sources.paper.pubmed import PubMedConnector
from app.models.paper import Paper, PaperSearchResult, PaperSource


# ───────── 헬퍼: 기존 Paper 객체 생성 ─────────


def _paper(pmid: str = "100", **overrides) -> Paper:
    base = dict(
        title="Sample title",
        abstract="Sample abstract.",
        authors=["First Author", "Second Author"],
        source=PaperSource.PUBMED,
        source_id=pmid,
        doi="10.1000/sample",
        year=2024,
        published_at=date(2024, 3, 15),
        journal="J Allergy",
        citation_count=None,
        pdf_url=None,
        keywords=["allergy", "peanut"],
    )
    base.update(overrides)
    return Paper(**base)


# ───────── Registration & metadata ─────────


class TestRegistration:
    def test_registered_as_pubmed(self):
        assert "pubmed" in registry.names()
        c = registry.get("pubmed")
        assert isinstance(c, PubMedConnector)
        assert c.name == "pubmed"
        assert c.kind == SourceKind.PAPER

    def test_capability_flags(self):
        c = PubMedConnector()
        assert c.SUPPORTS_YEAR_RANGE is True
        assert c.SUPPORTS_PDF_URL is False
        assert c.SUPPORTS_OPEN_ACCESS_FILTER is False

    def test_is_available_always_true(self):
        assert PubMedConnector().is_available() is True

    def test_get_pdf_url_returns_none(self):
        assert PubMedConnector().get_pdf_url("12345") is None


# ───────── search: 정상 흐름 ─────────


class TestSearchHappyPath:
    def test_search_returns_normalized_docs(self):
        legacy_result = PaperSearchResult(
            papers=[_paper(pmid="111"), _paper(pmid="222", title="Other")],
            total_count=2,
            query="peanut allergy",
            source=PaperSource.PUBMED,
            search_time_ms=42.0,
        )
        connector = PubMedConnector()
        with patch.object(
            connector._service, "search", return_value=legacy_result
        ) as mock_search:
            result = connector.search("peanut allergy", max_results=10)

        mock_search.assert_called_once_with(
            query="peanut allergy",
            max_results=10,
            sort="relevance",
            min_date=None,
            max_date=None,
        )
        assert isinstance(result, SourceSearchResult)
        assert result.source == "pubmed"
        assert result.query == "peanut allergy"
        assert result.count == 2
        assert result.meta["total_count"] == 2
        assert result.meta["search_time_ms"] == 42.0
        assert not result.has_error

    def test_normalized_doc_field_preservation(self):
        legacy_result = PaperSearchResult(
            papers=[_paper(pmid="333")],
            total_count=1,
            query="q",
            source=PaperSource.PUBMED,
            search_time_ms=1.0,
        )
        connector = PubMedConnector()
        with patch.object(
            connector._service, "search", return_value=legacy_result
        ):
            result = connector.search("q")

        doc = result.docs[0]
        assert doc.source == "pubmed"
        assert doc.source_id == "333"
        assert doc.title == "Sample title"
        assert doc.authors == ("First Author", "Second Author")
        assert doc.abstract == "Sample abstract."
        assert doc.doi == "10.1000/sample"
        assert doc.year == 2024
        assert doc.published_at == date(2024, 3, 15)
        assert doc.journal == "J Allergy"
        assert doc.keywords == ("allergy", "peanut")

    def test_empty_abstract_becomes_none(self):
        legacy_result = PaperSearchResult(
            papers=[_paper(pmid="444", abstract="")],
            total_count=1,
            query="q",
            source=PaperSource.PUBMED,
            search_time_ms=0.5,
        )
        connector = PubMedConnector()
        with patch.object(
            connector._service, "search", return_value=legacy_result
        ):
            result = connector.search("q")

        assert result.docs[0].abstract is None


# ───────── search: year_range / 직접 날짜 ─────────


class TestDateRange:
    def test_year_range_converted_to_dates(self):
        connector = PubMedConnector()
        legacy_result = PaperSearchResult(
            papers=[], total_count=0, query="q",
            source=PaperSource.PUBMED, search_time_ms=0.1,
        )
        with patch.object(
            connector._service, "search", return_value=legacy_result
        ) as mock_search:
            connector.search("q", year_range=(2020, 2024))

        kwargs = mock_search.call_args.kwargs
        assert kwargs["min_date"] == "2020/01/01"
        assert kwargs["max_date"] == "2024/12/31"

    def test_explicit_min_max_date_overrides_year_range(self):
        connector = PubMedConnector()
        legacy_result = PaperSearchResult(
            papers=[], total_count=0, query="q",
            source=PaperSource.PUBMED, search_time_ms=0.1,
        )
        with patch.object(
            connector._service, "search", return_value=legacy_result
        ) as mock_search:
            connector.search(
                "q",
                year_range=(2020, 2024),
                min_date="2022/06/01",
                max_date="2022/12/31",
            )

        kwargs = mock_search.call_args.kwargs
        assert kwargs["min_date"] == "2022/06/01"
        assert kwargs["max_date"] == "2022/12/31"

    def test_no_date_kwargs_passes_none(self):
        connector = PubMedConnector()
        legacy_result = PaperSearchResult(
            papers=[], total_count=0, query="q",
            source=PaperSource.PUBMED, search_time_ms=0.1,
        )
        with patch.object(
            connector._service, "search", return_value=legacy_result
        ) as mock_search:
            connector.search("q")

        kwargs = mock_search.call_args.kwargs
        assert kwargs["min_date"] is None
        assert kwargs["max_date"] is None

    def test_sort_kwarg_passes_through(self):
        connector = PubMedConnector()
        legacy_result = PaperSearchResult(
            papers=[], total_count=0, query="q",
            source=PaperSource.PUBMED, search_time_ms=0.1,
        )
        with patch.object(
            connector._service, "search", return_value=legacy_result
        ) as mock_search:
            connector.search("q", sort="pub_date")

        assert mock_search.call_args.kwargs["sort"] == "pub_date"


# ───────── search: 에러 처리 ─────────


class TestErrorHandling:
    def test_underlying_exception_returns_empty_with_error(self):
        connector = PubMedConnector()
        with patch.object(
            connector._service, "search", side_effect=RuntimeError("boom"),
        ):
            result = connector.search("q")

        assert result.count == 0
        assert result.has_error
        assert "boom" in result.meta["error"]
        assert result.source == "pubmed"
        assert result.query == "q"


# ───────── close ─────────


class TestClose:
    def test_close_calls_session_close(self):
        connector = PubMedConnector()
        mock_session = MagicMock()
        connector._service.session = mock_session
        connector.close()
        mock_session.close.assert_called_once()

    def test_close_is_safe_when_no_session(self):
        connector = PubMedConnector()
        connector._service.session = None  # 비정상 상태
        connector.close()  # no raise


# ───────── 환경변수 ─────────


class TestEnvironment:
    def test_api_key_from_ncbi_env(self, monkeypatch):
        monkeypatch.setenv("NCBI_API_KEY", "ncbi_key_123")
        monkeypatch.delenv("PUBMED_API_KEY", raising=False)
        c = PubMedConnector()
        assert c._service.api_key == "ncbi_key_123"

    def test_api_key_fallback_to_pubmed_env(self, monkeypatch):
        monkeypatch.delenv("NCBI_API_KEY", raising=False)
        monkeypatch.setenv("PUBMED_API_KEY", "pubmed_key_xyz")
        c = PubMedConnector()
        assert c._service.api_key == "pubmed_key_xyz"

    def test_no_api_key_when_neither_set(self, monkeypatch):
        monkeypatch.delenv("NCBI_API_KEY", raising=False)
        monkeypatch.delenv("PUBMED_API_KEY", raising=False)
        c = PubMedConnector()
        assert c._service.api_key is None

    def test_email_from_env(self, monkeypatch):
        monkeypatch.setenv("PUBMED_EMAIL", "test@example.com")
        c = PubMedConnector()
        assert c._service.email == "test@example.com"


# ───────── 회귀: legacy 호환 ─────────


class TestLegacyCompatibility:
    """기존 PubMedService 와 동일 입력 → 동일 의미의 출력 보장."""

    def test_total_count_propagated(self):
        legacy_result = PaperSearchResult(
            papers=[_paper()],
            total_count=12345,
            query="q",
            source=PaperSource.PUBMED,
            search_time_ms=99.9,
        )
        connector = PubMedConnector()
        with patch.object(
            connector._service, "search", return_value=legacy_result
        ):
            result = connector.search("q")

        # NormalizedDoc 에는 total_count 슬롯이 없으므로 meta 로 노출
        assert result.meta["total_count"] == 12345
        assert result.meta["search_time_ms"] == 99.9

    def test_paper_source_enum_serialized_as_string(self):
        connector = PubMedConnector()
        legacy_result = PaperSearchResult(
            papers=[_paper()],
            total_count=1, query="q",
            source=PaperSource.PUBMED, search_time_ms=1.0,
        )
        with patch.object(
            connector._service, "search", return_value=legacy_result
        ):
            result = connector.search("q")

        # NormalizedDoc.source 는 str (Paper.source.value)
        assert result.docs[0].source == "pubmed"
        assert isinstance(result.docs[0].source, str)
