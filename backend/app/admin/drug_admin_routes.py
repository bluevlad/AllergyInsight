"""관리자 약물 관리 대시보드 API.

Phase 1 구성:
- 수집 현황 (drug_ingest_cursors + drug_products 집계)
- 제품 목록/상세 (raw snapshot 포함)
- 미매핑 성분 큐 (unmapped_ingredients)
- 병태생리 ↔ ATC 엣지 감수
- 알러젠(symptom) ↔ 병태생리 엣지 감수

모두 super_admin 전용. 수집 실행(POST /drug-ingest/run)은
drug_ingest_routes.py 에 별도 정의.
"""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..database.connection import get_db
from ..database.allergen_models import AllergenMaster
from ..database.drug_models import (
    DrugIngestCursor,
    DrugProduct,
    DrugSourceRaw,
    PathophysAtc,
    Pathophysiology,
    SymptomPathophys,
    UnmappedIngredient,
)
from ..database.models import User
from ..utils.timezone import utc_now
from .dependencies import require_super_admin

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/drugs", tags=["admin-drugs"])


# ============================================================================
# 수집 현황
# ============================================================================


class SourceStatusDto(BaseModel):
    source: str
    product_count: int
    raw_count: int
    last_updated_at: datetime | None
    last_run_at: datetime | None
    last_status: str | None
    last_error: str | None


class DrugStatusResponse(BaseModel):
    total_products: int
    total_raws: int
    total_pathophys: int
    pathophys_atc_edges: int
    symptom_pathophys_edges: int
    unmapped_pending: int
    sources: list[SourceStatusDto]


@router.get("/status", response_model=DrugStatusResponse)
async def get_drug_status(
    current_user: User = Depends(require_super_admin),
    db: Session = Depends(get_db),
) -> DrugStatusResponse:
    """수집 현황 요약. 첫 화면 카드에서 사용."""
    product_by_source = dict(
        db.query(DrugProduct.source, func.count(DrugProduct.id))
        .group_by(DrugProduct.source)
        .all()
    )
    raw_by_source = dict(
        db.query(DrugSourceRaw.source, func.count(DrugSourceRaw.id))
        .group_by(DrugSourceRaw.source)
        .all()
    )

    cursors = db.query(DrugIngestCursor).all()
    seen = set()
    sources: list[SourceStatusDto] = []
    for c in cursors:
        seen.add(c.source)
        sources.append(
            SourceStatusDto(
                source=c.source,
                product_count=product_by_source.get(c.source, 0),
                raw_count=raw_by_source.get(c.source, 0),
                last_updated_at=c.last_updated_at,
                last_run_at=c.last_run_at,
                last_status=c.last_status,
                last_error=c.last_error,
            )
        )
    for src in sorted(set(product_by_source) - seen):
        sources.append(
            SourceStatusDto(
                source=src,
                product_count=product_by_source.get(src, 0),
                raw_count=raw_by_source.get(src, 0),
                last_updated_at=None,
                last_run_at=None,
                last_status=None,
                last_error=None,
            )
        )

    total_products = sum(product_by_source.values())
    total_raws = sum(raw_by_source.values())
    total_pathophys = db.query(func.count(Pathophysiology.id)).scalar() or 0
    pathophys_atc_edges = db.query(func.count(PathophysAtc.id)).scalar() or 0
    symptom_pathophys_edges = db.query(func.count(SymptomPathophys.id)).scalar() or 0
    unmapped_pending = (
        db.query(func.count(UnmappedIngredient.id))
        .filter(UnmappedIngredient.resolved == False)  # noqa: E712
        .scalar()
        or 0
    )

    return DrugStatusResponse(
        total_products=total_products,
        total_raws=total_raws,
        total_pathophys=total_pathophys,
        pathophys_atc_edges=pathophys_atc_edges,
        symptom_pathophys_edges=symptom_pathophys_edges,
        unmapped_pending=unmapped_pending,
        sources=sources,
    )


# ============================================================================
# 제품 목록 / 상세
# ============================================================================


class DrugProductListItem(BaseModel):
    id: int
    source: str
    source_product_id: str
    name_kr: str | None
    name_en: str | None
    atc_code: str | None
    rxcui: str | None
    product_type: str
    is_prescription: bool
    routes: Any | None
    updated_at: datetime


class DrugProductListResponse(BaseModel):
    items: list[DrugProductListItem]
    total: int
    page: int
    page_size: int


@router.get("/products", response_model=DrugProductListResponse)
async def list_drug_products(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    source: str | None = None,
    atc_prefix: str | None = None,
    search: str | None = None,
    current_user: User = Depends(require_super_admin),
    db: Session = Depends(get_db),
) -> DrugProductListResponse:
    """제품 목록. 소스/ATC prefix/검색어 필터 지원."""
    query = db.query(DrugProduct)

    if source:
        query = query.filter(DrugProduct.source == source)
    if atc_prefix:
        query = query.filter(DrugProduct.atc_code.like(f"{atc_prefix}%"))
    if search:
        like = f"%{search}%"
        query = query.filter(
            (DrugProduct.name_en.ilike(like))
            | (DrugProduct.name_kr.ilike(like))
            | (DrugProduct.source_product_id.ilike(like))
        )

    total = query.count()
    offset = (page - 1) * page_size
    rows = (
        query.order_by(DrugProduct.updated_at.desc())
        .offset(offset)
        .limit(page_size)
        .all()
    )

    items = [
        DrugProductListItem(
            id=r.id,
            source=r.source,
            source_product_id=r.source_product_id,
            name_kr=r.name_kr,
            name_en=r.name_en,
            atc_code=r.atc_code,
            rxcui=r.rxcui,
            product_type=r.product_type,
            is_prescription=r.is_prescription,
            routes=r.routes,
            updated_at=r.updated_at,
        )
        for r in rows
    ]

    return DrugProductListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    )


class DrugProductDetailResponse(BaseModel):
    id: int
    source: str
    source_product_id: str
    name_kr: str | None
    name_en: str | None
    atc_code: str | None
    rxcui: str | None
    kfda_item_seq: str | None
    product_type: str
    is_prescription: bool
    routes: Any | None
    indications: str | None
    dosage: str | None
    warnings: str | None
    raw_jsonb: Any | None
    created_at: datetime
    updated_at: datetime


@router.get("/products/{product_id}", response_model=DrugProductDetailResponse)
async def get_drug_product(
    product_id: int,
    current_user: User = Depends(require_super_admin),
    db: Session = Depends(get_db),
) -> DrugProductDetailResponse:
    row = db.query(DrugProduct).filter(DrugProduct.id == product_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="product not found")
    return DrugProductDetailResponse(
        id=row.id,
        source=row.source,
        source_product_id=row.source_product_id,
        name_kr=row.name_kr,
        name_en=row.name_en,
        atc_code=row.atc_code,
        rxcui=row.rxcui,
        kfda_item_seq=row.kfda_item_seq,
        product_type=row.product_type,
        is_prescription=row.is_prescription,
        routes=row.routes,
        indications=row.indications,
        dosage=row.dosage,
        warnings=row.warnings,
        raw_jsonb=row.raw_jsonb,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


# ============================================================================
# 미매핑 성분 큐
# ============================================================================


class UnmappedIngredientDto(BaseModel):
    id: int
    source: str
    source_product_id: str
    ingredient_text: str
    attempted_at: datetime
    resolved: bool
    resolved_rxcui: str | None


class UnmappedListResponse(BaseModel):
    items: list[UnmappedIngredientDto]
    total: int


@router.get("/unmapped", response_model=UnmappedListResponse)
async def list_unmapped(
    resolved: bool | None = Query(default=False),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    current_user: User = Depends(require_super_admin),
    db: Session = Depends(get_db),
) -> UnmappedListResponse:
    query = db.query(UnmappedIngredient)
    if resolved is not None:
        query = query.filter(UnmappedIngredient.resolved == resolved)

    total = query.count()
    rows = (
        query.order_by(UnmappedIngredient.attempted_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return UnmappedListResponse(
        items=[
            UnmappedIngredientDto(
                id=r.id,
                source=r.source,
                source_product_id=r.source_product_id,
                ingredient_text=r.ingredient_text,
                attempted_at=r.attempted_at,
                resolved=r.resolved,
                resolved_rxcui=r.resolved_rxcui,
            )
            for r in rows
        ],
        total=total,
    )


class ResolveUnmappedRequest(BaseModel):
    rxcui: str | None = Field(
        default=None,
        description="지정할 RxCUI. None 이면 보류 상태로 완료 처리.",
    )


@router.post("/unmapped/{unmapped_id}/resolve")
async def resolve_unmapped(
    unmapped_id: int,
    payload: ResolveUnmappedRequest,
    current_user: User = Depends(require_super_admin),
    db: Session = Depends(get_db),
):
    row = db.query(UnmappedIngredient).filter(UnmappedIngredient.id == unmapped_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="unmapped entry not found")
    row.resolved = True
    row.resolved_rxcui = payload.rxcui
    db.commit()
    return {"message": "resolved", "id": unmapped_id, "rxcui": payload.rxcui}


# ============================================================================
# 병태생리 목록 + ATC 엣지 감수
# ============================================================================


class PathophysDto(BaseModel):
    id: int
    code: str
    name_kr: str
    name_en: str
    description: str | None
    reference_pmids: Any | None
    atc_edge_count: int
    symptom_edge_count: int


@router.get("/pathophys", response_model=list[PathophysDto])
async def list_pathophys(
    current_user: User = Depends(require_super_admin),
    db: Session = Depends(get_db),
) -> list[PathophysDto]:
    rows = db.query(Pathophysiology).order_by(Pathophysiology.code).all()

    atc_counts = dict(
        db.query(PathophysAtc.pathophys_id, func.count(PathophysAtc.id))
        .group_by(PathophysAtc.pathophys_id)
        .all()
    )
    symptom_counts = dict(
        db.query(SymptomPathophys.pathophys_id, func.count(SymptomPathophys.id))
        .group_by(SymptomPathophys.pathophys_id)
        .all()
    )

    return [
        PathophysDto(
            id=r.id,
            code=r.code,
            name_kr=r.name_kr,
            name_en=r.name_en,
            description=r.description,
            reference_pmids=r.reference_pmids,
            atc_edge_count=atc_counts.get(r.id, 0),
            symptom_edge_count=symptom_counts.get(r.id, 0),
        )
        for r in rows
    ]


class PathophysAtcEdgeDto(BaseModel):
    id: int
    pathophys_id: int
    pathophys_code: str
    atc_prefix: str
    role: str
    reference_pmids: Any | None
    is_verified: bool
    verified_by: str | None
    verified_at: datetime | None
    review_comment: str | None
    created_at: datetime


@router.get("/pathophys/{pathophys_id}/atc", response_model=list[PathophysAtcEdgeDto])
async def list_pathophys_atc_edges(
    pathophys_id: int,
    current_user: User = Depends(require_super_admin),
    db: Session = Depends(get_db),
) -> list[PathophysAtcEdgeDto]:
    pathophys = db.query(Pathophysiology).filter(Pathophysiology.id == pathophys_id).first()
    if not pathophys:
        raise HTTPException(status_code=404, detail="pathophys not found")
    rows = (
        db.query(PathophysAtc)
        .filter(PathophysAtc.pathophys_id == pathophys_id)
        .order_by(PathophysAtc.role, PathophysAtc.atc_prefix)
        .all()
    )
    return [
        PathophysAtcEdgeDto(
            id=r.id,
            pathophys_id=r.pathophys_id,
            pathophys_code=pathophys.code,
            atc_prefix=r.atc_prefix,
            role=r.role,
            reference_pmids=r.reference_pmids,
            is_verified=r.is_verified,
            verified_by=r.verified_by,
            verified_at=r.verified_at,
            review_comment=r.review_comment,
            created_at=r.created_at,
        )
        for r in rows
    ]


class CreatePathophysAtcRequest(BaseModel):
    atc_prefix: str = Field(min_length=1, max_length=10)
    role: str = Field(pattern="^(first_line|adjunct|refractory)$")
    reference_pmids: list[int] | None = None
    review_comment: str | None = None


@router.post("/pathophys/{pathophys_id}/atc", response_model=PathophysAtcEdgeDto)
async def create_pathophys_atc_edge(
    pathophys_id: int,
    payload: CreatePathophysAtcRequest,
    current_user: User = Depends(require_super_admin),
    db: Session = Depends(get_db),
) -> PathophysAtcEdgeDto:
    pathophys = db.query(Pathophysiology).filter(Pathophysiology.id == pathophys_id).first()
    if not pathophys:
        raise HTTPException(status_code=404, detail="pathophys not found")

    existing = (
        db.query(PathophysAtc)
        .filter(
            PathophysAtc.pathophys_id == pathophys_id,
            PathophysAtc.atc_prefix == payload.atc_prefix,
            PathophysAtc.role == payload.role,
        )
        .first()
    )
    if existing:
        raise HTTPException(status_code=409, detail="edge already exists")

    row = PathophysAtc(
        pathophys_id=pathophys_id,
        atc_prefix=payload.atc_prefix,
        role=payload.role,
        reference_pmids=payload.reference_pmids,
        review_comment=payload.review_comment,
        is_verified=False,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return PathophysAtcEdgeDto(
        id=row.id,
        pathophys_id=row.pathophys_id,
        pathophys_code=pathophys.code,
        atc_prefix=row.atc_prefix,
        role=row.role,
        reference_pmids=row.reference_pmids,
        is_verified=row.is_verified,
        verified_by=row.verified_by,
        verified_at=row.verified_at,
        review_comment=row.review_comment,
        created_at=row.created_at,
    )


@router.delete("/pathophys/atc/{edge_id}")
async def delete_pathophys_atc_edge(
    edge_id: int,
    current_user: User = Depends(require_super_admin),
    db: Session = Depends(get_db),
):
    row = db.query(PathophysAtc).filter(PathophysAtc.id == edge_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="edge not found")
    db.delete(row)
    db.commit()
    return {"message": "deleted", "id": edge_id}


@router.post("/pathophys/atc/{edge_id}/verify", response_model=PathophysAtcEdgeDto)
async def verify_pathophys_atc_edge(
    edge_id: int,
    current_user: User = Depends(require_super_admin),
    db: Session = Depends(get_db),
) -> PathophysAtcEdgeDto:
    row = db.query(PathophysAtc).filter(PathophysAtc.id == edge_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="edge not found")
    row.is_verified = not row.is_verified
    if row.is_verified:
        row.verified_by = current_user.name or current_user.email
        row.verified_at = utc_now()
    else:
        row.verified_by = None
        row.verified_at = None
    db.commit()
    pathophys = db.query(Pathophysiology).filter(Pathophysiology.id == row.pathophys_id).first()
    return PathophysAtcEdgeDto(
        id=row.id,
        pathophys_id=row.pathophys_id,
        pathophys_code=pathophys.code if pathophys else "",
        atc_prefix=row.atc_prefix,
        role=row.role,
        reference_pmids=row.reference_pmids,
        is_verified=row.is_verified,
        verified_by=row.verified_by,
        verified_at=row.verified_at,
        review_comment=row.review_comment,
        created_at=row.created_at,
    )


# ============================================================================
# 알러젠 ↔ 병태생리 엣지
# ============================================================================


class SymptomPathophysEdgeDto(BaseModel):
    id: int
    symptom_id: int
    symptom_code: str
    symptom_name_kr: str
    pathophys_id: int
    pathophys_code: str
    weight: int
    is_verified: bool
    verified_by: str | None
    verified_at: datetime | None
    review_comment: str | None


@router.get("/pathophys/symptom-edges", response_model=list[SymptomPathophysEdgeDto])
async def list_symptom_pathophys_edges(
    pathophys_id: int | None = None,
    symptom_id: int | None = None,
    current_user: User = Depends(require_super_admin),
    db: Session = Depends(get_db),
) -> list[SymptomPathophysEdgeDto]:
    rows = (
        db.query(SymptomPathophys, AllergenMaster, Pathophysiology)
        .join(AllergenMaster, SymptomPathophys.symptom_id == AllergenMaster.id)
        .join(Pathophysiology, SymptomPathophys.pathophys_id == Pathophysiology.id)
    )
    if pathophys_id is not None:
        rows = rows.filter(SymptomPathophys.pathophys_id == pathophys_id)
    if symptom_id is not None:
        rows = rows.filter(SymptomPathophys.symptom_id == symptom_id)

    return [
        SymptomPathophysEdgeDto(
            id=edge.id,
            symptom_id=allergen.id,
            symptom_code=allergen.code,
            symptom_name_kr=allergen.name_kr,
            pathophys_id=pathophys.id,
            pathophys_code=pathophys.code,
            weight=edge.weight,
            is_verified=edge.is_verified,
            verified_by=edge.verified_by,
            verified_at=edge.verified_at,
            review_comment=edge.review_comment,
        )
        for edge, allergen, pathophys in rows.all()
    ]


class CreateSymptomPathophysRequest(BaseModel):
    symptom_code: str = Field(description="AllergenMaster.code (예: f13, d1)")
    pathophys_id: int
    weight: int = Field(ge=1, le=5, default=3)
    review_comment: str | None = None


@router.post("/pathophys/symptom-edges", response_model=SymptomPathophysEdgeDto)
async def create_symptom_pathophys_edge(
    payload: CreateSymptomPathophysRequest,
    current_user: User = Depends(require_super_admin),
    db: Session = Depends(get_db),
) -> SymptomPathophysEdgeDto:
    allergen = db.query(AllergenMaster).filter(AllergenMaster.code == payload.symptom_code).first()
    if not allergen:
        raise HTTPException(status_code=404, detail=f"allergen not found: {payload.symptom_code}")
    pathophys = db.query(Pathophysiology).filter(Pathophysiology.id == payload.pathophys_id).first()
    if not pathophys:
        raise HTTPException(status_code=404, detail="pathophys not found")

    existing = (
        db.query(SymptomPathophys)
        .filter(
            SymptomPathophys.symptom_id == allergen.id,
            SymptomPathophys.pathophys_id == payload.pathophys_id,
        )
        .first()
    )
    if existing:
        raise HTTPException(status_code=409, detail="edge already exists")

    edge = SymptomPathophys(
        symptom_id=allergen.id,
        pathophys_id=payload.pathophys_id,
        weight=payload.weight,
        review_comment=payload.review_comment,
        is_verified=False,
    )
    db.add(edge)
    db.commit()
    db.refresh(edge)

    return SymptomPathophysEdgeDto(
        id=edge.id,
        symptom_id=allergen.id,
        symptom_code=allergen.code,
        symptom_name_kr=allergen.name_kr,
        pathophys_id=pathophys.id,
        pathophys_code=pathophys.code,
        weight=edge.weight,
        is_verified=edge.is_verified,
        verified_by=edge.verified_by,
        verified_at=edge.verified_at,
        review_comment=edge.review_comment,
    )


@router.delete("/pathophys/symptom-edges/{edge_id}")
async def delete_symptom_pathophys_edge(
    edge_id: int,
    current_user: User = Depends(require_super_admin),
    db: Session = Depends(get_db),
):
    row = db.query(SymptomPathophys).filter(SymptomPathophys.id == edge_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="edge not found")
    db.delete(row)
    db.commit()
    return {"message": "deleted", "id": edge_id}


@router.post("/pathophys/symptom-edges/{edge_id}/verify", response_model=SymptomPathophysEdgeDto)
async def verify_symptom_pathophys_edge(
    edge_id: int,
    current_user: User = Depends(require_super_admin),
    db: Session = Depends(get_db),
) -> SymptomPathophysEdgeDto:
    edge = db.query(SymptomPathophys).filter(SymptomPathophys.id == edge_id).first()
    if not edge:
        raise HTTPException(status_code=404, detail="edge not found")
    edge.is_verified = not edge.is_verified
    if edge.is_verified:
        edge.verified_by = current_user.name or current_user.email
        edge.verified_at = utc_now()
    else:
        edge.verified_by = None
        edge.verified_at = None
    db.commit()

    allergen = db.query(AllergenMaster).filter(AllergenMaster.id == edge.symptom_id).first()
    pathophys = db.query(Pathophysiology).filter(Pathophysiology.id == edge.pathophys_id).first()
    return SymptomPathophysEdgeDto(
        id=edge.id,
        symptom_id=edge.symptom_id,
        symptom_code=allergen.code if allergen else "",
        symptom_name_kr=allergen.name_kr if allergen else "",
        pathophys_id=edge.pathophys_id,
        pathophys_code=pathophys.code if pathophys else "",
        weight=edge.weight,
        is_verified=edge.is_verified,
        verified_by=edge.verified_by,
        verified_at=edge.verified_at,
        review_comment=edge.review_comment,
    )
