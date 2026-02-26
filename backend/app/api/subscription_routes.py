"""공개 구독 API 라우터 (인증 불필요)"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from .subscription_schemas import (
    SubscribeRequest, VerifyRequest, UnsubscribeRequest,
    UpdateKeywordsRequest, ResendVerificationRequest,
)
from ..database.connection import get_db
from ..services.subscription_service import SubscriptionService

router = APIRouter(prefix="/subscribe", tags=["Subscription"])

_subscription_service = None


def get_subscription_service() -> SubscriptionService:
    global _subscription_service
    if _subscription_service is None:
        _subscription_service = SubscriptionService()
    return _subscription_service


@router.post("")
async def subscribe(
    request: SubscribeRequest,
    db: Session = Depends(get_db),
):
    """구독 신청"""
    service = get_subscription_service()
    return service.subscribe(
        db=db,
        email=request.email,
        name=request.name,
        keywords=request.keywords,
    )


@router.post("/verify")
async def verify_subscription(
    request: VerifyRequest,
    db: Session = Depends(get_db),
):
    """인증 코드 확인"""
    service = get_subscription_service()
    return service.verify(db=db, email=request.email, code=request.code)


@router.get("/status")
async def get_subscription_status(
    email: str = Query(...),
    db: Session = Depends(get_db),
):
    """구독 상태 조회"""
    service = get_subscription_service()
    return service.get_subscription_status(db=db, email=email)


@router.post("/unsubscribe")
async def unsubscribe(
    request: UnsubscribeRequest,
    db: Session = Depends(get_db),
):
    """구독 해지"""
    service = get_subscription_service()
    return service.unsubscribe(
        db=db,
        email=request.email,
        subscription_key=request.subscription_key,
    )


@router.put("/keywords")
async def update_keywords(
    request: UpdateKeywordsRequest,
    db: Session = Depends(get_db),
):
    """구독 키워드 수정"""
    service = get_subscription_service()
    return service.update_keywords(
        db=db,
        email=request.email,
        subscription_key=request.subscription_key,
        keywords=request.keywords,
    )


@router.post("/resend-verification")
async def resend_verification(
    request: ResendVerificationRequest,
    db: Session = Depends(get_db),
):
    """인증 코드 재발송"""
    service = get_subscription_service()
    return service.send_verification_email(db=db, email=request.email)
