"""Core Auth Module - 인증 및 권한 관리

기존 auth 모듈을 re-export하고 새로운 서비스별 권한 의존성을 추가합니다.
"""

# Re-export from original auth module
from ...auth.routes import router as auth_router
from ...auth.dependencies import (
    get_current_user,
    require_auth,
    require_admin,
    require_super_admin,
    require_hospital_staff,
    require_doctor,
    require_hospital_admin,
    require_roles,
    get_org_context,
    require_org_context,
    get_organization_context,
    OrganizationContext,
)
from ...auth.jwt_handler import create_access_token, verify_token, decode_token
from ...auth.config import auth_settings
from ...auth.schemas import (
    UserResponse,
    UserWithToken,
    Token,
    SimpleRegisterRequest,
    SimpleRegisterResponse,
    SimpleLoginRequest,
    KitRegisterRequest,
    UserDiagnosisResponse,
    UserDiagnosisSummary,
)

# New service-specific dependencies
from .dependencies import (
    require_professional,
    require_consumer,
)

__all__ = [
    # Router
    "auth_router",

    # Original dependencies
    "get_current_user",
    "require_auth",
    "require_admin",
    "require_super_admin",
    "require_hospital_staff",
    "require_doctor",
    "require_hospital_admin",
    "require_roles",
    "get_org_context",
    "require_org_context",
    "get_organization_context",
    "OrganizationContext",

    # New service-specific dependencies
    "require_professional",
    "require_consumer",

    # JWT
    "create_access_token",
    "verify_token",
    "decode_token",

    # Config
    "auth_settings",

    # Schemas
    "UserResponse",
    "UserWithToken",
    "Token",
    "SimpleRegisterRequest",
    "SimpleRegisterResponse",
    "SimpleLoginRequest",
    "KitRegisterRequest",
    "UserDiagnosisResponse",
    "UserDiagnosisSummary",
]
