"""경쟁사 뉴스 관리 API 스키마"""
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime


# ============================================================================
# 뉴스 목록/검색
# ============================================================================

class NewsArticleItem(BaseModel):
    """뉴스 기사 항목"""
    id: Optional[int] = None
    title: str
    description: Optional[str] = None
    url: str
    source: str  # 'naver', 'google'
    company_code: Optional[str] = None
    company_name: Optional[str] = None
    published_at: Optional[datetime] = None
    search_keyword: Optional[str] = None
    category: Optional[str] = "general"
    is_read: bool = False
    is_important: bool = False
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class NewsListResponse(BaseModel):
    """뉴스 목록 응답"""
    items: List[NewsArticleItem]
    total: int
    page: int
    page_size: int


class NewsSearchResponse(BaseModel):
    """실시간 뉴스 검색 응답"""
    articles: List[NewsArticleItem]
    total_count: int
    source: str
    search_time_ms: float


# ============================================================================
# 업체 관리
# ============================================================================

class CompanyItem(BaseModel):
    """경쟁사 항목"""
    id: int
    code: str
    name_kr: str
    name_en: str
    category: str
    keywords: List[str]
    homepage_url: Optional[str] = None
    is_active: bool = True
    news_count: int = 0

    class Config:
        from_attributes = True


class CompanyListResponse(BaseModel):
    """업체 목록 응답"""
    items: List[CompanyItem]
    total: int


# ============================================================================
# 수집 관련
# ============================================================================

class CollectRequest(BaseModel):
    """수집 요청"""
    company_code: Optional[str] = None  # None이면 전체 수집
    max_results: int = 10


class CollectResponse(BaseModel):
    """수집 응답"""
    total_new: int
    total_duplicate: int
    company_stats: Dict[str, Any]


# ============================================================================
# 뉴스 통계
# ============================================================================

class NewsStatsResponse(BaseModel):
    """뉴스 통계 응답"""
    total_news: int
    unread_count: int
    important_count: int
    by_company: Dict[str, int]
    by_source: Dict[str, int]
    recent_7days: int
