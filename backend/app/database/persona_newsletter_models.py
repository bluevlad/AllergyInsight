"""페르소나 적응형 뉴스레터 — Phase 1 데이터 모델.

NewsletterPersona: 페르소나 카탈로그 (시드 정의).
NewsletterTopicRequest: 주제 요청·결과 로그 (수요 신호 정본).

상세 설계: Claude-Opus-bluevlad/services/allergyinsight/plans/
            persona-adaptive-newsletter-phase1-design.md
"""
from __future__ import annotations

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Float,
    Index,
    Integer,
    String,
    Text,
)

from ..utils.timezone import utc_now
from .connection import Base


class NewsletterPersona(Base):
    """뉴스레터 페르소나 카탈로그.

    수신자의 역할·목적을 6종 페르소나로 정의하고, section_weights 로
    페르소나별 콘텐츠 구성(섹션·가중치·카테고리 부스트)을 표현한다.
    """

    __tablename__ = "newsletter_personas"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(30), unique=True, nullable=False, index=True)
    label = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    default_depth = Column(String(20), nullable=False, default="practical")
    guardrail_profile = Column(String(20), nullable=False, default="professional")
    section_weights = Column(JSON, nullable=False, default=dict)
    display_order = Column(Integer, nullable=False, default=0)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    def __repr__(self) -> str:
        return f"<NewsletterPersona(code={self.code!r})>"


class NewsletterTopicRequest(Base):
    """뉴스레터 주제 요청·결과 로그 — 수요 기반 역량 확장 루프의 학습 신호 정본.

    선택(select)/변형(transform) 요청을 결과(coverage)와 함께 적재한다.
    persona_code 는 FK 가 아닌 스냅샷 — 페르소나 정의 변경과 무관하게
    과거 요청의 의미를 보존한다 (수요 분석 시계열 정합성).
    """

    __tablename__ = "newsletter_topic_requests"

    id = Column(Integer, primary_key=True, index=True)
    request_id = Column(String(64), unique=True, nullable=False, index=True)
    tenant_id = Column(String(50), nullable=False, index=True)
    persona_code = Column(String(30), nullable=False, index=True)
    request_type = Column(String(20), nullable=False)  # 'select' | 'transform'
    topic = Column(String(500), nullable=True)
    topic_hash = Column(String(64), nullable=True, index=True)
    intent = Column(JSON, nullable=True)
    coverage = Column(String(20), nullable=False)  # 'covered' | 'unsupported'
    confidence = Column(Float, nullable=True)
    served = Column(Boolean, nullable=False, default=False)
    fallback_reason = Column(String(40), nullable=True)  # out_of_domain | not_indexed_yet
    elapsed_ms = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=utc_now, index=True)

    __table_args__ = (
        Index("idx_topic_req_persona_created", "persona_code", "created_at"),
        Index("idx_topic_req_coverage_created", "coverage", "created_at"),
    )

    def __repr__(self) -> str:
        return (
            f"<NewsletterTopicRequest(request_id={self.request_id!r}, "
            f"coverage={self.coverage!r})>"
        )


class CrawlExpansionJob(Base):
    """변형 요청의 비동기 크롤 확장 job — Phase 2.

    `expandable` 판정된 transform 요청에 대해 외부 소스(PubMed 등)를 크롤·인덱싱하고,
    완료 시 NewsletterPlatform 으로 webhook 콜백을 발신한다.
    request_id 로 유발 topic-request 와 연결된다 (별도 FK 없음).
    """

    __tablename__ = "crawl_expansion_jobs"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(String(64), unique=True, nullable=False, index=True)
    request_id = Column(String(64), nullable=True, index=True)
    tenant_id = Column(String(50), nullable=False, default="allergy-insight")
    topic = Column(String(500), nullable=False)
    topic_hash = Column(String(64), nullable=True, index=True)
    source = Column(String(30), nullable=False)  # 'pubmed' 등
    status = Column(String(20), nullable=False, default="pending")  # pending|collecting|ready|failed
    callback_url = Column(String(1000), nullable=True)
    result_summary = Column(JSON, nullable=True)
    error = Column(String(500), nullable=True)
    eta_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utc_now, index=True)
    started_at = Column(DateTime, nullable=True)
    finished_at = Column(DateTime, nullable=True)

    __table_args__ = (
        Index("idx_crawl_job_status_created", "status", "created_at"),
    )

    def __repr__(self) -> str:
        return (
            f"<CrawlExpansionJob(job_id={self.job_id!r}, status={self.status!r})>"
        )
