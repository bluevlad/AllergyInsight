"""Semantic Scholar API Connector.

기존 ``app.services.semantic_scholar_service.SemanticScholarService`` 위임.
PDF URL cross-lookup 을 지원 (``get_pdf_url``) — Step 1.D PDF 보강에서 활용.

WBS: P1-C-004
"""
from __future__ import annotations

import logging
import os
from typing import Any

from app.core.sources.base import SourceSearchResult
from app.core.sources.paper.base import PaperSourceConnector, paper_to_normalized
from app.core.sources.registry import register
from app.services.semantic_scholar_service import SemanticScholarService

logger = logging.getLogger(__name__)


@register("semantic_scholar")
class SemanticScholarConnector(PaperSourceConnector):
    """Semantic Scholar connector.

    Supported kwargs:
        year_range: tuple[int, int]
        open_access_only: bool
        fields_of_study: list[str]
    """

    SUPPORTS_YEAR_RANGE = True
    SUPPORTS_OPEN_ACCESS_FILTER = True
    SUPPORTS_PDF_URL = True

    def __init__(self) -> None:
        api_key = os.getenv("SEMANTIC_SCHOLAR_API_KEY")
        self._service = SemanticScholarService(api_key=api_key)

    def is_available(self) -> bool:
        # 공개 API, 키 없이도 동작
        return True

    def search(
        self,
        query: str,
        max_results: int = 20,
        **kwargs: Any,
    ) -> SourceSearchResult:
        try:
            legacy = self._service.search(
                query,
                max_results=max_results,
                year_range=kwargs.get("year_range"),
                open_access_only=kwargs.get("open_access_only", False),
                fields_of_study=kwargs.get("fields_of_study"),
            )
        except Exception as e:
            logger.warning("S2 search 예외: query=%r err=%s", query, e)
            return SourceSearchResult.empty(self.name, query, error=str(e))

        docs = [paper_to_normalized(p) for p in legacy.papers]
        return SourceSearchResult(
            docs=docs,
            source=self.name,
            query=query,
            meta={
                "total_count": legacy.total_count,
                "search_time_ms": legacy.search_time_ms,
            },
        )

    def get_pdf_url(self, source_id: str) -> str | None:
        """source_id = S2 paperId 로 PDF URL 조회.

        Step 1.D 의 cross-source PDF 보강은 별도 헬퍼 (``get_pdf_url_by_doi`` /
        ``get_pdf_url_by_pmid``) 로 추가 예정.
        """
        try:
            paper = self._service.get_paper_by_id(source_id)
        except Exception as e:
            logger.debug("S2 get_paper_by_id 실패: id=%r err=%s", source_id, e)
            return None
        return paper.pdf_url if paper else None

    def get_pdf_url_by_doi(self, doi: str) -> str | None:
        """DOI cross-lookup — PaperSearchService PDF 보강에서 사용."""
        try:
            paper = self._service.get_paper_by_doi(doi)
        except Exception:
            return None
        return paper.pdf_url if paper else None

    def get_pdf_url_by_pmid(self, pmid: str) -> str | None:
        """PMID cross-lookup — PubMed 결과 PDF 보강에서 사용."""
        try:
            paper = self._service.get_paper_by_pmid(pmid)
        except Exception:
            return None
        return paper.pdf_url if paper else None

    def close(self) -> None:
        session = getattr(self._service, "session", None)
        if session is not None:
            try:
                session.close()
            except Exception:
                pass
