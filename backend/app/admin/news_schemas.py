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
    # AI 분석 필드
    summary: Optional[str] = None
    importance_score: Optional[float] = None
    is_processed: bool = False

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


# ============================================================================
# AI 분석
# ============================================================================

class AnalyzeRequest(BaseModel):
    """AI 분석 요청"""
    limit: int = 50  # 한 번에 처리할 기사 수


class AnalyzeResponse(BaseModel):
    """AI 분석 응답"""
    analyzed: int
    message: str


class ArticleAnalysisDetail(BaseModel):
    """기사 분석 상세"""
    id: int
    title: str
    summary: Optional[str] = None
    importance_score: Optional[float] = None
    category: Optional[str] = None
    is_processed: bool = False
    processed_at: Optional[datetime] = None


# ============================================================================
# 스케줄러
# ============================================================================

class SchedulerJobItem(BaseModel):
    """스케줄러 작업 항목"""
    id: str
    name: str
    next_run: Optional[str] = None
    trigger: str


class SchedulerStatusResponse(BaseModel):
    """스케줄러 상태 응답"""
    is_running: bool
    jobs: List[SchedulerJobItem]


class SchedulerTriggerRequest(BaseModel):
    """스케줄러 즉시 실행 요청"""
    job_type: str  # 'crawl', 'send', 'all'


class SchedulerConfigRequest(BaseModel):
    """스케줄러 설정 변경 요청"""
    crawl_hour: Optional[int] = None
    crawl_minute: Optional[int] = None
    send_hour: Optional[int] = None
    send_minute: Optional[int] = None


# ============================================================================
# 뉴스레터
# ============================================================================

class NewsletterSendRequest(BaseModel):
    """뉴스레터 발송 요청"""
    recipients: List[str]
    days: int = 1
    subject: Optional[str] = None


class NewsletterSendResponse(BaseModel):
    """뉴스레터 발송 응답"""
    sent: int
    failed: int
    article_count: int
    message: str


class SendHistoryItem(BaseModel):
    """발송 이력 항목"""
    id: int
    recipient_email: str
    subject: str
    article_count: int
    is_success: bool
    error_message: Optional[str] = None
    sent_at: Optional[str] = None


class NewsletterStatsResponse(BaseModel):
    """뉴스레터 통계 응답"""
    total_sent: int
    success_count: int
    failed_count: int
    recent_7days: int
