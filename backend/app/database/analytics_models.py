"""예측 분석 시스템 DB 모델

Quick Win 3가지를 위한 테이블 정의:
1. AnalyticsSnapshot - 월별 알러젠 양성률 집계
2. KeywordTrend - 뉴스/논문 키워드 트렌드
3. PatientActivityLog - 환자 행동 로그
4. AllergenInsightReport - AI 기반 알러젠별 인사이트 리포트
5. NewsAllergenLink - 뉴스-알러젠 자동 태깅
"""
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, Date,
    ForeignKey, JSON, Text, Index,
)
from .connection import Base


class AnalyticsSnapshot(Base):
    """월별 알러젠 양성률 집계 (Module A: 임상 트렌드 분석)"""
    __tablename__ = "analytics_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    snapshot_date = Column(Date, nullable=False)  # 집계 기준일 (월 첫째날)
    period_type = Column(String(20), nullable=False, default="monthly")  # 'monthly', 'quarterly', 'yearly'
    allergen_code = Column(String(30), nullable=False)  # 알러젠 코드 (e.g., 'peanut')
    total_tests = Column(Integer, nullable=False, default=0)  # 총 검사 건수
    positive_count = Column(Integer, nullable=False, default=0)  # 양성 건수 (grade >= 1)
    positive_rate = Column(Float, nullable=True)  # 양성률 (0.0 ~ 1.0)
    avg_grade = Column(Float, nullable=True)  # 평균 등급
    grade_distribution = Column(JSON, nullable=True)  # {0: 45, 1: 12, 2: 8, ...}
    cooccurrence_top5 = Column(JSON, nullable=True)  # [{"allergen": "crab", "rate": 0.82}, ...]
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index('idx_analytics_snapshot_date', 'snapshot_date'),
        Index('idx_analytics_snapshot_allergen', 'allergen_code'),
        Index('idx_analytics_snapshot_period', 'period_type', 'snapshot_date'),
        Index('idx_analytics_snapshot_unique', 'period_type', 'snapshot_date', 'allergen_code', unique=True),
    )


class KeywordTrend(Base):
    """뉴스/논문 키워드 트렌드 (Module B: 시장 인텔리전스)"""
    __tablename__ = "keyword_trends"

    id = Column(Integer, primary_key=True, index=True)
    keyword = Column(String(100), nullable=False)  # 추적 키워드
    keyword_category = Column(String(30), nullable=False)  # 'company', 'technology', 'regulation', 'product', 'allergen'
    source_type = Column(String(20), nullable=False)  # 'news', 'paper'
    period_date = Column(Date, nullable=False)  # 집계 기간 (월 첫째날)
    mention_count = Column(Integer, nullable=False, default=0)  # 언급 횟수
    context_samples = Column(JSON, nullable=True)  # 대표 문장 3-5개
    trend_direction = Column(String(20), nullable=True)  # 'rising', 'stable', 'declining'
    change_rate = Column(Float, nullable=True)  # 전기 대비 변화율 (%)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index('idx_keyword_trend_keyword', 'keyword'),
        Index('idx_keyword_trend_category', 'keyword_category'),
        Index('idx_keyword_trend_period', 'period_date'),
        Index('idx_keyword_trend_source', 'source_type'),
        Index('idx_keyword_trend_unique', 'keyword', 'source_type', 'period_date', unique=True),
    )


class PatientActivityLog(Base):
    """환자 행동 로그 (Module C: 환자 인식 추적)"""
    __tablename__ = "patient_activity_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # 비로그인 행동도 기록
    action_type = Column(String(30), nullable=False)  # 'login', 'view', 'download', 'search', 'toggle'
    resource_type = Column(String(30), nullable=True)  # 'diagnosis', 'prescription', 'paper', 'qa', 'news_read', 'news_important'
    resource_id = Column(String(50), nullable=True)  # 리소스 식별자
    metadata_json = Column(JSON, nullable=True)  # 추가 컨텍스트 (검색어, 필터 등)
    ip_hash = Column(String(64), nullable=True)  # IP 해시 (비식별)
    user_agent = Column(String(200), nullable=True)  # 브라우저/디바이스
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index('idx_activity_log_user', 'user_id'),
        Index('idx_activity_log_action', 'action_type'),
        Index('idx_activity_log_resource', 'resource_type'),
        Index('idx_activity_log_created', 'created_at'),
        Index('idx_activity_log_user_action', 'user_id', 'action_type'),
    )


class NewsAllergenLink(Base):
    """뉴스-알러젠 자동 태깅 (수집 뉴스에 대한 알러젠 코드 매핑)"""
    __tablename__ = "news_allergen_links"

    id = Column(Integer, primary_key=True, index=True)
    news_id = Column(Integer, ForeignKey("competitor_news.id", ondelete="CASCADE"), nullable=False)
    allergen_code = Column(String(30), nullable=False)  # 'peanut', 'milk', 'egg' 등
    content_category = Column(String(30), nullable=True)  # 'treatment', 'epidemiology', 'diagnosis_method', 'regulation', 'research'
    relevance_score = Column(Float, nullable=True)  # 0.0~1.0
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index('idx_news_allergen_news', 'news_id'),
        Index('idx_news_allergen_code', 'allergen_code'),
        Index('idx_news_allergen_category', 'content_category'),
        Index('idx_news_allergen_unique', 'news_id', 'allergen_code', unique=True),
    )


class AllergenInsightReport(Base):
    """AI 기반 알러젠별 인사이트 리포트"""
    __tablename__ = "allergen_insight_reports"

    id = Column(Integer, primary_key=True, index=True)
    allergen_code = Column(String(30), nullable=False)  # 'peanut', 'milk', 'egg' 등
    period_date = Column(Date, nullable=False)  # 분석 기간 (월 첫째날)
    period_type = Column(String(20), nullable=False, default="monthly")  # 'monthly', 'quarterly'
    title = Column(String(200), nullable=False)  # 리포트 제목
    content = Column(Text, nullable=False)  # AI 생성 마크다운 본문
    source_paper_ids = Column(JSON, nullable=True)  # 참고 논문 ID 목록
    source_news_ids = Column(JSON, nullable=True)  # 참고 뉴스 ID 목록
    key_findings = Column(JSON, nullable=True)  # 핵심 발견 요약 ["finding1", "finding2"]
    treatment_score = Column(Integer, nullable=True)  # 치료 발전도 지표 (0-100)
    source_count = Column(Integer, nullable=True, default=0)  # 분석에 사용된 소스 수
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index('idx_insight_allergen', 'allergen_code'),
        Index('idx_insight_period', 'period_date'),
        Index('idx_insight_unique', 'allergen_code', 'period_date', 'period_type', unique=True),
    )
