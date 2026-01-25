"""Organization Schemas - Phase 1"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field

from ..database.organization_models import OrganizationType, OrganizationStatus


# ===== Organization Schemas =====

class OrganizationBase(BaseModel):
    """조직 기본 스키마"""
    name: str = Field(..., min_length=2, max_length=200, description="조직명")
    org_type: OrganizationType = Field(default=OrganizationType.HOSPITAL, description="조직 유형")
    business_number: Optional[str] = Field(None, max_length=20, description="사업자등록번호")
    license_number: Optional[str] = Field(None, max_length=50, description="의료기관 허가번호")
    address: Optional[str] = Field(None, max_length=500, description="주소")
    phone: Optional[str] = Field(None, max_length=20, description="전화번호")
    email: Optional[EmailStr] = Field(None, description="이메일")


class OrganizationCreate(OrganizationBase):
    """조직 생성 요청"""
    pass


class OrganizationUpdate(BaseModel):
    """조직 수정 요청"""
    name: Optional[str] = Field(None, min_length=2, max_length=200)
    org_type: Optional[OrganizationType] = None
    business_number: Optional[str] = Field(None, max_length=20)
    license_number: Optional[str] = Field(None, max_length=50)
    address: Optional[str] = Field(None, max_length=500)
    phone: Optional[str] = Field(None, max_length=20)
    email: Optional[EmailStr] = None
    subscription_plan: Optional[str] = None
    status: Optional[OrganizationStatus] = None


class OrganizationResponse(OrganizationBase):
    """조직 응답"""
    id: int
    subscription_plan: str
    status: OrganizationStatus
    created_at: datetime
    updated_at: datetime
    expires_at: Optional[datetime] = None
    member_count: Optional[int] = None
    patient_count: Optional[int] = None

    class Config:
        from_attributes = True


class OrganizationListResponse(BaseModel):
    """조직 목록 응답"""
    items: List[OrganizationResponse]
    total: int
    page: int
    page_size: int


# ===== Organization Member Schemas =====

class OrganizationMemberBase(BaseModel):
    """조직 멤버 기본 스키마"""
    role: str = Field(..., description="조직 내 역할 (doctor, nurse, lab_tech, hospital_admin)")
    department: Optional[str] = Field(None, max_length=100, description="소속 부서")
    employee_number: Optional[str] = Field(None, max_length=50, description="사번")
    license_number: Optional[str] = Field(None, max_length=50, description="면허번호")


class OrganizationMemberCreate(OrganizationMemberBase):
    """조직 멤버 추가 요청"""
    user_id: int = Field(..., description="사용자 ID")


class OrganizationMemberInvite(BaseModel):
    """조직 멤버 초대 요청 (신규 사용자)"""
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    role: str
    department: Optional[str] = None
    license_number: Optional[str] = None


class OrganizationMemberUpdate(BaseModel):
    """조직 멤버 수정 요청"""
    role: Optional[str] = None
    department: Optional[str] = None
    employee_number: Optional[str] = None
    license_number: Optional[str] = None
    is_active: Optional[bool] = None


class OrganizationMemberResponse(OrganizationMemberBase):
    """조직 멤버 응답"""
    id: int
    organization_id: int
    user_id: int
    is_active: bool
    joined_at: datetime
    left_at: Optional[datetime] = None

    # User info (nested)
    user_name: Optional[str] = None
    user_email: Optional[str] = None

    class Config:
        from_attributes = True


class OrganizationMemberListResponse(BaseModel):
    """조직 멤버 목록 응답"""
    items: List[OrganizationMemberResponse]
    total: int


# ===== Hospital Admin Registration =====

class HospitalAdminRegisterRequest(BaseModel):
    """병원 관리자 등록 요청"""
    # 조직 정보
    organization_name: str = Field(..., min_length=2, max_length=200)
    org_type: OrganizationType = OrganizationType.HOSPITAL
    business_number: str = Field(..., max_length=20, description="사업자등록번호")
    license_number: Optional[str] = None
    address: Optional[str] = None
    org_phone: Optional[str] = None
    org_email: Optional[EmailStr] = None

    # 관리자 정보
    admin_name: str = Field(..., min_length=2, max_length=100)
    admin_email: EmailStr
    admin_phone: str = Field(..., max_length=20)


class HospitalAdminRegisterResponse(BaseModel):
    """병원 관리자 등록 응답"""
    organization: OrganizationResponse
    admin_user_id: int
    access_pin: str = Field(..., description="관리자 로그인 PIN (6자리)")
    message: str = "병원 등록이 완료되었습니다. 승인 후 서비스 이용이 가능합니다."
