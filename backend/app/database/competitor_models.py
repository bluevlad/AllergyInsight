"""경쟁사 뉴스 DB 모델"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, JSON, Index
from sqlalchemy.orm import relationship
from .connection import Base


class CompetitorCompany(Base):
    """모니터링 대상 경쟁사"""
    __tablename__ = "competitor_companies"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), unique=True, nullable=False)  # 'sugentech', 'phadia' 등
    name_kr = Column(String(100), nullable=False)
    name_en = Column(String(100), nullable=False)
    category = Column(String(20), nullable=False)  # 'self', 'overseas', 'domestic', 'industry'
    keywords = Column(JSON, nullable=False, default=list)
    homepage_url = Column(String(500), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    news_articles = relationship("CompetitorNews", back_populates="company")

    __table_args__ = (
        Index('idx_competitor_companies_code', 'code'),
        Index('idx_competitor_companies_category', 'category'),
    )


class CompetitorNews(Base):
    """수집된 경쟁사 뉴스"""
    __tablename__ = "competitor_news"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("competitor_companies.id"), nullable=False)
    source = Column(String(20), nullable=False)  # 'naver', 'google'
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    url = Column(String(1000), nullable=False)
    original_url = Column(String(1000), nullable=True)
    published_at = Column(DateTime, nullable=True)
    search_keyword = Column(String(200), nullable=True)
    category = Column(String(50), default="general")  # 'product', 'regulatory', 'financial', 'partnership', 'general'
    is_read = Column(Boolean, default=False)
    is_important = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    company = relationship("CompetitorCompany", back_populates="news_articles")

    __table_args__ = (
        Index('idx_competitor_news_company', 'company_id'),
        Index('idx_competitor_news_source', 'source'),
        Index('idx_competitor_news_published', 'published_at'),
        Index('idx_competitor_news_url', 'url'),
    )
