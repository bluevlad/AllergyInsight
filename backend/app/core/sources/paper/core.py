"""CORE API v3 Connector.

기존 ``app.services.core_service.CoreService`` 위임.
``CORE_API_KEY`` 미설정 시 ``is_available()=False`` 로 registry 가 자동 skip.

WBS: P1-C-003
"""
from __future__ import annotations

import logging
from typing import Any

from app.core.sources.base import SourceSearchResult
from app.core.sources.paper.base import PaperSourceConnector, paper_to_normalized
from app.core.sources.registry import register
from app.services.core_service import CoreService

logger = logging.getLogger(__name__)


@register("core")
class CoreConnector(PaperSourceConnector):
    """CORE API v3 connector.

    CORE 는 검색 결과 자체에 PDF URL (``downloadUrl``) 을 포함하므로
    cross-lookup 용 ``get_pdf_url`` 은 사용하지 않는다 (NormalizedDoc.pdf_url 직접 사용).
    """

    SUPPORTS_YEAR_RANGE = False
    SUPPORTS_OPEN_ACCESS_FILTER = False
    SUPPORTS_PDF_URL = False  # 검색 결과에 PDF URL 직접 포함, cross-lookup 불필요

    def __init__(self) -> None:
        # CoreService 가 CORE_API_KEY 환경변수를 읽음
        self._service = CoreService()

    def is_available(self) -> bool:
        return bool(self._service.is_available)

    def search(
        self,
        query: str,
        max_results: int = 20,
        **kwargs: Any,
    ) -> SourceSearchResult:
        try:
            legacy = self._service.search(query, max_results=max_results)
        except Exception as e:
            logger.warning("CORE search 예외: query=%r err=%s", query, e)
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
        try:
            self._service.close()
        except Exception:
            pass
