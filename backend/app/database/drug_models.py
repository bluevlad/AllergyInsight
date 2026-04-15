"""약물 정보 데이터 모델

학술 전용 알러지 치료 Agent를 위한 약물·성분·병태생리 테이블.
상업정보(가격·제조사·브랜드 UI 노출)는 배제 — ADR-007 참조.

관련 문서:
- services/allergyinsight/plans/academic-drug-agent-plan.md
- services/allergyinsight/adr/007-commercial-info-exclusion.md
- services/allergyinsight/adr/008-pathophysiology-knowledge-graph.md
"""
from sqlalchemy import (
    Column, Integer, String, Text, Boolean, DateTime,
    ForeignKey, JSON, Index, Float, CheckConstraint, UniqueConstraint,
)

from .connection import Base
from ..utils.timezone import utc_now


class DrugProduct(Base):
    """약물 제품 통합 테이블 (소스별 제품 메타데이터)

    - source: mfds_eyakeunyo | mfds_license | mfds_hfood | openfda | dailymed | dsld
    - product_type: drug | supplement
    - raw_jsonb: 원본 응답 보관 (재파싱·감사 추적용)
    """
    __tablename__ = "drug_products"

    id = Column(Integer, primary_key=True, index=True)
    source = Column(String(30), nullable=False)
    source_product_id = Column(String(100), nullable=False)

    atc_code = Column(String(10), nullable=True, index=True)
    rxcui = Column(String(20), nullable=True, index=True)
    kfda_item_seq = Column(String(30), nullable=True)

    name_kr = Column(String(300), nullable=True)
    name_en = Column(String(300), nullable=True)

    product_type = Column(String(20), nullable=False, default="drug")
    is_prescription = Column(Boolean, nullable=False, default=False)

    routes = Column(JSON, nullable=True)
    indications = Column(Text, nullable=True)
    dosage = Column(Text, nullable=True)
    warnings = Column(Text, nullable=True)

    raw_jsonb = Column(JSON, nullable=True)

    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    __table_args__ = (
        UniqueConstraint('source', 'source_product_id', name='uq_drug_product_source'),
        Index('idx_drug_product_atc', 'atc_code'),
        Index('idx_drug_product_rxcui', 'rxcui'),
        Index('idx_drug_product_type', 'product_type'),
        Index('idx_drug_product_updated', 'updated_at'),
        CheckConstraint("product_type IN ('drug', 'supplement')", name='ck_drug_product_type'),
    )


class DrugIngredient(Base):
    """성분 정규화 테이블 (RxNorm 기준)

    - rxcui가 unique key
    - moa: 작용 기전 (자유 텍스트)
    - pk: 약동학 (JSON: {bioavailability, t_half, cl, ...})
    - anticholinergic_score: ACB 점수 (0~3)
    """
    __tablename__ = "drug_ingredients"

    id = Column(Integer, primary_key=True, index=True)
    rxcui = Column(String(20), unique=True, nullable=False, index=True)
    inn = Column(String(200), nullable=False)
    atc_code = Column(String(10), nullable=True, index=True)

    moa = Column(Text, nullable=True)
    pk = Column(JSON, nullable=True)
    anticholinergic_score = Column(Integer, nullable=True)

    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    __table_args__ = (
        Index('idx_drug_ingredient_inn', 'inn'),
        Index('idx_drug_ingredient_atc', 'atc_code'),
        CheckConstraint(
            "anticholinergic_score IS NULL OR anticholinergic_score BETWEEN 0 AND 3",
            name='ck_drug_ingredient_acb_range',
        ),
    )


class DrugSourceRaw(Base):
    """원본 응답 보관 (재파싱·감사 추적용)

    소스 API 포맷 변경에 대비해 raw payload를 그대로 보관.
    drug_products 테이블의 raw_jsonb와 별개로 시간순 이력을 남긴다.
    """
    __tablename__ = "drug_source_raws"

    id = Column(Integer, primary_key=True, index=True)
    source = Column(String(30), nullable=False)
    source_product_id = Column(String(100), nullable=False)
    fetched_at = Column(DateTime, default=utc_now, nullable=False)
    payload = Column(JSON, nullable=False)

    __table_args__ = (
        Index('idx_drug_source_raw_source_pid', 'source', 'source_product_id'),
        Index('idx_drug_source_raw_fetched', 'fetched_at'),
    )


class DrugIngestCursor(Base):
    """증분 수집 커서 (소스별 마지막 수집 시각·토큰)"""
    __tablename__ = "drug_ingest_cursors"

    source = Column(String(30), primary_key=True)
    last_updated_at = Column(DateTime, nullable=True)
    next_page_token = Column(String(500), nullable=True)
    last_run_at = Column(DateTime, default=utc_now, nullable=False)
    last_status = Column(String(20), nullable=True)
    last_error = Column(Text, nullable=True)


class Pathophysiology(Base):
    """병태생리 마스터 (알러지 치료 기전 태그)

    ADR-008 참조. 초기 15개 태그 시드는 seed_pathophysiology.py 에서 관리.
    """
    __tablename__ = "pathophysiologies"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), unique=True, nullable=False, index=True)
    name_kr = Column(String(200), nullable=False)
    name_en = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    reference_pmids = Column(JSON, nullable=True)

    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)


class SymptomPathophys(Base):
    """증상 → 병태생리 매핑 (다대다)

    allergen_master.id를 참조. 감수 필드 필수.
    """
    __tablename__ = "symptom_pathophys"

    id = Column(Integer, primary_key=True, index=True)
    symptom_id = Column(Integer, ForeignKey("allergen_master.id"), nullable=False, index=True)
    pathophys_id = Column(Integer, ForeignKey("pathophysiologies.id"), nullable=False, index=True)
    weight = Column(Integer, nullable=False)

    is_verified = Column(Boolean, nullable=False, default=False)
    verified_by = Column(String(100), nullable=True)
    verified_at = Column(DateTime, nullable=True)
    review_comment = Column(Text, nullable=True)

    created_at = Column(DateTime, default=utc_now, nullable=False)

    __table_args__ = (
        UniqueConstraint('symptom_id', 'pathophys_id', name='uq_symptom_pathophys'),
        CheckConstraint('weight BETWEEN 1 AND 5', name='ck_symptom_pathophys_weight'),
        Index('idx_symptom_pathophys_verified', 'is_verified'),
    )


class PathophysAtc(Base):
    """병태생리 → ATC 약리군 매핑

    role: first_line | adjunct | refractory
    """
    __tablename__ = "pathophys_atc"

    id = Column(Integer, primary_key=True, index=True)
    pathophys_id = Column(Integer, ForeignKey("pathophysiologies.id"), nullable=False, index=True)
    atc_prefix = Column(String(10), nullable=False)
    role = Column(String(20), nullable=False)
    reference_pmids = Column(JSON, nullable=True)

    is_verified = Column(Boolean, nullable=False, default=False)
    verified_by = Column(String(100), nullable=True)
    verified_at = Column(DateTime, nullable=True)
    review_comment = Column(Text, nullable=True)

    created_at = Column(DateTime, default=utc_now, nullable=False)

    __table_args__ = (
        UniqueConstraint('pathophys_id', 'atc_prefix', 'role', name='uq_pathophys_atc'),
        CheckConstraint("role IN ('first_line', 'adjunct', 'refractory')", name='ck_pathophys_atc_role'),
        Index('idx_pathophys_atc_prefix', 'atc_prefix'),
    )


class UnmappedIngredient(Base):
    """RxNorm 매핑 실패 성분 큐 (관리자 검토 대기열)"""
    __tablename__ = "unmapped_ingredients"

    id = Column(Integer, primary_key=True, index=True)
    source = Column(String(30), nullable=False)
    source_product_id = Column(String(100), nullable=False)
    ingredient_text = Column(String(500), nullable=False)
    attempted_at = Column(DateTime, default=utc_now, nullable=False)
    resolved = Column(Boolean, nullable=False, default=False)
    resolved_rxcui = Column(String(20), nullable=True)

    __table_args__ = (
        Index('idx_unmapped_ingredient_resolved', 'resolved'),
        Index('idx_unmapped_ingredient_source', 'source', 'source_product_id'),
    )
