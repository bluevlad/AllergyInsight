"""Admin 메인 라우터"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from datetime import datetime, timedelta, timezone

from .news_routes import router as news_router
from .analytics_routes import router as analytics_router
from .subscriber_routes import router as subscriber_router
from typing import Optional, List

from .dependencies import require_super_admin
from .schemas import (
    DashboardResponse, DashboardStats, UserStats, DiagnosisStats,
    PaperStats, OrganizationStats,
    UserListResponse, UserListItem, UserDetail,
    UserUpdateRequest, UserRoleUpdateRequest,
    PaperListResponse, PaperListItem, AllergenLinkItem,
    OrganizationListResponse, OrganizationListItem
)
from ..database.connection import get_db
from ..database.models import User, DiagnosisKit, UserDiagnosis, Paper, PaperAllergenLink
from ..database.organization_models import Organization, OrganizationMember
from ..database.clinical_models import ClinicalStatement
from ..core.allergen import service as allergen_service

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
    now = datetime.now(timezone.utc)
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
    allergen_summary = allergen_service.get_summary(db)

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
    now = datetime.now(timezone.utc)

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

    items = []
    for paper in papers:
        # 알레르겐 연결 정보 조회
        allergen_link_items = []
        if paper.allergen_links:
            for link in paper.allergen_links:
                allergen_info = allergen_service.get_by_code(db, link.allergen_code)
                allergen_link_items.append(AllergenLinkItem(
                    allergen_code=link.allergen_code,
                    allergen_name=allergen_info.name_kr if allergen_info else link.allergen_code,
                    link_type=link.link_type,
                    specific_item=link.specific_item,
                    note=link.note
                ))

        # 수집 근거 생성
        collection_reason = _build_collection_reason(paper, allergen_link_items)

        items.append(PaperListItem(
            id=paper.id,
            title=paper.title,
            authors=paper.authors,
            journal=paper.journal,
            year=paper.year,
            is_guideline=paper.is_guideline or False,
            evidence_level=paper.evidence_level,
            source=paper.source,
            created_at=paper.created_at,
            pmid=paper.pmid,
            doi=paper.doi,
            url=paper.url,
            allergen_links=allergen_link_items,
            collection_reason=collection_reason
        ))

    return PaperListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size
    )


# 수집 근거 문구 생성 헬퍼
LINK_TYPE_NAMES = {
    "symptom": "증상",
    "dietary": "식이",
    "cross_reactivity": "교차반응",
    "substitute": "대체식품",
    "emergency": "응급",
    "management": "관리",
    "general": "일반",
}

def _build_collection_reason(paper: Paper, allergen_links: List[AllergenLinkItem]) -> str:
    """논문 수집 근거 문구를 생성한다."""
    parts = []

    # 출처
    source_names = {
        "pubmed": "PubMed",
        "semantic_scholar": "Semantic Scholar",
        "manual_upload": "직접 업로드",
        "manual": "직접 입력",
    }
    source_label = source_names.get(paper.source, paper.source or "알 수 없음")

    if paper.source in ("manual_upload", "manual"):
        parts.append(f"{source_label}으로 등록된 논문")
    else:
        parts.append(f"{source_label} 자동 수집")

    # 연결된 알레르겐
    if allergen_links:
        allergen_names = list(dict.fromkeys(
            link.allergen_name or link.allergen_code for link in allergen_links
        ))
        link_types = list(dict.fromkeys(
            LINK_TYPE_NAMES.get(link.link_type, link.link_type) for link in allergen_links
        ))
        parts.append(f"대상 알레르겐: {', '.join(allergen_names[:5])}")
        parts.append(f"관련 유형: {', '.join(link_types)}")

        # Auto-extracted 노트에서 검색 키워드 추출
        for link in allergen_links:
            if link.note and link.note.startswith("Auto-extracted:"):
                keyword = link.note.replace("Auto-extracted:", "").strip()
                parts.append(f"검색 키워드: \"{keyword}\"")
                break

    return " | ".join(parts)


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
# 알러젠 관리 (CRUD)
# ============================================================================

@router.get("/allergens")
async def get_allergens(
    category: Optional[str] = None,
    search: Optional[str] = None,
    current_user: User = Depends(require_super_admin),
    db: Session = Depends(get_db),
):
    """알러젠 목록 조회 (DB 기준)"""
    from ..data.allergen_master import AllergenCategory
    from ..data.allergen_prescription_db import ALLERGEN_PRESCRIPTION_DB

    items, total = allergen_service.list_allergens(
        db, category=category, search=search, limit=500, offset=0,
    )

    allergens = []
    for a in items:
        has_prescription = (
            a.code in ALLERGEN_PRESCRIPTION_DB or
            a.name_en.lower().replace(" ", "_") in ALLERGEN_PRESCRIPTION_DB
        )
        allergens.append({
            "code": a.code,
            "name_kr": a.name_kr,
            "name_en": a.name_en,
            "category": a.category,
            "type": a.type,
            "description": a.description,
            "has_prescription": has_prescription,
        })

    return {
        "items": allergens,
        "total": total,
        "categories": [c.value for c in AllergenCategory],
    }


@router.get("/allergens/{code}")
async def get_allergen_detail(
    code: str,
    current_user: User = Depends(require_super_admin),
    db: Session = Depends(get_db),
):
    """알러젠 상세 조회"""
    from ..data.allergen_master import get_legacy_code
    from ..data.allergen_prescription_db import ALLERGEN_PRESCRIPTION_DB
    from fastapi import HTTPException

    allergen = allergen_service.get_by_code(db, code)
    if not allergen:
        raise HTTPException(status_code=404, detail="알러젠을 찾을 수 없습니다.")

    # 처방 정보 조회
    legacy_code = get_legacy_code(code)
    prescription = None
    if legacy_code and legacy_code in ALLERGEN_PRESCRIPTION_DB:
        prescription = ALLERGEN_PRESCRIPTION_DB[legacy_code]

    return {
        "code": allergen.code,
        "name_kr": allergen.name_kr,
        "name_en": allergen.name_en,
        "category": allergen.category,
        "type": allergen.type,
        "description": allergen.description,
        "note": allergen.note,
        "prescription": prescription,
    }


@router.post("/allergens")
async def create_allergen(
    request: dict,
    current_user: User = Depends(require_super_admin),
    db: Session = Depends(get_db),
):
    """알러젠 추가"""
    from ..data.allergen_master import AllergenCategory, AllergenType
    from fastapi import HTTPException

    # 필수 필드 검증
    for field in ("code", "name_kr", "name_en", "category", "type"):
        if not request.get(field):
            raise HTTPException(status_code=400, detail=f"'{field}' 필드는 필수입니다.")

    # 카테고리/타입 유효성 검증
    valid_categories = [c.value for c in AllergenCategory]
    if request["category"] not in valid_categories:
        raise HTTPException(status_code=400, detail=f"유효하지 않은 카테고리: {request['category']}")

    valid_types = [t.value for t in AllergenType]
    if request["type"] not in valid_types:
        raise HTTPException(status_code=400, detail=f"유효하지 않은 타입: {request['type']}")

    # 중복 확인
    existing = allergen_service.get_by_code(db, request["code"])
    if existing:
        raise HTTPException(status_code=409, detail=f"이미 존재하는 코드: {request['code']}")

    allergen = allergen_service.create_allergen(db, request)
    return {"message": f"알러젠 '{allergen.code}' 추가 완료", "allergen": allergen.to_dict()}


@router.put("/allergens/{code}")
async def update_allergen(
    code: str,
    request: dict,
    current_user: User = Depends(require_super_admin),
    db: Session = Depends(get_db),
):
    """알러젠 수정"""
    from ..data.allergen_master import AllergenCategory, AllergenType
    from fastapi import HTTPException

    # 카테고리/타입 유효성 검증 (제공된 경우)
    if "category" in request:
        valid_categories = [c.value for c in AllergenCategory]
        if request["category"] not in valid_categories:
            raise HTTPException(status_code=400, detail=f"유효하지 않은 카테고리: {request['category']}")

    if "type" in request:
        valid_types = [t.value for t in AllergenType]
        if request["type"] not in valid_types:
            raise HTTPException(status_code=400, detail=f"유효하지 않은 타입: {request['type']}")

    allergen = allergen_service.update_allergen(db, code, request)
    if not allergen:
        raise HTTPException(status_code=404, detail="알러젠을 찾을 수 없습니다.")

    return {"message": f"알러젠 '{code}' 수정 완료", "allergen": allergen.to_dict()}


@router.delete("/allergens/{code}")
async def delete_allergen(
    code: str,
    current_user: User = Depends(require_super_admin),
    db: Session = Depends(get_db),
):
    """알러젠 삭제 (비활성화)"""
    from fastapi import HTTPException

    if not allergen_service.delete_allergen(db, code):
        raise HTTPException(status_code=404, detail="알러젠을 찾을 수 없습니다.")

    return {"message": f"알러젠 '{code}' 삭제 완료"}


@router.post("/allergens/{code}/restore")
async def restore_allergen(
    code: str,
    current_user: User = Depends(require_super_admin),
    db: Session = Depends(get_db),
):
    """삭제된 알러젠 복원"""
    from fastapi import HTTPException

    if not allergen_service.restore_allergen(db, code):
        raise HTTPException(status_code=404, detail="알러젠을 찾을 수 없습니다.")

    return {"message": f"알러젠 '{code}' 복원 완료"}


# ============================================================================
# 경쟁사 뉴스 관리 (별도 라우터 include)
# ============================================================================

router.include_router(news_router)
router.include_router(analytics_router)
router.include_router(subscriber_router)
