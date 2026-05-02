"""임상 이미지 갤러리 모델 (Phase 4 P4-PR1)

논문/전문기관 출처의 알러지 임상 이미지를 알러젠/증상별로 저장하고
비회원 페이지에서 단방향(갤러리) 으로만 노출한다.

원칙:
- 사용자 업로드/비교는 제공하지 않는다 (의료기기 인허가 영역 회피)
- 모든 이미지는 라이선스(CC-BY/CC0/Public Domain) + attribution 필수
- 본 PR에서는 스키마/조회 API만. 실제 이미지 수집은 별도 PR로 분리
"""
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Index,
    Integer,
    JSON,
    String,
    Text,
)

from .connection import Base
from ..utils.timezone import utc_now


class ClinicalImage(Base):
    """알러지 임상 이미지 메타데이터.

    이미지 자체는 외부 저장소(image_url)에 두고, 본 테이블은 메타·라이선스·
    출처·태그만 저장한다. 라이선스 컬럼은 nullable 이지만 운영 데이터에서는
    필수 (수집 파이프라인에서 검증).
    """
    __tablename__ = "clinical_images"

    id = Column(Integer, primary_key=True, index=True)

    # 분류 (알러젠 코드 또는 증상 키워드 — 둘 중 하나 이상 권장)
    allergen_code = Column(String(30), nullable=True, index=True)
    symptom_keywords = Column(JSON, nullable=True)   # ["urticaria", "anaphylaxis"]
    body_part = Column(String(50), nullable=True)    # face, lips, hands, generalized
    severity_level = Column(String(20), nullable=True)  # mild | moderate | severe

    # 이미지
    image_url = Column(String(800), nullable=False)
    thumbnail_url = Column(String(800), nullable=True)
    width = Column(Integer, nullable=True)
    height = Column(Integer, nullable=True)

    # 캡션
    caption_kr = Column(Text, nullable=True)
    caption_en = Column(Text, nullable=True)

    # 출처 (논문/전문기관)
    source_type = Column(String(30), nullable=False, default="pubmed")  # pubmed | pmc | journal | society
    paper_pmcid = Column(String(30), nullable=True, index=True)
    paper_pmid = Column(String(30), nullable=True, index=True)
    paper_doi = Column(String(200), nullable=True)
    paper_title = Column(String(500), nullable=True)
    paper_year = Column(Integer, nullable=True)

    # 라이선스 (CC-BY / CC-BY-NC / CC0 / Public Domain 등) — 표준 SPDX 식별자 권장
    license = Column(String(40), nullable=True)
    license_url = Column(String(400), nullable=True)
    attribution = Column(String(500), nullable=True)  # "Author et al. (2023). Title."

    # 운영
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    indexed_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    __table_args__ = (
        Index("idx_clinical_images_allergen_active", "allergen_code", "is_active"),
        Index("idx_clinical_images_source", "source_type", "paper_pmcid"),
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "allergen_code": self.allergen_code,
            "symptom_keywords": self.symptom_keywords or [],
            "body_part": self.body_part,
            "severity_level": self.severity_level,
            "image_url": self.image_url,
            "thumbnail_url": self.thumbnail_url,
            "width": self.width,
            "height": self.height,
            "caption_kr": self.caption_kr,
            "caption_en": self.caption_en,
            "source": {
                "type": self.source_type,
                "pmcid": self.paper_pmcid,
                "pmid": self.paper_pmid,
                "doi": self.paper_doi,
                "title": self.paper_title,
                "year": self.paper_year,
            },
            "license": {
                "name": self.license,
                "url": self.license_url,
                "attribution": self.attribution,
            },
            "indexed_at": self.indexed_at.isoformat() if self.indexed_at else None,
        }
