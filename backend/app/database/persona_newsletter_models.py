"""페르소나 적응형 뉴스레터 — 데이터 모델 (Phase 1~4).

Phase 1: NewsletterPersona, NewsletterTopicRequest
Phase 2: CrawlExpansionJob
Phase 3: NewsletterContentBlock
Phase 4: NewsletterEngagement, EvolutionProposal

상세 설계: Claude-Opus-bluevlad/services/allergyinsight/plans/
            persona-adaptive-newsletter-plan.md
"""
from __future__ import annotations

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    Date,
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


class NewsletterContentBlock(Base):
    """페르소나 조건부 생성 콘텐츠 캐시 — Phase 3.

    페르소나별 LLM 편집 요약(editorial)을 (페르소나 × 일자) 단위로 1회 생성·캐시한다.
    세그먼트 단위 생성 — 수신자 1인 단위 LLM 호출을 피한다.
    """

    __tablename__ = "newsletter_content_blocks"

    id = Column(Integer, primary_key=True, index=True)
    persona_code = Column(String(30), nullable=False, index=True)
    block_type = Column(String(30), nullable=False, default="editorial")
    period_key = Column(String(20), nullable=False)  # 'YYYY-MM-DD' — 캐시 키
    payload = Column(JSON, nullable=False)  # {text, model, grounding_score}
    model = Column(String(80), nullable=True)
    grounding_score = Column(Float, nullable=True)
    generated_at = Column(DateTime, default=utc_now)

    __table_args__ = (
        Index(
            "idx_content_block_lookup",
            "persona_code",
            "block_type",
            "period_key",
            unique=True,
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<NewsletterContentBlock(persona={self.persona_code!r}, "
            f"type={self.block_type!r}, period={self.period_key!r})>"
        )


class NewsletterEngagement(Base):
    """수신자 인게이지먼트 — Phase 4.

    NewsletterPlatform 이 전달하는 오픈·클릭 이벤트. 수요 분석의 보조 신호.
    """

    __tablename__ = "newsletter_engagements"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String(50), nullable=False, default="allergy-insight", index=True)
    persona_code = Column(String(30), nullable=True, index=True)
    section_type = Column(String(40), nullable=True)
    content_ref = Column(String(120), nullable=True)
    event = Column(String(20), nullable=False)  # 'open' | 'click'
    occurred_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utc_now, index=True)

    __table_args__ = (
        Index("idx_engagement_persona_created", "persona_code", "created_at"),
    )

    def __repr__(self) -> str:
        return (
            f"<NewsletterEngagement(persona={self.persona_code!r}, "
            f"event={self.event!r})>"
        )


class EvolutionProposal(Base):
    """운영자용 역량 고도화 제안 — Phase 4.

    수요 로그·인게이지먼트를 주기적으로 분석해 자동 생성. 운영자가 승인/반려한다.
    """

    __tablename__ = "evolution_proposals"

    id = Column(Integer, primary_key=True, index=True)
    period_start = Column(Date, nullable=True)
    period_end = Column(Date, nullable=True)
    # new_source | keyword_expansion | template_tuning | section_revision
    proposal_type = Column(String(40), nullable=False)
    title = Column(String(200), nullable=False)
    recommended_action = Column(Text, nullable=False)
    evidence = Column(JSON, nullable=True)  # 수요 근거 요약
    priority = Column(String(10), nullable=False, default="medium")  # high|medium|low
    status = Column(String(20), nullable=False, default="pending")  # pending|approved|rejected
    reviewed_by = Column(String(120), nullable=True)
    review_note = Column(String(500), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utc_now, index=True)

    __table_args__ = (
        Index("idx_evolution_status_created", "status", "created_at"),
    )

    def __repr__(self) -> str:
        return (
            f"<EvolutionProposal(id={self.id}, type={self.proposal_type!r}, "
            f"status={self.status!r})>"
        )
