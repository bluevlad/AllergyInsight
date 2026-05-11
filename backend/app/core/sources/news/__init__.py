"""News source connectors (Layer 1 — news subdomain).

Importing this package auto-registers all news connectors via @register.
"""
from app.core.sources.news.base import (
    NewsSourceConnector,
    news_article_to_normalized,
    normalized_to_news_article,
)

# Auto-register concrete connectors on package import.
from app.core.sources.news import (  # noqa: F401  (side-effect imports)
    naver_news,
    google_news_rss,
)

__all__ = [
    "NewsSourceConnector",
    "news_article_to_normalized",
    "normalized_to_news_article",
]
