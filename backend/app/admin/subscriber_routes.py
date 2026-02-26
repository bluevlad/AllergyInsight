"""Admin 구독자 관리 라우터"""
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional

from .dependencies import require_super_admin
from .subscriber_schemas import (
    SubscriberListItem, SubscriberDetail,
    SubscriberUpdateRequest, SubscriberStatsResponse,
)
from ..database.connection import get_db
from ..database.models import User
from ..database.subscriber_models import NewsletterSubscriber

router = APIRouter()


@router.get("/subscribers")
async def get_subscribers(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    is_verified: Optional[bool] = None,
    is_active: Optional[bool] = None,
    search: Optional[str] = None,
    current_user: User = Depends(require_super_admin),
    db: Session = Depends(get_db),
):
    """구독자 목록 조회"""
    query = db.query(NewsletterSubscriber)

    if is_verified is not None:
        query = query.filter(NewsletterSubscriber.is_verified == is_verified)
    if is_active is not None:
        query = query.filter(NewsletterSubscriber.is_active == is_active)
    if search:
        search_filter = f"%{search}%"
        query = query.filter(
            (NewsletterSubscriber.email.ilike(search_filter)) |
            (NewsletterSubscriber.name.ilike(search_filter))
        )

    total = query.count()
    offset = (page - 1) * page_size
    subscribers = query.order_by(
        NewsletterSubscriber.subscribed_at.desc()
    ).offset(offset).limit(page_size).all()

    items = [
        SubscriberListItem(
            id=s.id,
            email=s.email,
            name=s.name,
            is_verified=s.is_verified,
            is_active=s.is_active,
            keywords=s.keywords or [],
            group_name=s.group_name or "general",
            subscribed_at=s.subscribed_at.isoformat() if s.subscribed_at else None,
            verified_at=s.verified_at.isoformat() if s.verified_at else None,
        )
        for s in subscribers
    ]

    return {
        "items": [item.model_dump() for item in items],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get("/subscribers/stats", response_model=SubscriberStatsResponse)
async def get_subscriber_stats(
    current_user: User = Depends(require_super_admin),
    db: Session = Depends(get_db),
):
    """구독자 통계"""
    total = db.query(func.count(NewsletterSubscriber.id)).scalar() or 0
    verified = db.query(func.count(NewsletterSubscriber.id)).filter(
        NewsletterSubscriber.is_verified == True
    ).scalar() or 0
    active = db.query(func.count(NewsletterSubscriber.id)).filter(
        NewsletterSubscriber.is_active == True
    ).scalar() or 0

    # 그룹별 통계
    group_counts = db.query(
        NewsletterSubscriber.group_name,
        func.count(NewsletterSubscriber.id),
    ).group_by(NewsletterSubscriber.group_name).all()
    by_group = {g or "general": c for g, c in group_counts}

    return SubscriberStatsResponse(
        total=total,
        verified=verified,
        unverified=total - verified,
        active=active,
        inactive=total - active,
        by_group=by_group,
    )


@router.get("/subscribers/{subscriber_id}")
async def get_subscriber_detail(
    subscriber_id: int,
    current_user: User = Depends(require_super_admin),
    db: Session = Depends(get_db),
):
    """구독자 상세 조회"""
    subscriber = db.query(NewsletterSubscriber).filter(
        NewsletterSubscriber.id == subscriber_id
    ).first()

    if not subscriber:
        raise HTTPException(status_code=404, detail="구독자를 찾을 수 없습니다.")

    return SubscriberDetail(
        id=subscriber.id,
        email=subscriber.email,
        name=subscriber.name,
        is_verified=subscriber.is_verified,
        is_active=subscriber.is_active,
        keywords=subscriber.keywords or [],
        group_name=subscriber.group_name or "general",
        subscribed_at=subscriber.subscribed_at.isoformat() if subscriber.subscribed_at else None,
        verified_at=subscriber.verified_at.isoformat() if subscriber.verified_at else None,
        unsubscribed_at=subscriber.unsubscribed_at.isoformat() if subscriber.unsubscribed_at else None,
    ).model_dump()


@router.put("/subscribers/{subscriber_id}")
async def update_subscriber(
    subscriber_id: int,
    request: SubscriberUpdateRequest,
    current_user: User = Depends(require_super_admin),
    db: Session = Depends(get_db),
):
    """구독자 정보 수정"""
    subscriber = db.query(NewsletterSubscriber).filter(
        NewsletterSubscriber.id == subscriber_id
    ).first()

    if not subscriber:
        raise HTTPException(status_code=404, detail="구독자를 찾을 수 없습니다.")

    if request.name is not None:
        subscriber.name = request.name
    if request.keywords is not None:
        subscriber.keywords = request.keywords
    if request.group_name is not None:
        subscriber.group_name = request.group_name
    if request.is_active is not None:
        subscriber.is_active = request.is_active

    db.commit()
    return {"message": "구독자 정보가 수정되었습니다."}


@router.delete("/subscribers/{subscriber_id}")
async def delete_subscriber(
    subscriber_id: int,
    current_user: User = Depends(require_super_admin),
    db: Session = Depends(get_db),
):
    """구독자 삭제"""
    subscriber = db.query(NewsletterSubscriber).filter(
        NewsletterSubscriber.id == subscriber_id
    ).first()

    if not subscriber:
        raise HTTPException(status_code=404, detail="구독자를 찾을 수 없습니다.")

    db.delete(subscriber)
    db.commit()
    return {"message": "구독자가 삭제되었습니다."}
