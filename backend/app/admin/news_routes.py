"""경쟁사 뉴스 관리 API 라우터"""
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta, timezone
from typing import Optional

from .dependencies import require_super_admin
from .news_schemas import (
    NewsArticleItem, NewsListResponse, NewsSearchResponse,
    CompanyItem, CompanyListResponse,
    CollectRequest, CollectResponse,
    NewsStatsResponse,
    AnalyzeRequest, AnalyzeResponse, ArticleAnalysisDetail,
    SchedulerStatusResponse, SchedulerTriggerRequest, SchedulerConfigRequest,
    NewsletterSendRequest, NewsletterSendResponse, NewsletterStatsResponse,
)
from ..database.connection import get_db
from ..database.models import User
from ..database.competitor_models import CompetitorCompany, CompetitorNews
from ..services.competitor_news_service import CompetitorNewsService
from ..models.competitor_news import DEFAULT_COMPETITORS

router = APIRouter()

# 서비스 인스턴스 (모듈 레벨)
_news_service: Optional[CompetitorNewsService] = None


def get_news_service() -> CompetitorNewsService:
    """뉴스 서비스 싱글톤"""
    global _news_service
    if _news_service is None:
        _news_service = CompetitorNewsService()
    return _news_service


# ============================================================================
# 뉴스 목록 (DB에서 조회)
# ============================================================================

@router.get("/news", response_model=NewsListResponse)
async def get_news_list(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    company: Optional[str] = None,
    source: Optional[str] = None,
    is_read: Optional[bool] = None,
    is_important: Optional[bool] = None,
    search: Optional[str] = None,
    current_user: User = Depends(require_super_admin),
    db: Session = Depends(get_db),
):
    """수집된 뉴스 목록 조회 (페이지네이션, 필터링)"""
    query = db.query(CompetitorNews).join(CompetitorCompany, isouter=True)

    # 필터 적용
    if company:
        query = query.filter(CompetitorCompany.code == company)
    if source:
        query = query.filter(CompetitorNews.source == source)
    if is_read is not None:
        query = query.filter(CompetitorNews.is_read == is_read)
    if is_important is not None:
        query = query.filter(CompetitorNews.is_important == is_important)
    if search:
        search_filter = f"%{search}%"
        query = query.filter(
            (CompetitorNews.title.ilike(search_filter)) |
            (CompetitorNews.description.ilike(search_filter))
        )

    total = query.count()
    offset = (page - 1) * page_size
    news_items = query.order_by(
        CompetitorNews.published_at.desc().nullslast(),
        CompetitorNews.created_at.desc(),
    ).offset(offset).limit(page_size).all()

    items = []
    for news in news_items:
        items.append(NewsArticleItem(
            id=news.id,
            title=news.title,
            description=news.description,
            url=news.url,
            source=news.source,
            company_code=news.company.code if news.company else None,
            company_name=news.company.name_kr if news.company else None,
            published_at=news.published_at,
            search_keyword=news.search_keyword,
            category=news.category,
            is_read=news.is_read,
            is_important=news.is_important,
            created_at=news.created_at,
            summary=news.summary,
            importance_score=news.importance_score,
            is_processed=news.is_processed,
        ))

    return NewsListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    )


# ============================================================================
# 실시간 뉴스 검색 (API 직접 호출)
# ============================================================================

@router.get("/news/search")
async def search_news(
    company: Optional[str] = None,
    keyword: Optional[str] = None,
    source: Optional[str] = None,
    max_results: int = Query(20, ge=1, le=100),
    current_user: User = Depends(require_super_admin),
    db: Session = Depends(get_db),
):
    """실시간 뉴스 검색 (네이버/구글 API 직접 호출)"""
    service = get_news_service()
    sources = [source] if source else None

    if company:
        result = service.search_company_news(
            company, max_results, sources=sources, db=db,
        )
        articles = []
        for article in result.naver_articles + result.google_articles:
            articles.append(NewsArticleItem(
                title=article.title,
                description=article.description,
                url=article.url,
                source=article.source,
                company_code=result.company_code,
                company_name=result.company_name,
                published_at=article.published_at,
                search_keyword=article.search_keyword,
            ))

        return {
            "articles": [a.model_dump() for a in articles],
            "total_count": result.total_count,
            "company": result.company_code,
            "search_time_ms": result.search_time_ms,
        }

    elif keyword:
        # 키워드 직접 검색
        naver_result = service.naver.search(keyword, max_results)
        google_result = service.google.search(keyword, max_results=max_results)

        articles = []
        for article in naver_result.articles + google_result.articles:
            articles.append(NewsArticleItem(
                title=article.title,
                description=article.description,
                url=article.url,
                source=article.source,
                published_at=article.published_at,
                search_keyword=keyword,
            ))

        return {
            "articles": [a.model_dump() for a in articles],
            "total_count": naver_result.total_count + google_result.total_count,
            "keyword": keyword,
            "search_time_ms": naver_result.search_time_ms + google_result.search_time_ms,
        }

    else:
        raise HTTPException(status_code=400, detail="company 또는 keyword 파라미터가 필요합니다.")


# ============================================================================
# 모니터링 대상 업체 목록
# ============================================================================

@router.get("/news/companies", response_model=CompanyListResponse)
async def get_companies(
    current_user: User = Depends(require_super_admin),
    db: Session = Depends(get_db),
):
    """모니터링 대상 업체 목록"""
    companies = db.query(CompetitorCompany).order_by(
        CompetitorCompany.category,
        CompetitorCompany.name_kr,
    ).all()

    # DB에 업체가 없으면 기본값 반환
    if not companies:
        items = []
        for code, data in DEFAULT_COMPETITORS.items():
            items.append(CompanyItem(
                id=0,
                code=code,
                name_kr=data["name_kr"],
                name_en=data["name_en"],
                category=data["category"].value,
                keywords=data["keywords"],
                homepage_url=data.get("homepage_url"),
                is_active=True,
                news_count=0,
            ))
        return CompanyListResponse(items=items, total=len(items))

    items = []
    for company in companies:
        news_count = db.query(func.count(CompetitorNews.id)).filter(
            CompetitorNews.company_id == company.id
        ).scalar() or 0

        items.append(CompanyItem(
            id=company.id,
            code=company.code,
            name_kr=company.name_kr,
            name_en=company.name_en,
            category=company.category,
            keywords=company.keywords or [],
            homepage_url=company.homepage_url,
            is_active=company.is_active,
            news_count=news_count,
        ))

    return CompanyListResponse(items=items, total=len(items))


# ============================================================================
# 수동 뉴스 수집
# ============================================================================

@router.post("/news/collect", response_model=CollectResponse)
async def collect_news(
    request: CollectRequest,
    current_user: User = Depends(require_super_admin),
    db: Session = Depends(get_db),
):
    """수동 뉴스 수집 트리거"""
    service = get_news_service()

    result = service.collect_and_save(
        db=db,
        company_code=request.company_code,
        max_results_per_company=request.max_results,
    )

    return CollectResponse(**result)


# ============================================================================
# 읽음/중요 표시
# ============================================================================

@router.put("/news/{news_id}/read")
async def toggle_read(
    news_id: int,
    current_user: User = Depends(require_super_admin),
    db: Session = Depends(get_db),
):
    """읽음 상태 토글"""
    news = db.query(CompetitorNews).filter(CompetitorNews.id == news_id).first()
    if not news:
        raise HTTPException(status_code=404, detail="뉴스를 찾을 수 없습니다.")

    news.is_read = not news.is_read
    db.commit()

    return {"id": news_id, "is_read": news.is_read}


@router.put("/news/{news_id}/important")
async def toggle_important(
    news_id: int,
    current_user: User = Depends(require_super_admin),
    db: Session = Depends(get_db),
):
    """중요 표시 토글"""
    news = db.query(CompetitorNews).filter(CompetitorNews.id == news_id).first()
    if not news:
        raise HTTPException(status_code=404, detail="뉴스를 찾을 수 없습니다.")

    news.is_important = not news.is_important
    db.commit()

    return {"id": news_id, "is_important": news.is_important}


# ============================================================================
# 뉴스 통계
# ============================================================================

@router.get("/news/stats", response_model=NewsStatsResponse)
async def get_news_stats(
    current_user: User = Depends(require_super_admin),
    db: Session = Depends(get_db),
):
    """뉴스 통계"""
    total = db.query(func.count(CompetitorNews.id)).scalar() or 0
    unread = db.query(func.count(CompetitorNews.id)).filter(
        CompetitorNews.is_read == False
    ).scalar() or 0
    important = db.query(func.count(CompetitorNews.id)).filter(
        CompetitorNews.is_important == True
    ).scalar() or 0

    # 업체별 건수
    company_counts = db.query(
        CompetitorCompany.code,
        func.count(CompetitorNews.id),
    ).join(CompetitorNews, isouter=True).group_by(CompetitorCompany.code).all()
    by_company = {code: count for code, count in company_counts}

    # 소스별 건수
    source_counts = db.query(
        CompetitorNews.source,
        func.count(CompetitorNews.id),
    ).group_by(CompetitorNews.source).all()
    by_source = {source: count for source, count in source_counts}

    # 최근 7일
    week_ago = datetime.now(timezone.utc) - timedelta(days=7)
    recent = db.query(func.count(CompetitorNews.id)).filter(
        CompetitorNews.created_at >= week_ago
    ).scalar() or 0

    return NewsStatsResponse(
        total_news=total,
        unread_count=unread,
        important_count=important,
        by_company=by_company,
        by_source=by_source,
        recent_7days=recent,
    )


# ============================================================================
# AI 분석
# ============================================================================

@router.post("/news/analyze", response_model=AnalyzeResponse)
async def analyze_news(
    request: AnalyzeRequest,
    current_user: User = Depends(require_super_admin),
    db: Session = Depends(get_db),
):
    """미분석 기사 AI 처리"""
    from ..services.news_pipeline_service import NewsPipelineService

    pipeline = NewsPipelineService()
    try:
        analyzed = pipeline.process_unanalyzed_articles(db, limit=request.limit)
        return AnalyzeResponse(
            analyzed=analyzed,
            message=f"{analyzed}건의 기사가 분석되었습니다.",
        )
    finally:
        pipeline.close()


@router.get("/news/{news_id}/analysis", response_model=ArticleAnalysisDetail)
async def get_article_analysis(
    news_id: int,
    current_user: User = Depends(require_super_admin),
    db: Session = Depends(get_db),
):
    """기사 분석 상세 조회"""
    news = db.query(CompetitorNews).filter(CompetitorNews.id == news_id).first()
    if not news:
        raise HTTPException(status_code=404, detail="뉴스를 찾을 수 없습니다.")

    return ArticleAnalysisDetail(
        id=news.id,
        title=news.title,
        summary=news.summary,
        importance_score=news.importance_score,
        category=news.category,
        is_processed=news.is_processed,
        processed_at=news.processed_at,
    )


@router.post("/news/{news_id}/reanalyze", response_model=ArticleAnalysisDetail)
async def reanalyze_article(
    news_id: int,
    current_user: User = Depends(require_super_admin),
    db: Session = Depends(get_db),
):
    """기사 재분석"""
    from ..services.news_pipeline_service import NewsPipelineService

    pipeline = NewsPipelineService()
    try:
        result = pipeline.reanalyze_article(db, news_id)
        if result is None:
            raise HTTPException(status_code=404, detail="뉴스를 찾을 수 없습니다.")

        news = db.query(CompetitorNews).filter(CompetitorNews.id == news_id).first()
        return ArticleAnalysisDetail(
            id=news.id,
            title=news.title,
            summary=news.summary,
            importance_score=news.importance_score,
            category=news.category,
            is_processed=news.is_processed,
            processed_at=news.processed_at,
        )
    finally:
        pipeline.close()


# ============================================================================
# 스케줄러 관리
# ============================================================================

@router.get("/scheduler/status", response_model=SchedulerStatusResponse)
async def get_scheduler_status(
    current_user: User = Depends(require_super_admin),
):
    """스케줄러 상태 조회"""
    from ..api.main import get_scheduler_service

    scheduler = get_scheduler_service()
    if scheduler is None:
        return SchedulerStatusResponse(is_running=False, jobs=[])

    status = scheduler.get_status()
    jobs = scheduler.get_jobs()
    return SchedulerStatusResponse(
        is_running=status["running"],
        jobs=[
            {"id": j["id"], "name": j["name"], "next_run": j["next_run_time"], "trigger": "cron"}
            for j in jobs
        ],
    )


@router.post("/scheduler/trigger")
async def trigger_scheduler(
    request: SchedulerTriggerRequest,
    current_user: User = Depends(require_super_admin),
):
    """스케줄러 즉시 실행"""
    from ..api.main import get_scheduler_service

    scheduler = get_scheduler_service()
    if scheduler is None:
        raise HTTPException(status_code=503, detail="스케줄러가 비활성화되어 있습니다.")

    if request.job_type == "crawl":
        scheduler.trigger_job("news_pipeline")
        return {"message": "뉴스 수집이 실행되었습니다."}
    elif request.job_type == "send":
        scheduler.trigger_job("newsletter_send")
        return {"message": "뉴스레터 발송이 실행되었습니다."}
    elif request.job_type == "all":
        scheduler.trigger_job("news_pipeline")
        scheduler.trigger_job("newsletter_send")
        return {"message": "뉴스 수집 및 발송이 실행되었습니다."}
    else:
        raise HTTPException(status_code=400, detail="유효하지 않은 job_type입니다. (crawl, send, all)")


@router.put("/scheduler/config")
async def update_scheduler_config(
    request: SchedulerConfigRequest,
    current_user: User = Depends(require_super_admin),
):
    """스케줄러 설정 변경 (통합 스케줄러에서는 환경변수 기반으로 동작)"""
    from ..api.main import get_scheduler_service

    scheduler = get_scheduler_service()
    if scheduler is None:
        raise HTTPException(status_code=503, detail="스케줄러가 비활성화되어 있습니다.")

    return {"message": "스케줄러 설정은 환경변수(CRAWL_HOUR, CRAWL_MINUTE, SEND_HOUR, SEND_MINUTE)로 관리됩니다. 컨테이너 재시작이 필요합니다."}


# ============================================================================
# 뉴스레터
# ============================================================================

@router.get("/newsletter/preview")
async def preview_newsletter(
    days: int = Query(1, ge=1, le=7),
    current_user: User = Depends(require_super_admin),
    db: Session = Depends(get_db),
):
    """뉴스레터 미리보기"""
    from ..services.newsletter_service import NewsletterService
    from fastapi.responses import HTMLResponse

    service = NewsletterService()
    html = service.preview_newsletter(db, days=days)
    return HTMLResponse(content=html)


@router.post("/newsletter/send", response_model=NewsletterSendResponse)
async def send_newsletter(
    request: NewsletterSendRequest,
    current_user: User = Depends(require_super_admin),
    db: Session = Depends(get_db),
):
    """뉴스레터 발송"""
    from ..services.newsletter_service import NewsletterService

    service = NewsletterService()
    result = service.send_newsletter(
        db=db,
        recipients=request.recipients,
        days=request.days,
        subject=request.subject,
    )
    return NewsletterSendResponse(**result)


@router.get("/newsletter/history")
async def get_newsletter_history(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(require_super_admin),
    db: Session = Depends(get_db),
):
    """뉴스레터 발송 이력"""
    from ..services.newsletter_service import NewsletterService

    service = NewsletterService()
    return service.get_send_history(db, page=page, page_size=page_size)


@router.get("/newsletter/stats", response_model=NewsletterStatsResponse)
async def get_newsletter_stats(
    current_user: User = Depends(require_super_admin),
    db: Session = Depends(get_db),
):
    """뉴스레터 발송 통계"""
    from ..services.newsletter_service import NewsletterService

    service = NewsletterService()
    return NewsletterStatsResponse(**service.get_send_stats(db))
