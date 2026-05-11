"""SourceConnector ABC + 표준 데이터 모델.

Vertical Insight Framework Layer 1 의 기반. 모든 외부 데이터 source 가
따르는 인터페이스를 정의한다.

설계 문서: plans/phase1-source-connector-abc.md
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from enum import Enum
from typing import Any


class SourceKind(str, Enum):
    """수집 소스 분류."""

    PAPER = "paper"
    NEWS = "news"
    REGULATORY = "regulatory"
    RSS = "rss"


@dataclass(frozen=True)
class NormalizedDoc:
    """모든 source 가 반환하는 표준 문서 모델.

    필드는 backend/app/models/paper.py 의 Paper 모델과 호환되며,
    to_paper_dict() 로 ORM 입력 dict 로 변환 가능.
    """

    source: str
    source_id: str
    title: str
    authors: tuple[str, ...] = ()
    abstract: str | None = None
    doi: str | None = None
    year: int | None = None
    published_at: date | None = None
    journal: str | None = None
    citation_count: int | None = None
    pdf_url: str | None = None
    keywords: tuple[str, ...] = ()
    url: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_paper_dict(self) -> dict[str, Any]:
        """models.paper.Paper ORM 생성에 사용할 dict 반환."""
        return {
            "source": self.source,
            "source_id": self.source_id,
            "title": self.title,
            "authors": list(self.authors),
            "abstract": self.abstract,
            "doi": self.doi,
            "year": self.year,
            "published_at": self.published_at,
            "journal": self.journal,
            "citation_count": self.citation_count,
            "pdf_url": self.pdf_url,
            "keywords": list(self.keywords),
        }


@dataclass(frozen=True)
class SourceSearchResult:
    """단일 source 검색 결과 + 메타.

    부분 실패 시 docs=[] 이고 meta["error"] 에 에러 정보가 담긴다.
    """

    docs: list[NormalizedDoc]
    source: str
    query: str
    fetched_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    meta: dict[str, Any] = field(default_factory=dict)

    @property
    def count(self) -> int:
        return len(self.docs)

    @property
    def has_error(self) -> bool:
        return "error" in self.meta

    @classmethod
    def empty(
        cls,
        source: str,
        query: str,
        *,
        error: str | None = None,
    ) -> "SourceSearchResult":
        """0건 결과 생성. error 가 주어지면 meta 에 기록."""
        meta: dict[str, Any] = {"error": error} if error else {}
        return cls(docs=[], source=source, query=query, meta=meta)


class SourceConnector(ABC):
    """모든 외부 source 의 베이스 ABC.

    구현체는 @registry.register("name") 데코레이터로 등록한다.

    Subclass-specific kwargs (search 의 **kwargs):
    - PaperSourceConnector: year_range, open_access_only
    - NewsSourceConnector: since
    """

    # 클래스 속성 — registry.register 가 채움
    name: str = ""
    kind: SourceKind = SourceKind.PAPER

    @abstractmethod
    def search(
        self,
        query: str,
        max_results: int = 20,
        **kwargs: Any,
    ) -> SourceSearchResult:
        """질의 실행. 구현체는 알 수 없는 kwargs 는 무시할 것."""
        ...

    @abstractmethod
    def is_available(self) -> bool:
        """호출 가능 여부 (API 키·필수 설정 점검). False 시 registry 가 skip."""
        ...

    def close(self) -> None:
        """리소스 정리 (httpx.Client 등). 기본 no-op."""

    def __enter__(self) -> "SourceConnector":
        return self

    def __exit__(self, *exc: Any) -> None:
        self.close()
