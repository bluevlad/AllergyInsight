"""논문 데이터 모델"""
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class PaperSource(str, Enum):
    """논문 출처"""
    PUBMED = "pubmed"
    SEMANTIC_SCHOLAR = "semantic_scholar"
    MANUAL_UPLOAD = "manual_upload"


@dataclass
class Paper:
    """논문 정보 모델"""
    title: str
    abstract: str
    authors: list[str]
    source: PaperSource
    source_id: str  # PubMed ID 또는 Semantic Scholar Paper ID

    # 선택적 필드
    doi: Optional[str] = None
    year: Optional[int] = None
    journal: Optional[str] = None
    citation_count: Optional[int] = None
    pdf_url: Optional[str] = None
    keywords: list[str] = field(default_factory=list)

    # 메타데이터
    collected_at: datetime = field(default_factory=datetime.now)
    local_pdf_path: Optional[str] = None

    def to_dict(self) -> dict:
        """딕셔너리로 변환"""
        return {
            "title": self.title,
            "abstract": self.abstract,
            "authors": self.authors,
            "source": self.source.value,
            "source_id": self.source_id,
            "doi": self.doi,
            "year": self.year,
            "journal": self.journal,
            "citation_count": self.citation_count,
            "pdf_url": self.pdf_url,
            "keywords": self.keywords,
            "collected_at": self.collected_at.isoformat(),
            "local_pdf_path": self.local_pdf_path,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Paper":
        """딕셔너리에서 생성"""
        data = data.copy()
        data["source"] = PaperSource(data["source"])
        if isinstance(data.get("collected_at"), str):
            data["collected_at"] = datetime.fromisoformat(data["collected_at"])
        return cls(**data)


@dataclass
class PaperSearchResult:
    """논문 검색 결과"""
    papers: list[Paper]
    total_count: int
    query: str
    source: PaperSource
    search_time_ms: float

    def to_dict(self) -> dict:
        """딕셔너리로 변환"""
        return {
            "papers": [p.to_dict() for p in self.papers],
            "total_count": self.total_count,
            "query": self.query,
            "source": self.source.value,
            "search_time_ms": self.search_time_ms,
        }
