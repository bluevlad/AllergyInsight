"""관리자 전용 약물 정보 수집 API.

POST /api/admin/drug-ingest/run — DrugIngestPipeline 즉시 실행.
super_admin 만 접근 가능. 스케줄러 작업과 동일한 factory 를 쓰므로
수동 실행·재시도·소스별 부분 수집 용도로 사용한다.
"""
from __future__ import annotations

import logging
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..database.connection import get_db
from ..database.models import User
from ..services.drug_ingest.factory import build_default_pipeline
from ..services.drug_ingest.pipeline import IngestResult
from .dependencies import require_super_admin

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/drug-ingest", tags=["admin-drug-ingest"])


class DrugIngestRunRequest(BaseModel):
    source: str | None = Field(
        default=None,
        description="특정 소스만 실행. None 이면 모든 소스 순차 실행.",
    )
    limit: int | None = Field(
        default=None,
        ge=1,
        le=10_000,
        description="수집할 제품 수 상한 (디버그·스모크 테스트용).",
    )


class IngestResultDto(BaseModel):
    source: str
    run_started_at: datetime
    success_count: int
    failed_count: int
    failed_items: list[dict]
    fatal_error: str | None
    ok: bool

    @classmethod
    def from_result(cls, r: IngestResult) -> "IngestResultDto":
        return cls(
            source=r.source,
            run_started_at=r.run_started_at,
            success_count=r.success_count,
            failed_count=len(r.failed_items),
            failed_items=[
                {"source_product_id": pid, "error": err}
                for pid, err in r.failed_items[:20]
            ],
            fatal_error=r.fatal_error,
            ok=r.ok,
        )


class DrugIngestRunResponse(BaseModel):
    results: list[IngestResultDto]


@router.post("/run", response_model=DrugIngestRunResponse)
async def run_drug_ingest(
    payload: DrugIngestRunRequest,
    current_user: User = Depends(require_super_admin),
    db: Session = Depends(get_db),
) -> DrugIngestRunResponse:
    """약물 정보 수집을 즉시 실행 (super_admin 전용)."""
    logger.info(
        "admin.drug_ingest.run user=%s source=%s limit=%s",
        current_user.id,
        payload.source,
        payload.limit,
    )
    try:
        pipeline = build_default_pipeline()
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    if payload.source is not None and payload.source not in pipeline.source_names:
        raise HTTPException(
            status_code=400,
            detail=f"unknown source: {payload.source}. available={pipeline.source_names}",
        )

    if payload.source:
        results = [pipeline.run_source(db, payload.source, limit=payload.limit)]
    else:
        results = pipeline.run_all(db, limit=payload.limit)

    return DrugIngestRunResponse(
        results=[IngestResultDto.from_result(r) for r in results]
    )
