"""알러젠 인사이트 리포트 서비스

수집된 논문/뉴스를 AI로 분석하여 알러젠별 인사이트 리포트를 생성합니다.
1단계: 뉴스/논문 알러젠 자동 태깅
2단계: 월별 인사이트 리포트 생성
"""
import logging
from datetime import date, datetime
from collections import defaultdict

from sqlalchemy.orm import Session
from sqlalchemy import func, and_

from ..database.analytics_models import AllergenInsightReport, NewsAllergenLink
from ..database.competitor_models import CompetitorNews
from ..database.models import Paper, PaperAllergenLink
from .ollama_service import get_ollama_service

logger = logging.getLogger(__name__)


class InsightReportService:
    """알러젠 인사이트 리포트 생성 서비스"""

    def tag_untagged_news(self, db: Session, limit: int = 100) -> int:
        """미태깅 뉴스에 알러젠 태그 자동 부여

        Returns:
            태깅된 뉴스 건수
        """
        ollama = get_ollama_service()

        # 이미 태깅된 뉴스 ID 조회
        tagged_ids = db.query(NewsAllergenLink.news_id).distinct().subquery()

        # 미태깅 + AI 분석 완료된 뉴스 조회
        untagged = (
            db.query(CompetitorNews)
            .filter(
                CompetitorNews.is_processed == True,
                CompetitorNews.is_duplicate == False,
                ~CompetitorNews.id.in_(db.query(tagged_ids)),
            )
            .order_by(CompetitorNews.created_at.desc())
            .limit(limit)
            .all()
        )

        tagged_count = 0
        for news in untagged:
            allergens = ollama.extract_allergens(
                news.title or "",
                news.description or news.summary or "",
            )
            for item in allergens:
                link = NewsAllergenLink(
                    news_id=news.id,
                    allergen_code=item["allergen"],
                    content_category=item["category"],
                    relevance_score=item["relevance"],
                )
                db.add(link)
            if allergens:
                tagged_count += 1

        db.commit()
        logger.info(f"뉴스 알러젠 태깅 완료: {tagged_count}/{len(untagged)}건")
        return tagged_count

    def generate_monthly_report(self, db: Session, year: int, month: int) -> list[dict]:
        """월별 알러젠 인사이트 리포트 생성

        Returns:
            생성된 리포트 정보 목록
        """
        ollama = get_ollama_service()
        period = date(year, month, 1)
        results = []

        # 해당 월의 알러젠별 소스 수집
        allergen_sources = self._collect_sources(db, year, month)

        for allergen_code, sources in allergen_sources.items():
            if len(sources) < 2:
                logger.debug(f"{allergen_code}: 소스 부족 ({len(sources)}건), 스킵")
                continue

            # 이미 리포트가 있으면 스킵
            existing = (
                db.query(AllergenInsightReport)
                .filter(
                    AllergenInsightReport.allergen_code == allergen_code,
                    AllergenInsightReport.period_date == period,
                    AllergenInsightReport.period_type == "monthly",
                )
                .first()
            )
            if existing:
                continue

            # AI 리포트 생성
            report_data = ollama.generate_insight_report(allergen_code, sources)
            if not report_data:
                logger.warning(f"{allergen_code}: 리포트 생성 실패")
                continue

            paper_ids = [s["id"] for s in sources if s["type"] == "paper"]
            news_ids = [s["id"] for s in sources if s["type"] == "news"]

            report = AllergenInsightReport(
                allergen_code=allergen_code,
                period_date=period,
                period_type="monthly",
                title=report_data["title"],
                content=report_data["content"],
                source_paper_ids=paper_ids if paper_ids else None,
                source_news_ids=news_ids if news_ids else None,
                key_findings=report_data["key_findings"] if report_data["key_findings"] else None,
                treatment_score=report_data["treatment_score"],
                source_count=len(sources),
            )
            db.add(report)
            results.append({
                "allergen": allergen_code,
                "title": report_data["title"],
                "sources": len(sources),
            })

        db.commit()
        logger.info(f"{year}-{month:02d} 인사이트 리포트 생성 완료: {len(results)}건")
        return results

    def _collect_sources(self, db: Session, year: int, month: int) -> dict[str, list[dict]]:
        """해당 월의 알러젠별 논문/뉴스 소스 수집"""
        allergen_sources = defaultdict(list)

        # 1. 논문 소스 (PaperAllergenLink 기반)
        paper_links = (
            db.query(PaperAllergenLink, Paper)
            .join(Paper, PaperAllergenLink.paper_id == Paper.id)
            .filter(
                func.extract("year", Paper.created_at) == year,
                func.extract("month", Paper.created_at) == month,
            )
            .all()
        )
        for link, paper in paper_links:
            allergen_sources[link.allergen_code].append({
                "type": "paper",
                "id": paper.id,
                "title": paper.title or "",
                "abstract": paper.abstract or paper.abstract_kr or "",
            })

        # 2. 뉴스 소스 (NewsAllergenLink 기반)
        news_links = (
            db.query(NewsAllergenLink, CompetitorNews)
            .join(CompetitorNews, NewsAllergenLink.news_id == CompetitorNews.id)
            .filter(
                func.extract("year", CompetitorNews.created_at) == year,
                func.extract("month", CompetitorNews.created_at) == month,
            )
            .all()
        )
        for link, news in news_links:
            allergen_sources[link.allergen_code].append({
                "type": "news",
                "id": news.id,
                "title": news.title or "",
                "abstract": news.description or news.summary or "",
            })

        return dict(allergen_sources)

    # --- 조회 API ---

    def get_reports(
        self, db: Session, allergen_code: str | None = None, limit: int = 12
    ) -> list[dict]:
        """인사이트 리포트 목록 조회"""
        query = db.query(AllergenInsightReport)
        if allergen_code:
            query = query.filter(AllergenInsightReport.allergen_code == allergen_code)
        query = query.order_by(AllergenInsightReport.period_date.desc()).limit(limit)

        return [
            {
                "id": r.id,
                "allergen_code": r.allergen_code,
                "period_date": r.period_date.isoformat(),
                "title": r.title,
                "key_findings": r.key_findings,
                "treatment_score": r.treatment_score,
                "source_count": r.source_count,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in query.all()
        ]

    def get_report_detail(self, db: Session, report_id: int) -> dict | None:
        """인사이트 리포트 상세 조회"""
        r = db.query(AllergenInsightReport).filter(AllergenInsightReport.id == report_id).first()
        if not r:
            return None

        return {
            "id": r.id,
            "allergen_code": r.allergen_code,
            "period_date": r.period_date.isoformat(),
            "period_type": r.period_type,
            "title": r.title,
            "content": r.content,
            "key_findings": r.key_findings,
            "treatment_score": r.treatment_score,
            "source_paper_ids": r.source_paper_ids,
            "source_news_ids": r.source_news_ids,
            "source_count": r.source_count,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }

    def get_available_allergens(self, db: Session) -> list[dict]:
        """리포트가 있는 알러젠 목록 조회"""
        results = (
            db.query(
                AllergenInsightReport.allergen_code,
                func.count(AllergenInsightReport.id).label("report_count"),
                func.max(AllergenInsightReport.period_date).label("latest_period"),
            )
            .group_by(AllergenInsightReport.allergen_code)
            .order_by(func.count(AllergenInsightReport.id).desc())
            .all()
        )
        return [
            {
                "allergen_code": r.allergen_code,
                "report_count": r.report_count,
                "latest_period": r.latest_period.isoformat() if r.latest_period else None,
            }
            for r in results
        ]
