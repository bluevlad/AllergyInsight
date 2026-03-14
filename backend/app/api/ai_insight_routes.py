"""알러지 인사이트 공개 API (인증 불필요)

알러젠별 논문, 뉴스, 트렌드 정보를 통합 제공합니다.
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta, timezone
from typing import Optional

from ..database.connection import get_db
from ..database.models import Paper, PaperAllergenLink
from ..database.competitor_models import CompetitorNews, CompetitorCompany
from ..data.allergen_prescription_db import get_allergen_list, FOOD_ALLERGENS, INHALANT_ALLERGENS
from ..services.analytics_service import AnalyticsService
from ..services.keyword_trend_service import KeywordTrendService

router = APIRouter(prefix="/ai/insight", tags=["AI Insight"])

_analytics_service = AnalyticsService()
_keyword_trend_service = KeywordTrendService()


@router.get("/overview")
def get_insight_overview(db: Session = Depends(get_db)):
    """인사이트 개요 - 전체 통계 및 알러젠별 논문 수

    논문 총 수, 알러젠별 논문 수, 최근 논문 등을 반환합니다.
    """
    total_papers = db.query(func.count(Paper.id)).scalar() or 0

    # 알러젠별 논문 수
    allergen_rows = db.query(
        PaperAllergenLink.allergen_code,
        func.count(PaperAllergenLink.id),
    ).group_by(PaperAllergenLink.allergen_code).order_by(
        func.count(PaperAllergenLink.id).desc()
    ).all()

    allergen_stats = []
    all_allergens = {**FOOD_ALLERGENS, **INHALANT_ALLERGENS}
    allergen_count_map = {code: cnt for code, cnt in allergen_rows}

    for code, info in all_allergens.items():
        allergen_stats.append({
            "code": code,
            "name_kr": info["name_kr"],
            "name_en": info["name_en"],
            "category": info["category"] if "category" in info else (
                "food" if code in FOOD_ALLERGENS else "inhalant"
            ),
            "paper_count": allergen_count_map.get(code, 0),
        })

    # 정렬: 논문 수 내림차순
    allergen_stats.sort(key=lambda x: x["paper_count"], reverse=True)

    # 최근 논문 5개
    recent = db.query(Paper).order_by(Paper.created_at.desc()).limit(5).all()
    recent_papers = [
        {
            "title": p.title,
            "source": p.source,
            "year": p.year,
            "journal": p.journal,
            "created_at": p.created_at.isoformat() if p.created_at else None,
        }
        for p in recent
    ]

    # 연도별 분포
    year_rows = db.query(
        Paper.year,
        func.count(Paper.id),
    ).filter(Paper.year.isnot(None)).group_by(Paper.year).order_by(Paper.year).all()
    by_year = [{"year": yr, "count": cnt} for yr, cnt in year_rows]

    return {
        "success": True,
        "total_papers": total_papers,
        "allergen_stats": allergen_stats,
        "recent_papers": recent_papers,
        "by_year": by_year,
    }


@router.get("/allergen/{allergen_code}")
def get_allergen_detail(
    allergen_code: str,
    db: Session = Depends(get_db),
):
    """특정 알러젠 상세 정보 - 논문, 트렌드, 기본 정보

    알러젠 코드에 해당하는 상세 정보를 반환합니다.
    """
    from fastapi import HTTPException

    all_allergens = {**FOOD_ALLERGENS, **INHALANT_ALLERGENS}
    if allergen_code not in all_allergens:
        raise HTTPException(status_code=404, detail="해당 알러젠을 찾을 수 없습니다.")

    info = all_allergens[allergen_code]

    # 관련 논문
    paper_links = db.query(PaperAllergenLink).filter(
        PaperAllergenLink.allergen_code == allergen_code
    ).limit(20).all()

    paper_ids = [link.paper_id for link in paper_links]
    papers = []
    if paper_ids:
        paper_objs = db.query(Paper).filter(Paper.id.in_(paper_ids)).order_by(
            Paper.year.desc().nullslast(),
            Paper.created_at.desc(),
        ).all()
        papers = [
            {
                "title": p.title,
                "authors": p.authors,
                "year": p.year,
                "journal": p.journal,
                "abstract": (p.abstract[:200] + "...") if p.abstract and len(p.abstract) > 200 else p.abstract,
                "doi": p.doi,
                "source": p.source,
            }
            for p in paper_objs
        ]

    # 알러젠 트렌드
    trend_data = _analytics_service.get_allergen_trend(db, allergen_code, limit=12)

    # 알러젠 기본 정보
    allergen_info = {
        "code": allergen_code,
        "name_kr": info["name_kr"],
        "name_en": info["name_en"],
        "category": "food" if allergen_code in FOOD_ALLERGENS else "inhalant",
        "description": info.get("description", ""),
    }

    # 식품 알러젠인 경우 회피 식품, 대체 식품 정보 포함
    if allergen_code in FOOD_ALLERGENS:
        allergen_info["avoid_foods"] = info.get("avoid_foods", [])[:5]
        allergen_info["substitutes"] = info.get("substitutes", [])[:3]

    return {
        "success": True,
        "allergen": allergen_info,
        "papers": papers,
        "paper_count": len(papers),
        "trend": trend_data,
    }


@router.get("/news")
def get_allergy_news(
    days: int = Query(default=3, ge=1, le=7, description="최근 N일"),
    limit: int = Query(default=20, ge=1, le=50),
    db: Session = Depends(get_db),
):
    """최근 알러지 관련 뉴스

    수집된 뉴스를 최신순으로 반환합니다.
    """
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)

    news_items = (
        db.query(CompetitorNews)
        .join(CompetitorCompany, isouter=True)
        .filter(
            CompetitorNews.is_duplicate == False,
            CompetitorNews.created_at >= cutoff,
        )
        .order_by(
            CompetitorNews.importance_score.desc().nullslast(),
            CompetitorNews.published_at.desc().nullslast(),
            CompetitorNews.created_at.desc(),
        )
        .limit(limit)
        .all()
    )

    items = [
        {
            "id": news.id,
            "title": news.title,
            "description": news.description,
            "url": news.url,
            "source": news.source,
            "published_at": news.published_at.isoformat() if news.published_at else None,
            "category": news.category,
            "summary": news.summary,
            "importance_score": news.importance_score,
        }
        for news in news_items
    ]

    return {
        "success": True,
        "items": items,
        "total": len(items),
        "days": days,
    }


@router.get("/trends")
def get_allergy_trends(db: Session = Depends(get_db)):
    """알러지 키워드 트렌드 개요"""
    return {
        "success": True,
        **_keyword_trend_service.get_overview(db),
    }
