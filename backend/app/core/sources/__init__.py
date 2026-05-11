"""Source Connector framework — Layer 1 of Vertical Insight Framework.

설계 문서:
- plans/phase1-source-connector-abc.md
- adr/011-vertical-insight-framework.md

모든 외부 데이터 source (학술 논문, 뉴스, 규제 등) 는 SourceConnector ABC 를
상속하고 @registry.register("name") 으로 등록한다.
"""
from app.core.sources.base import (
    NormalizedDoc,
    SourceConnector,
    SourceKind,
    SourceSearchResult,
)
from app.core.sources.errors import (
    RateLimitError,
    SourceAuthError,
    SourceError,
    SourceTimeoutError,
    SourceUnavailableError,
)
from app.core.sources import registry

__all__ = [
    "NormalizedDoc",
    "SourceConnector",
    "SourceKind",
    "SourceSearchResult",
    "RateLimitError",
    "SourceAuthError",
    "SourceError",
    "SourceTimeoutError",
    "SourceUnavailableError",
    "registry",
]
