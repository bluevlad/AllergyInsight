"""Europe PMC API Connector.

기존 ``app.services.europe_pmc_service.EuropePMCService`` 위임.
공개 API, API 키 불필요.

WBS: P1-C-005
"""
from __future__ import annotations

import logging
from typing import Any

from app.core.sources.base import SourceSearchResult
from app.core.sources.paper.base import PaperSourceConnector, paper_to_normalized
from app.core.sources.registry import register
from app.services.europe_pmc_service import EuropePMCService

logger = logging.getLogger(__name__)


@register("europe_pmc")
class EuropePMCConnector(PaperSourceConnector):
    """Europe PMC connector.

    Supported kwargs:
        sort: str — "RELEVANCE" (default) | "DATE"
    """

    SUPPORTS_YEAR_RANGE = False
    SUPPORTS_OPEN_ACCESS_FILTER = False
    SUPPORTS_PDF_URL = False  # fullTextUrl 이 검색 결과에 직접 포함

    def __init__(self) -> None:
        self._service = EuropePMCService()

    def is_available(self) -> bool:
        return True

    def search(
        self,
        query: str,
        max_results: int = 20,
        **kwargs: Any,
    ) -> SourceSearchResult:
        sort = kwargs.get("sort", "RELEVANCE")
        try:
            legacy = self._service.search(
                query, max_results=max_results, sort=sort
            )
        except Exception as e:
            logger.warning("EPMC search 예외: query=%r err=%s", query, e)
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
        return None

    def close(self) -> None:
        client = getattr(self._service, "_client", None)
        if client is not None:
            try:
                client.close()
            except Exception:
                pass
