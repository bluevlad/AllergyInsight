"""Tests for the registry-based PaperSearchService refactor.

WBS: P1-D-001 (registry path), P1-D-002 (S2 connector PDF 보강),
     P1-D-003 (errors meta)
"""
from __future__ import annotations

from datetime import date
from unittest.mock import MagicMock, patch

import pytest

from app.core.sources.base import (
    NormalizedDoc,
    SourceSearchResult,
)
from app.core.sources.paper.semantic_scholar import SemanticScholarConnector
from app.models.paper import Paper, PaperSource
from app.services.paper_search_service import (
    PaperSearchService,
    UnifiedSearchResult,
)


# ───────── 헬퍼 ─────────


def _make_doc(source: str, source_id: str, **kw) -> NormalizedDoc:
    base = dict(
        source=source,
        source_id=source_id,
        title=kw.get("title", "t"),
        authors=kw.get("authors", ("A",)),
        abstract=kw.get("abstract", "a"),
        doi=kw.get("doi"),
        year=kw.get("year"),
        published_at=kw.get("published_at"),
        journal=kw.get("journal"),
        citation_count=kw.get("citation_count"),
        pdf_url=kw.get("pdf_url"),
        keywords=kw.get("keywords", ()),
    )
    return NormalizedDoc(**base)


def _result(source: str, docs: list[NormalizedDoc], **kw) -> SourceSearchResult:
    return SourceSearchResult(
        docs=docs,
        source=source,
        query=kw.get("query", "q"),
        meta=kw.get("meta", {"total_count": len(docs)}),
    )


# ───────── UnifiedSearchResult ─────────


class TestUnifiedSearchResultShape:
    def test_errors_field_default_empty(self):
        r = UnifiedSearchResult(
            papers=[], pubmed_count=0, semantic_scholar_count=0,
            total_unique=0, query="q", search_time_ms=0.0,
        )
        assert r.errors == {}

    def test_to_dict_includes_errors_and_existing_fields(self):
        r = UnifiedSearchResult(
            papers=[], pubmed_count=1, semantic_scholar_count=2,
            europe_pmc_count=3, openalex_count=4, biorxiv_count=5, core_count=6,
            total_unique=7, downloadable_count=8, query="q",
            search_time_ms=9.0, errors={"core": "timeout"},
        )
        d = r.to_dict()
        assert d["errors"] == {"core": "timeout"}
        # 기존 필드 모두 유지 (backward compat)
        for f in (
            "pubmed_count", "semantic_scholar_count", "europe_pmc_count",
            "openalex_count", "biorxiv_count", "core_count",
            "total_unique", "downloadable_count", "query", "search_time_ms",
            "papers",
        ):
            assert f in d


# ───────── Registry 기반 search() ─────────


class TestRegistrySearch:
    def test_uses_registry_connectors(self):
        svc = PaperSearchService()
        # 기본적으로 6 paper connector 가 모두 _connectors 에 있어야 함
        names = set(svc._connectors.keys())
        for n in ("pubmed", "semantic_scholar", "europe_pmc",
                  "openalex", "biorxiv", "core"):
            assert n in names

    def test_search_only_calls_enabled_sources(self):
        svc = PaperSearchService()
        # 모든 connector 의 search 를 mock
        for c in svc._connectors.values():
            c.search = MagicMock(return_value=_result(c.name, []))
            c.is_available = MagicMock(return_value=True)

        svc.search("q", sources=["pubmed", "core"], enrich_pdf_links=False)

        svc._connectors["pubmed"].search.assert_called_once()
        svc._connectors["core"].search.assert_called_once()
        svc._connectors["semantic_scholar"].search.assert_not_called()
        svc._connectors["europe_pmc"].search.assert_not_called()
        svc._connectors["openalex"].search.assert_not_called()
        svc._connectors["biorxiv"].search.assert_not_called()

    def test_search_skips_unavailable_connector(self):
        svc = PaperSearchService()
        for c in svc._connectors.values():
            c.search = MagicMock(return_value=_result(c.name, []))
            c.is_available = MagicMock(return_value=True)
        # CORE 만 unavailable
        svc._connectors["core"].is_available.return_value = False

        svc.search("q", enrich_pdf_links=False)

        svc._connectors["pubmed"].search.assert_called_once()
        svc._connectors["core"].search.assert_not_called()

    def test_search_default_sources_uses_all_available(self):
        svc = PaperSearchService()
        for c in svc._connectors.values():
            c.search = MagicMock(return_value=_result(c.name, []))
            c.is_available = MagicMock(return_value=True)

        svc.search("q", enrich_pdf_links=False)

        # 모든 connector 호출됨 (CORE 도 is_available=True 라서)
        for c in svc._connectors.values():
            c.search.assert_called_once()


# ───────── NormalizedDoc → Paper 역변환 ─────────


class TestResultConversion:
    def test_normalized_docs_become_papers(self):
        svc = PaperSearchService()
        # 빈 결과 + 한 connector 만 응답
        for c in svc._connectors.values():
            c.search = MagicMock(return_value=_result(c.name, []))
            c.is_available = MagicMock(return_value=True)

        svc._connectors["pubmed"].search.return_value = _result(
            "pubmed",
            [
                _make_doc("pubmed", "111", title="P1", doi="10.1/a"),
                _make_doc("pubmed", "222", title="P2", doi="10.1/b"),
            ],
            meta={"total_count": 42},
        )

        result = svc.search("q", enrich_pdf_links=False)

        assert result.pubmed_count == 42
        assert len(result.papers) == 2
        assert {p.title for p in result.papers} == {"P1", "P2"}
        assert all(p.source == PaperSource.PUBMED for p in result.papers)

    def test_per_source_counts_populated(self):
        svc = PaperSearchService()
        for c in svc._connectors.values():
            c.is_available = MagicMock(return_value=True)
            c.search = MagicMock(return_value=_result(c.name, [], meta={"total_count": 0}))

        svc._connectors["pubmed"].search.return_value = _result(
            "pubmed", [], meta={"total_count": 10},
        )
        svc._connectors["semantic_scholar"].search.return_value = _result(
            "semantic_scholar", [], meta={"total_count": 20},
        )
        svc._connectors["core"].search.return_value = _result(
            "core", [], meta={"total_count": 30},
        )

        result = svc.search("q", enrich_pdf_links=False)

        assert result.pubmed_count == 10
        assert result.semantic_scholar_count == 20
        assert result.core_count == 30


# ───────── D-003: 에러 가시화 ─────────


class TestErrorVisibility:
    def test_partial_failure_recorded_in_errors(self):
        svc = PaperSearchService()
        for c in svc._connectors.values():
            c.is_available = MagicMock(return_value=True)
            c.search = MagicMock(return_value=_result(c.name, []))

        # CORE 가 부분 실패 (connector 내부 캐치)
        svc._connectors["core"].search.return_value = SourceSearchResult.empty(
            "core", "q", error="rate limit",
        )

        result = svc.search("q", enrich_pdf_links=False)

        assert "core" in result.errors
        assert "rate limit" in result.errors["core"]
        assert result.core_count == 0
        # 다른 source 는 에러 없음
        assert "pubmed" not in result.errors

    def test_future_exception_recorded_in_errors(self):
        svc = PaperSearchService()
        for c in svc._connectors.values():
            c.is_available = MagicMock(return_value=True)
            c.search = MagicMock(return_value=_result(c.name, []))

        # PubMed connector.search 자체가 예외 raise
        svc._connectors["pubmed"].search.side_effect = RuntimeError("boom")

        result = svc.search("q", enrich_pdf_links=False)

        assert "pubmed" in result.errors
        assert "RuntimeError" in result.errors["pubmed"]
        assert "boom" in result.errors["pubmed"]

    def test_no_errors_when_all_succeed(self):
        svc = PaperSearchService()
        for c in svc._connectors.values():
            c.is_available = MagicMock(return_value=True)
            c.search = MagicMock(return_value=_result(c.name, []))

        result = svc.search("q", enrich_pdf_links=False)
        assert result.errors == {}


# ───────── D-002: PDF 보강 via S2 connector ─────────


class TestPdfEnrichment:
    def test_pubmed_paper_pdf_via_s2_connector_pmid_lookup(self):
        svc = PaperSearchService()
        for c in svc._connectors.values():
            c.is_available = MagicMock(return_value=True)
            c.search = MagicMock(return_value=_result(c.name, []))

        # PubMed 결과 1건 (pdf_url 없음)
        svc._connectors["pubmed"].search.return_value = _result(
            "pubmed",
            [_make_doc("pubmed", "111", title="P1", pdf_url=None)],
        )
        # S2 connector 의 cross-lookup 메서드 mock
        svc._s2_connector.get_pdf_url_by_pmid = MagicMock(
            return_value="https://s2/p.pdf"
        )

        result = svc.search("q", enrich_pdf_links=True)

        svc._s2_connector.get_pdf_url_by_pmid.assert_called_once_with("111")
        assert result.papers[0].pdf_url == "https://s2/p.pdf"

    def test_doi_paper_pdf_via_s2_connector_doi_lookup(self):
        svc = PaperSearchService()
        for c in svc._connectors.values():
            c.is_available = MagicMock(return_value=True)
            c.search = MagicMock(return_value=_result(c.name, []))

        # OpenAlex 결과 1건 (PubMed 아님, doi 있음, pdf 없음)
        svc._connectors["openalex"].search.return_value = _result(
            "openalex",
            [_make_doc("openalex", "W1", doi="10.1/x", pdf_url=None)],
        )
        svc._s2_connector.get_pdf_url_by_doi = MagicMock(
            return_value="https://s2/d.pdf"
        )

        result = svc.search("q", enrich_pdf_links=True)

        svc._s2_connector.get_pdf_url_by_doi.assert_called_once_with("10.1/x")
        assert result.papers[0].pdf_url == "https://s2/d.pdf"

    def test_pdf_already_present_skips_lookup(self):
        svc = PaperSearchService()
        for c in svc._connectors.values():
            c.is_available = MagicMock(return_value=True)
            c.search = MagicMock(return_value=_result(c.name, []))

        svc._connectors["pubmed"].search.return_value = _result(
            "pubmed",
            [_make_doc("pubmed", "111", pdf_url="https://existing/p.pdf")],
        )
        svc._s2_connector.get_pdf_url_by_pmid = MagicMock()

        result = svc.search("q", enrich_pdf_links=True)

        svc._s2_connector.get_pdf_url_by_pmid.assert_not_called()
        assert result.papers[0].pdf_url == "https://existing/p.pdf"

    def test_enrich_disabled_skips_s2(self):
        svc = PaperSearchService()
        for c in svc._connectors.values():
            c.is_available = MagicMock(return_value=True)
            c.search = MagicMock(return_value=_result(c.name, []))

        svc._connectors["pubmed"].search.return_value = _result(
            "pubmed",
            [_make_doc("pubmed", "111", pdf_url=None)],
        )
        svc._s2_connector.get_pdf_url_by_pmid = MagicMock(return_value="x")

        svc.search("q", enrich_pdf_links=False)

        svc._s2_connector.get_pdf_url_by_pmid.assert_not_called()


# ───────── 중복 제거 (기존 동작 회귀) ─────────


class TestDeduplication:
    def test_same_doi_merged(self):
        svc = PaperSearchService()
        for c in svc._connectors.values():
            c.is_available = MagicMock(return_value=True)
            c.search = MagicMock(return_value=_result(c.name, []))

        # 동일 DOI 가 PubMed 와 S2 양쪽 결과로 나옴
        svc._connectors["pubmed"].search.return_value = _result(
            "pubmed",
            [_make_doc("pubmed", "111", title="Same paper", doi="10.1/same")],
        )
        svc._connectors["semantic_scholar"].search.return_value = _result(
            "semantic_scholar",
            [_make_doc(
                "semantic_scholar", "S2:1", title="Same paper",
                doi="10.1/same", pdf_url="https://s2/p.pdf",
            )],
        )

        result = svc.search("q", enrich_pdf_links=False)

        # DOI 매칭 → 1건만 남음, 정보 병합으로 pdf_url 채워짐
        assert result.total_unique == 1
        assert result.papers[0].pdf_url == "https://s2/p.pdf"


# ───────── close ─────────


class TestClose:
    def test_close_closes_all_connectors_and_legacy(self):
        svc = PaperSearchService()
        # connector / legacy 모두 mock
        for c in svc._connectors.values():
            c.close = MagicMock()
        svc.europe_pmc.close = MagicMock()
        svc.openalex.close = MagicMock()
        svc.biorxiv.close = MagicMock()
        svc.core.close = MagicMock()

        svc.close()

        for c in svc._connectors.values():
            c.close.assert_called_once()
        svc.europe_pmc.close.assert_called_once()


# ───────── search_allergy (legacy path 회귀) ─────────


class TestSearchAllergyLegacyPath:
    def test_search_allergy_calls_legacy_services(self):
        svc = PaperSearchService()

        # 모든 legacy service 의 search_allergy* 를 mock
        from app.models.paper import PaperSearchResult as LegacyResult

        def _legacy(source):
            return LegacyResult(
                papers=[], total_count=0, query="x",
                source=source, search_time_ms=0.0,
            )

        svc.pubmed.search_allergy_papers = MagicMock(
            return_value=_legacy(PaperSource.PUBMED)
        )
        svc.semantic_scholar.search_allergy_papers = MagicMock(
            return_value=_legacy(PaperSource.SEMANTIC_SCHOLAR)
        )
        svc.europe_pmc.search_allergy = MagicMock(
            return_value=_legacy(PaperSource.EUROPE_PMC)
        )
        svc.openalex.search_allergy = MagicMock(
            return_value=_legacy(PaperSource.OPENALEX)
        )
        svc.biorxiv.search_allergy = MagicMock(
            return_value=_legacy(PaperSource.BIORXIV_MEDRXIV)
        )
        # CORE 는 is_available=False 면 skip
        svc.core.api_key = None  # 키 없음

        # _enrich_pdf_links 도 mock (S2 cross-lookup 회피)
        svc._s2_connector = None  # disable enrichment

        result = svc.search_allergy("peanut", include_cross_reactivity=True)

        svc.pubmed.search_allergy_papers.assert_called_once()
        svc.semantic_scholar.search_allergy_papers.assert_called_once()
        svc.europe_pmc.search_allergy.assert_called_once()
        svc.openalex.search_allergy.assert_called_once()
        svc.biorxiv.search_allergy.assert_called_once()
        assert "peanut" in result.query
        assert "cross-reactivity" in result.query
