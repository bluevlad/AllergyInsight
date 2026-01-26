"""Clinical Document Models - 의사 전용 임상 문서 모델"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, Index
from sqlalchemy.orm import relationship
from .connection import Base


class ClinicalStatement(Base):
    """Clinical Statement - 근거 기반 임상 진술문"""
    __tablename__ = "clinical_statements"

    id = Column(Integer, primary_key=True, index=True)

    # 진술문 내용
    statement_en = Column(Text, nullable=False)  # 영문 원문
    statement_kr = Column(Text, nullable=True)   # 한국어 번역

    # 적용 범위
    allergen_code = Column(String(30), index=True)  # 'shrimp', 'peanut', 'general'
    context = Column(String(50), nullable=False)     # 'cross_reactivity', 'avoidance', 'treatment', 'diagnosis', 'pathophysiology'

    # 근거 수준 (GRADE)
    evidence_level = Column(String(10), nullable=True)      # 'A', 'B', 'C', 'D'
    recommendation_grade = Column(String(10), nullable=True) # '1A', '1B', '2A', '2B'

    # 출처
    paper_id = Column(Integer, ForeignKey("papers.id"), nullable=True)
    source_location = Column(String(100), nullable=True)  # "Results, p.198"

    # 메타데이터
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)

    # Relationships
    paper = relationship("Paper", back_populates="clinical_statements")

    # Indexes
    __table_args__ = (
        Index('idx_clinical_statements_allergen', 'allergen_code'),
        Index('idx_clinical_statements_context', 'context'),
        Index('idx_clinical_statements_allergen_context', 'allergen_code', 'context'),
    )

    def get_grade_display(self) -> str:
        """GRADE 표시 문자열 반환"""
        grade_map = {
            'A': '⊕⊕⊕⊕',
            'B': '⊕⊕⊕◯',
            'C': '⊕⊕◯◯',
            'D': '⊕◯◯◯',
        }
        return grade_map.get(self.evidence_level, '')

    def get_evidence_label(self) -> str:
        """근거 수준 라벨 반환"""
        label_map = {
            'A': 'High',
            'B': 'Moderate',
            'C': 'Low',
            'D': 'Very Low',
        }
        return label_map.get(self.evidence_level, '')
