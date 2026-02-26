"""구독자 DB 모델"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, JSON, ForeignKey, Index
from .connection import Base


class NewsletterSubscriber(Base):
    """뉴스레터 구독자"""
    __tablename__ = "newsletter_subscribers"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False)
    name = Column(String(100), nullable=True)
    subscription_key = Column(String(64), unique=True, nullable=False)
    is_verified = Column(Boolean, default=False)
    keywords = Column(JSON, nullable=True, default=list)  # 관심 키워드 목록
    group_name = Column(String(50), default="general")  # 구독 그룹
    is_active = Column(Boolean, default=True)
    subscribed_at = Column(DateTime, default=datetime.utcnow)
    verified_at = Column(DateTime, nullable=True)
    unsubscribed_at = Column(DateTime, nullable=True)

    __table_args__ = (
        Index('idx_subscribers_email', 'email'),
        Index('idx_subscribers_key', 'subscription_key'),
        Index('idx_subscribers_verified_active', 'is_verified', 'is_active'),
    )


class EmailVerification(Base):
    """이메일 인증 코드"""
    __tablename__ = "email_verifications"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), nullable=False)
    code = Column(String(6), nullable=False)  # 6자리 인증 코드
    attempts = Column(Integer, default=0)
    max_attempts = Column(Integer, default=5)
    expires_at = Column(DateTime, nullable=False)
    is_used = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index('idx_verification_email', 'email'),
        Index('idx_verification_code', 'code'),
    )
