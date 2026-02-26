"""공개 구독 API 스키마"""
from pydantic import BaseModel, EmailStr
from typing import Optional, List


class SubscribeRequest(BaseModel):
    """구독 신청 요청"""
    email: EmailStr
    name: Optional[str] = None
    keywords: Optional[List[str]] = None


class VerifyRequest(BaseModel):
    """인증 코드 확인 요청"""
    email: EmailStr
    code: str


class UnsubscribeRequest(BaseModel):
    """구독 해지 요청"""
    email: EmailStr
    subscription_key: str


class UpdateKeywordsRequest(BaseModel):
    """키워드 수정 요청"""
    email: EmailStr
    subscription_key: str
    keywords: List[str]


class ResendVerificationRequest(BaseModel):
    """인증 코드 재발송 요청"""
    email: EmailStr


class SubscriptionStatusRequest(BaseModel):
    """구독 상태 조회"""
    email: EmailStr
