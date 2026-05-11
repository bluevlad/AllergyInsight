"""뉴스 source 의 ABC + 변환 헬퍼.

news 전용 search kwargs:
- since: datetime — 이 시간 이후 발행된 항목만 (지원하는 source 만)

**미결 O1 결정** (phase1-source-connector-abc.md §11):
``relevance_score`` 는 connector 가 아닌 Service 계층의 post-fetch AI 분석에서
처리한다. Connector 는 raw news 만 반환 — DomainPack 의 ``prompts.news_relevance``
를 통해 도메인별로 분석되어야 하므로 source-agnostic 인터페이스 유지.
"""
from __future__ import annotations

from datetime import datetime

from app.core.sources.base import NormalizedDoc, SourceConnector, SourceKind
from app.models.competitor_news import NewsArticle


class NewsSourceConnector(SourceConnector):
    """뉴스 source 의 ABC.

    PaperSourceConnector 와 달리 PDF URL 인터페이스는 없다.
    """

    kind: SourceKind = SourceKind.NEWS

    SUPPORTS_SINCE: bool = False


def news_article_to_normalized(
    a: NewsArticle,
    *,
    source_name: str | None = None,
) -> NormalizedDoc:
    """``NewsArticle`` → ``NormalizedDoc`` 변환.

    필드 매핑:
    - url → source_id (뉴스 도메인에서 URL 이 unique 식별자)
    - description → abstract
    - published_at (datetime) → published_at (date) + metadata["published_datetime"]
    - company, search_keyword → metadata

    Args:
        source_name: connector 의 registry 이름 (지정 시 NewsArticle.source 보다 우선).
    """
    pub_date = a.published_at.date() if a.published_at else None
    meta: dict = {}
    if a.company:
        meta["company"] = a.company
    if a.search_keyword:
        meta["search_keyword"] = a.search_keyword
    if a.published_at:
        meta["published_datetime"] = a.published_at.isoformat()

    return NormalizedDoc(
        source=source_name or a.source,
        source_id=a.url,
        title=a.title,
        authors=(),
        abstract=a.description or None,
        published_at=pub_date,
        url=a.url,
        metadata=meta,
    )


def normalized_to_news_article(doc: NormalizedDoc) -> NewsArticle:
    """``NormalizedDoc`` → ``NewsArticle`` 역변환 (backward-compat).

    metadata 의 published_datetime/company/search_keyword 복원.
    """
    pub_dt: datetime | None = None
    raw_dt = doc.metadata.get("published_datetime")
    if isinstance(raw_dt, str):
        try:
            pub_dt = datetime.fromisoformat(raw_dt)
        except ValueError:
            pub_dt = None
    if pub_dt is None and doc.published_at:
        pub_dt = datetime.combine(doc.published_at, datetime.min.time())

    return NewsArticle(
        title=doc.title,
        url=doc.url or doc.source_id,
        source=doc.source,
        company=doc.metadata.get("company", ""),
        description=doc.abstract or "",
        published_at=pub_dt,
        search_keyword=doc.metadata.get("search_keyword", ""),
    )
