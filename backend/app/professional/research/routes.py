"""Professional Research Routes - 논문 검색/Q&A API

의료진을 위한 논문 검색 및 Q&A 기능을 제공합니다.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from pydantic import BaseModel, Field

from ...database.connection import get_db
from ...database.models import User, Paper, PaperAllergenLink
from ...core.auth import require_professional, require_admin
from ...services.paper_link_extractor import get_extractor

router = APIRouter(prefix="/research", tags=["Professional - Research"])


# ============================================================================
# Schemas
# ============================================================================

class PaperSearchRequest(BaseModel):
    """논문 검색 요청"""
    query: str = Field(..., min_length=1, description="검색어")
    allergen_code: Optional[str] = None
    link_type: Optional[str] = None
    paper_type: Optional[str] = None
    year_from: Optional[int] = None
    year_to: Optional[int] = None
    verified_only: bool = True
    page: int = Field(1, ge=1)
    size: int = Field(20, ge=1, le=100)

class PaperBrief(BaseModel):
    """논문 요약 정보"""
    id: int
    pmid: Optional[str]
    doi: Optional[str]
    title: str
    title_kr: Optional[str]
    authors: Optional[str]
    journal: Optional[str]
    year: Optional[int]
    url: Optional[str]
    paper_type: Optional[str]
    is_verified: bool

    class Config:
        from_attributes = True

class PaperDetail(PaperBrief):
    """논문 상세 정보"""
    abstract: Optional[str]
    abstract_kr: Optional[str]
    pdf_url: Optional[str]
    allergen_links: List[dict] = []

class PaperSearchResponse(BaseModel):
    """논문 검색 결과"""
    items: List[PaperBrief]
    total: int
    page: int
    size: int

class PaperCreateRequest(BaseModel):
    """논문 등록 요청"""
    pmid: Optional[str] = None
    doi: Optional[str] = None
    title: str = Field(..., min_length=1)
    title_kr: Optional[str] = None
    authors: Optional[str] = None
    journal: Optional[str] = None
    year: Optional[int] = None
    abstract: Optional[str] = None
    abstract_kr: Optional[str] = None
    url: Optional[str] = None
    pdf_url: Optional[str] = None
    paper_type: Optional[str] = None
    allergen_links: Optional[List[dict]] = None

class QARequest(BaseModel):
    """Q&A 질문 요청"""
    question: str = Field(..., min_length=5, description="질문 내용")
    context_allergens: Optional[List[str]] = Field(None, description="관련 알러젠 코드")

class QAResponse(BaseModel):
    """Q&A 응답"""
    answer: str
    related_papers: List[PaperBrief]
    confidence: float


# ============================================================================
# Endpoints - Paper Search
# ============================================================================

@router.post("/search", response_model=PaperSearchResponse)
async def search_papers(
    request: PaperSearchRequest,
    user: User = Depends(require_professional),
    db: Session = Depends(get_db)
):
    """논문 검색"""
    query = db.query(Paper)

    # 텍스트 검색
    search_term = f"%{request.query}%"
    query = query.filter(
        or_(
            Paper.title.ilike(search_term),
            Paper.title_kr.ilike(search_term),
            Paper.abstract.ilike(search_term),
            Paper.authors.ilike(search_term)
        )
    )

    # 알러젠 필터
    if request.allergen_code:
        query = query.join(PaperAllergenLink).filter(
            PaperAllergenLink.allergen_code == request.allergen_code
        )

    # 링크 타입 필터
    if request.link_type:
        if not request.allergen_code:
            query = query.join(PaperAllergenLink)
        query = query.filter(PaperAllergenLink.link_type == request.link_type)

    # 논문 타입 필터
    if request.paper_type:
        query = query.filter(Paper.paper_type == request.paper_type)

    # 연도 필터
    if request.year_from:
        query = query.filter(Paper.year >= request.year_from)
    if request.year_to:
        query = query.filter(Paper.year <= request.year_to)

    # 검증된 논문만
    if request.verified_only:
        query = query.filter(Paper.is_verified == True)

    total = query.distinct().count()
    offset = (request.page - 1) * request.size
    papers = query.distinct().order_by(
        Paper.year.desc(), Paper.id.desc()
    ).offset(offset).limit(request.size).all()

    return PaperSearchResponse(
        items=papers,
        total=total,
        page=request.page,
        size=request.size
    )


@router.get("/papers", response_model=PaperSearchResponse)
async def list_papers(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    allergen: Optional[str] = None,
    link_type: Optional[str] = None,
    paper_type: Optional[str] = None,
    year: Optional[int] = None,
    search: Optional[str] = None,
    verified_only: bool = True,
    user: User = Depends(require_professional),
    db: Session = Depends(get_db)
):
    """논문 목록 조회"""
    query = db.query(Paper)

    if allergen:
        query = query.join(PaperAllergenLink).filter(
            PaperAllergenLink.allergen_code == allergen
        )

    if link_type:
        if not allergen:
            query = query.join(PaperAllergenLink)
        query = query.filter(PaperAllergenLink.link_type == link_type)

    if paper_type:
        query = query.filter(Paper.paper_type == paper_type)

    if year:
        query = query.filter(Paper.year == year)

    if verified_only:
        query = query.filter(Paper.is_verified == True)

    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                Paper.title.ilike(search_term),
                Paper.title_kr.ilike(search_term),
                Paper.abstract.ilike(search_term)
            )
        )

    total = query.distinct().count()
    offset = (page - 1) * size
    papers = query.distinct().order_by(
        Paper.year.desc(), Paper.id.desc()
    ).offset(offset).limit(size).all()

    return PaperSearchResponse(
        items=papers,
        total=total,
        page=page,
        size=size
    )


@router.get("/papers/{paper_id}", response_model=PaperDetail)
async def get_paper(
    paper_id: int,
    user: User = Depends(require_professional),
    db: Session = Depends(get_db)
):
    """논문 상세 조회"""
    paper = db.query(Paper).filter(Paper.id == paper_id).first()
    if not paper:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="논문을 찾을 수 없습니다"
        )

    # 알러젠 링크 조회
    links = db.query(PaperAllergenLink).filter(
        PaperAllergenLink.paper_id == paper_id
    ).all()

    return PaperDetail(
        id=paper.id,
        pmid=paper.pmid,
        doi=paper.doi,
        title=paper.title,
        title_kr=paper.title_kr,
        authors=paper.authors,
        journal=paper.journal,
        year=paper.year,
        url=paper.url,
        paper_type=paper.paper_type,
        is_verified=paper.is_verified,
        abstract=paper.abstract,
        abstract_kr=paper.abstract_kr,
        pdf_url=paper.pdf_url,
        allergen_links=[
            {
                "id": l.id,
                "allergen_code": l.allergen_code,
                "link_type": l.link_type,
                "specific_item": l.specific_item,
                "relevance_score": l.relevance_score,
                "note": l.note
            }
            for l in links
        ]
    )


@router.post("/papers", response_model=PaperDetail)
async def create_paper(
    data: PaperCreateRequest,
    auto_extract_links: bool = Query(True, description="자동 키워드 추출"),
    user: User = Depends(require_professional),
    db: Session = Depends(get_db)
):
    """논문 등록"""
    # 중복 체크
    if data.pmid:
        existing = db.query(Paper).filter(Paper.pmid == data.pmid).first()
        if existing:
            raise HTTPException(400, f"PMID {data.pmid}가 이미 등록되어 있습니다")

    if data.doi:
        existing = db.query(Paper).filter(Paper.doi == data.doi).first()
        if existing:
            raise HTTPException(400, f"DOI {data.doi}가 이미 등록되어 있습니다")

    # 논문 타입 자동 감지
    extractor = get_extractor()
    detected_type = data.paper_type
    if not detected_type and data.abstract:
        detected_type = extractor.detect_paper_type(
            data.title or "", data.abstract or ""
        )

    paper = Paper(
        pmid=data.pmid,
        doi=data.doi,
        title=data.title,
        title_kr=data.title_kr,
        authors=data.authors,
        journal=data.journal,
        year=data.year,
        abstract=data.abstract,
        abstract_kr=data.abstract_kr,
        url=data.url,
        pdf_url=data.pdf_url,
        paper_type=detected_type or "research",
        created_by=user.id,
        is_verified=(user.role in ["admin", "super_admin"])
    )
    db.add(paper)
    db.flush()

    # 수동 링크 추가
    if data.allergen_links:
        for link_data in data.allergen_links:
            link = PaperAllergenLink(
                paper_id=paper.id,
                allergen_code=link_data.get("allergen_code"),
                link_type=link_data.get("link_type"),
                specific_item=link_data.get("specific_item"),
                relevance_score=link_data.get("relevance_score", 0.5),
                note=link_data.get("note")
            )
            db.add(link)

    # 자동 링크 추출
    if auto_extract_links and data.abstract:
        extracted_links = extractor.extract_links(
            title=data.title or "", abstract=data.abstract or ""
        )
        for ext_link in extracted_links:
            existing_link = any(
                l.get("allergen_code") == ext_link.allergen_code and
                l.get("link_type") == ext_link.link_type and
                l.get("specific_item") == ext_link.specific_item
                for l in (data.allergen_links or [])
            )
            if not existing_link:
                link = PaperAllergenLink(
                    paper_id=paper.id,
                    allergen_code=ext_link.allergen_code,
                    link_type=ext_link.link_type,
                    specific_item=ext_link.specific_item,
                    relevance_score=ext_link.relevance_score,
                    note=f"Auto-extracted: {ext_link.matched_keyword}"
                )
                db.add(link)

    db.commit()
    db.refresh(paper)

    # 링크 조회
    links = db.query(PaperAllergenLink).filter(
        PaperAllergenLink.paper_id == paper.id
    ).all()

    return PaperDetail(
        id=paper.id,
        pmid=paper.pmid,
        doi=paper.doi,
        title=paper.title,
        title_kr=paper.title_kr,
        authors=paper.authors,
        journal=paper.journal,
        year=paper.year,
        url=paper.url,
        paper_type=paper.paper_type,
        is_verified=paper.is_verified,
        abstract=paper.abstract,
        abstract_kr=paper.abstract_kr,
        pdf_url=paper.pdf_url,
        allergen_links=[
            {
                "id": l.id,
                "allergen_code": l.allergen_code,
                "link_type": l.link_type,
                "specific_item": l.specific_item,
                "relevance_score": l.relevance_score,
                "note": l.note
            }
            for l in links
        ]
    )


# ============================================================================
# Endpoints - Citations
# ============================================================================

@router.get("/citations/{allergen_code}", response_model=List[PaperBrief])
async def get_citations_for_allergen(
    allergen_code: str,
    link_type: Optional[str] = None,
    specific_item: Optional[str] = None,
    limit: int = Query(10, ge=1, le=50),
    user: User = Depends(require_professional),
    db: Session = Depends(get_db)
):
    """특정 알러젠 관련 논문 조회"""
    query = db.query(Paper).join(PaperAllergenLink).filter(
        PaperAllergenLink.allergen_code == allergen_code,
        Paper.is_verified == True
    )

    if link_type:
        query = query.filter(PaperAllergenLink.link_type == link_type)

    if specific_item:
        query = query.filter(
            PaperAllergenLink.specific_item.ilike(f"%{specific_item}%")
        )

    papers = query.order_by(
        PaperAllergenLink.relevance_score.desc(),
        Paper.year.desc()
    ).limit(limit).all()

    return papers


# ============================================================================
# Endpoints - Q&A (Placeholder)
# ============================================================================

@router.post("/qa", response_model=QAResponse)
async def ask_question(
    request: QARequest,
    user: User = Depends(require_professional),
    db: Session = Depends(get_db)
):
    """Q&A 질문 (AI 기반 - 추후 구현)

    현재는 관련 논문 검색 기반의 단순 응답을 제공합니다.
    향후 LLM 기반 Q&A 시스템으로 확장 예정입니다.
    """
    # 간단한 키워드 기반 논문 검색
    search_term = f"%{request.question}%"
    query = db.query(Paper).filter(
        or_(
            Paper.title.ilike(search_term),
            Paper.title_kr.ilike(search_term),
            Paper.abstract.ilike(search_term)
        ),
        Paper.is_verified == True
    )

    # 알러젠 컨텍스트가 있으면 필터 추가
    if request.context_allergens:
        query = query.join(PaperAllergenLink).filter(
            PaperAllergenLink.allergen_code.in_(request.context_allergens)
        )

    papers = query.order_by(Paper.year.desc()).limit(5).all()

    # 간단한 응답 생성
    if papers:
        answer = f"'{request.question}'에 관련된 {len(papers)}개의 논문을 찾았습니다. "
        answer += "아래 논문들을 참고하시기 바랍니다."
        confidence = 0.7
    else:
        answer = f"'{request.question}'에 대한 관련 논문을 찾지 못했습니다. "
        answer += "다른 키워드로 검색해 보시기 바랍니다."
        confidence = 0.3

    return QAResponse(
        answer=answer,
        related_papers=papers,
        confidence=confidence
    )
