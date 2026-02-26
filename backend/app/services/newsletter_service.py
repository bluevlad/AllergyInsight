"""뉴스레터 서비스

이메일 발송 + 리포트 생성 + DB 이력 관리를 조합합니다.
"""
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy.orm import Session
from sqlalchemy import func

from .email_service import EmailService, get_email_service
from .report_generator import NewsReportGenerator
from ..database.competitor_models import CompetitorNews, CompetitorCompany
from ..database.newsletter_models import NewsletterSendHistory

logger = logging.getLogger(__name__)


class NewsletterService:
    """뉴스레터 서비스"""

    def __init__(
        self,
        email_service: Optional[EmailService] = None,
        report_generator: Optional[NewsReportGenerator] = None,
    ):
        self.email_service = email_service or get_email_service()
        self.report_generator = report_generator or NewsReportGenerator()

    def _get_today_articles(self, db: Session, days: int = 1) -> list[dict]:
        """오늘(또는 최근 N일) 기사 조회"""
        since = datetime.now(timezone.utc) - timedelta(days=days)

        articles = db.query(CompetitorNews).join(CompetitorCompany).filter(
            CompetitorNews.created_at >= since,
            CompetitorNews.is_duplicate == False,
        ).order_by(
            CompetitorNews.importance_score.desc().nullslast(),
            CompetitorNews.created_at.desc(),
        ).limit(100).all()

        return [
            {
                "title": a.title,
                "url": a.url,
                "source": a.source,
                "company_name": a.company.name_kr if a.company else None,
                "published_at": a.published_at,
                "summary": a.summary,
                "importance_score": a.importance_score,
                "category": a.category or "general",
            }
            for a in articles
        ]

    def preview_newsletter(self, db: Session, days: int = 1) -> str:
        """뉴스레터 미리보기 HTML"""
        articles = self._get_today_articles(db, days=days)
        return self.report_generator.generate_daily_report(articles)

    def send_newsletter(
        self,
        db: Session,
        recipients: list[str],
        days: int = 1,
        subject: Optional[str] = None,
    ) -> dict:
        """뉴스레터 발송

        Args:
            db: DB 세션
            recipients: 수신자 이메일 목록
            days: 최근 N일 기사
            subject: 이메일 제목 (None이면 자동 생성)

        Returns:
            발송 결과 요약
        """
        articles = self._get_today_articles(db, days=days)

        if not articles:
            return {
                "sent": 0,
                "failed": 0,
                "article_count": 0,
                "message": "발송할 기사가 없습니다.",
            }

        report_date = datetime.now().strftime("%Y년 %m월 %d일")
        if subject is None:
            subject = f"[AllergyInsight] 뉴스 브리핑 - {report_date}"

        html = self.report_generator.generate_daily_report(
            articles, report_date=report_date,
        )

        sent = 0
        failed = 0
        now = datetime.utcnow()

        for recipient in recipients:
            result = self.email_service.send(recipient, subject, html)

            # 발송 이력 저장
            history = NewsletterSendHistory(
                recipient_email=recipient,
                subject=subject,
                article_count=len(articles),
                report_date=now,
                is_success=result.success,
                error_message=result.error,
                sent_at=now,
            )
            db.add(history)

            if result.success:
                sent += 1
            else:
                failed += 1

        db.commit()

        return {
            "sent": sent,
            "failed": failed,
            "article_count": len(articles),
            "message": f"{sent}건 발송 성공, {failed}건 실패",
        }

    def get_send_history(
        self,
        db: Session,
        page: int = 1,
        page_size: int = 20,
    ) -> dict:
        """발송 이력 조회"""
        query = db.query(NewsletterSendHistory)
        total = query.count()
        offset = (page - 1) * page_size

        items = query.order_by(
            NewsletterSendHistory.sent_at.desc()
        ).offset(offset).limit(page_size).all()

        return {
            "items": [
                {
                    "id": h.id,
                    "recipient_email": h.recipient_email,
                    "subject": h.subject,
                    "article_count": h.article_count,
                    "is_success": h.is_success,
                    "error_message": h.error_message,
                    "sent_at": h.sent_at.isoformat() if h.sent_at else None,
                }
                for h in items
            ],
            "total": total,
            "page": page,
            "page_size": page_size,
        }

    def send_to_subscribers(self, db: Session, days: int = 1) -> dict:
        """인증된 구독자에게 뉴스레터 발송 (키워드 매칭)

        각 구독자의 관심 키워드에 맞는 기사를 필터링하여 발송합니다.
        """
        from ..database.subscriber_models import NewsletterSubscriber

        subscribers = db.query(NewsletterSubscriber).filter(
            NewsletterSubscriber.is_verified == True,
            NewsletterSubscriber.is_active == True,
        ).all()

        if not subscribers:
            return {"sent": 0, "failed": 0, "message": "발송할 구독자가 없습니다."}

        all_articles = self._get_today_articles(db, days=days)
        if not all_articles:
            return {"sent": 0, "failed": 0, "message": "발송할 기사가 없습니다."}

        import os
        base_url = os.getenv("SUBSCRIPTION_BASE_URL", "http://localhost:4040/subscribe")

        sent = 0
        failed = 0
        now = datetime.utcnow()
        report_date = datetime.now().strftime("%Y년 %m월 %d일")

        for subscriber in subscribers:
            # 키워드 필터링
            keywords = subscriber.keywords or []
            if keywords:
                filtered = []
                for article in all_articles:
                    text = f"{article['title']} {article.get('summary', '')} {article.get('category', '')}".lower()
                    if any(kw.lower() in text for kw in keywords):
                        filtered.append(article)
                articles = filtered if filtered else all_articles[:10]
            else:
                articles = all_articles

            if not articles:
                continue

            unsubscribe_url = f"{base_url}/unsubscribe?email={subscriber.email}&key={subscriber.subscription_key}"
            manage_url = f"{base_url}/manage?email={subscriber.email}&key={subscriber.subscription_key}"

            subject = f"[AllergyInsight] 뉴스 브리핑 - {report_date}"
            html = self.report_generator.generate_summary_report(
                articles,
                report_date=report_date,
                unsubscribe_url=unsubscribe_url,
                manage_url=manage_url,
            )

            result = self.email_service.send(subscriber.email, subject, html)

            history = NewsletterSendHistory(
                recipient_email=subscriber.email,
                subject=subject,
                article_count=len(articles),
                report_date=now,
                is_success=result.success,
                error_message=result.error,
                sent_at=now,
            )
            db.add(history)

            if result.success:
                sent += 1
            else:
                failed += 1

        db.commit()
        return {"sent": sent, "failed": failed, "message": f"{sent}건 발송 성공, {failed}건 실패"}

    def get_send_stats(self, db: Session) -> dict:
        """발송 통계"""
        total = db.query(func.count(NewsletterSendHistory.id)).scalar() or 0
        success = db.query(func.count(NewsletterSendHistory.id)).filter(
            NewsletterSendHistory.is_success == True
        ).scalar() or 0
        failed = total - success

        # 최근 7일 발송
        week_ago = datetime.now(timezone.utc) - timedelta(days=7)
        recent = db.query(func.count(NewsletterSendHistory.id)).filter(
            NewsletterSendHistory.sent_at >= week_ago
        ).scalar() or 0

        return {
            "total_sent": total,
            "success_count": success,
            "failed_count": failed,
            "recent_7days": recent,
        }
