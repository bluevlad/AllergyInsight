"""운영자용 역량 고도화 제안 admin API — Phase 4.

뉴스레터 수요 분석으로 자동 생성된 EvolutionProposal 을 운영자가 검토·승인/반려한다.
super_admin 전용. /api/admin/newsletter/* 로 노출된다.
"""
from __future__ import annotations

import logging
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..database.connection import get_db
from ..database.models import User
from ..database.persona_newsletter_models import EvolutionProposal
from ..services.persona_newsletter import evolution
from ..utils.timezone import utc_now
from .dependencies import require_super_admin

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/newsletter", tags=["Newsletter Evolution"])

_VALID_STATUS = ("pending", "approved", "rejected")


class ReviewBody(BaseModel):
    note: Optional[str] = None


def _serialize(p: EvolutionProposal) -> dict[str, Any]:
    return {
        "id": p.id,
        "proposal_type": p.proposal_type,
        "title": p.title,
        "recommended_action": p.recommended_action,
        "priority": p.priority,
        "status": p.status,
        "evidence": p.evidence,
        "period_start": p.period_start.isoformat() if p.period_start else None,
        "period_end": p.period_end.isoformat() if p.period_end else None,
        "reviewed_by": p.reviewed_by,
        "review_note": p.review_note,
        "reviewed_at": p.reviewed_at.isoformat() if p.reviewed_at else None,
        "created_at": p.created_at.isoformat() if p.created_at else None,
    }


@router.get("/evolution-proposals")
def list_proposals(
    status: Optional[str] = Query(None, description="pending|approved|rejected"),
    limit: int = Query(50, ge=1, le=200),
    user: User = Depends(require_super_admin),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """고도화 제안 목록 (status 필터)."""
    query = db.query(EvolutionProposal)
    if status:
        if status not in _VALID_STATUS:
            raise HTTPException(status_code=422, detail="유효하지 않은 status")
        query = query.filter(EvolutionProposal.status == status)
    rows = (
        query.order_by(EvolutionProposal.created_at.desc()).limit(limit).all()
    )
    return {
        "data": {"proposals": [_serialize(p) for p in rows]},
        "meta": {"count": len(rows), "status": status},
    }


@router.get("/evolution-proposals/{proposal_id}")
def get_proposal(
    proposal_id: int,
    user: User = Depends(require_super_admin),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """고도화 제안 상세."""
    proposal = (
        db.query(EvolutionProposal)
        .filter(EvolutionProposal.id == proposal_id)
        .first()
    )
    if proposal is None:
        raise HTTPException(status_code=404, detail="제안을 찾을 수 없습니다")
    return {"data": _serialize(proposal)}


def _review(
    db: Session,
    proposal_id: int,
    user: User,
    new_status: str,
    note: Optional[str],
) -> EvolutionProposal:
    proposal = (
        db.query(EvolutionProposal)
        .filter(EvolutionProposal.id == proposal_id)
        .first()
    )
    if proposal is None:
        raise HTTPException(status_code=404, detail="제안을 찾을 수 없습니다")
    if proposal.status != "pending":
        raise HTTPException(
            status_code=409,
            detail=f"이미 처리된 제안입니다 (status={proposal.status})",
        )
    proposal.status = new_status
    proposal.reviewed_by = (
        getattr(user, "email", None) or getattr(user, "name", None)
    )
    proposal.review_note = note or None
    proposal.reviewed_at = utc_now()
    db.commit()
    db.refresh(proposal)
    return proposal


@router.post("/evolution-proposals/{proposal_id}/approve")
def approve_proposal(
    proposal_id: int,
    body: Optional[ReviewBody] = None,
    user: User = Depends(require_super_admin),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """고도화 제안 승인."""
    proposal = _review(
        db, proposal_id, user, "approved", body.note if body else None
    )
    return {"data": _serialize(proposal)}


@router.post("/evolution-proposals/{proposal_id}/reject")
def reject_proposal(
    proposal_id: int,
    body: Optional[ReviewBody] = None,
    user: User = Depends(require_super_admin),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """고도화 제안 반려."""
    proposal = _review(
        db, proposal_id, user, "rejected", body.note if body else None
    )
    return {"data": _serialize(proposal)}


@router.get("/demand-stats")
def demand_stats(
    since_days: int = Query(30, ge=1, le=180),
    user: User = Depends(require_super_admin),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """현재 수요 분석 요약 (제안 생성 잡과 동일 집계)."""
    summary = evolution.analyze_demand(db, since_days=since_days)
    return {"data": summary}
