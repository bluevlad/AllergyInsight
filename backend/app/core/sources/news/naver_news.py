"""Naver News API Connector.

기존 ``app.services.naver_news_service.NaverNewsService`` 위임.
환경변수 ``NAVER_CLIENT_ID`` + ``NAVER_CLIENT_SECRET`` 필요.

WBS: P1-E-001
"""
from __future__ import annotations

import logging
from typing import Any

from app.core.sources.base import SourceSearchResult
from app.core.sources.news.base import NewsSourceConnector, news_article_to_normalized
from app.core.sources.registry import register
from app.services.naver_news_service import NaverNewsService

logger = logging.getLogger(__name__)


@register("naver_news")
class NaverNewsConnector(NewsSourceConnector):
    """Naver News API connector.

    Supported kwargs:
        sort: str — "date" (default, 최신순) | "sim" (정확도순)
        start: int — pagination 시작 위치 (default 1, 최대 1000)
    """

    SUPPORTS_SINCE = False  # Naver Open API 자체에 since 필터 없음

    def __init__(self) -> None:
        # NaverNewsService 가 NAVER_CLIENT_ID / NAVER_CLIENT_SECRET 환경변수 읽음
        self._service = NaverNewsService()

    def is_available(self) -> bool:
        return bool(self._service.client_id and self._service.client_secret)

    def search(
        self,
        query: str,
        max_results: int = 20,
        **kwargs: Any,
    ) -> SourceSearchResult:
        try:
            legacy = self._service.search(
                query,
                display=max_results,
                start=kwargs.get("start", 1),
                sort=kwargs.get("sort", "date"),
            )
        except Exception as e:
            logger.warning("Naver news search 예외: query=%r err=%s", query, e)
            return SourceSearchResult.empty(self.name, query, error=str(e))

        docs = [
            news_article_to_normalized(a, source_name=self.name)
            for a in legacy.articles
        ]
        return SourceSearchResult(
            docs=docs,
            source=self.name,
            query=query,
            meta={
                "total_count": legacy.total_count,
                "search_time_ms": legacy.search_time_ms,
            },
        )

    def close(self) -> None:
        session = getattr(self._service, "session", None)
        if session is not None:
            try:
                session.close()
            except Exception:
                pass
