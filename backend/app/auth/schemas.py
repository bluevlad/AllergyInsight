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
