"""Paper Persistence Service - 검색 결과 DB 영속화

검색 결과를 PostgreSQL에 저장하고, 중복 검사, 로컬 DB 검색을 제공합니다.
"""
import logging
from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session
from sqlalchemy import or_, func

from ..models.paper import Paper as PaperDC, PaperSource
from ..database.models import Paper as PaperORM, PaperAllergenLink, SearchHistory
from .paper_mapper import PaperMapper
from .paper_link_extractor import get_extractor

logger = logging.getLogger(__name__)


class PaperPersistenceService:
    """검색 결과 DB 영속화 서비스"""

    def __init__(self):
        self._extractor = get_extractor()

    def save_search_results(
        self,
        results,  # UnifiedSearchResult
        db: Session,
        allergen_code: Optional[str] = None,
        user_id: Optional[int] = None,
    ) -> int:
        """통합 검색 결과를 DB에 저장

        Args:
            results: UnifiedSearchResult (paper_search_service에서 반환)
            db: DB 세션
            allergen_code: 알러젠 코드 (알러지 검색인 경우)
            user_id: 검색한 사용자 ID

        Returns:
            새로 저장된 논문 수
        """
        new_count = 0

        for paper_dc in results.papers:
            try:
                saved = self.save_paper(paper_dc, db, allergen_code=allergen_code)
                if saved:
                    new_count += 1
            except Exception as e:
                logger.warning(f"논문 저장 실패 (title={paper_dc.title[:50]}): {e}")
                continue

        # SearchHistory 레코드 생성
        history = SearchHistory(
            query=results.query,
            allergen_code=allergen_code,
            source="both",
            result_count=results.total_unique,
            new_papers_saved=new_count,
            search_time_ms=results.search_time_ms,
            user_id=user_id,
        )
        db.add(history)

        try:
            db.commit()
        except Exception as e:
            logger.error(f"검색 이력 저장 실패: {e}")
            db.rollback()

        logger.info(
            f"검색 결과 저장 완료: query={results.query}, "
            f"total={results.total_unique}, new={new_count}"
        )
        return new_count

    def save_paper(
        self,
        paper_dc: PaperDC,
        db: Session,
        allergen_code: Optional[str] = None,
    ) -> bool:
        """단일 논문 저장 (중복 검사 포함)

        Returns:
            True if new paper was saved, False if duplicate was updated
        """
        existing = self.find_duplicate(paper_dc, db)

        if existing:
            # 기존 논문 정보 갱신
            PaperMapper.update_orm_from_dc(existing, paper_dc)
            db.flush()
            return False

        # 신규 논문 저장
        paper_orm = PaperMapper.dc_to_orm(paper_dc)

        # PaperLinkExtractor로 알러젠 링크 자동 생성
        paper_type = self._extractor.detect_paper_type(
            paper_dc.title, paper_dc.abstract or ""
        )
        paper_orm.paper_type = paper_type

        db.add(paper_orm)
        db.flush()  # paper_orm.id 생성

        # 알러젠 링크 추출 및 저장
        extracted_links = self._extractor.extract_links(
            title=paper_dc.title,
            abstract=paper_dc.abstract or "",
            keywords=paper_dc.keywords,
            target_allergen=allergen_code,
        )

        for link in extracted_links:
            allergen_link = PaperAllergenLink(
                paper_id=paper_orm.id,
                allergen_code=link.allergen_code,
                link_type=link.link_type,
                specific_item=link.specific_item,
                relevance_score=link.relevance_score,
                note=f"Auto-extracted: {link.matched_keyword}",
            )
            db.add(allergen_link)

        return True

    def find_duplicate(self, paper_dc: PaperDC, db: Session) -> Optional[PaperORM]:
        """중복 논문 검사 (DOI → PMID → S2 ID → 제목 유사도)"""

        # 1. DOI로 검색
        if paper_dc.doi:
            existing = db.query(PaperORM).filter(
                func.lower(PaperORM.doi) == paper_dc.doi.lower()
            ).first()
            if existing:
                return existing

        # 2. PMID로 검색
        if paper_dc.source == PaperSource.PUBMED and paper_dc.source_id:
            existing = db.query(PaperORM).filter(
                PaperORM.pmid == paper_dc.source_id
            ).first()
            if existing:
                return existing

        # 3. Semantic Scholar ID로 검색
        if paper_dc.source == PaperSource.SEMANTIC_SCHOLAR and paper_dc.source_id:
            existing = db.query(PaperORM).filter(
                PaperORM.semantic_scholar_id == paper_dc.source_id
            ).first()
            if existing:
                return existing

        # 4. 제목 유사도 (정확 일치)
        if paper_dc.title:
            existing = db.query(PaperORM).filter(
                func.lower(PaperORM.title) == paper_dc.title.lower().strip()
            ).first()
            if existing:
                return existing

        return None

    def search_local(
        self,
        query: str,
        db: Session,
        allergen_code: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> list[PaperORM]:
        """로컬 DB에서 논문 검색

        Args:
            query: 검색어
            db: DB 세션
            allergen_code: 알러젠 코드 필터
            limit: 최대 결과 수
            offset: 오프셋

        Returns:
            ORM Paper 목록
        """
        q = db.query(PaperORM)

        # 알러젠 코드 필터
        if allergen_code:
            q = q.join(PaperAllergenLink).filter(
                PaperAllergenLink.allergen_code == allergen_code
            )

        # 텍스트 검색 (제목 + 초록)
        if query:
            search_term = f"%{query}%"
            q = q.filter(
                or_(
                    PaperORM.title.ilike(search_term),
                    PaperORM.abstract.ilike(search_term),
                )
            )

        q = q.order_by(PaperORM.year.desc().nullslast(), PaperORM.id.desc())
        return q.offset(offset).limit(limit).all()

    def get_search_history(
        self,
        db: Session,
        limit: int = 50,
        offset: int = 0,
    ) -> list[SearchHistory]:
        """검색 이력 조회"""
        return (
            db.query(SearchHistory)
            .order_by(SearchHistory.created_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )
