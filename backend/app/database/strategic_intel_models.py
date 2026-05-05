"""Strategic Intel — 기술/회사 적합도 매트릭스 + 가설/검증 + 일별 주가 모델

내부 경영진 분석용. 외부 사용자 노출 금지.
대상 회사: 수젠텍, 녹십자MS, 바디텍메드 (검증 가능) + MADx (fit matrix만, 비상장)
"""
from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    DateTime,
    Date,
    Text,
    Float,
    Numeric,
    BigInteger,
    ForeignKey,
    JSON,
    Index,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from .connection import Base
from ..utils.timezone import utc_now


class TechCategory(Base):
    """기술 카테고리 마스터 — Tech Taxonomy v1 (12개)"""
    __tablename__ = "tech_categories"

    id = Column(String(50), primary_key=True)  # 'multiplex_microarray' 등
    name_kr = Column(String(100), nullable=False)
    name_en = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    keywords_en = Column(JSON, nullable=False, default=list)
    keywords_kr = Column(JSON, nullable=False, default=list)
    sort_order = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    fits = relationship("CompanyTechFit", back_populates="tech_category")

    __table_args__ = (
        Index("idx_tech_categories_active", "is_active"),
    )


class CompanyTechFit(Base):
    """회사-기술 적합도 매트릭스 (Strategic Fit Matrix)

    score 0.0~1.0:
      0.0 : 무관
      0.3 : 미보유 (기회/위협 잠재)
      0.6 : 보유·확장 가능
      0.9+: 핵심 사업 영역
    """
    __tablename__ = "company_tech_fits"

    id = Column(Integer, primary_key=True, index=True)
    company_code = Column(String(50), ForeignKey("competitor_companies.code"), nullable=False)
    tech_category_id = Column(String(50), ForeignKey("tech_categories.id"), nullable=False)
    fit_score = Column(Numeric(3, 2), nullable=False)
    rationale = Column(Text, nullable=True)
    version = Column(String(20), default="v1")
    effective_from = Column(Date, nullable=False)
    effective_to = Column(Date, nullable=True)
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    tech_category = relationship("TechCategory", back_populates="fits")

    __table_args__ = (
        UniqueConstraint("company_code", "tech_category_id", "effective_from", name="uq_company_tech_effective"),
        Index("idx_company_tech_fits_company", "company_code"),
        Index("idx_company_tech_fits_tech", "tech_category_id"),
        Index("idx_company_tech_fits_effective", "effective_from", "effective_to"),
    )


class PaperTechLink(Base):
    """논문 ↔ 기술 카테고리 다대다 라벨링 (LLM 분류기 결과)"""
    __tablename__ = "paper_tech_links"

    id = Column(Integer, primary_key=True, index=True)
    paper_id = Column(Integer, ForeignKey("papers.id"), nullable=False)
    tech_category_id = Column(String(50), ForeignKey("tech_categories.id"), nullable=False)
    confidence = Column(Numeric(3, 2), nullable=False)  # 0.0~1.0
    classifier_version = Column(String(30), nullable=True)  # 'gpt-4o-2024-11', 'rule-v1' 등
    classified_at = Column(DateTime, default=utc_now)

    __table_args__ = (
        UniqueConstraint("paper_id", "tech_category_id", name="uq_paper_tech"),
        Index("idx_paper_tech_links_paper", "paper_id"),
        Index("idx_paper_tech_links_tech", "tech_category_id"),
        Index("idx_paper_tech_links_confidence", "confidence"),
    )


class NewsTechLink(Base):
    """뉴스 ↔ 기술 카테고리 다대다 라벨링"""
    __tablename__ = "news_tech_links"

    id = Column(Integer, primary_key=True, index=True)
    news_id = Column(Integer, ForeignKey("competitor_news.id"), nullable=False)
    tech_category_id = Column(String(50), ForeignKey("tech_categories.id"), nullable=False)
    confidence = Column(Numeric(3, 2), nullable=False)
    classifier_version = Column(String(30), nullable=True)
    classified_at = Column(DateTime, default=utc_now)

    __table_args__ = (
        UniqueConstraint("news_id", "tech_category_id", name="uq_news_tech"),
        Index("idx_news_tech_links_news", "news_id"),
        Index("idx_news_tech_links_tech", "tech_category_id"),
    )


class DailyPrice(Base):
    """일별 주가 / 시장 지수

    ticker 예시:
      - '253840' (수젠텍, KOSDAQ)
      - '142280' (녹십자엠에스, KOSDAQ)
      - '206640' (바디텍메드, KOSDAQ)
      - 'KQ150HC' (KOSDAQ150 헬스케어 지수, 시장 벤치마크)
    """
    __tablename__ = "daily_prices"

    id = Column(Integer, primary_key=True, index=True)
    ticker = Column(String(20), nullable=False)
    market = Column(String(10), nullable=False)  # 'KOSDAQ', 'INDEX'
    trade_date = Column(Date, nullable=False)
    open_price = Column(Numeric(12, 2), nullable=True)
    high_price = Column(Numeric(12, 2), nullable=True)
    low_price = Column(Numeric(12, 2), nullable=True)
    close_price = Column(Numeric(12, 2), nullable=False)
    volume = Column(BigInteger, nullable=True)
    market_cap = Column(BigInteger, nullable=True)
    source = Column(String(20), default="pykrx")  # 'pykrx', 'yfinance'
    collected_at = Column(DateTime, default=utc_now)

    __table_args__ = (
        UniqueConstraint("ticker", "trade_date", name="uq_ticker_trade_date"),
        Index("idx_daily_prices_ticker", "ticker"),
        Index("idx_daily_prices_date", "trade_date"),
        Index("idx_daily_prices_ticker_date", "ticker", "trade_date"),
    )


class HypothesisLog(Base):
    """가설 + 시장 검증 로그

    트리거 (paper 또는 news) → 기술 카테고리 라벨 → 회사별 영향 가설 생성
    → T+5d 검증 (메인 KPI), T+1d/T+30d 보조

    impact_direction:
      'positive' : 회사에 긍정적 영향 예상
      'neutral'  : 중립
      'negative' : 위협
    """
    __tablename__ = "hypothesis_logs"

    id = Column(Integer, primary_key=True, index=True)
    trigger_type = Column(String(20), nullable=False)  # 'paper', 'news'
    trigger_paper_id = Column(Integer, ForeignKey("papers.id"), nullable=True)
    trigger_news_id = Column(Integer, ForeignKey("competitor_news.id"), nullable=True)
    trigger_date = Column(Date, nullable=False)  # 발표일/공시일
    trigger_title = Column(String(500), nullable=True)  # 스냅샷 (원본 제거 대비)

    # 분류 스냅샷
    tech_categories = Column(JSON, nullable=False, default=list)
    # 형식: [{"id": "multiplex_microarray", "confidence": 0.92}, ...]

    # 회사별 가설
    company_code = Column(String(50), ForeignKey("competitor_companies.code"), nullable=False)
    impact_direction = Column(String(10), nullable=False)  # 'positive'/'neutral'/'negative'
    impact_score = Column(Numeric(4, 2), nullable=False)  # -1.00 ~ 1.00
    fit_score_snapshot = Column(Numeric(3, 2), nullable=True)  # 가설 생성 시점 fit
    rationale = Column(Text, nullable=False)  # LLM 생성 가설 본문

    # 검증 (주가)
    validation_t1d_return = Column(Numeric(8, 5), nullable=True)
    validation_t5d_return = Column(Numeric(8, 5), nullable=True)  # 메인 KPI
    validation_t30d_return = Column(Numeric(8, 5), nullable=True)
    market_t1d_return = Column(Numeric(8, 5), nullable=True)
    market_t5d_return = Column(Numeric(8, 5), nullable=True)
    market_t30d_return = Column(Numeric(8, 5), nullable=True)
    abnormal_t1d = Column(Numeric(8, 5), nullable=True)  # 종목 - 시장
    abnormal_t5d = Column(Numeric(8, 5), nullable=True)  # 메인 KPI
    abnormal_t30d = Column(Numeric(8, 5), nullable=True)
    benchmark_ticker = Column(String(20), nullable=True)  # 벤치마크 지수 코드

    # 적중 여부 (abnormal_t5d 부호와 impact_direction 일치 여부)
    hit_t5d = Column(Boolean, nullable=True)

    # 보조 시그널 (Phase A-3) — abnormal_t5d 단일 의존 회피
    volume_zscore_t1d = Column(Numeric(8, 3), nullable=True)
    # 트리거 직후 첫 거래일의 거래량 z-score (직전 60 영업일 분포 기준)
    # |z| >= 2.0 이면 비정상 거래량 — 정보 누출/거래 집중 신호
    market_cap_change_t5d = Column(Numeric(8, 5), nullable=True)
    # T+5d 시가총액 변화율 — abnormal_t5d 와 평소 동일하지만 유증/감자/배당 등에서 분기

    # LLM 정성 보강 (Phase B) — 룰 결정 위에 정성 분석 레이어
    qualitative_score = Column(Numeric(4, 2), nullable=True)
    # LLM의 정성 점수 (-1.0 ~ 1.0). 룰 impact_score 와 별도로 비교/모니터링.
    qualitative_rationale = Column(Text, nullable=True)
    # LLM 보강 rationale — 트리거 본문 + fit context 반영한 정성 분석
    qualitative_override = Column(Boolean, nullable=True)
    # True 이면 LLM 이 룰 방향(direction)을 뒤집을 정황 발견. drift 모니터링 KPI.
    qualitative_version = Column(String(30), nullable=True)
    # 정성 보강기 버전 — 'qual-v1-2026-05' 등. 미보강 가설은 NULL.

    validation_status = Column(String(20), default="pending")
    # 'pending' / 'partial' (T+1d) / 'validated' (T+5d 완료) / 'closed' (T+30d) / 'no_data'

    validated_at = Column(DateTime, nullable=True)
    classifier_version = Column(String(30), nullable=True)
    generator_version = Column(String(30), nullable=True)
    notes = Column(Text, nullable=True)

    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    __table_args__ = (
        Index("idx_hypothesis_logs_company", "company_code"),
        Index("idx_hypothesis_logs_trigger_date", "trigger_date"),
        Index("idx_hypothesis_logs_status", "validation_status"),
        Index("idx_hypothesis_logs_trigger", "trigger_type", "trigger_paper_id", "trigger_news_id"),
        Index("idx_hypothesis_logs_hit", "hit_t5d"),
    )


class StrategicIntelAuditLog(Base):
    """Strategic Intel 접근 audit 로그 (Phase E)

    super_admin 의 조회·발행·접근을 모두 기록 — 외부 유출 추적 + 운영 가시성.
    민감 정보(IP)는 hash 로만 보관.
    """
    __tablename__ = "strategic_intel_audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_email = Column(String(255), nullable=True, index=True)
    # 접근 시점의 super_admin email — User 객체에서 추출, 향후 이메일 변경 시에도 보존
    action_type = Column(String(50), nullable=False)
    # 'access_page' | 'view_report' | 'view_hypothesis' | 'generate_report' |
    # 'view_matrix' | 'view_stats' | 'view_unhit_clusters'
    resource_type = Column(String(50), nullable=True)
    # 'report' | 'hypothesis' | 'page' | 'matrix' | 'stats' | 'unhit_clusters'
    resource_id = Column(String(100), nullable=True)
    # report.id / hypothesis.id / page name 등
    metadata_json = Column(JSON, nullable=True)
    # 추가 컨텍스트 (예: 발행 month, 필터 파라미터)
    ip_hash = Column(String(64), nullable=True)
    user_agent = Column(String(500), nullable=True)
    accessed_at = Column(DateTime, default=utc_now, index=True)

    __table_args__ = (
        Index("idx_si_audit_user_time", "user_email", "accessed_at"),
        Index("idx_si_audit_action", "action_type", "accessed_at"),
        Index("idx_si_audit_resource", "resource_type", "resource_id"),
    )


class StrategicIntelReport(Base):
    """Strategic Intel 경영진 리포트 (이벤트 트리거 + 월말 종합)

    내부 의사결정 보조용 — 외부 노출 금지.
    """
    __tablename__ = "strategic_intel_reports"

    id = Column(Integer, primary_key=True, index=True)
    report_type = Column(String(20), nullable=False)  # 'event' | 'monthly'
    period_start = Column(Date, nullable=False)
    period_end = Column(Date, nullable=False)

    title = Column(String(300), nullable=False)
    summary = Column(Text, nullable=True)  # 한 줄 요약
    content = Column(Text, nullable=False)  # markdown 본문

    # 트리거 / 집계 메타데이터
    trigger_hypothesis_id = Column(Integer, ForeignKey("hypothesis_logs.id"), nullable=True)
    hypothesis_ids = Column(JSON, nullable=False, default=list)  # 본 리포트에 포함된 가설 IDs
    metrics = Column(JSON, nullable=True)  # {"hit_rate": 0.62, "n_hypotheses": 35, ...}

    generator_version = Column(String(30), nullable=True)
    generated_at = Column(DateTime, default=utc_now)
    created_at = Column(DateTime, default=utc_now)

    __table_args__ = (
        Index("idx_strategic_reports_type", "report_type"),
        Index("idx_strategic_reports_period", "period_start", "period_end"),
        Index("idx_strategic_reports_trigger", "trigger_hypothesis_id"),
    )
