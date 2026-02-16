"""예측 분석 시스템 DB 모델

Quick Win 3가지를 위한 테이블 정의:
1. AnalyticsSnapshot - 월별 알러젠 양성률 집계
2. KeywordTrend - 뉴스/논문 키워드 트렌드
3. PatientActivityLog - 환자 행동 로그
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
