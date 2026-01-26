"""Database Models"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Date, ForeignKey, JSON, Index, Text
from sqlalchemy.orm import relationship
from .connection import Base


class User(Base):
    """User model - supports both Google OAuth and simple registration"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)

    # Common fields
    name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, nullable=True)

    # Auth type: 'google' or 'simple'
    auth_type = Column(String(20), nullable=False)

    # Google OAuth fields
    google_id = Column(String(255), unique=True, nullable=True)
    profile_image = Column(String(500), nullable=True)

    # Simple registration fields
    phone = Column(String(20), nullable=True)  # Hashed
    birth_date = Column(Date, nullable=True)
    access_pin_hash = Column(String(255), nullable=True)  # For simple login

    # Role: 확장된 역할 체계 지원
    # 'patient', 'doctor', 'nurse', 'lab_tech', 'hospital_admin', 'super_admin'
    # Legacy: 'user', 'admin'
    role = Column(String(20), default="user")

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)

    # Relationships
    diagnoses = relationship("UserDiagnosis", back_populates="user", foreign_keys="[UserDiagnosis.user_id]")
    registered_kits = relationship("DiagnosisKit", back_populates="registered_user", foreign_keys="[DiagnosisKit.registered_user_id]")

    # Phase 1: 조직 관련 관계 추가
    organization_memberships = relationship("OrganizationMember", back_populates="user", cascade="all, delete-orphan")
    hospital_connections = relationship("HospitalPatient", back_populates="patient_user", foreign_keys="[HospitalPatient.patient_user_id]")

    # Indexes
    __table_args__ = (
        Index('idx_users_google_id', 'google_id'),
        Index('idx_users_name_birth', 'name', 'birth_date'),
        Index('idx_users_role', 'role'),
    )

    def is_staff(self) -> bool:
        """병원 직원 역할인지 확인"""
        staff_roles = ['doctor', 'nurse', 'lab_tech', 'hospital_admin']
        return self.role in staff_roles

    def is_admin_role(self) -> bool:
        """관리자 역할인지 확인 (super_admin 또는 legacy admin)"""
        return self.role in ['super_admin', 'admin']


class DiagnosisKit(Base):
    """Diagnosis Kit - S-Blot 3 PLUS results"""
    __tablename__ = "diagnosis_kits"

    id = Column(Integer, primary_key=True, index=True)

    # Serial number: SGT-2024-XXXXX-XXXX
    serial_number = Column(String(30), unique=True, nullable=False, index=True)

    # PIN for verification (hashed)
    pin_hash = Column(String(255), nullable=False)
    pin_attempts = Column(Integer, default=0)

    # S-Blot 3 PLUS results (JSON)
    # Format: {"peanut": 3, "milk": 2, "egg": 0, ...}
    results = Column(JSON, nullable=False)
    diagnosis_date = Column(Date, nullable=False)

    # Registration status
    is_registered = Column(Boolean, default=False)
    registered_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    registered_at = Column(DateTime, nullable=True)

    # Phase 1: 병원에서 생성한 키트인 경우 조직 ID
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=True)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)

    # Relationships
    registered_user = relationship("User", back_populates="registered_kits", foreign_keys=[registered_user_id])
    user_diagnoses = relationship("UserDiagnosis", back_populates="kit")


class UserDiagnosis(Base):
    """User Diagnosis History"""
    __tablename__ = "user_diagnoses"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    kit_id = Column(Integer, ForeignKey("diagnosis_kits.id"), nullable=True)

    # Copy of results (preserved even if kit data changes)
    results = Column(JSON, nullable=False)
    diagnosis_date = Column(Date, nullable=False)

    # Cached prescription
    prescription = Column(JSON, nullable=True)

    # Phase 1: 병원에서 입력한 경우
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=True)
    entered_by = Column(Integer, ForeignKey("users.id"), nullable=True)  # 입력한 의료진
    doctor_note = Column(Text, nullable=True)  # 의사 소견

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="diagnoses", foreign_keys=[user_id])
    kit = relationship("DiagnosisKit", back_populates="user_diagnoses")

    # Indexes
    __table_args__ = (
        Index('idx_user_diagnoses_user', 'user_id'),
        Index('idx_user_diagnoses_org', 'organization_id'),
    )


class Paper(Base):
    """Research Paper - 논문 정보"""
    __tablename__ = "papers"

    id = Column(Integer, primary_key=True, index=True)

    # Identifiers
    pmid = Column(String(20), unique=True, nullable=True, index=True)  # PubMed ID
    doi = Column(String(100), unique=True, nullable=True)

    # Paper info
    title = Column(String(500), nullable=False)
    title_kr = Column(String(500), nullable=True)  # Korean translation
    authors = Column(String(1000), nullable=True)  # "Kim J, Lee S, et al."
    journal = Column(String(200), nullable=True)
    year = Column(Integer, nullable=True)

    # Content
    abstract = Column(String(5000), nullable=True)
    abstract_kr = Column(String(5000), nullable=True)

    # URLs
    url = Column(String(500), nullable=True)  # PubMed or DOI URL
    pdf_url = Column(String(500), nullable=True)

    # Paper type: 'research', 'review', 'guideline', 'meta_analysis'
    paper_type = Column(String(30), default="research")

    # Evidence level (GRADE): 'A', 'B', 'C', 'D'
    evidence_level = Column(String(10), nullable=True)

    # Guideline info
    is_guideline = Column(Boolean, default=False)
    guideline_org = Column(String(50), nullable=True)  # 'EAACI', 'AAAAI', 'WAO'

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    is_verified = Column(Boolean, default=False)  # Admin verified

    # Relationships
    allergen_links = relationship("PaperAllergenLink", back_populates="paper", cascade="all, delete-orphan")
    clinical_statements = relationship("ClinicalStatement", back_populates="paper")

    # Indexes
    __table_args__ = (
        Index('idx_papers_year', 'year'),
        Index('idx_papers_type', 'paper_type'),
    )


class PaperAllergenLink(Base):
    """Paper-Allergen Link - 논문과 알러젠 정보 연결"""
    __tablename__ = "paper_allergen_links"

    id = Column(Integer, primary_key=True, index=True)

    paper_id = Column(Integer, ForeignKey("papers.id", ondelete="CASCADE"), nullable=False)

    # Allergen code: 'peanut', 'milk', 'egg', etc. or 'general' for general allergy info
    allergen_code = Column(String(30), nullable=False, index=True)

    # Link type: what aspect of the allergen this paper covers
    # 'symptom', 'dietary', 'cross_reactivity', 'substitute', 'emergency', 'management', 'general'
    link_type = Column(String(30), nullable=False)

    # Specific item this paper supports (optional)
    # e.g., "전신 두드러기", "땅콩버터", "견과류" etc.
    specific_item = Column(String(200), nullable=True)

    # Relevance score (0.0 - 1.0)
    relevance_score = Column(Integer, default=80)  # 0-100 for simplicity

    # Note about the citation
    note = Column(String(500), nullable=True)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    paper = relationship("Paper", back_populates="allergen_links")

    # Indexes
    __table_args__ = (
        Index('idx_paper_allergen_links_allergen', 'allergen_code'),
        Index('idx_paper_allergen_links_type', 'link_type'),
        Index('idx_paper_allergen_links_allergen_type', 'allergen_code', 'link_type'),
    )
