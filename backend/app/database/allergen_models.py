"""알러젠 마스터 데이터 모델

allergen_master 테이블: SGTi-Allergy Screen PLUS 119종 알러젠 정보
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, Index

from .connection import Base


class AllergenMaster(Base):
    """알러젠 마스터 데이터"""
    __tablename__ = "allergen_master"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(10), unique=True, nullable=False, index=True)
    name_kr = Column(String(100), nullable=False)
    name_en = Column(String(200), nullable=False)
    category = Column(String(30), nullable=False)   # mite, dust, animal, ...
    type = Column(String(20), nullable=False)        # food, inhalant, contact, venom
    description = Column(Text, nullable=True)
    note = Column(String(500), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    sort_order = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, nullable=True, onupdate=datetime.utcnow)

    __table_args__ = (
        Index('idx_allergen_master_category', 'category'),
        Index('idx_allergen_master_type', 'type'),
        Index('idx_allergen_master_category_type', 'category', 'type'),
        Index('idx_allergen_master_is_active', 'is_active'),
    )

    def to_dict(self) -> dict:
        return {
            "code": self.code,
            "name_kr": self.name_kr,
            "name_en": self.name_en,
            "category": self.category,
            "type": self.type,
            "description": self.description,
            "note": self.note,
            "is_active": self.is_active,
            "sort_order": self.sort_order,
        }
