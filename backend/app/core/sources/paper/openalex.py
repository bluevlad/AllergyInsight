"""OpenAlex API Connector.

기존 ``app.services.openalex_service.OpenAlexService`` 위임.
이메일 제공 시 polite pool (rate limit 완화) 이용 — ``OPENALEX_EMAIL`` 또는
``PUBMED_EMAIL`` 환경변수.

WBS: P1-C-006
"""
from __future__ import annotations

import logging
import os
from typing import Any

from app.core.sources.base import SourceSearchResult
from app.core.sources.paper.base import PaperSourceConnector, paper_to_normalized
from app.core.sources.registry import register
from app.services.openalex_service import OpenAlexService

logger = logging.getLogger(__name__)


@register("openalex")
class OpenAlexConnector(PaperSourceConnector):
    """OpenAlex connector.

    Supported kwargs:
        concept_id: str — OpenAlex Concept ID 로 필터 검색 (search_by_concept 위임)
    """

    SUPPORTS_YEAR_RANGE = False
    SUPPORTS_OPEN_ACCESS_FILTER = False
    SUPPORTS_PDF_URL = False  # open_access.oa_url 이 검색 결과에 직접 포함

    def __init__(self) -> None:
        email = os.getenv("OPENALEX_EMAIL") or os.getenv("PUBMED_EMAIL")
        self._service = OpenAlexService(email=email)

    def is_available(self) -> bool:
        return True

    def search(
        self,
        query: str,
        max_results: int = 20,
        **kwargs: Any,
    ) -> SourceSearchResult:
        concept_id = kwargs.get("concept_id")
        try:
            if concept_id:
                legacy = self._service.search_by_concept(
                    concept_id, max_results=max_results
                )
            else:
                legacy = self._service.search(query, max_results=max_results)
        except Exception as e:
            logger.warning("OpenAlex search 예외: query=%r err=%s", query, e)
            return SourceSearchResult.empty(self.name, query, error=str(e))

        docs = [paper_to_normalized(p) for p in legacy.papers]
        return SourceSearchResult(
            docs=docs,
            source=self.name,
            query=query,
            meta={
                "total_count": legacy.total_count,
                "search_time_ms": legacy.search_time_ms,
                "concept_id": concept_id,
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
