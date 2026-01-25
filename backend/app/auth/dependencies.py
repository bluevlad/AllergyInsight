"""Authentication Dependencies - Phase 1: 확장된 권한 체계"""
from typing import Optional, List
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from ..database.connection import get_db
from ..database.models import User
from ..database.organization_models import (
    UserRole,
    OrganizationMember,
    HospitalPatient,
    HospitalPatientStatus,
)
from .jwt_handler import verify_token

security = HTTPBearer(auto_error=False)


# ===== 기본 인증 의존성 =====

async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """Get current authenticated user (returns None if not authenticated)"""
    if not credentials:
        return None

    token = credentials.credentials
    payload = verify_token(token)

    if not payload:
        return None

    user_id = payload.get("sub")
    if not user_id:
        return None

    user = db.query(User).filter(User.id == int(user_id)).first()
    return user


async def require_auth(
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer()),
    db: Session = Depends(get_db)
) -> User:
    """Require authentication - raises 401 if not authenticated"""
    token = credentials.credentials
    payload = verify_token(token)

    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled",
        )

    return user


# ===== Legacy 권한 (하위 호환) =====

async def require_admin(user: User = Depends(require_auth)) -> User:
    """Require admin role (legacy + super_admin)"""
    if not user.is_admin_role():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return user


# ===== Phase 1: 확장된 역할 기반 권한 =====

async def require_super_admin(user: User = Depends(require_auth)) -> User:
    """Require super_admin role (플랫폼 관리자)"""
    if user.role != UserRole.SUPER_ADMIN.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Super admin access required",
        )
    return user


async def require_hospital_staff(
    user: User = Depends(require_auth),
    db: Session = Depends(get_db)
) -> User:
    """Require hospital staff role (doctor, nurse, lab_tech, hospital_admin)"""
    if not user.is_staff():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Hospital staff access required",
        )

    # 조직에 소속되어 있는지 확인
    membership = db.query(OrganizationMember).filter(
        OrganizationMember.user_id == user.id,
        OrganizationMember.is_active == True
    ).first()

    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not affiliated with any organization",
        )

    return user


async def require_doctor(user: User = Depends(require_auth)) -> User:
    """Require doctor role"""
    allowed_roles = [UserRole.DOCTOR.value, UserRole.SUPER_ADMIN.value, UserRole.ADMIN.value]
    if user.role not in allowed_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Doctor access required",
        )
    return user


async def require_hospital_admin(user: User = Depends(require_auth)) -> User:
    """Require hospital_admin role"""
    allowed_roles = [UserRole.HOSPITAL_ADMIN.value, UserRole.SUPER_ADMIN.value, UserRole.ADMIN.value]
    if user.role not in allowed_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Hospital admin access required",
        )
    return user


def require_roles(*roles: str):
    """Factory function to create role requirement dependency"""
    async def role_checker(user: User = Depends(require_auth)) -> User:
        # super_admin과 admin은 항상 허용
        if user.is_admin_role():
            return user

        if user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Required role: {', '.join(roles)}",
            )
        return user

    return role_checker


# ===== 조직 컨텍스트 의존성 =====

class OrganizationContext:
    """현재 사용자의 조직 컨텍스트"""
    def __init__(self, user: User, membership: Optional[OrganizationMember], db: Session):
        self.user = user
        self.membership = membership
        self.db = db

    @property
    def organization_id(self) -> Optional[int]:
        return self.membership.organization_id if self.membership else None

    @property
    def organization(self):
        return self.membership.organization if self.membership else None

    @property
    def role_in_org(self) -> Optional[str]:
        return self.membership.role if self.membership else None

    def can_view_patient(self, patient_user_id: int) -> bool:
        """해당 환자를 조회할 수 있는지 확인"""
        if not self.membership:
            return False

        # 해당 조직에 연결된 환자인지 확인
        hospital_patient = self.db.query(HospitalPatient).filter(
            HospitalPatient.organization_id == self.organization_id,
            HospitalPatient.patient_user_id == patient_user_id,
            HospitalPatient.status == HospitalPatientStatus.ACTIVE.value,
        ).first()

        return hospital_patient is not None

    def can_edit_diagnosis(self) -> bool:
        """진단 결과를 입력/수정할 수 있는지 확인"""
        if not self.membership:
            return False
        allowed_roles = [UserRole.DOCTOR.value, UserRole.NURSE.value, UserRole.LAB_TECH.value]
        return self.role_in_org in allowed_roles

    def can_write_prescription(self) -> bool:
        """처방을 작성할 수 있는지 확인 (의사만)"""
        if not self.membership:
            return False
        return self.role_in_org == UserRole.DOCTOR.value

    def can_manage_staff(self) -> bool:
        """직원을 관리할 수 있는지 확인 (병원 관리자만)"""
        if not self.membership:
            return False
        return self.role_in_org == UserRole.HOSPITAL_ADMIN.value


async def get_org_context(
    user: User = Depends(require_auth),
    db: Session = Depends(get_db)
) -> OrganizationContext:
    """Get organization context for current user"""
    membership = db.query(OrganizationMember).filter(
        OrganizationMember.user_id == user.id,
        OrganizationMember.is_active == True
    ).first()

    return OrganizationContext(user=user, membership=membership, db=db)


async def require_org_context(
    ctx: OrganizationContext = Depends(get_org_context)
) -> OrganizationContext:
    """Require user to be affiliated with an organization"""
    if not ctx.membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Organization affiliation required",
        )
    return ctx
