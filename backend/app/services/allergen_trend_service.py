"""논문 기반 알러젠 언급률 트렌드 서비스

Phase 1: 알러젠 트렌드 분석
- Paper + PaperAllergenLink 데이터를 연도/분기별로 집계
- 언급 비율(mention_rate) 기반 상대적 관심도 추적
- 트렌드 방향 계산 (KeywordTrendService ±20% 패턴 재사용)
"""
import logging
from datetime import date
from collections import Counter
from typing import Optional

from sqlalchemy.orm import Session
from sqlalchemy import func

from ..database.models import Paper, PaperAllergenLink
from ..database.analytics_models import PaperAllergenTrend

logger = logging.getLogger(__name__)


class AllergenTrendService:
    """논문 기반 알러젠 언급률 트렌드 서비스"""

    def aggregate_yearly(self, db: Session, year: int) -> dict:
        """연도별 알러젠 논문 언급률 집계

        Args:
            db: DB 세션
            year: 대상 연도

        Returns:
            집계 결과 요약
        """
        # 해당 연도 전체 논문 수
        total_papers = db.query(func.count(Paper.id)).filter(
            Paper.year == year,
        ).scalar() or 0

        if total_papers == 0:
            logger.info(f"No papers found for year {year}")
            return {"year": year, "total_papers": 0, "allergens_processed": 0}

        # 알러젠별 논문 집계 (PaperAllergenLink JOIN Paper)
        allergen_rows = (
            db.query(
                PaperAllergenLink.allergen_code,
                func.count(func.distinct(PaperAllergenLink.paper_id)).label("paper_count"),
                func.avg(PaperAllergenLink.relevance_score).label("avg_relevance"),
            )
            .join(Paper, PaperAllergenLink.paper_id == Paper.id)
            .filter(Paper.year == year)
            .group_by(PaperAllergenLink.allergen_code)
            .all()
        )

        if not allergen_rows:
            logger.info(f"No allergen links found for year {year}")
            return {"year": year, "total_papers": total_papers, "allergens_processed": 0}

        # 알러젠별 소스 분류 + link_type 분포 (별도 쿼리)
        source_data = (
            db.query(
                PaperAllergenLink.allergen_code,
                Paper.source,
                func.count(func.distinct(PaperAllergenLink.paper_id)),
            )
            .join(Paper, PaperAllergenLink.paper_id == Paper.id)
            .filter(Paper.year == year)
            .group_by(PaperAllergenLink.allergen_code, Paper.source)
            .all()
        )
        source_map = {}  # {allergen_code: {source: count}}
        for allergen_code, source, cnt in source_data:
            if allergen_code not in source_map:
                source_map[allergen_code] = {}
            source_map[allergen_code][source or "unknown"] = cnt

        link_type_data = (
            db.query(
                PaperAllergenLink.allergen_code,
                PaperAllergenLink.link_type,
                func.count(PaperAllergenLink.id),
            )
            .join(Paper, PaperAllergenLink.paper_id == Paper.id)
            .filter(Paper.year == year)
            .group_by(PaperAllergenLink.allergen_code, PaperAllergenLink.link_type)
            .all()
        )
        link_type_map = {}  # {allergen_code: Counter}
        for allergen_code, link_type, cnt in link_type_data:
            if allergen_code not in link_type_map:
                link_type_map[allergen_code] = Counter()
            link_type_map[allergen_code][link_type] = cnt

        # 전년도 데이터로 트렌드 방향 계산
        prev_trends = {}
        prev_records = db.query(PaperAllergenTrend).filter(
            PaperAllergenTrend.period_type == "yearly",
            PaperAllergenTrend.year == year - 1,
        ).all()
        for rec in prev_records:
            prev_trends[rec.allergen_code] = rec.mention_rate

        # 기존 스냅샷 삭제 (upsert)
        db.query(PaperAllergenTrend).filter(
            PaperAllergenTrend.period_type == "yearly",
            PaperAllergenTrend.year == year,
        ).delete()

        # 알러젠별 트렌드 저장
        created_count = 0
        for row in allergen_rows:
            allergen_code = row.allergen_code
            paper_count = row.paper_count
            mention_rate = round(paper_count / total_papers, 6) if total_papers > 0 else 0.0

            # 트렌드 방향 계산 (KeywordTrendService 패턴)
            prev_rate = prev_trends.get(allergen_code)
            if prev_rate is not None and prev_rate > 0:
                change_rate = round(((mention_rate - prev_rate) / prev_rate) * 100, 1)
                if change_rate > 20:
                    direction = "rising"
                elif change_rate < -20:
                    direction = "declining"
                else:
                    direction = "stable"
            else:
                change_rate = None
                direction = "new" if paper_count > 0 else None

            # top link types (상위 5개)
            lt_counter = link_type_map.get(allergen_code, Counter())
            top_link_types = [
                {"type": lt, "count": cnt}
                for lt, cnt in lt_counter.most_common(5)
            ]

            trend = PaperAllergenTrend(
                allergen_code=allergen_code,
                period_type="yearly",
                year=year,
                quarter=None,
                paper_count=paper_count,
                total_papers_in_period=total_papers,
                mention_rate=mention_rate,
                source_breakdown=source_map.get(allergen_code, {}),
                avg_relevance_score=round(float(row.avg_relevance or 0), 1),
                top_link_types=top_link_types,
                trend_direction=direction,
                change_rate=change_rate,
            )
            db.add(trend)
            created_count += 1

        db.commit()
        logger.info(f"Yearly aggregation completed: {year}, {created_count} allergens")

        return {
            "year": year,
            "total_papers": total_papers,
            "allergens_processed": created_count,
        }

    def aggregate_quarterly(self, db: Session, year: int, quarter: int) -> dict:
        """분기별 알러젠 논문 언급률 집계

        Args:
            db: DB 세션
            year: 대상 연도
            quarter: 대상 분기 (1-4)
        """
        # 분기 월 범위
        start_month = (quarter - 1) * 3 + 1
        end_month = start_month + 2

        # 해당 분기 전체 논문 수 (Paper.year + created_at month로 필터)
        total_papers = (
            db.query(func.count(Paper.id))
            .filter(
                Paper.year == year,
                func.extract("month", Paper.created_at) >= start_month,
                func.extract("month", Paper.created_at) <= end_month,
            )
            .scalar() or 0
        )

        if total_papers == 0:
            return {"year": year, "quarter": quarter, "total_papers": 0, "allergens_processed": 0}

        # 알러젠별 집계
        allergen_rows = (
            db.query(
                PaperAllergenLink.allergen_code,
                func.count(func.distinct(PaperAllergenLink.paper_id)).label("paper_count"),
                func.avg(PaperAllergenLink.relevance_score).label("avg_relevance"),
            )
            .join(Paper, PaperAllergenLink.paper_id == Paper.id)
            .filter(
                Paper.year == year,
                func.extract("month", Paper.created_at) >= start_month,
                func.extract("month", Paper.created_at) <= end_month,
            )
            .group_by(PaperAllergenLink.allergen_code)
            .all()
        )

        if not allergen_rows:
            return {"year": year, "quarter": quarter, "total_papers": total_papers, "allergens_processed": 0}

        # 전분기 데이터
        prev_q = quarter - 1
        prev_y = year
        if prev_q == 0:
            prev_q = 4
            prev_y = year - 1

        prev_trends = {}
        prev_records = db.query(PaperAllergenTrend).filter(
            PaperAllergenTrend.period_type == "quarterly",
            PaperAllergenTrend.year == prev_y,
            PaperAllergenTrend.quarter == prev_q,
        ).all()
        for rec in prev_records:
            prev_trends[rec.allergen_code] = rec.mention_rate

        # 기존 삭제 (upsert)
        db.query(PaperAllergenTrend).filter(
            PaperAllergenTrend.period_type == "quarterly",
            PaperAllergenTrend.year == year,
            PaperAllergenTrend.quarter == quarter,
        ).delete()

        created_count = 0
        for row in allergen_rows:
            allergen_code = row.allergen_code
            paper_count = row.paper_count
            mention_rate = round(paper_count / total_papers, 6) if total_papers > 0 else 0.0

            prev_rate = prev_trends.get(allergen_code)
            if prev_rate is not None and prev_rate > 0:
                change_rate = round(((mention_rate - prev_rate) / prev_rate) * 100, 1)
                if change_rate > 20:
                    direction = "rising"
                elif change_rate < -20:
                    direction = "declining"
                else:
                    direction = "stable"
            else:
                change_rate = None
                direction = "new" if paper_count > 0 else None

            trend = PaperAllergenTrend(
                allergen_code=allergen_code,
                period_type="quarterly",
                year=year,
                quarter=quarter,
                paper_count=paper_count,
                total_papers_in_period=total_papers,
                mention_rate=mention_rate,
                source_breakdown={},
                avg_relevance_score=round(float(row.avg_relevance or 0), 1),
                top_link_types=[],
                trend_direction=direction,
                change_rate=change_rate,
            )
            db.add(trend)
            created_count += 1

        db.commit()
        logger.info(f"Quarterly aggregation completed: {year} Q{quarter}, {created_count} allergens")

        return {
            "year": year,
            "quarter": quarter,
            "total_papers": total_papers,
            "allergens_processed": created_count,
        }

    def aggregate_all_years(self, db: Session) -> list[dict]:
        """모든 연도에 대해 연도별 집계 실행"""
        year_range = db.query(
            func.min(Paper.year),
            func.max(Paper.year),
        ).filter(Paper.year.isnot(None)).first()

        if not year_range or not year_range[0]:
            return []

        results = []
        for year in range(year_range[0], year_range[1] + 1):
            result = self.aggregate_yearly(db, year)
            if result["total_papers"] > 0:
                results.append(result)

        return results

    def get_allergen_paper_trend(
        self,
        db: Session,
        allergen_code: str,
        period_type: str = "yearly",
        limit: int = 20,
    ) -> dict:
        """특정 알러젠의 논문 언급률 시계열 데이터 조회"""
        trends = db.query(PaperAllergenTrend).filter(
            PaperAllergenTrend.allergen_code == allergen_code,
            PaperAllergenTrend.period_type == period_type,
        ).order_by(
            PaperAllergenTrend.year.desc(),
            PaperAllergenTrend.quarter.desc().nullslast(),
        ).limit(limit).all()

        data = [
            {
                "year": t.year,
                "quarter": t.quarter,
                "period": f"{t.year}" if period_type == "yearly" else f"{t.year} Q{t.quarter}",
                "paper_count": t.paper_count,
                "total_papers": t.total_papers_in_period,
                "mention_rate": t.mention_rate,
                "source_breakdown": t.source_breakdown,
                "avg_relevance_score": t.avg_relevance_score,
                "top_link_types": t.top_link_types,
                "trend_direction": t.trend_direction,
                "change_rate": t.change_rate,
            }
            for t in reversed(trends)
        ]

        return {
            "allergen_code": allergen_code,
            "period_type": period_type,
            "data_points": len(data),
            "trends": data,
        }

    def get_top_rising_allergens(
        self,
        db: Session,
        direction: str = "rising",
        limit: int = 10,
    ) -> dict:
        """트렌드 방향별 상위 알러젠 목록 (최근 연도 기준)"""
        latest_year = db.query(func.max(PaperAllergenTrend.year)).filter(
            PaperAllergenTrend.period_type == "yearly",
        ).scalar()

        if not latest_year:
            return {"year": None, "direction": direction, "allergens": []}

        query = db.query(PaperAllergenTrend).filter(
            PaperAllergenTrend.period_type == "yearly",
            PaperAllergenTrend.year == latest_year,
            PaperAllergenTrend.trend_direction == direction,
        )

        if direction == "rising":
            query = query.order_by(PaperAllergenTrend.change_rate.desc().nullslast())
        elif direction == "declining":
            query = query.order_by(PaperAllergenTrend.change_rate.asc().nullslast())
        else:
            query = query.order_by(PaperAllergenTrend.paper_count.desc())

        allergens = query.limit(limit).all()

        return {
            "year": latest_year,
            "direction": direction,
            "total": len(allergens),
            "allergens": [
                {
                    "allergen_code": a.allergen_code,
                    "paper_count": a.paper_count,
                    "total_papers": a.total_papers_in_period,
                    "mention_rate": a.mention_rate,
                    "change_rate": a.change_rate,
                    "source_breakdown": a.source_breakdown,
                    "top_link_types": a.top_link_types,
                }
                for a in allergens
            ],
        }

    def get_overview(self, db: Session) -> dict:
        """논문 알러젠 트렌드 개요 (최근 연도 전체 알러젠)"""
        latest_year = db.query(func.max(PaperAllergenTrend.year)).filter(
            PaperAllergenTrend.period_type == "yearly",
        ).scalar()

        if not latest_year:
            return {"latest_year": None, "allergens": [], "summary": {}}

        trends = db.query(PaperAllergenTrend).filter(
            PaperAllergenTrend.period_type == "yearly",
            PaperAllergenTrend.year == latest_year,
        ).order_by(
            PaperAllergenTrend.paper_count.desc()
        ).all()

        rising = [t for t in trends if t.trend_direction == "rising"]
        declining = [t for t in trends if t.trend_direction == "declining"]
        stable = [t for t in trends if t.trend_direction == "stable"]
        new = [t for t in trends if t.trend_direction == "new"]

        return {
            "latest_year": latest_year,
            "total_allergens": len(trends),
            "total_papers": trends[0].total_papers_in_period if trends else 0,
            "summary": {
                "rising": len(rising),
                "declining": len(declining),
                "stable": len(stable),
                "new": len(new),
            },
            "top_allergens": [
                {
                    "allergen_code": t.allergen_code,
                    "paper_count": t.paper_count,
                    "mention_rate": t.mention_rate,
                    "trend_direction": t.trend_direction,
                    "change_rate": t.change_rate,
                }
                for t in trends[:15]
            ],
        }
