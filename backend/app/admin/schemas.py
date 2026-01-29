"""Admin 모듈 Pydantic 스키마"""
from pydantic import BaseModel
from typing import Optional, Dict, List, Any
from datetime import datetime


# ============================================================================
# 대시보드 스키마
# ============================================================================

class UserStats(BaseModel):
    """사용자 통계"""
    total: int
    by_role: Dict[str, int]
    active: int
    inactive: int
    recent_signups: int  # 최근 7일


class DiagnosisStats(BaseModel):
    """진단 통계"""
    total_kits: int
    registered_kits: int
    total_diagnoses: int
    recent_diagnoses: int  # 최근 7일


class PaperStats(BaseModel):
    """논문 통계"""
    total: int
    guidelines: int
    by_source: Dict[str, int]
    clinical_statements: int


class OrganizationStats(BaseModel):
    """조직 통계"""
    total: int
    pending_approval: int
    active: int


class DashboardStats(BaseModel):
    """대시보드 전체 통계"""
    users: UserStats
    diagnoses: DiagnosisStats
    papers: PaperStats
    organizations: OrganizationStats
    allergens: Dict[str, Any]


class RecentActivity(BaseModel):
    """최근 활동"""
    id: int
    action: str
    target_type: Optional[str] = None
    target_id: Optional[str] = None
    user_name: Optional[str] = None
    created_at: datetime


class DashboardResponse(BaseModel):
    """대시보드 응답"""
    stats: DashboardStats
    recent_activities: List[RecentActivity] = []
    pending_items: Dict[str, int] = {}


# ============================================================================
# 사용자 관리 스키마
# ============================================================================

class UserListItem(BaseModel):
    """사용자 목록 항목"""
    id: int
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    role: str
    auth_type: str
    is_active: bool
    created_at: datetime
    last_login_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class UserDetail(UserListItem):
    """사용자 상세"""
    birth_date: Optional[str] = None
    organization_names: List[str] = []
    diagnosis_count: int = 0


class UserUpdateRequest(BaseModel):
    """사용자 수정 요청"""
    name: Optional[str] = None
    email: Optional[str] = None
    is_active: Optional[bool] = None


class UserRoleUpdateRequest(BaseModel):
    """역할 변경 요청"""
    role: str


class UserListResponse(BaseModel):
    """사용자 목록 응답"""
    items: List[UserListItem]
    total: int
    page: int
    page_size: int


# ============================================================================
# 알러젠 관리 스키마
# ============================================================================

class AllergenListItem(BaseModel):
    """알러젠 목록 항목"""
    code: str
    name_kr: str
    name_en: str
    category: str
    type: str
    has_prescription: bool = False


class AllergenDetail(AllergenListItem):
    """알러젠 상세"""
    description: Optional[str] = None
    note: Optional[str] = None


class AllergenUpdateRequest(BaseModel):
    """알러젠 수정 요청"""
    name_kr: Optional[str] = None
    name_en: Optional[str] = None
    description: Optional[str] = None
    note: Optional[str] = None


# ============================================================================
# 논문 관리 스키마
# ============================================================================

class PaperListItem(BaseModel):
    """논문 목록 항목"""
    id: int
    title: str
    authors: Optional[str] = None
    journal: Optional[str] = None
    year: Optional[int] = None
    is_guideline: bool = False
    evidence_level: Optional[str] = None
    source: Optional[str] = None

    class Config:
        from_attributes = True


class PaperListResponse(BaseModel):
    """논문 목록 응답"""
    items: List[PaperListItem]
    total: int
    page: int
    page_size: int


# ============================================================================
# 조직 관리 스키마
# ============================================================================

class OrganizationListItem(BaseModel):
    """조직 목록 항목"""
    id: int
    name: str
    org_type: str
    status: str
    member_count: int = 0
    created_at: datetime

    class Config:
        from_attributes = True


class OrganizationListResponse(BaseModel):
    """조직 목록 응답"""
    items: List[OrganizationListItem]
    total: int
    page: int
    page_size: int
