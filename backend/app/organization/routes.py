"""Organization Routes - Phase 1"""
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from ..database.connection import get_db
from ..database.models import User
from ..database.organization_models import (
    Organization,
    OrganizationMember,
    HospitalPatient,
    OrganizationType,
    OrganizationStatus,
    UserRole,
)
from ..auth.dependencies import (
    require_auth,
    require_admin,
    require_super_admin,
    require_hospital_admin,
    get_org_context,
    require_org_context,
    OrganizationContext,
)
from .schemas import (
    OrganizationCreate,
    OrganizationUpdate,
    OrganizationResponse,
    OrganizationListResponse,
    OrganizationMemberCreate,
    OrganizationMemberUpdate,
    OrganizationMemberResponse,
    OrganizationMemberListResponse,
    HospitalAdminRegisterRequest,
    HospitalAdminRegisterResponse,
)

router = APIRouter(prefix="/organizations", tags=["Organizations"])


# ===== Helper Functions =====

def _org_to_response(org: Organization, db: Session) -> OrganizationResponse:
    """Organization 모델을 Response로 변환"""
    member_count = db.query(func.count(OrganizationMember.id)).filter(
        OrganizationMember.organization_id == org.id,
        OrganizationMember.is_active == True
    ).scalar()

    patient_count = db.query(func.count(HospitalPatient.id)).filter(
        HospitalPatient.organization_id == org.id
    ).scalar()

    return OrganizationResponse(
        id=org.id,
        name=org.name,
        org_type=org.org_type,
        business_number=org.business_number,
        license_number=org.license_number,
        address=org.address,
        phone=org.phone,
        email=org.email,
        subscription_plan=org.subscription_plan,
        status=org.status,
        created_at=org.created_at,
        updated_at=org.updated_at,
        expires_at=org.expires_at,
        member_count=member_count,
        patient_count=patient_count,
    )


def _member_to_response(member: OrganizationMember) -> OrganizationMemberResponse:
    """OrganizationMember 모델을 Response로 변환"""
    return OrganizationMemberResponse(
        id=member.id,
        organization_id=member.organization_id,
        user_id=member.user_id,
        role=member.role,
        department=member.department,
        employee_number=member.employee_number,
        license_number=member.license_number,
        is_active=member.is_active,
        joined_at=member.joined_at,
        left_at=member.left_at,
        user_name=member.user.name if member.user else None,
        user_email=member.user.email if member.user else None,
    )


# ===== Organization CRUD =====

@router.post("", response_model=OrganizationResponse, status_code=status.HTTP_201_CREATED)
async def create_organization(
    data: OrganizationCreate,
    user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """조직 생성 (관리자 전용)"""
    # 사업자등록번호 중복 확인
    if data.business_number:
        existing = db.query(Organization).filter(
            Organization.business_number == data.business_number
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="이미 등록된 사업자등록번호입니다."
            )

    org = Organization(
        name=data.name,
        org_type=data.org_type.value,
        business_number=data.business_number,
        license_number=data.license_number,
        address=data.address,
        phone=data.phone,
        email=data.email,
        status=OrganizationStatus.PENDING.value,
    )
    db.add(org)
    db.commit()
    db.refresh(org)

    return _org_to_response(org, db)


@router.get("", response_model=OrganizationListResponse)
async def list_organizations(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[OrganizationStatus] = None,
    org_type: Optional[OrganizationType] = None,
    search: Optional[str] = None,
    user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """조직 목록 조회 (관리자 전용)"""
    query = db.query(Organization)

    if status:
        query = query.filter(Organization.status == status.value)
    if org_type:
        query = query.filter(Organization.org_type == org_type.value)
    if search:
        query = query.filter(Organization.name.ilike(f"%{search}%"))

    total = query.count()
    items = query.order_by(Organization.created_at.desc()).offset(
        (page - 1) * page_size
    ).limit(page_size).all()

    return OrganizationListResponse(
        items=[_org_to_response(org, db) for org in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/my", response_model=OrganizationResponse)
async def get_my_organization(
    ctx: OrganizationContext = Depends(require_org_context),
    db: Session = Depends(get_db)
):
    """내 조직 정보 조회"""
    return _org_to_response(ctx.organization, db)


@router.get("/{org_id}", response_model=OrganizationResponse)
async def get_organization(
    org_id: int,
    user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """조직 상세 조회"""
    org = db.query(Organization).filter(Organization.id == org_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    # 권한 확인: 관리자이거나 해당 조직 멤버
    if not user.is_admin_role():
        membership = db.query(OrganizationMember).filter(
            OrganizationMember.organization_id == org_id,
            OrganizationMember.user_id == user.id,
            OrganizationMember.is_active == True
        ).first()
        if not membership:
            raise HTTPException(status_code=403, detail="Access denied")

    return _org_to_response(org, db)


@router.put("/{org_id}", response_model=OrganizationResponse)
async def update_organization(
    org_id: int,
    data: OrganizationUpdate,
    user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """조직 정보 수정"""
    org = db.query(Organization).filter(Organization.id == org_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    # 권한 확인: 관리자이거나 해당 조직의 hospital_admin
    if not user.is_admin_role():
        membership = db.query(OrganizationMember).filter(
            OrganizationMember.organization_id == org_id,
            OrganizationMember.user_id == user.id,
            OrganizationMember.role == UserRole.HOSPITAL_ADMIN.value,
            OrganizationMember.is_active == True
        ).first()
        if not membership:
            raise HTTPException(status_code=403, detail="Hospital admin access required")

    # 업데이트
    update_data = data.model_dump(exclude_unset=True)

    # status 변경은 super_admin만 가능
    if "status" in update_data and not user.is_admin_role():
        del update_data["status"]

    for field, value in update_data.items():
        if hasattr(org, field):
            if hasattr(value, 'value'):  # Enum 처리
                setattr(org, field, value.value)
            else:
                setattr(org, field, value)

    org.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(org)

    return _org_to_response(org, db)


@router.delete("/{org_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_organization(
    org_id: int,
    user: User = Depends(require_super_admin),
    db: Session = Depends(get_db)
):
    """조직 삭제 (Super Admin 전용, Soft Delete)"""
    org = db.query(Organization).filter(Organization.id == org_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    org.status = OrganizationStatus.SUSPENDED.value
    org.updated_at = datetime.utcnow()
    db.commit()


# ===== Organization Member Management =====

@router.get("/{org_id}/members", response_model=OrganizationMemberListResponse)
async def list_organization_members(
    org_id: int,
    role: Optional[str] = None,
    is_active: Optional[bool] = True,
    user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """조직 멤버 목록 조회"""
    # 권한 확인
    if not user.is_admin_role():
        membership = db.query(OrganizationMember).filter(
            OrganizationMember.organization_id == org_id,
            OrganizationMember.user_id == user.id,
            OrganizationMember.is_active == True
        ).first()
        if not membership:
            raise HTTPException(status_code=403, detail="Access denied")

    query = db.query(OrganizationMember).filter(
        OrganizationMember.organization_id == org_id
    )

    if role:
        query = query.filter(OrganizationMember.role == role)
    if is_active is not None:
        query = query.filter(OrganizationMember.is_active == is_active)

    members = query.all()

    return OrganizationMemberListResponse(
        items=[_member_to_response(m) for m in members],
        total=len(members),
    )


@router.post("/{org_id}/members", response_model=OrganizationMemberResponse, status_code=status.HTTP_201_CREATED)
async def add_organization_member(
    org_id: int,
    data: OrganizationMemberCreate,
    user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """조직 멤버 추가"""
    # 권한 확인: 관리자 또는 해당 조직의 hospital_admin
    if not user.is_admin_role():
        membership = db.query(OrganizationMember).filter(
            OrganizationMember.organization_id == org_id,
            OrganizationMember.user_id == user.id,
            OrganizationMember.role == UserRole.HOSPITAL_ADMIN.value,
            OrganizationMember.is_active == True
        ).first()
        if not membership:
            raise HTTPException(status_code=403, detail="Hospital admin access required")

    # 조직 존재 확인
    org = db.query(Organization).filter(Organization.id == org_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    # 사용자 존재 확인
    target_user = db.query(User).filter(User.id == data.user_id).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")

    # 이미 멤버인지 확인
    existing = db.query(OrganizationMember).filter(
        OrganizationMember.organization_id == org_id,
        OrganizationMember.user_id == data.user_id
    ).first()
    if existing:
        if existing.is_active:
            raise HTTPException(status_code=400, detail="User is already a member")
        else:
            # 비활성 멤버 재활성화
            existing.is_active = True
            existing.role = data.role
            existing.department = data.department
            existing.employee_number = data.employee_number
            existing.license_number = data.license_number
            existing.left_at = None
            db.commit()
            db.refresh(existing)
            return _member_to_response(existing)

    # 새 멤버 추가
    member = OrganizationMember(
        organization_id=org_id,
        user_id=data.user_id,
        role=data.role,
        department=data.department,
        employee_number=data.employee_number,
        license_number=data.license_number,
    )
    db.add(member)

    # 사용자 역할 업데이트
    if data.role in [r.value for r in UserRole.staff_roles()]:
        target_user.role = data.role

    db.commit()
    db.refresh(member)

    return _member_to_response(member)


@router.put("/{org_id}/members/{member_id}", response_model=OrganizationMemberResponse)
async def update_organization_member(
    org_id: int,
    member_id: int,
    data: OrganizationMemberUpdate,
    user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """조직 멤버 정보 수정"""
    # 권한 확인
    if not user.is_admin_role():
        membership = db.query(OrganizationMember).filter(
            OrganizationMember.organization_id == org_id,
            OrganizationMember.user_id == user.id,
            OrganizationMember.role == UserRole.HOSPITAL_ADMIN.value,
            OrganizationMember.is_active == True
        ).first()
        if not membership:
            raise HTTPException(status_code=403, detail="Hospital admin access required")

    member = db.query(OrganizationMember).filter(
        OrganizationMember.id == member_id,
        OrganizationMember.organization_id == org_id
    ).first()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if hasattr(member, field):
            setattr(member, field, value)

    if data.is_active == False:
        member.left_at = datetime.utcnow()

    db.commit()
    db.refresh(member)

    return _member_to_response(member)


@router.delete("/{org_id}/members/{member_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_organization_member(
    org_id: int,
    member_id: int,
    user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """조직 멤버 제거 (비활성화)"""
    # 권한 확인
    if not user.is_admin_role():
        membership = db.query(OrganizationMember).filter(
            OrganizationMember.organization_id == org_id,
            OrganizationMember.user_id == user.id,
            OrganizationMember.role == UserRole.HOSPITAL_ADMIN.value,
            OrganizationMember.is_active == True
        ).first()
        if not membership:
            raise HTTPException(status_code=403, detail="Hospital admin access required")

    member = db.query(OrganizationMember).filter(
        OrganizationMember.id == member_id,
        OrganizationMember.organization_id == org_id
    ).first()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")

    member.is_active = False
    member.left_at = datetime.utcnow()
    db.commit()


# ===== Hospital Admin Registration =====

@router.post("/register-hospital", response_model=HospitalAdminRegisterResponse)
async def register_hospital_admin(
    data: HospitalAdminRegisterRequest,
    db: Session = Depends(get_db)
):
    """병원 관리자 등록 (조직 + 관리자 계정 동시 생성)"""
    import secrets
    import bcrypt

    # 사업자등록번호 중복 확인
    existing_org = db.query(Organization).filter(
        Organization.business_number == data.business_number
    ).first()
    if existing_org:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="이미 등록된 사업자등록번호입니다."
        )

    # 이메일 중복 확인
    existing_user = db.query(User).filter(User.email == data.admin_email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="이미 등록된 이메일입니다."
        )

    # Access PIN 생성 (6자리)
    access_pin = ''.join([str(secrets.randbelow(10)) for _ in range(6)])
    pin_hash = bcrypt.hashpw(access_pin.encode(), bcrypt.gensalt()).decode()

    # 조직 생성
    org = Organization(
        name=data.organization_name,
        org_type=data.org_type.value,
        business_number=data.business_number,
        license_number=data.license_number,
        address=data.address,
        phone=data.org_phone,
        email=data.org_email,
        status=OrganizationStatus.PENDING.value,
    )
    db.add(org)
    db.flush()  # ID 생성

    # 관리자 사용자 생성
    admin_user = User(
        name=data.admin_name,
        email=data.admin_email,
        phone=data.admin_phone,
        auth_type="simple",
        access_pin_hash=pin_hash,
        role=UserRole.HOSPITAL_ADMIN.value,
    )
    db.add(admin_user)
    db.flush()

    # 조직 멤버로 추가
    member = OrganizationMember(
        organization_id=org.id,
        user_id=admin_user.id,
        role=UserRole.HOSPITAL_ADMIN.value,
    )
    db.add(member)

    db.commit()
    db.refresh(org)

    return HospitalAdminRegisterResponse(
        organization=_org_to_response(org, db),
        admin_user_id=admin_user.id,
        access_pin=access_pin,
        message="병원 등록이 완료되었습니다. 승인 후 서비스 이용이 가능합니다.",
    )


# ===== Organization Approval (Super Admin) =====

@router.post("/{org_id}/approve", response_model=OrganizationResponse)
async def approve_organization(
    org_id: int,
    user: User = Depends(require_super_admin),
    db: Session = Depends(get_db)
):
    """조직 승인 (Super Admin 전용)"""
    org = db.query(Organization).filter(Organization.id == org_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    if org.status != OrganizationStatus.PENDING.value:
        raise HTTPException(status_code=400, detail="Organization is not pending approval")

    org.status = OrganizationStatus.ACTIVE.value
    org.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(org)

    return _org_to_response(org, db)
