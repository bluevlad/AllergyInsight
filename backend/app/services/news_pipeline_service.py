"""뉴스 파이프라인 서비스

수집 → 중복 제거 → AI 분석 파이프라인을 조합합니다.
"""
import logging
from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from .competitor_news_service import CompetitorNewsService
from .ollama_service import OllamaService, get_ollama_service
from .deduplication_service import DeduplicationService, get_deduplication_service
from ..database.competitor_models import CompetitorNews

logger = logging.getLogger(__name__)


class NewsPipelineService:
    """뉴스 수집 + 중복 제거 + AI 분석 파이프라인"""

    def __init__(
        self,
        news_service: Optional[CompetitorNewsService] = None,
        ollama_service: Optional[OllamaService] = None,
        dedup_service: Optional[DeduplicationService] = None,
    ):
        self.news_service = news_service or CompetitorNewsService()
        self.ollama_service = ollama_service or get_ollama_service()
        self.dedup_service = dedup_service or get_deduplication_service()

    def run_collection_pipeline(
        self,
        db: Session,
        company_code: Optional[str] = None,
        max_results_per_company: int = 10,
        auto_analyze: bool = True,
    ) -> dict:
        """수집 + 중복 제거 + AI 분석 파이프라인

        Args:
            db: DB 세션
            company_code: 특정 업체만 수집 (None이면 전체)
            max_results_per_company: 업체당 최대 결과 수
            auto_analyze: 수집 후 자동 AI 분석 여부

        Returns:
            파이프라인 실행 결과
        """
        # 1. 뉴스 수집 + DB 저장
        collect_result = self.news_service.collect_and_save(
            db=db,
            company_code=company_code,
            max_results_per_company=max_results_per_company,
        )

        result = {
            "collected": collect_result["total_new"],
            "duplicates": collect_result["total_duplicate"],
            "analyzed": 0,
            "company_stats": collect_result["company_stats"],
        }

        # 2. 중복 제거 (content_hash 기반)
        self._mark_hash_duplicates(db)

        # 3. AI 분석 (auto_analyze가 True일 때)
        if auto_analyze and collect_result["total_new"] > 0:
            analyzed = self.process_unanalyzed_articles(db)
            result["analyzed"] = analyzed

        return result

    def _mark_hash_duplicates(self, db: Session):
        """content_hash 기반 중복 마킹"""
        # is_processed=False인 기사들의 해시 계산
        unprocessed = db.query(CompetitorNews).filter(
            CompetitorNews.is_processed == False,
            CompetitorNews.content_hash == None,
        ).all()

        if not unprocessed:
            return

        # 기존 해시 집합 로드
        existing_hashes = set()
        existing = db.query(CompetitorNews.content_hash).filter(
            CompetitorNews.content_hash != None,
        ).all()
        for row in existing:
            existing_hashes.add(row[0])

        dup_count = 0
        for article in unprocessed:
            is_dup, content_hash = self.dedup_service.check_duplicate(
                article.title, article.url, existing_hashes,
            )
            article.content_hash = content_hash
            if is_dup:
                article.is_duplicate = True
                dup_count += 1
            else:
                existing_hashes.add(content_hash)

        db.commit()
        if dup_count > 0:
            logger.info(f"해시 중복 {dup_count}건 마킹")

    def process_unanalyzed_articles(self, db: Session, limit: int = 50) -> int:
        """미분석 기사 AI 처리

        Args:
            db: DB 세션
            limit: 한 번에 처리할 최대 기사 수

        Returns:
            처리된 기사 수
        """
        articles = db.query(CompetitorNews).filter(
            CompetitorNews.is_processed == False,
            CompetitorNews.is_duplicate == False,
        ).order_by(CompetitorNews.created_at.desc()).limit(limit).all()

        if not articles:
            logger.info("분석할 기사가 없습니다")
            return 0

        analyzed = 0
        for article in articles:
            try:
                analysis = self.ollama_service.analyze_article(
                    title=article.title,
                    description=article.description or "",
                )
                article.summary = analysis["summary"]
                article.importance_score = analysis["importance_score"]
                article.category = analysis["category"]
                article.is_processed = True
                article.processed_at = datetime.utcnow()
                analyzed += 1
            except Exception as e:
                logger.warning(f"기사 분석 실패 (id={article.id}): {e}")

        db.commit()
        logger.info(f"기사 {analyzed}/{len(articles)}건 분석 완료")
        return analyzed

    def reanalyze_article(self, db: Session, article_id: int) -> Optional[dict]:
        """특정 기사 재분석"""
        article = db.query(CompetitorNews).filter(
            CompetitorNews.id == article_id
        ).first()

        if not article:
            return None

        analysis = self.ollama_service.analyze_article(
            title=article.title,
            description=article.description or "",
        )
        article.summary = analysis["summary"]
        article.importance_score = analysis["importance_score"]
        article.category = analysis["category"]
        article.is_processed = True
        article.processed_at = datetime.utcnow()
        db.commit()

        return analysis

    def close(self):
        """리소스 정리"""
        self.news_service.close()
