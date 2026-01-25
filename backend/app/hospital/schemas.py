"""Hospital Schemas - Phase 2: 병원-환자 관리"""
from datetime import datetime, date
from typing import Optional, List
from pydantic import BaseModel, Field, EmailStr

from ..database.organization_models import HospitalPatientStatus


# ===== Hospital Patient Schemas =====

class HospitalPatientBase(BaseModel):
    """병원 환자 기본 스키마"""
    patient_number: Optional[str] = Field(None, max_length=50, description="병원 내 환자번호")


class HospitalPatientCreate(HospitalPatientBase):
    """병원 환자 등록 요청 (기존 사용자 연결)"""
    patient_user_id: int = Field(..., description="환자 사용자 ID")
    assigned_doctor_id: Optional[int] = Field(None, description="담당 의사 멤버 ID")


class HospitalPatientCreateNew(HospitalPatientBase):
    """병원 환자 신규 등록 요청 (신규 사용자 생성)"""
    name: str = Field(..., min_length=2, max_length=100, description="환자 이름")
    phone: str = Field(..., max_length=20, description="환자 전화번호")
    birth_date: Optional[date] = Field(None, description="생년월일")
    assigned_doctor_id: Optional[int] = Field(None, description="담당 의사 멤버 ID")


class HospitalPatientUpdate(BaseModel):
    """병원 환자 정보 수정"""
    patient_number: Optional[str] = None
    assigned_doctor_id: Optional[int] = None
    status: Optional[HospitalPatientStatus] = None


class HospitalPatientResponse(HospitalPatientBase):
    """병원 환자 응답"""
    id: int
    organization_id: int
    patient_user_id: int
    consent_signed: bool
    consent_date: Optional[datetime] = None
    status: HospitalPatientStatus
    created_at: datetime
    updated_at: datetime

    # Patient user info
    patient_name: Optional[str] = None
    patient_phone: Optional[str] = None
    patient_birth_date: Optional[date] = None

    # Assigned doctor info
    assigned_doctor_id: Optional[int] = None
    assigned_doctor_name: Optional[str] = None

    # Stats
    diagnosis_count: Optional[int] = None
    last_diagnosis_date: Optional[date] = None

    class Config:
        from_attributes = True


class HospitalPatientListResponse(BaseModel):
    """병원 환자 목록 응답"""
    items: List[HospitalPatientResponse]
    total: int
    page: int
    page_size: int


# ===== Patient Consent Schemas =====

class PatientConsentRequest(BaseModel):
    """환자 동의서 서명 요청"""
    consent_type: str = Field(default="general", description="동의서 유형")
    consent_agreed: bool = Field(..., description="동의 여부")
    signature_data: Optional[str] = Field(None, description="서명 데이터 (base64)")


class PatientConsentResponse(BaseModel):
    """환자 동의서 응답"""
    hospital_patient_id: int
    consent_signed: bool
    consent_date: Optional[datetime] = None
    status: HospitalPatientStatus
    message: str


# ===== Patient Search Schemas =====

class PatientSearchRequest(BaseModel):
    """환자 검색 요청"""
    query: Optional[str] = Field(None, description="검색어 (이름, 전화번호, 환자번호)")
    status: Optional[HospitalPatientStatus] = None
    assigned_doctor_id: Optional[int] = None
    has_diagnosis: Optional[bool] = None


# ===== Patient Diagnosis Schemas =====

class PatientDiagnosisResponse(BaseModel):
    """환자 진단 결과 응답"""
    id: int
    diagnosis_date: date
    results: dict
    prescription: Optional[dict] = None
    doctor_note: Optional[str] = None
    entered_by_name: Optional[str] = None
    created_at: datetime


class PatientDiagnosisListResponse(BaseModel):
    """환자 진단 목록 응답"""
    patient_id: int
    patient_name: str
    items: List[PatientDiagnosisResponse]
    total: int


class PatientDiagnosisCreate(BaseModel):
    """환자 진단 입력 요청 (병원에서 입력)"""
    diagnosis_date: date = Field(..., description="진단 날짜")
    results: dict = Field(..., description="진단 결과 (알러젠별 등급)")
    doctor_note: Optional[str] = Field(None, max_length=2000, description="의사 소견")


# ===== Hospital Dashboard Schemas =====

class HospitalDashboardStats(BaseModel):
    """병원 대시보드 통계"""
    total_patients: int
    active_patients: int
    pending_consent: int
    today_diagnoses: int
    this_month_diagnoses: int

    # 최근 활동
    recent_patients: List[HospitalPatientResponse]
    recent_diagnoses: List[PatientDiagnosisResponse]


class DoctorPatientStats(BaseModel):
    """의사별 환자 통계"""
    doctor_id: int
    doctor_name: str
    total_patients: int
    this_month_diagnoses: int
