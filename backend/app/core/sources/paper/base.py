"""학술 논문 source 의 ABC.

PaperSourceConnector 는 SourceConnector 의 paper 분기로,
PDF URL 보강 인터페이스 (get_pdf_url) 를 추가한다.

paper 전용 search kwargs:
- year_range: tuple[int, int] — 발행 연도 범위
- open_access_only: bool — open access 만 (지원하는 source 만)
"""
from __future__ import annotations

from abc import abstractmethod

from app.core.sources.base import NormalizedDoc, SourceConnector, SourceKind
from app.models.paper import Paper


class PaperSourceConnector(SourceConnector):
    """학술 논문 source 의 ABC."""

    kind: SourceKind = SourceKind.PAPER

    # 기능 플래그 — 구현체가 override
    SUPPORTS_YEAR_RANGE: bool = False
    SUPPORTS_OPEN_ACCESS_FILTER: bool = False
    SUPPORTS_PDF_URL: bool = False

    @abstractmethod
    def get_pdf_url(self, source_id: str) -> str | None:
        """source_id 에 대응하는 PDF URL 반환 (없으면 None).

        PaperSearchService 의 PDF 보강 (예: PubMed → S2 조회) 에 사용.
        SUPPORTS_PDF_URL = False 인 connector 는 항상 None 반환 가능.
        """
        ...


def paper_to_normalized(p: Paper) -> NormalizedDoc:
    """기존 ``models.paper.Paper`` → ``NormalizedDoc`` 변환.

    모든 paper connector 가 delegation 후 동일 변환을 거치므로 공통 헬퍼로 추출.
    Paper.source (Enum) → NormalizedDoc.source (str) 변환 포함.
    빈 문자열 abstract 는 None 으로 정규화.
    """
    return NormalizedDoc(
        source=p.source.value,
        source_id=p.source_id,
        title=p.title,
        authors=tuple(p.authors),
        abstract=p.abstract or None,
        doi=p.doi,
        year=p.year,
        published_at=p.published_at,
        journal=p.journal,
        citation_count=p.citation_count,
        pdf_url=p.pdf_url,
        keywords=tuple(p.keywords),
    )


def normalized_to_paper(doc: NormalizedDoc) -> Paper:
    """``NormalizedDoc`` → 기존 ``Paper`` 역변환.

    ``paper_to_normalized`` 의 역방향. PaperSearchService 등 backward-compat
    출력이 필요한 통합 계층에서 사용.

    Note: ``doc.source`` 는 ``PaperSource`` enum 의 유효 value 여야 한다
    (모든 paper connector 가 paper_to_normalized 를 거치므로 보장됨).
    """
    from app.models.paper import PaperSource

    return Paper(
        title=doc.title,
        abstract=doc.abstract or "",
        authors=list(doc.authors),
        source=PaperSource(doc.source),
        source_id=doc.source_id,
        doi=doc.doi,
        year=doc.year,
        published_at=doc.published_at,
        journal=doc.journal,
        citation_count=doc.citation_count,
        pdf_url=doc.pdf_url,
        keywords=list(doc.keywords),
    )
