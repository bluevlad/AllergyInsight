"""Admin 모듈 권한 체크 의존성"""
from fastapi import Depends, HTTPException, status
from ..auth.dependencies import get_current_user
from ..database.models import User


async def require_super_admin(
    current_user: User = Depends(get_current_user)
) -> User:
    """super_admin 역할만 접근 허용

    Raises:
        HTTPException: 403 Forbidden if not super_admin
    """
    if not current_user.is_admin_role():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="관리자 권한이 필요합니다."
        )
    return current_user


async def require_admin_or_hospital_admin(
    current_user: User = Depends(get_current_user)
) -> User:
    """super_admin 또는 hospital_admin 역할 허용

    일부 관리 기능은 병원 관리자도 접근 가능
    """
    allowed_roles = ['super_admin', 'admin', 'hospital_admin']
    if current_user.role not in allowed_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="관리자 권한이 필요합니다."
        )
    return current_user
