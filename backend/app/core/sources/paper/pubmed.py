"""PubMed E-utilities Connector.

기존 ``app.services.pubmed_service.PubMedService`` 의 XML 파싱·재시도
로직을 그대로 위임(delegation)하여 회귀 위험을 0 으로 유지한다.

WBS: P1-C-001
"""
from __future__ import annotations

import logging
import os
from typing import Any

from app.core.sources.base import SourceSearchResult
from app.core.sources.paper.base import PaperSourceConnector, paper_to_normalized
from app.core.sources.registry import register
from app.services.pubmed_service import PubMedService

logger = logging.getLogger(__name__)


@register("pubmed")
class PubMedConnector(PaperSourceConnector):
    """PubMed E-utilities connector.

    Supported kwargs (search):
        year_range: tuple[int, int] — (min_year, max_year), inclusive
        sort: str — "relevance" (default) | "pub_date"
        min_date: str — YYYY/MM/DD (year_range 보다 우선)
        max_date: str — YYYY/MM/DD
    """

    SUPPORTS_YEAR_RANGE = True
    SUPPORTS_OPEN_ACCESS_FILTER = False
    # PubMed 자체는 PDF URL 을 제공하지 않음 — PDF 보강은 S2 connector 가 담당
    SUPPORTS_PDF_URL = False

    def __init__(self) -> None:
        api_key = os.getenv("NCBI_API_KEY") or os.getenv("PUBMED_API_KEY")
        email = os.getenv("PUBMED_EMAIL")
        self._service = PubMedService(api_key=api_key, email=email)

    def is_available(self) -> bool:
        # PubMed E-utilities 는 공개 — API 키 없이도 동작 (rate limit 완화만 차이)
        return True

    def search(
        self,
        query: str,
        max_results: int = 20,
        **kwargs: Any,
    ) -> SourceSearchResult:
        sort = kwargs.get("sort", "relevance")
        min_date, max_date = self._resolve_date_range(kwargs)

        try:
            legacy_result = self._service.search(
                query=query,
                max_results=max_results,
                sort=sort,
                min_date=min_date,
                max_date=max_date,
            )
        except Exception as e:
            logger.warning("PubMed search 예외: query=%r err=%s", query, e)
            return SourceSearchResult.empty(self.name, query, error=str(e))

        docs = [paper_to_normalized(p) for p in legacy_result.papers]
        return SourceSearchResult(
            docs=docs,
            source=self.name,
            query=query,
            meta={
                "total_count": legacy_result.total_count,
                "search_time_ms": legacy_result.search_time_ms,
            },
        )

    def get_pdf_url(self, source_id: str) -> str | None:
        # PubMed 자체는 PDF URL 제공 안 함
        return None

    def close(self) -> None:
        session = getattr(self._service, "session", None)
        if session is not None:
            try:
                session.close()
            except Exception:
                pass

    # ───────── internals ─────────

    @staticmethod
    def _resolve_date_range(
        kwargs: dict[str, Any],
    ) -> tuple[str | None, str | None]:
        """year_range tuple → min_date/max_date string, 직접 지정 시 우선."""
        min_date = kwargs.get("min_date")
        max_date = kwargs.get("max_date")
        year_range = kwargs.get("year_range")
        if year_range and not (min_date or max_date):
            lo, hi = year_range
            min_date = f"{lo:04d}/01/01"
            max_date = f"{hi:04d}/12/31"
        return min_date, max_date
