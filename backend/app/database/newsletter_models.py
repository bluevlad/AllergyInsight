"""뉴스레터 발송 이력 DB 모델"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, Index
from .connection import Base


class NewsletterSendHistory(Base):
    """뉴스레터 발송 이력"""
    __tablename__ = "newsletter_send_history"

    id = Column(Integer, primary_key=True, index=True)
    recipient_email = Column(String(255), nullable=False)
    subject = Column(String(500), nullable=False)
    article_count = Column(Integer, default=0)
    report_date = Column(DateTime, nullable=True)
    is_success = Column(Boolean, default=False)
    error_message = Column(Text, nullable=True)
    sent_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index('idx_newsletter_history_email', 'recipient_email'),
        Index('idx_newsletter_history_date', 'report_date'),
        Index('idx_newsletter_history_sent', 'sent_at'),
    )
