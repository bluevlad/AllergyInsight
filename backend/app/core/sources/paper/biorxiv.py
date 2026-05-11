"""bioRxiv / medRxiv Connector.

기존 ``app.services.biorxiv_service.BiorxivService`` 위임.

**미결 사항 O2 결정** (phase1-source-connector-abc.md §11):
이중 호출 패턴 (Europe PMC 키워드 검색 + bioRxiv 날짜 범위 수집) 을
**connector 내부에 은닉** 한다. ``search()`` 가 ``date_from`` / ``date_to``
kwargs 를 받으면 bioRxiv 직접 API 의 ``collect_recent`` 로 위임, 그 외에는
Europe PMC SRC:PPR 필터를 통한 키워드 검색을 사용한다. 호출자는 단일
인터페이스로 두 모드를 모두 활용 가능.

WBS: P1-C-007
"""
from __future__ import annotations

import logging
from typing import Any

from app.core.sources.base import SourceSearchResult
from app.core.sources.paper.base import PaperSourceConnector, paper_to_normalized
from app.core.sources.registry import register
from app.services.biorxiv_service import BiorxivService

logger = logging.getLogger(__name__)


@register("biorxiv")
class BiorxivConnector(PaperSourceConnector):
    """bioRxiv/medRxiv connector (이중 모드).

    Supported kwargs:
        sort: str — "DATE" (default) | "RELEVANCE" (키워드 모드)
        date_from: str — YYYY-MM-DD (지정 시 날짜 수집 모드)
        date_to: str — YYYY-MM-DD (date_from 와 함께)
        server: str — "biorxiv" | "medrxiv" (default "medrxiv", 날짜 모드)
    """

    SUPPORTS_YEAR_RANGE = False  # date_from/date_to 별도 kwarg 로 처리
    SUPPORTS_OPEN_ACCESS_FILTER = False
    SUPPORTS_PDF_URL = False

    def __init__(self) -> None:
        self._service = BiorxivService()

    def is_available(self) -> bool:
        return True

    def search(
        self,
        query: str,
        max_results: int = 20,
        **kwargs: Any,
    ) -> SourceSearchResult:
        date_from = kwargs.get("date_from")
        date_to = kwargs.get("date_to")
        server = kwargs.get("server", "medrxiv")
        sort = kwargs.get("sort", "DATE")

        try:
            if date_from and date_to:
                # 날짜 범위 수집 모드 (bioRxiv API 직접)
                legacy = self._service.collect_recent(
                    date_from=date_from,
                    date_to=date_to,
                    server=server,
                    max_results=max_results,
                )
                mode = "date_range"
            else:
                # 키워드 검색 모드 (Europe PMC SRC:PPR)
                legacy = self._service.search(
                    query, max_results=max_results, sort=sort
                )
                mode = "keyword"
        except Exception as e:
            logger.warning("bioRxiv search 예외: query=%r err=%s", query, e)
            return SourceSearchResult.empty(self.name, query, error=str(e))

        docs = [paper_to_normalized(p) for p in legacy.papers]
        return SourceSearchResult(
            docs=docs,
            source=self.name,
            query=query,
            meta={
                "total_count": legacy.total_count,
                "search_time_ms": legacy.search_time_ms,
                "mode": mode,
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
