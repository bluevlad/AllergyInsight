"""Authentication Schemas"""
from datetime import date, datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, EmailStr


# ============================================================================
# User Schemas
# ============================================================================

class UserBase(BaseModel):
    name: str
    email: Optional[EmailStr] = None


class UserCreate(UserBase):
    auth_type: str  # 'google' or 'simple'
    google_id: Optional[str] = None
    phone: Optional[str] = None
    birth_date: Optional[date] = None


class UserResponse(UserBase):
    id: int
    auth_type: str
    role: str
    profile_image: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class UserWithToken(BaseModel):
    user: UserResponse
    access_token: str
    token_type: str = "bearer"


# ============================================================================
# Simple Registration Schemas
# ============================================================================

class SimpleRegisterRequest(BaseModel):
    """Simple registration with kit verification"""
    name: str
    phone: Optional[str] = None
    birth_date: Optional[date] = None
    serial_number: str
    pin: str


class SimpleRegisterResponse(BaseModel):
    user: UserResponse
    access_token: str
    access_pin: str  # New PIN for future logins
    message: str


class SimpleLoginRequest(BaseModel):
    """Simple login with name + birth_date/phone + PIN"""
    name: str
    birth_date: Optional[date] = None
    phone: Optional[str] = None
    access_pin: str


# ============================================================================
# Diagnosis Kit Schemas
# ============================================================================

class DiagnosisKitCreate(BaseModel):
    """For admin to create kits"""
    serial_number: str
    pin: str  # Will be hashed
    results: Dict[str, int]  # {"peanut": 3, "milk": 2, ...}
    diagnosis_date: date


class DiagnosisKitResponse(BaseModel):
    id: int
    serial_number: str
    results: Dict[str, int]
    diagnosis_date: date
    is_registered: bool
    created_at: datetime

    class Config:
        from_attributes = True


class KitRegisterRequest(BaseModel):
    """For user to register kit"""
    serial_number: str
    pin: str


# ============================================================================
# User Diagnosis Schemas
# ============================================================================

class UserDiagnosisResponse(BaseModel):
    id: int
    results: Dict[str, int]
    diagnosis_date: date
    prescription: Optional[Dict[str, Any]] = None
    created_at: datetime
    kit_serial: Optional[str] = None

    class Config:
        from_attributes = True


class UserDiagnosisSummary(BaseModel):
    """Summary for mobile/quick view"""
    id: int
    diagnosis_date: date
    high_risk: List[str]  # Allergens with grade >= 4
    moderate_risk: List[str]  # Allergens with grade 2-3
    total_positive: int

    class Config:
        from_attributes = True


# ============================================================================
# Token Schemas
# ============================================================================

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    sub: str  # User ID
    exp: datetime
    auth_type: str


# ============================================================================
# Paper Schemas
# ============================================================================

class PaperAllergenLinkCreate(BaseModel):
    """Link paper to allergen"""
    allergen_code: str  # 'peanut', 'milk', etc.
    link_type: str  # 'symptom', 'dietary', 'cross_reactivity', 'substitute', 'emergency', 'management', 'general'
    specific_item: Optional[str] = None
    relevance_score: int = 80
    note: Optional[str] = None


class PaperAllergenLinkResponse(BaseModel):
    id: int
    allergen_code: str
    link_type: str
    specific_item: Optional[str] = None
    relevance_score: int
    note: Optional[str] = None

    class Config:
        from_attributes = True


class PaperCreate(BaseModel):
    """Create a new paper"""
    pmid: Optional[str] = None
    doi: Optional[str] = None
    title: str
    title_kr: Optional[str] = None
    authors: Optional[str] = None
    journal: Optional[str] = None
    year: Optional[int] = None
    abstract: Optional[str] = None
    abstract_kr: Optional[str] = None
    url: Optional[str] = None
    pdf_url: Optional[str] = None
    paper_type: str = "research"  # 'research', 'review', 'guideline', 'meta_analysis'
    allergen_links: Optional[List[PaperAllergenLinkCreate]] = None


class PaperUpdate(BaseModel):
    """Update a paper"""
    pmid: Optional[str] = None
    doi: Optional[str] = None
    title: Optional[str] = None
    title_kr: Optional[str] = None
    authors: Optional[str] = None
    journal: Optional[str] = None
    year: Optional[int] = None
    abstract: Optional[str] = None
    abstract_kr: Optional[str] = None
    url: Optional[str] = None
    pdf_url: Optional[str] = None
    paper_type: Optional[str] = None
    is_verified: Optional[bool] = None


class PaperResponse(BaseModel):
    """Paper response"""
    id: int
    pmid: Optional[str] = None
    doi: Optional[str] = None
    title: str
    title_kr: Optional[str] = None
    authors: Optional[str] = None
    journal: Optional[str] = None
    year: Optional[int] = None
    abstract: Optional[str] = None
    abstract_kr: Optional[str] = None
    url: Optional[str] = None
    pdf_url: Optional[str] = None
    paper_type: str
    is_verified: bool
    created_at: datetime
    allergen_links: List[PaperAllergenLinkResponse] = []

    # Phase 1: 검색 결과 영속화 필드
    source: Optional[str] = None
    source_id: Optional[str] = None
    citation_count: Optional[int] = None
    keywords: Optional[List[str]] = None

    class Config:
        from_attributes = True


class PaperBrief(BaseModel):
    """Brief paper info for citation display"""
    id: int
    pmid: Optional[str] = None
    doi: Optional[str] = None
    title: str
    title_kr: Optional[str] = None
    authors: Optional[str] = None
    journal: Optional[str] = None
    year: Optional[int] = None
    url: Optional[str] = None
    paper_type: str

    class Config:
        from_attributes = True


class PaperListResponse(BaseModel):
    """Paginated paper list"""
    items: List[PaperResponse]
    total: int
    page: int
    size: int
