"""Paper source connectors (Layer 1 — paper subdomain).

Importing this package auto-registers all 6 paper connectors via the
@register decorator. Order is irrelevant — registry is name-keyed.
"""
from app.core.sources.paper.base import PaperSourceConnector, paper_to_normalized

# Auto-register concrete connectors on package import.
# DomainPack YAML 의 sources.enabled 항목이 registry 에서 찾을 수 있도록 보장.
from app.core.sources.paper import (  # noqa: F401  (side-effect imports)
    pubmed,
    semantic_scholar,
    europe_pmc,
    openalex,
    biorxiv,
    core,
)

__all__ = ["PaperSourceConnector", "paper_to_normalized"]
