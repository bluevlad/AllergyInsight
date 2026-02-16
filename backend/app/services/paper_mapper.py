"""Paper Mapper - dataclass Paper ↔ ORM Paper 양방향 변환

검색 서비스의 dataclass Paper와 DB ORM Paper 간 변환을 담당합니다.
"""
from datetime import datetime
from typing import Optional

from ..models.paper import Paper as PaperDC, PaperSource
from ..database.models import Paper as PaperORM


class PaperMapper:
    """dataclass Paper ↔ ORM Paper 양방향 변환"""

    @staticmethod
    def dc_to_orm(paper_dc: PaperDC) -> PaperORM:
        """dataclass Paper → ORM Paper 변환 (신규 생성용)"""
        # authors: list[str] → 쉼표 구분 문자열
        authors_str = ", ".join(paper_dc.authors) if paper_dc.authors else None

        # source에 따라 pmid / semantic_scholar_id 설정
        pmid = None
        semantic_scholar_id = None
        if paper_dc.source == PaperSource.PUBMED:
            pmid = paper_dc.source_id
        elif paper_dc.source == PaperSource.SEMANTIC_SCHOLAR:
            semantic_scholar_id = paper_dc.source_id

        # URL 생성 (없으면)
        url = None
        if pmid:
            url = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"
        elif paper_dc.doi:
            url = f"https://doi.org/{paper_dc.doi}"

        return PaperORM(
            pmid=pmid,
            doi=paper_dc.doi,
            title=paper_dc.title,
            authors=authors_str,
            journal=paper_dc.journal,
            year=paper_dc.year,
            abstract=paper_dc.abstract,
            url=url,
            pdf_url=paper_dc.pdf_url,
            paper_type="research",
            source=paper_dc.source.value,
            source_id=paper_dc.source_id,
            semantic_scholar_id=semantic_scholar_id,
            citation_count=paper_dc.citation_count,
            keywords=paper_dc.keywords if paper_dc.keywords else None,
            last_synced_at=datetime.utcnow(),
            created_at=paper_dc.collected_at or datetime.utcnow(),
        )

    @staticmethod
    def orm_to_dc(paper_orm: PaperORM) -> PaperDC:
        """ORM Paper → dataclass Paper 변환"""
        # authors: 쉼표 구분 문자열 → list[str]
        authors = []
        if paper_orm.authors:
            authors = [a.strip() for a in paper_orm.authors.split(",")]

        # source 결정
        source = PaperSource.PUBMED  # 기본값
        if paper_orm.source:
            try:
                source = PaperSource(paper_orm.source)
            except ValueError:
                source = PaperSource.MANUAL_UPLOAD

        # source_id 결정
        source_id = paper_orm.source_id or paper_orm.pmid or paper_orm.semantic_scholar_id or ""

        return PaperDC(
            title=paper_orm.title,
            abstract=paper_orm.abstract or "",
            authors=authors,
            source=source,
            source_id=source_id,
            doi=paper_orm.doi,
            year=paper_orm.year,
            journal=paper_orm.journal,
            citation_count=paper_orm.citation_count,
            pdf_url=paper_orm.pdf_url,
            keywords=paper_orm.keywords or [],
            collected_at=paper_orm.created_at or datetime.utcnow(),
        )

    @staticmethod
    def update_orm_from_dc(orm: PaperORM, dc: PaperDC) -> bool:
        """기존 ORM 레코드를 최신 dataclass 정보로 갱신

        Returns:
            True if any field was updated
        """
        updated = False

        # citation_count 갱신 (더 큰 값으로)
        if dc.citation_count is not None:
            if orm.citation_count is None or dc.citation_count > orm.citation_count:
                orm.citation_count = dc.citation_count
                updated = True

        # pdf_url 보강 (없던 것 추가)
        if dc.pdf_url and not orm.pdf_url:
            orm.pdf_url = dc.pdf_url
            updated = True

        # keywords 병합
        if dc.keywords:
            existing = set(orm.keywords or [])
            new_keywords = list(existing | set(dc.keywords))
            if len(new_keywords) > len(existing):
                orm.keywords = new_keywords
                updated = True

        # abstract 보강 (없던 것 추가)
        if dc.abstract and not orm.abstract:
            orm.abstract = dc.abstract
            updated = True

        # semantic_scholar_id 보강
        if dc.source == PaperSource.SEMANTIC_SCHOLAR and not orm.semantic_scholar_id:
            orm.semantic_scholar_id = dc.source_id
            updated = True

        # doi 보강
        if dc.doi and not orm.doi:
            orm.doi = dc.doi
            updated = True

        if updated:
            orm.last_synced_at = datetime.utcnow()

        return updated
