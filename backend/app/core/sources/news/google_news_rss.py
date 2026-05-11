"""Google News RSS Connector.

기존 ``app.services.google_news_service.GoogleNewsService`` 위임.
무료, API 키 불필요.

WBS: P1-E-002
"""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from app.core.sources.base import NormalizedDoc, SourceSearchResult
from app.core.sources.news.base import NewsSourceConnector, news_article_to_normalized
from app.core.sources.registry import register
from app.services.google_news_service import GoogleNewsService

logger = logging.getLogger(__name__)


@register("google_news_rss")
class GoogleNewsRssConnector(NewsSourceConnector):
    """Google News RSS connector.

    Supported kwargs:
        lang: str — 언어 코드 (default "ko")
        country: str — 국가 코드 (default "KR")
        when: str — lookback 윈도우, e.g. "1d" | "7d" (default) | "30d"
        since: datetime — RSS 응답 후처리 필터 (since 이전 항목 제외)
    """

    SUPPORTS_SINCE = True  # client-side post-filter

    def __init__(self) -> None:
        self._service = GoogleNewsService()

    def is_available(self) -> bool:
        return True  # public RSS

    def search(
        self,
        query: str,
        max_results: int = 20,
        **kwargs: Any,
    ) -> SourceSearchResult:
        try:
            legacy = self._service.search(
                query,
                lang=kwargs.get("lang", "ko"),
                country=kwargs.get("country", "KR"),
                when=kwargs.get("when", "7d"),
                max_results=max_results,
            )
        except Exception as e:
            logger.warning("Google news RSS 예외: query=%r err=%s", query, e)
            return SourceSearchResult.empty(self.name, query, error=str(e))

        docs = [
            news_article_to_normalized(a, source_name=self.name)
            for a in legacy.articles
        ]

        # since post-filter
        since: datetime | None = kwargs.get("since")
        if since is not None:
            docs = [d for d in docs if self._published_after(d, since)]

        return SourceSearchResult(
            docs=docs,
            source=self.name,
            query=query,
            meta={
                "total_count": len(docs),  # post-filter 적용된 count
                "raw_count": legacy.total_count,
                "search_time_ms": legacy.search_time_ms,
                "since_filtered": since is not None,
            },
        )

    @staticmethod
    def _published_after(doc: NormalizedDoc, since: datetime) -> bool:
        """metadata.published_datetime 우선, 없으면 published_at (date) 비교."""
        raw_dt = doc.metadata.get("published_datetime")
        if isinstance(raw_dt, str):
            try:
                return datetime.fromisoformat(raw_dt) >= since
            except ValueError:
                pass
        if doc.published_at is not None:
            return datetime.combine(doc.published_at, datetime.min.time()) >= since
        # 발행일 미상 — 보수적으로 포함
        return True
