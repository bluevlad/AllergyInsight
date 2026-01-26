"""Core module - 공통 서비스 (인증, 알러젠 데이터)

서비스 이원화를 위한 공통 모듈입니다.
- auth: 인증 및 권한 관리
- allergen: 알러젠 데이터베이스
"""

from .auth import (
    # Router
    auth_router,

    # Original dependencies
    require_auth,
    require_admin,
    require_super_admin,
    require_hospital_staff,
    require_doctor,
    require_hospital_admin,
    require_roles,
    get_current_user,
    get_org_context,
    require_org_context,
    get_organization_context,
    OrganizationContext,

    # New service-specific dependencies
    require_professional,
    require_consumer,

    # JWT
    create_access_token,
    verify_token,

    # Config
    auth_settings,
)

from .allergen import (
    FOOD_ALLERGENS,
    INHALANT_ALLERGENS,
    ALLERGEN_PRESCRIPTION_DB,
    EMERGENCY_GUIDELINES,
    get_allergen_info,
    get_allergen_list,
)

__all__ = [
    # Router
    "auth_router",

    # Auth dependencies
    "require_auth",
    "require_admin",
    "require_professional",
    "require_consumer",
    "require_super_admin",
    "require_hospital_staff",
    "require_doctor",
    "require_hospital_admin",
    "require_roles",
    "get_current_user",
    "get_org_context",
    "require_org_context",
    "get_organization_context",
    "OrganizationContext",

    # JWT
    "create_access_token",
    "verify_token",

    # Config
    "auth_settings",

    # Allergen data
    "FOOD_ALLERGENS",
    "INHALANT_ALLERGENS",
    "ALLERGEN_PRESCRIPTION_DB",
    "EMERGENCY_GUIDELINES",
    "get_allergen_info",
    "get_allergen_list",
]
