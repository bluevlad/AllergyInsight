"""Service-specific Authentication Dependencies

Professional과 Consumer 서비스를 위한 권한 의존성을 정의합니다.
"""
from fastapi import Depends, HTTPException, status

from ...database.models import User
from ...database.organization_models import UserRole
from ...auth.dependencies import require_auth


async def require_professional(user: User = Depends(require_auth)) -> User:
    """
    Professional 서비스 접근 권한 확인

    허용 역할:
    - doctor: 의사
    - nurse: 간호사
    - lab_tech: 검사 담당자
    - hospital_admin: 병원 관리자
    - admin: 시스템 관리자 (legacy)
    - super_admin: 플랫폼 관리자

    Raises:
        HTTPException 403: Professional 서비스 접근 권한 없음
    """
    professional_roles = [
        UserRole.DOCTOR.value,
        UserRole.NURSE.value,
        UserRole.LAB_TECH.value,
        UserRole.HOSPITAL_ADMIN.value,
        UserRole.ADMIN.value,
        UserRole.SUPER_ADMIN.value,
    ]

    if user.role not in professional_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Professional service access required. "
                   "This service is only available for healthcare professionals.",
        )

    return user


async def require_consumer(user: User = Depends(require_auth)) -> User:
    """
    Consumer 서비스 접근 권한 확인

    모든 인증된 사용자에게 허용 (환자 및 의료진 모두 접근 가능)

    Note:
        의료진도 Consumer 서비스에 접근하여 자신의 진단 결과를 조회할 수 있습니다.
    """
    # 모든 인증된 사용자 허용
    return user


def require_professional_or_self(target_user_id_param: str = "user_id"):
    """
    Professional 또는 본인 확인 팩토리 함수

    Professional 역할이거나 요청 대상이 본인인 경우 허용

    Args:
        target_user_id_param: 요청 경로의 사용자 ID 파라미터 이름

    Usage:
        @router.get("/users/{user_id}")
        async def get_user(
            user_id: int,
            user: User = Depends(require_professional_or_self("user_id"))
        ):
            ...
    """
    async def checker(
        user: User = Depends(require_auth),
        **kwargs
    ) -> User:
        # Professional 역할 확인
        professional_roles = [
            UserRole.DOCTOR.value,
            UserRole.NURSE.value,
            UserRole.LAB_TECH.value,
            UserRole.HOSPITAL_ADMIN.value,
            UserRole.ADMIN.value,
            UserRole.SUPER_ADMIN.value,
        ]

        if user.role in professional_roles:
            return user

        # 본인 확인 (target_user_id와 현재 사용자 ID 비교)
        target_user_id = kwargs.get(target_user_id_param)
        if target_user_id and int(target_user_id) == user.id:
            return user

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Professional role or self-access required.",
        )

    return checker
