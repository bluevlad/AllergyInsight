"""Organization Models - Phase 1: 병원 서비스 확장"""
from datetime import datetime
from enum import Enum
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Index, Text
from sqlalchemy.orm import relationship
from .connection import Base


# ===== Enum Definitions =====

class UserRole(str, Enum):
    """사용자 역할 정의"""
    # 일반 서비스 (B2C)
    PATIENT = "patient"          # 환자/일반 사용자

    # 병원 서비스 (B2B)
    HOSPITAL_ADMIN = "hospital_admin"  # 병원 관리자
    DOCTOR = "doctor"            # 의사
    NURSE = "nurse"              # 간호사
    LAB_TECH = "lab_tech"        # 검사 담당자

    # 플랫폼 운영
    SUPER_ADMIN = "super_admin"  # 시스템 관리자

    # Legacy (하위 호환)
    USER = "user"                # 기존 일반 사용자 (→ patient로 마이그레이션)
    ADMIN = "admin"              # 기존 관리자 (→ super_admin으로 마이그레이션)

    @classmethod
    def staff_roles(cls):
        """병원 직원 역할 목록"""
        return [cls.DOCTOR, cls.NURSE, cls.LAB_TECH, cls.HOSPITAL_ADMIN]

    @classmethod
    def admin_roles(cls):
        """관리자 역할 목록"""
        return [cls.SUPER_ADMIN, cls.ADMIN]


class OrganizationType(str, Enum):
    """조직 유형"""
    HOSPITAL = "hospital"        # 병원
    CLINIC = "clinic"            # 의원
    RESEARCH = "research"        # 연구기관
    LAB = "lab"                  # 검사기관


class OrganizationStatus(str, Enum):
    """조직 상태"""
    PENDING = "pending"          # 승인 대기
    ACTIVE = "active"            # 활성
    SUSPENDED = "suspended"      # 정지
    EXPIRED = "expired"          # 만료


class HospitalPatientStatus(str, Enum):
    """병원-환자 연결 상태"""
    PENDING_CONSENT = "pending_consent"  # 동의 대기
    ACTIVE = "active"            # 활성
    INACTIVE = "inactive"        # 비활성
    TRANSFERRED = "transferred"  # 전원


# ===== Organization Models =====

class Organization(Base):
    """조직 (병원/의원/연구기관)"""
    __tablename__ = "organizations"

    id = Column(Integer, primary_key=True, index=True)

    # 기본 정보
    name = Column(String(200), nullable=False)
    org_type = Column(String(20), default=OrganizationType.HOSPITAL.value)

    # 사업자 정보
    business_number = Column(String(20), unique=True, nullable=True)  # 사업자등록번호
    license_number = Column(String(50), nullable=True)  # 의료기관 허가번호

    # 연락처
    address = Column(String(500), nullable=True)
    phone = Column(String(20), nullable=True)
    email = Column(String(255), nullable=True)

    # 구독/상태
    subscription_plan = Column(String(30), default="basic")  # basic, professional, enterprise
    status = Column(String(20), default=OrganizationStatus.PENDING.value)

    # 메타데이터
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)  # 구독 만료일

    # 관계
    members = relationship("OrganizationMember", back_populates="organization", cascade="all, delete-orphan")
    hospital_patients = relationship("HospitalPatient", back_populates="organization", cascade="all, delete-orphan")

    __table_args__ = (
        Index('idx_organizations_status', 'status'),
        Index('idx_organizations_type', 'org_type'),
    )


class OrganizationMember(Base):
    """조직 멤버 (직원)"""
    __tablename__ = "organization_members"

    id = Column(Integer, primary_key=True, index=True)

    # 관계
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    # 역할 (조직 내 역할)
    role = Column(String(30), nullable=False)  # doctor, nurse, lab_tech, hospital_admin

    # 직원 정보
    department = Column(String(100), nullable=True)  # 소속 부서
    employee_number = Column(String(50), nullable=True)  # 사번
    license_number = Column(String(50), nullable=True)  # 면허번호 (의사/간호사)

    # 상태
    is_active = Column(Boolean, default=True)
    joined_at = Column(DateTime, default=datetime.utcnow)
    left_at = Column(DateTime, nullable=True)

    # 관계
    organization = relationship("Organization", back_populates="members")
    user = relationship("User", back_populates="organization_memberships")

    __table_args__ = (
        Index('idx_org_members_org', 'organization_id'),
        Index('idx_org_members_user', 'user_id'),
        Index('idx_org_members_role', 'role'),
    )


class HospitalPatient(Base):
    """병원-환자 연결"""
    __tablename__ = "hospital_patients"

    id = Column(Integer, primary_key=True, index=True)

    # 관계
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    patient_user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    # 병원 내 환자 정보
    patient_number = Column(String(50), nullable=True)  # 병원 내 환자번호

    # 동의서
    consent_signed = Column(Boolean, default=False)
    consent_date = Column(DateTime, nullable=True)
    consent_document_url = Column(String(500), nullable=True)

    # 담당 의료진
    assigned_doctor_id = Column(Integer, ForeignKey("organization_members.id"), nullable=True)

    # 상태
    status = Column(String(30), default=HospitalPatientStatus.PENDING_CONSENT.value)

    # 메타데이터
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 관계
    organization = relationship("Organization", back_populates="hospital_patients")
    patient_user = relationship("User", back_populates="hospital_connections", foreign_keys=[patient_user_id])
    assigned_doctor = relationship("OrganizationMember", foreign_keys=[assigned_doctor_id])

    __table_args__ = (
        Index('idx_hospital_patients_org', 'organization_id'),
        Index('idx_hospital_patients_patient', 'patient_user_id'),
        Index('idx_hospital_patients_status', 'status'),
    )
