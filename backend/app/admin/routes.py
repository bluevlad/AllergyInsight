"""Admin 메인 라우터"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from datetime import datetime, timedelta

from .news_routes import router as news_router
from .analytics_routes import router as analytics_router
from typing import Optional

from .dependencies import require_super_admin
from .schemas import (
    DashboardResponse, DashboardStats, UserStats, DiagnosisStats,
    PaperStats, OrganizationStats,
    UserListResponse, UserListItem, UserDetail,
    UserUpdateRequest, UserRoleUpdateRequest,
    PaperListResponse, PaperListItem,
    OrganizationListResponse, OrganizationListItem
)
from ..database.connection import get_db
from ..database.models import User, DiagnosisKit, UserDiagnosis, Paper
from ..database.organization_models import Organization, OrganizationMember
from ..database.clinical_models import ClinicalStatement
from ..data.allergen_master import get_allergen_summary

router = APIRouter()


# ============================================================================
# 대시보드
# ============================================================================

@router.get("/dashboard", response_model=DashboardResponse)
async def get_dashboard(
    current_user: User = Depends(require_super_admin),
    db: Session = Depends(get_db)
):
    """관리자 대시보드 데이터"""
    now = datetime.utcnow()
    week_ago = now - timedelta(days=7)

    # 사용자 통계
    total_users = db.query(func.count(User.id)).scalar() or 0
    active_users = db.query(func.count(User.id)).filter(User.is_active == True).scalar() or 0
    recent_signups = db.query(func.count(User.id)).filter(User.created_at >= week_ago).scalar() or 0

    # 역할별 사용자 수
    role_counts = db.query(User.role, func.count(User.id)).group_by(User.role).all()
    by_role = {role: count for role, count in role_counts}

    user_stats = UserStats(
        total=total_users,
        by_role=by_role,
        active=active_users,
        inactive=total_users - active_users,
        recent_signups=recent_signups
    )

    # 진단 통계
    total_kits = db.query(func.count(DiagnosisKit.id)).scalar() or 0
    registered_kits = db.query(func.count(DiagnosisKit.id)).filter(
        DiagnosisKit.is_registered == True
    ).scalar() or 0
    total_diagnoses = db.query(func.count(UserDiagnosis.id)).scalar() or 0
    recent_diagnoses = db.query(func.count(UserDiagnosis.id)).filter(
        UserDiagnosis.created_at >= week_ago
    ).scalar() or 0

    diagnosis_stats = DiagnosisStats(
        total_kits=total_kits,
        registered_kits=registered_kits,
        total_diagnoses=total_diagnoses,
        recent_diagnoses=recent_diagnoses
    )

    # 논문 통계
    total_papers = db.query(func.count(Paper.id)).scalar() or 0
    guideline_papers = db.query(func.count(Paper.id)).filter(
        Paper.is_guideline == True
    ).scalar() or 0
    clinical_statements = db.query(func.count(ClinicalStatement.id)).scalar() or 0

    paper_stats = PaperStats(
        total=total_papers,
        guidelines=guideline_papers,
        by_source={},  # TODO: source 필드 추가 후 구현
        clinical_statements=clinical_statements
    )

    # 조직 통계
    total_orgs = db.query(func.count(Organization.id)).scalar() or 0
    pending_orgs = db.query(func.count(Organization.id)).filter(
        Organization.status == "pending"
    ).scalar() or 0
    active_orgs = db.query(func.count(Organization.id)).filter(
        Organization.status == "active"
    ).scalar() or 0

    org_stats = OrganizationStats(
        total=total_orgs,
        pending_approval=pending_orgs,
        active=active_orgs
    )

    # 알러젠 통계
    allergen_summary = get_allergen_summary()

    stats = DashboardStats(
        users=user_stats,
        diagnoses=diagnosis_stats,
        papers=paper_stats,
        organizations=org_stats,
        allergens=allergen_summary
    )

    # 대기 중인 항목
    pending_items = {
        "organizations": pending_orgs
    }

    return DashboardResponse(
        stats=stats,
        recent_activities=[],  # TODO: 활동 로그 테이블 추가 후 구현
        pending_items=pending_items
    )


# ============================================================================
# 사용자 관리
# ============================================================================

@router.get("/users", response_model=UserListResponse)
async def get_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    role: Optional[str] = None,
    is_active: Optional[bool] = None,
    search: Optional[str] = None,
    current_user: User = Depends(require_super_admin),
    db: Session = Depends(get_db)
):
    """사용자 목록 조회"""
    query = db.query(User)

    # 필터 적용
    if role:
        query = query.filter(User.role == role)
    if is_active is not None:
        query = query.filter(User.is_active == is_active)
    if search:
        search_filter = f"%{search}%"
        query = query.filter(
            (User.name.ilike(search_filter)) |
            (User.email.ilike(search_filter))
        )

    # 총 개수
    total = query.count()

    # 페이지네이션
    offset = (page - 1) * page_size
    users = query.order_by(User.created_at.desc()).offset(offset).limit(page_size).all()

    items = [
        UserListItem(
            id=user.id,
            name=user.name,
            email=user.email,
            phone=user.phone[:4] + "****" if user.phone else None,  # 마스킹
            role=user.role,
            auth_type=user.auth_type,
            is_active=user.is_active,
            created_at=user.created_at,
            last_login_at=user.last_login_at
        )
        for user in users
    ]

    return UserListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/users/{user_id}", response_model=UserDetail)
async def get_user_detail(
    user_id: int,
    current_user: User = Depends(require_super_admin),
    db: Session = Depends(get_db)
):
    """사용자 상세 조회"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")

    # 소속 조직명
    org_names = []
    for membership in user.organization_memberships:
        if membership.organization:
            org_names.append(membership.organization.name)

    # 진단 건수
    diagnosis_count = db.query(func.count(UserDiagnosis.id)).filter(
        UserDiagnosis.user_id == user_id
    ).scalar() or 0

    return UserDetail(
        id=user.id,
        name=user.name,
        email=user.email,
        phone=user.phone[:4] + "****" if user.phone else None,
        role=user.role,
        auth_type=user.auth_type,
        is_active=user.is_active,
        created_at=user.created_at,
        last_login_at=user.last_login_at,
        birth_date=str(user.birth_date) if user.birth_date else None,
        organization_names=org_names,
        diagnosis_count=diagnosis_count
    )


@router.put("/users/{user_id}")
async def update_user(
    user_id: int,
    request: UserUpdateRequest,
    current_user: User = Depends(require_super_admin),
    db: Session = Depends(get_db)
):
    """사용자 정보 수정"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")

    if request.name is not None:
        user.name = request.name
    if request.email is not None:
        user.email = request.email
    if request.is_active is not None:
        user.is_active = request.is_active

    db.commit()
    return {"message": "사용자 정보가 수정되었습니다."}


@router.put("/users/{user_id}/role")
async def update_user_role(
    user_id: int,
    request: UserRoleUpdateRequest,
    current_user: User = Depends(require_super_admin),
    db: Session = Depends(get_db)
):
    """사용자 역할 변경"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")

    # 자기 자신의 역할은 변경 불가
    if user.id == current_user.id:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="자신의 역할은 변경할 수 없습니다.")

    valid_roles = ['patient', 'doctor', 'nurse', 'lab_tech', 'hospital_admin', 'super_admin', 'user', 'admin']
    if request.role not in valid_roles:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail=f"유효하지 않은 역할입니다. 허용: {valid_roles}")

    user.role = request.role
    db.commit()

    return {"message": f"역할이 '{request.role}'로 변경되었습니다."}


@router.get("/users/stats/summary")
async def get_user_stats(
    current_user: User = Depends(require_super_admin),
    db: Session = Depends(get_db)
):
    """사용자 통계 요약"""
    now = datetime.utcnow()

    # 역할별 통계
    role_stats = db.query(User.role, func.count(User.id)).group_by(User.role).all()

    # 가입 유형별 통계
    auth_stats = db.query(User.auth_type, func.count(User.id)).group_by(User.auth_type).all()

    # 월별 가입자 추이 (최근 6개월)
    monthly_signups = []
    for i in range(5, -1, -1):
        month_start = (now.replace(day=1) - timedelta(days=i*30)).replace(day=1)
        if i > 0:
            month_end = (now.replace(day=1) - timedelta(days=(i-1)*30)).replace(day=1)
        else:
            month_end = now

        count = db.query(func.count(User.id)).filter(
            and_(User.created_at >= month_start, User.created_at < month_end)
        ).scalar() or 0

        monthly_signups.append({
            "month": month_start.strftime("%Y-%m"),
            "count": count
        })

    return {
        "by_role": {role: count for role, count in role_stats},
        "by_auth_type": {auth: count for auth, count in auth_stats},
        "monthly_signups": monthly_signups
    }


# ============================================================================
# 논문 관리 (기본)
# ============================================================================

@router.get("/papers", response_model=PaperListResponse)
async def get_papers(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    is_guideline: Optional[bool] = None,
    search: Optional[str] = None,
    current_user: User = Depends(require_super_admin),
    db: Session = Depends(get_db)
):
    """논문 목록 조회"""
    query = db.query(Paper)

    if is_guideline is not None:
        query = query.filter(Paper.is_guideline == is_guideline)

    if search:
        search_filter = f"%{search}%"
        query = query.filter(
            (Paper.title.ilike(search_filter)) |
            (Paper.authors.ilike(search_filter))
        )

    total = query.count()
    offset = (page - 1) * page_size
    papers = query.order_by(Paper.created_at.desc()).offset(offset).limit(page_size).all()

    items = [
        PaperListItem(
            id=paper.id,
            title=paper.title,
            authors=paper.authors,
            journal=paper.journal,
            year=paper.year,
            is_guideline=paper.is_guideline or False,
            evidence_level=paper.evidence_level
        )
        for paper in papers
    ]

    return PaperListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size
    )


# ============================================================================
# 조직 관리 (기본)
# ============================================================================

@router.get("/organizations", response_model=OrganizationListResponse)
async def get_organizations(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
    search: Optional[str] = None,
    current_user: User = Depends(require_super_admin),
    db: Session = Depends(get_db)
):
    """조직 목록 조회"""
    query = db.query(Organization)

    if status:
        query = query.filter(Organization.status == status)

    if search:
        query = query.filter(Organization.name.ilike(f"%{search}%"))

    total = query.count()
    offset = (page - 1) * page_size
    orgs = query.order_by(Organization.created_at.desc()).offset(offset).limit(page_size).all()

    items = []
    for org in orgs:
        member_count = db.query(func.count(OrganizationMember.id)).filter(
            OrganizationMember.organization_id == org.id
        ).scalar() or 0

        items.append(OrganizationListItem(
            id=org.id,
            name=org.name,
            org_type=org.org_type or "hospital",
            status=org.status or "pending",
            member_count=member_count,
            created_at=org.created_at
        ))

    return OrganizationListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size
    )


@router.post("/organizations/{org_id}/approve")
async def approve_organization(
    org_id: int,
    current_user: User = Depends(require_super_admin),
    db: Session = Depends(get_db)
):
    """조직 승인"""
    org = db.query(Organization).filter(Organization.id == org_id).first()
    if not org:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="조직을 찾을 수 없습니다.")

    org.status = "active"
    db.commit()

    return {"message": f"'{org.name}' 조직이 승인되었습니다."}


@router.post("/organizations/{org_id}/reject")
async def reject_organization(
    org_id: int,
    current_user: User = Depends(require_super_admin),
    db: Session = Depends(get_db)
):
    """조직 반려"""
    org = db.query(Organization).filter(Organization.id == org_id).first()
    if not org:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="조직을 찾을 수 없습니다.")

    org.status = "rejected"
    db.commit()

    return {"message": f"'{org.name}' 조직이 반려되었습니다."}


# ============================================================================
# 알러젠 정보 (읽기 전용)
# ============================================================================

@router.get("/allergens")
async def get_allergens(
    category: Optional[str] = None,
    search: Optional[str] = None,
    current_user: User = Depends(require_super_admin)
):
    """알러젠 목록 조회 (마스터 DB 기준)"""
    from ..data.allergen_master import ALLERGEN_MASTER_DB, AllergenCategory
    from ..data.allergen_prescription_db import ALLERGEN_PRESCRIPTION_DB

    allergens = []
    for code, data in ALLERGEN_MASTER_DB.items():
        # 카테고리 필터
        if category:
            cat = data.get("category")
            cat_value = cat.value if hasattr(cat, 'value') else str(cat)
            if cat_value != category:
                continue

        # 검색 필터
        if search:
            search_lower = search.lower()
            if not (search_lower in data.get("name_kr", "").lower() or
                    search_lower in data.get("name_en", "").lower() or
                    search_lower in code.lower()):
                continue

        # 처방 정보 유무 확인
        has_prescription = code in ALLERGEN_PRESCRIPTION_DB or data.get("name_en", "").lower().replace(" ", "_") in ALLERGEN_PRESCRIPTION_DB

        cat = data.get("category")
        typ = data.get("type")

        allergens.append({
            "code": code,
            "name_kr": data.get("name_kr"),
            "name_en": data.get("name_en"),
            "category": cat.value if hasattr(cat, 'value') else str(cat),
            "type": typ.value if hasattr(typ, 'value') else str(typ),
            "description": data.get("description"),
            "has_prescription": has_prescription
        })

    # 코드 순 정렬
    allergens.sort(key=lambda x: x["code"])

    return {
        "items": allergens,
        "total": len(allergens),
        "categories": [c.value for c in AllergenCategory]
    }


@router.get("/allergens/{code}")
async def get_allergen_detail(
    code: str,
    current_user: User = Depends(require_super_admin)
):
    """알러젠 상세 조회"""
    from ..data.allergen_master import get_allergen_by_code, get_legacy_code
    from ..data.allergen_prescription_db import ALLERGEN_PRESCRIPTION_DB

    allergen = get_allergen_by_code(code)
    if not allergen:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="알러젠을 찾을 수 없습니다.")

    # 처방 정보 조회
    legacy_code = get_legacy_code(code)
    prescription = None
    if legacy_code and legacy_code in ALLERGEN_PRESCRIPTION_DB:
        prescription = ALLERGEN_PRESCRIPTION_DB[legacy_code]

    cat = allergen.get("category")
    typ = allergen.get("type")

    return {
        "code": code,
        "name_kr": allergen.get("name_kr"),
        "name_en": allergen.get("name_en"),
        "category": cat.value if hasattr(cat, 'value') else str(cat),
        "type": typ.value if hasattr(typ, 'value') else str(typ),
        "description": allergen.get("description"),
        "note": allergen.get("note"),
        "prescription": prescription
    }


# ============================================================================
# 경쟁사 뉴스 관리 (별도 라우터 include)
# ============================================================================

router.include_router(news_router)
router.include_router(analytics_router)
