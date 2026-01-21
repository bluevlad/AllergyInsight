"""Paper Routes - Research paper management"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_

from ..database.connection import get_db
from ..database.models import User, Paper, PaperAllergenLink
from .dependencies import require_auth, require_admin
from .schemas import (
    PaperCreate, PaperUpdate, PaperResponse, PaperBrief,
    PaperListResponse, PaperAllergenLinkCreate, PaperAllergenLinkResponse
)
from ..services.paper_link_extractor import get_extractor, ExtractedLink

router = APIRouter(prefix="/papers", tags=["Papers"])


# ============================================================================
# Paper CRUD
# ============================================================================

@router.post("", response_model=PaperResponse)
async def create_paper(
    paper_data: PaperCreate,
    auto_extract_links: bool = Query(True, description="자동으로 키워드 기반 링크 추출"),
    user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Create a new paper (requires auth)"""
    # Check for duplicate PMID or DOI
    if paper_data.pmid:
        existing = db.query(Paper).filter(Paper.pmid == paper_data.pmid).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Paper with PMID {paper_data.pmid} already exists"
            )

    if paper_data.doi:
        existing = db.query(Paper).filter(Paper.doi == paper_data.doi).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Paper with DOI {paper_data.doi} already exists"
            )

    # Auto-detect paper type if not provided
    extractor = get_extractor()
    detected_type = paper_data.paper_type
    if not detected_type and paper_data.abstract:
        detected_type = extractor.detect_paper_type(
            paper_data.title or "",
            paper_data.abstract or ""
        )

    # Create paper
    paper = Paper(
        pmid=paper_data.pmid,
        doi=paper_data.doi,
        title=paper_data.title,
        title_kr=paper_data.title_kr,
        authors=paper_data.authors,
        journal=paper_data.journal,
        year=paper_data.year,
        abstract=paper_data.abstract,
        abstract_kr=paper_data.abstract_kr,
        url=paper_data.url,
        pdf_url=paper_data.pdf_url,
        paper_type=detected_type or "research",
        created_by=user.id,
        is_verified=(user.role == "admin")  # Auto-verify if admin
    )
    db.add(paper)
    db.flush()  # Get paper.id

    # Add manually provided allergen links
    if paper_data.allergen_links:
        for link_data in paper_data.allergen_links:
            link = PaperAllergenLink(
                paper_id=paper.id,
                allergen_code=link_data.allergen_code,
                link_type=link_data.link_type,
                specific_item=link_data.specific_item,
                relevance_score=link_data.relevance_score,
                note=link_data.note
            )
            db.add(link)

    # Auto-extract links from abstract
    if auto_extract_links and paper_data.abstract:
        extracted_links = extractor.extract_links(
            title=paper_data.title or "",
            abstract=paper_data.abstract or "",
        )
        for ext_link in extracted_links:
            # Check if similar link already exists
            existing_link = any(
                l.allergen_code == ext_link.allergen_code and
                l.link_type == ext_link.link_type and
                l.specific_item == ext_link.specific_item
                for l in (paper_data.allergen_links or [])
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

    return paper


@router.get("", response_model=PaperListResponse)
async def list_papers(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    allergen: Optional[str] = None,
    link_type: Optional[str] = None,
    paper_type: Optional[str] = None,
    year: Optional[int] = None,
    search: Optional[str] = None,
    verified_only: bool = False,
    db: Session = Depends(get_db)
):
    """List papers with filtering and pagination"""
    query = db.query(Paper)

    # Filter by allergen
    if allergen:
        query = query.join(PaperAllergenLink).filter(
            PaperAllergenLink.allergen_code == allergen
        )

    # Filter by link type
    if link_type:
        if not allergen:  # Need to join if not already joined
            query = query.join(PaperAllergenLink)
        query = query.filter(PaperAllergenLink.link_type == link_type)

    # Filter by paper type
    if paper_type:
        query = query.filter(Paper.paper_type == paper_type)

    # Filter by year
    if year:
        query = query.filter(Paper.year == year)

    # Filter verified only
    if verified_only:
        query = query.filter(Paper.is_verified == True)

    # Search in title, title_kr, abstract
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                Paper.title.ilike(search_term),
                Paper.title_kr.ilike(search_term),
                Paper.abstract.ilike(search_term),
                Paper.authors.ilike(search_term)
            )
        )

    # Get total count
    total = query.distinct().count()

    # Pagination
    offset = (page - 1) * size
    papers = query.distinct().order_by(Paper.year.desc(), Paper.id.desc()).offset(offset).limit(size).all()

    return PaperListResponse(
        items=papers,
        total=total,
        page=page,
        size=size
    )


@router.get("/{paper_id}", response_model=PaperResponse)
async def get_paper(
    paper_id: int,
    db: Session = Depends(get_db)
):
    """Get a paper by ID"""
    paper = db.query(Paper).filter(Paper.id == paper_id).first()
    if not paper:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Paper not found"
        )
    return paper


@router.put("/{paper_id}", response_model=PaperResponse)
async def update_paper(
    paper_id: int,
    paper_data: PaperUpdate,
    user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Update a paper (requires auth)"""
    paper = db.query(Paper).filter(Paper.id == paper_id).first()
    if not paper:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Paper not found"
        )

    # Only admin or creator can update
    if user.role != "admin" and paper.created_by != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied"
        )

    # Update fields
    update_data = paper_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(paper, field, value)

    db.commit()
    db.refresh(paper)

    return paper


@router.delete("/{paper_id}")
async def delete_paper(
    paper_id: int,
    user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Delete a paper (admin only)"""
    paper = db.query(Paper).filter(Paper.id == paper_id).first()
    if not paper:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Paper not found"
        )

    db.delete(paper)
    db.commit()

    return {"message": "Paper deleted"}


# ============================================================================
# Allergen Link Management
# ============================================================================

@router.post("/{paper_id}/links", response_model=PaperAllergenLinkResponse)
async def add_allergen_link(
    paper_id: int,
    link_data: PaperAllergenLinkCreate,
    user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Add allergen link to a paper"""
    paper = db.query(Paper).filter(Paper.id == paper_id).first()
    if not paper:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Paper not found"
        )

    link = PaperAllergenLink(
        paper_id=paper_id,
        allergen_code=link_data.allergen_code,
        link_type=link_data.link_type,
        specific_item=link_data.specific_item,
        relevance_score=link_data.relevance_score,
        note=link_data.note
    )
    db.add(link)
    db.commit()
    db.refresh(link)

    return link


@router.delete("/{paper_id}/links/{link_id}")
async def remove_allergen_link(
    paper_id: int,
    link_id: int,
    user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Remove allergen link from a paper"""
    link = db.query(PaperAllergenLink).filter(
        PaperAllergenLink.id == link_id,
        PaperAllergenLink.paper_id == paper_id
    ).first()

    if not link:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Link not found"
        )

    db.delete(link)
    db.commit()

    return {"message": "Link removed"}


# ============================================================================
# Citation Queries
# ============================================================================

@router.get("/citations/{allergen_code}", response_model=List[PaperBrief])
async def get_citations_for_allergen(
    allergen_code: str,
    link_type: Optional[str] = None,
    specific_item: Optional[str] = None,
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db)
):
    """Get papers citing specific allergen information"""
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


@router.get("/citations/by-type/{link_type}", response_model=List[PaperBrief])
async def get_citations_by_type(
    link_type: str,
    allergen_code: Optional[str] = None,
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db)
):
    """Get papers by link type (symptom, dietary, etc.)"""
    query = db.query(Paper).join(PaperAllergenLink).filter(
        PaperAllergenLink.link_type == link_type,
        Paper.is_verified == True
    )

    if allergen_code:
        query = query.filter(PaperAllergenLink.allergen_code == allergen_code)

    papers = query.order_by(
        PaperAllergenLink.relevance_score.desc(),
        Paper.year.desc()
    ).limit(limit).all()

    return papers


# ============================================================================
# Auto Link Extraction
# ============================================================================

@router.post("/{paper_id}/extract-links")
async def extract_links_for_paper(
    paper_id: int,
    replace_existing: bool = Query(False, description="기존 자동추출 링크 교체 여부"),
    user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """기존 논문에서 자동으로 링크 추출"""
    paper = db.query(Paper).filter(Paper.id == paper_id).first()
    if not paper:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Paper not found"
        )

    if not paper.abstract:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Paper has no abstract for extraction"
        )

    extractor = get_extractor()
    extracted_links = extractor.extract_links(
        title=paper.title or "",
        abstract=paper.abstract or "",
    )

    # Remove existing auto-extracted links if requested
    if replace_existing:
        db.query(PaperAllergenLink).filter(
            PaperAllergenLink.paper_id == paper_id,
            PaperAllergenLink.note.like("Auto-extracted:%")
        ).delete(synchronize_session=False)

    # Get existing links to avoid duplicates
    existing_links = db.query(PaperAllergenLink).filter(
        PaperAllergenLink.paper_id == paper_id
    ).all()

    added_count = 0
    for ext_link in extracted_links:
        # Check if similar link already exists
        exists = any(
            l.allergen_code == ext_link.allergen_code and
            l.link_type == ext_link.link_type and
            l.specific_item == ext_link.specific_item
            for l in existing_links
        )
        if not exists:
            link = PaperAllergenLink(
                paper_id=paper_id,
                allergen_code=ext_link.allergen_code,
                link_type=ext_link.link_type,
                specific_item=ext_link.specific_item,
                relevance_score=ext_link.relevance_score,
                note=f"Auto-extracted: {ext_link.matched_keyword}"
            )
            db.add(link)
            added_count += 1

    db.commit()

    return {
        "paper_id": paper_id,
        "extracted_count": len(extracted_links),
        "added_count": added_count,
        "links": [
            {
                "allergen_code": l.allergen_code,
                "link_type": l.link_type,
                "specific_item": l.specific_item,
                "relevance_score": l.relevance_score,
                "matched_keyword": l.matched_keyword
            }
            for l in extracted_links
        ]
    }


@router.post("/extract-links/batch")
async def extract_links_batch(
    paper_ids: List[int] = Query(None, description="논문 ID 목록 (없으면 전체)"),
    replace_existing: bool = Query(False),
    user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """여러 논문에서 일괄 링크 추출 (관리자 전용)"""
    if paper_ids:
        papers = db.query(Paper).filter(Paper.id.in_(paper_ids)).all()
    else:
        papers = db.query(Paper).filter(Paper.abstract.isnot(None)).all()

    extractor = get_extractor()
    results = []

    for paper in papers:
        if not paper.abstract:
            continue

        extracted_links = extractor.extract_links(
            title=paper.title or "",
            abstract=paper.abstract or "",
        )

        if replace_existing:
            db.query(PaperAllergenLink).filter(
                PaperAllergenLink.paper_id == paper.id,
                PaperAllergenLink.note.like("Auto-extracted:%")
            ).delete(synchronize_session=False)

        existing_links = db.query(PaperAllergenLink).filter(
            PaperAllergenLink.paper_id == paper.id
        ).all()

        added_count = 0
        for ext_link in extracted_links:
            exists = any(
                l.allergen_code == ext_link.allergen_code and
                l.link_type == ext_link.link_type and
                l.specific_item == ext_link.specific_item
                for l in existing_links
            )
            if not exists:
                link = PaperAllergenLink(
                    paper_id=paper.id,
                    allergen_code=ext_link.allergen_code,
                    link_type=ext_link.link_type,
                    specific_item=ext_link.specific_item,
                    relevance_score=ext_link.relevance_score,
                    note=f"Auto-extracted: {ext_link.matched_keyword}"
                )
                db.add(link)
                added_count += 1

        results.append({
            "paper_id": paper.id,
            "title": paper.title[:50] + "..." if len(paper.title) > 50 else paper.title,
            "extracted_count": len(extracted_links),
            "added_count": added_count
        })

    db.commit()

    total_added = sum(r["added_count"] for r in results)
    return {
        "processed_count": len(results),
        "total_links_added": total_added,
        "results": results
    }


@router.get("/citations/by-specific-item")
async def get_citations_by_specific_item(
    allergen_code: str,
    specific_item: str,
    link_type: Optional[str] = None,
    limit: int = Query(5, ge=1, le=20),
    db: Session = Depends(get_db)
):
    """특정 항목(증상, 식품 등)에 대한 출처 논문 조회"""
    query = db.query(Paper).join(PaperAllergenLink).filter(
        PaperAllergenLink.allergen_code == allergen_code,
        PaperAllergenLink.specific_item == specific_item,
        Paper.is_verified == True
    )

    if link_type:
        query = query.filter(PaperAllergenLink.link_type == link_type)

    papers = query.order_by(
        PaperAllergenLink.relevance_score.desc(),
        Paper.year.desc()
    ).limit(limit).all()

    return [
        {
            "id": p.id,
            "pmid": p.pmid,
            "title": p.title,
            "title_kr": p.title_kr,
            "authors": p.authors,
            "journal": p.journal,
            "year": p.year,
            "url": p.url,
            "paper_type": p.paper_type
        }
        for p in papers
    ]
