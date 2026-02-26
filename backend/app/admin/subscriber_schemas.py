"""Admin 구독자 관리 스키마"""
from pydantic import BaseModel
from typing import Optional, List, Dict
from datetime import datetime


class SubscriberListItem(BaseModel):
    """구독자 목록 항목"""
    id: int
    email: str
    name: Optional[str] = None
    is_verified: bool
    is_active: bool
    keywords: List[str] = []
    group_name: str = "general"
    subscribed_at: Optional[str] = None
    verified_at: Optional[str] = None


class SubscriberDetail(BaseModel):
    """구독자 상세"""
    id: int
    email: str
    name: Optional[str] = None
    is_verified: bool
    is_active: bool
    keywords: List[str] = []
    group_name: str = "general"
    subscribed_at: Optional[str] = None
    verified_at: Optional[str] = None
    unsubscribed_at: Optional[str] = None


class SubscriberUpdateRequest(BaseModel):
    """구독자 수정 요청"""
    name: Optional[str] = None
    keywords: Optional[List[str]] = None
    group_name: Optional[str] = None
    is_active: Optional[bool] = None


class SubscriberStatsResponse(BaseModel):
    """구독자 통계"""
    total: int
    verified: int
    unverified: int
    active: int
    inactive: int
    by_group: Dict[str, int] = {}
