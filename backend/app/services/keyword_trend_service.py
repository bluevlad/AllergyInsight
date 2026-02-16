"""키워드 트렌드 분석 서비스

Module B: 시장 인텔리전스
- 경쟁사 뉴스에서 키워드 빈도 추출
- 월별 트렌드 방향 계산
"""
import re
import logging
from datetime import date, datetime
from typing import Optional

from sqlalchemy.orm import Session
from sqlalchemy import func, extract, and_

from ..database.competitor_models import CompetitorNews, CompetitorCompany
from ..database.analytics_models import KeywordTrend

logger = logging.getLogger(__name__)

# 추적 키워드 정의
TRACKED_KEYWORDS = {
    "company": {
        "수젠텍": ["수젠텍", "Sugentech", "SGTi"],
        "Phadia": ["Phadia", "ImmunoCap", "ImmunoCAP"],
        "Siemens": ["Siemens", "Atellica"],
        "Hycor": ["Hycor", "NOVEOS"],
        "MADx": ["ALEX2", "MADx"],
        "LG화학": ["LG화학", "LG Chem"],
        "녹십자MS": ["녹십자MS", "녹십자엠에스"],
        "바디텍메드": ["바디텍메드", "Boditech"],
    },
    "technology": {
        "CRD": ["CRD", "component resolved", "컴포넌트"],
        "멀티플렉스": ["multiplex", "멀티플렉스", "다중"],
        "POC": ["POC", "point of care", "현장검사"],
        "MAST": ["MAST", "다항목동시검사"],
        "lateral flow": ["lateral flow", "래피드"],
    },
    "regulation": {
        "FDA": ["FDA", "미국식품의약국"],
        "CE-IVD": ["CE-IVD", "IVDR", "CE 인증"],
        "식약처": ["식약처", "MFDS", "식품의약품안전처"],
        "가이드라인": ["가이드라인", "guideline", "consensus"],
    },
    "product": {
        "알러지진단": ["알러지 진단", "allergy diagnostic", "알레르기 진단"],
        "체외진단": ["체외진단", "IVD", "in vitro"],
        "진단키트": ["진단키트", "diagnostic kit", "검사키트"],
    },
    "allergen": {
        "식품알러지": ["식품 알러지", "식품알레르기", "food allergy"],
        "아나필락시스": ["아나필락시스", "anaphylaxis"],
        "교차반응": ["교차반응", "cross-reactivity", "cross reactivity"],
    },
}


class KeywordTrendService:
    """키워드 트렌드 분석 서비스"""

    def extract_monthly(self, db: Session, year: int, month: int) -> dict:
        """월별 키워드 빈도 추출

        Args:
            db: DB 세션
            year: 대상 연도
            month: 대상 월

        Returns:
            추출 결과 요약
        """
        period_date = date(year, month, 1)

        # 해당 월 뉴스 조회
        news_list = db.query(CompetitorNews).filter(
            extract('year', CompetitorNews.published_at) == year,
            extract('month', CompetitorNews.published_at) == month,
        ).all()

        if not news_list:
            # published_at이 null인 경우 created_at으로 폴백
            news_list = db.query(CompetitorNews).filter(
                extract('year', CompetitorNews.created_at) == year,
                extract('month', CompetitorNews.created_at) == month,
            ).all()

        if not news_list:
            logger.info(f"No news found for {year}-{month:02d}")
            return {"period": f"{year}-{month:02d}", "total_news": 0, "keywords_extracted": 0}

        # 키워드별 언급 횟수 및 컨텍스트 수집
        keyword_data = {}  # {(keyword, category): {"count": int, "contexts": []}}

        for news in news_list:
            text = f"{news.title or ''} {news.description or ''}"
            text_lower = text.lower()

            for category, keywords_map in TRACKED_KEYWORDS.items():
                for display_keyword, variants in keywords_map.items():
                    matched = False
                    for variant in variants:
                        if variant.lower() in text_lower:
                            matched = True
                            break

                    if matched:
                        key = (display_keyword, category)
                        if key not in keyword_data:
                            keyword_data[key] = {"count": 0, "contexts": []}

                        keyword_data[key]["count"] += 1
                        # 컨텍스트 샘플 저장 (최대 5개)
                        if len(keyword_data[key]["contexts"]) < 5:
                            context = news.title[:100] if news.title else ""
                            if context and context not in keyword_data[key]["contexts"]:
                                keyword_data[key]["contexts"].append(context)

        # 이전 달 데이터로 트렌드 방향 계산
        prev_month = month - 1
        prev_year = year
        if prev_month == 0:
            prev_month = 12
            prev_year = year - 1
        prev_date = date(prev_year, prev_month, 1)

        prev_trends = {}
        prev_records = db.query(KeywordTrend).filter(
            KeywordTrend.period_date == prev_date,
        ).all()
        for rec in prev_records:
            prev_trends[rec.keyword] = rec.mention_count

        # 기존 스냅샷 삭제 (upsert)
        db.query(KeywordTrend).filter(
            KeywordTrend.period_date == period_date,
            KeywordTrend.source_type == "news",
        ).delete()

        # 키워드별 트렌드 저장
        created_count = 0
        for (keyword, category), data in keyword_data.items():
            prev_count = prev_trends.get(keyword, 0)
            if prev_count > 0:
                change_rate = round(((data["count"] - prev_count) / prev_count) * 100, 1)
                if change_rate > 20:
                    direction = "rising"
                elif change_rate < -20:
                    direction = "declining"
                else:
                    direction = "stable"
            else:
                change_rate = None
                direction = "new" if data["count"] > 0 else None

            trend = KeywordTrend(
                keyword=keyword,
                keyword_category=category,
                source_type="news",
                period_date=period_date,
                mention_count=data["count"],
                context_samples=data["contexts"],
                trend_direction=direction,
                change_rate=change_rate,
            )
            db.add(trend)
            created_count += 1

        db.commit()
        logger.info(f"Keyword extraction completed: {year}-{month:02d}, {created_count} keywords")

        return {
            "period": f"{year}-{month:02d}",
            "total_news": len(news_list),
            "keywords_extracted": created_count,
        }

    def extract_all_months(self, db: Session) -> list[dict]:
        """모든 미추출 월에 대해 키워드 추출 실행"""
        oldest_date = db.query(func.min(CompetitorNews.created_at)).scalar()
        if not oldest_date:
            return []

        results = []
        current = date(oldest_date.year, oldest_date.month, 1)
        today = date.today()

        while current < today:
            result = self.extract_monthly(db, current.year, current.month)
            if result["total_news"] > 0:
                results.append(result)

            if current.month == 12:
                current = date(current.year + 1, 1, 1)
            else:
                current = date(current.year, current.month + 1, 1)

        return results

    def get_keyword_trend(
        self,
        db: Session,
        keyword: Optional[str] = None,
        category: Optional[str] = None,
        limit: int = 12,
    ) -> list[dict]:
        """키워드 트렌드 조회"""
        query = db.query(KeywordTrend)

        if keyword:
            query = query.filter(KeywordTrend.keyword == keyword)
        if category:
            query = query.filter(KeywordTrend.keyword_category == category)

        trends = query.order_by(
            KeywordTrend.period_date.desc()
        ).limit(limit).all()

        return [
            {
                "keyword": t.keyword,
                "category": t.keyword_category,
                "source": t.source_type,
                "period": t.period_date.isoformat(),
                "mention_count": t.mention_count,
                "trend_direction": t.trend_direction,
                "change_rate": t.change_rate,
                "context_samples": t.context_samples,
            }
            for t in reversed(trends)
        ]

    def get_overview(self, db: Session) -> dict:
        """최근 키워드 트렌드 개요"""
        latest_date = db.query(func.max(KeywordTrend.period_date)).scalar()
        if not latest_date:
            return {"latest_period": None, "categories": {}}

        trends = db.query(KeywordTrend).filter(
            KeywordTrend.period_date == latest_date,
        ).order_by(
            KeywordTrend.mention_count.desc()
        ).all()

        # 카테고리별 그룹핑
        categories = {}
        for t in trends:
            if t.keyword_category not in categories:
                categories[t.keyword_category] = []
            categories[t.keyword_category].append({
                "keyword": t.keyword,
                "mention_count": t.mention_count,
                "trend_direction": t.trend_direction,
                "change_rate": t.change_rate,
            })

        # 상승 트렌드 키워드
        rising = [
            {"keyword": t.keyword, "category": t.keyword_category, "change_rate": t.change_rate}
            for t in trends
            if t.trend_direction == "rising"
        ]

        return {
            "latest_period": latest_date.isoformat(),
            "total_keywords": len(trends),
            "rising_keywords": rising,
            "categories": categories,
        }
