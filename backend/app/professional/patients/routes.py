"""Professional Patients Routes - 환자 관리 API

병원에 등록된 환자를 관리하는 API입니다.
기존 hospital/routes.py의 기능을 Professional 서비스로 통합합니다.
"""
from typing import Optional, List
from datetime import datetime, date
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, func
from pydantic import BaseModel, Field

from ...database import get_db
from ...database.models import User, UserDiagnosis
from ...database.organization_models import (
    Organization, OrganizationMember, HospitalPatient,
    HospitalPatientStatus, UserRole
)
from ...core.auth import (
    require_professional,
    OrganizationContext, get_organization_context
)
from sqlalchemy.orm import joinedload

router = APIRouter(prefix="/patients", tags=["Professional - Patients"])


# ============================================================================
# Schemas
# ============================================================================

class PatientCreateRequest(BaseModel):
    """기존 사용자를 환자로 등록"""
    patient_user_id: int
    patient_number: Optional[str] = None
    assigned_doctor_id: Optional[int] = None

class PatientCreateNewRequest(BaseModel):
    """신규 환자 등록 (사용자 생성 포함)"""
    name: str = Field(..., min_length=1)
    phone: str = Field(..., min_length=10)
    birth_date: Optional[date] = None
    patient_number: Optional[str] = None
    assigned_doctor_id: Optional[int] = None

class PatientUpdateRequest(BaseModel):
    """환자 정보 수정"""
    patient_number: Optional[str] = None
    assigned_doctor_id: Optional[int] = None
    status: Optional[HospitalPatientStatus] = None

class PatientResponse(BaseModel):
    """환자 정보 응답"""
    id: int
    organization_id: int
    patient_user_id: int
    patient_number: Optional[str]
    patient_name: Optional[str]
    patient_phone: Optional[str]
    patient_birth_date: Optional[date]
    assigned_doctor_id: Optional[int]
    assigned_doctor_name: Optional[str]
    consent_signed: bool
    consent_date: Optional[datetime]
    status: HospitalPatientStatus
    diagnosis_count: Optional[int] = None
    last_diagnosis_date: Optional[date] = None
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True

class PatientListResponse(BaseModel):
    """환자 목록 응답"""
    items: List[PatientResponse]
    total: int
    page: int
    page_size: int


# ============================================================================
# Helper Functions
# ============================================================================

def build_patient_response(
    hp: HospitalPatient,
    db: Session,
    include_stats: bool = False,
    users_map: dict = None,
    doctors_map: dict = None,
    diag_stats_map: dict = None,
) -> PatientResponse:
    """HospitalPatient를 PatientResponse로 변환

    Args:
        users_map: {user_id: User} 사전 로딩된 사용자 맵
        doctors_map: {doctor_member_id: doctor_name} 사전 로딩된 의사 맵
        diag_stats_map: {user_id: (count, last_date)} 사전 로딩된 진단 통계 맵
    """
    # 사전 로딩된 맵 사용, 없으면 개별 쿼리 (단건 조회 시)
    if users_map is not None:
        patient_user = users_map.get(hp.patient_user_id)
    else:
        patient_user = db.query(User).filter(User.id == hp.patient_user_id).first()

    # 담당 의사 정보
    doctor_name = None
    if hp.assigned_doctor_id:
        if doctors_map is not None:
            doctor_name = doctors_map.get(hp.assigned_doctor_id)
        else:
            doctor_member = db.query(OrganizationMember).filter(
                OrganizationMember.id == hp.assigned_doctor_id
            ).first()
            if doctor_member:
                doctor_user = db.query(User).filter(User.id == doctor_member.user_id).first()
                if doctor_user:
                    doctor_name = doctor_user.name

    # 진단 통계
    diagnosis_count = None
    last_diagnosis_date = None
    if include_stats and patient_user:
        if diag_stats_map is not None:
            stats = diag_stats_map.get(patient_user.id)
            if stats:
                diagnosis_count, last_diagnosis_date = stats
            else:
                diagnosis_count = 0
        else:
            diagnosis_count = db.query(UserDiagnosis).filter(
                UserDiagnosis.user_id == patient_user.id
            ).count()

            last_diagnosis = db.query(UserDiagnosis).filter(
                UserDiagnosis.user_id == patient_user.id
            ).order_by(UserDiagnosis.created_at.desc()).first()

            if last_diagnosis:
                last_diagnosis_date = last_diagnosis.created_at.date()

    return PatientResponse(
        id=hp.id,
        organization_id=hp.organization_id,
        patient_user_id=hp.patient_user_id,
        patient_number=hp.patient_number,
        patient_name=patient_user.name if patient_user else None,
        patient_phone=patient_user.phone if patient_user else None,
        patient_birth_date=patient_user.birth_date if patient_user else None,
        assigned_doctor_id=hp.assigned_doctor_id,
        assigned_doctor_name=doctor_name,
        consent_signed=hp.consent_signed,
        consent_date=hp.consent_date,
        status=hp.status,
        diagnosis_count=diagnosis_count,
        last_diagnosis_date=last_diagnosis_date,
        created_at=hp.created_at,
        updated_at=hp.updated_at
    )


# ============================================================================
# Endpoints
# ============================================================================

@router.get("", response_model=PatientListResponse)
async def list_patients(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[HospitalPatientStatus] = None,
    assigned_doctor_id: Optional[int] = None,
    query: Optional[str] = None,
    db: Session = Depends(get_db),
    org_ctx: OrganizationContext = Depends(get_organization_context)
):
    """병원 환자 목록 조회"""
    org_filter = [HospitalPatient.organization_id == org_ctx.organization_id] if org_ctx.organization_id else []
    base_query = db.query(HospitalPatient).filter(*org_filter)

    if status:
        base_query = base_query.filter(HospitalPatient.status == status)

    if assigned_doctor_id:
        base_query = base_query.filter(HospitalPatient.assigned_doctor_id == assigned_doctor_id)

    if query:
        base_query = base_query.outerjoin(
            User, HospitalPatient.patient_user_id == User.id
        ).filter(
            or_(
                HospitalPatient.patient_number.ilike(f"%{query}%"),
                User.name.ilike(f"%{query}%"),
                User.phone.ilike(f"%{query}%")
            )
        )

    total = base_query.count()
    patients = base_query.order_by(
        HospitalPatient.created_at.desc()
    ).offset((page - 1) * page_size).limit(page_size).all()

    # 배치 로딩: N+1 방지
    patient_user_ids = [p.patient_user_id for p in patients]
    doctor_member_ids = [p.assigned_doctor_id for p in patients if p.assigned_doctor_id]

    # 사용자 맵
    users_map = {}
    if patient_user_ids:
        users = db.query(User).filter(User.id.in_(patient_user_ids)).all()
        users_map = {u.id: u for u in users}

    # 의사 이름 맵
    doctors_map = {}
    if doctor_member_ids:
        members = db.query(OrganizationMember).filter(
            OrganizationMember.id.in_(doctor_member_ids)
        ).all()
        member_user_ids = [m.user_id for m in members]
        if member_user_ids:
            doc_users = db.query(User).filter(User.id.in_(member_user_ids)).all()
            doc_user_map = {u.id: u.name for u in doc_users}
            doctors_map = {m.id: doc_user_map.get(m.user_id) for m in members}

    # 진단 통계 맵 (count + last_date)
    diag_stats_map = {}
    if patient_user_ids:
        diag_counts = db.query(
            UserDiagnosis.user_id,
            func.count(UserDiagnosis.id),
            func.max(UserDiagnosis.created_at)
        ).filter(
            UserDiagnosis.user_id.in_(patient_user_ids)
        ).group_by(UserDiagnosis.user_id).all()
        for uid, cnt, last_dt in diag_counts:
            diag_stats_map[uid] = (cnt, last_dt.date() if last_dt else None)

    items = [
        build_patient_response(
            p, db, include_stats=True,
            users_map=users_map, doctors_map=doctors_map, diag_stats_map=diag_stats_map
        ) for p in patients
    ]

    return PatientListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size
    )


@router.post("", response_model=PatientResponse)
async def register_existing_patient(
    data: PatientCreateRequest,
    db: Session = Depends(get_db),
    org_ctx: OrganizationContext = Depends(get_organization_context)
):
    """기존 사용자를 병원 환자로 등록"""
    patient_user = db.query(User).filter(User.id == data.patient_user_id).first()
    if not patient_user:
        raise HTTPException(404, "환자 사용자를 찾을 수 없습니다")

    existing = db.query(HospitalPatient).filter(
        HospitalPatient.organization_id == org_ctx.organization_id,
        HospitalPatient.patient_user_id == data.patient_user_id
    ).first()
    if existing:
        raise HTTPException(400, "이미 등록된 환자입니다")

    if data.assigned_doctor_id:
        doctor = db.query(OrganizationMember).filter(
            OrganizationMember.id == data.assigned_doctor_id,
            OrganizationMember.organization_id == org_ctx.organization_id,
            OrganizationMember.role == "doctor"
        ).first()
        if not doctor:
            raise HTTPException(400, "유효하지 않은 담당 의사입니다")

    hp = HospitalPatient(
        organization_id=org_ctx.organization_id,
        patient_user_id=data.patient_user_id,
        patient_number=data.patient_number,
        assigned_doctor_id=data.assigned_doctor_id,
        status=HospitalPatientStatus.PENDING_CONSENT
    )
    db.add(hp)
    db.commit()
    db.refresh(hp)

    return build_patient_response(hp, db)


@router.post("/new", response_model=PatientResponse)
async def register_new_patient(
    data: PatientCreateNewRequest,
    db: Session = Depends(get_db),
    org_ctx: OrganizationContext = Depends(get_organization_context)
):
    """신규 사용자 생성 및 병원 환자 등록"""
    import secrets

    existing_user = db.query(User).filter(User.phone == data.phone).first()
    if existing_user:
        raise HTTPException(
            400,
            "해당 전화번호로 등록된 사용자가 있습니다. 기존 환자 등록 API를 사용하세요."
        )

    access_pin = ''.join([str(secrets.randbelow(10)) for _ in range(6)])

    new_user = User(
        name=data.name,
        phone=data.phone,
        birth_date=data.birth_date,
        access_pin=access_pin,
        role=UserRole.PATIENT.value,
        is_active=True
    )
    db.add(new_user)
    db.flush()

    hp = HospitalPatient(
        organization_id=org_ctx.organization_id,
        patient_user_id=new_user.id,
        patient_number=data.patient_number,
        assigned_doctor_id=data.assigned_doctor_id,
        status=HospitalPatientStatus.PENDING_CONSENT
    )
    db.add(hp)
    db.commit()
    db.refresh(hp)

    return build_patient_response(hp, db)


@router.get("/{patient_id}", response_model=PatientResponse)
async def get_patient(
    patient_id: int,
    db: Session = Depends(get_db),
    org_ctx: OrganizationContext = Depends(get_organization_context)
):
    """병원 환자 상세 조회"""
    hp = db.query(HospitalPatient).filter(
        HospitalPatient.id == patient_id,
        HospitalPatient.organization_id == org_ctx.organization_id
    ).first()

    if not hp:
        raise HTTPException(404, "환자를 찾을 수 없습니다")

    return build_patient_response(hp, db, include_stats=True)


@router.put("/{patient_id}", response_model=PatientResponse)
async def update_patient(
    patient_id: int,
    data: PatientUpdateRequest,
    db: Session = Depends(get_db),
    org_ctx: OrganizationContext = Depends(get_organization_context)
):
    """병원 환자 정보 수정"""
    hp = db.query(HospitalPatient).filter(
        HospitalPatient.id == patient_id,
        HospitalPatient.organization_id == org_ctx.organization_id
    ).first()

    if not hp:
        raise HTTPException(404, "환자를 찾을 수 없습니다")

    if data.patient_number is not None:
        hp.patient_number = data.patient_number

    if data.assigned_doctor_id is not None:
        if data.assigned_doctor_id > 0:
            doctor = db.query(OrganizationMember).filter(
                OrganizationMember.id == data.assigned_doctor_id,
                OrganizationMember.organization_id == org_ctx.organization_id,
                OrganizationMember.role == "doctor"
            ).first()
            if not doctor:
                raise HTTPException(400, "유효하지 않은 담당 의사입니다")
            hp.assigned_doctor_id = data.assigned_doctor_id
        else:
            hp.assigned_doctor_id = None

    if data.status is not None:
        hp.status = data.status

    hp.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(hp)

    return build_patient_response(hp, db)


@router.get("/search/by-phone")
async def search_patient_by_phone(
    phone: str = Query(..., min_length=10),
    db: Session = Depends(get_db),
    user: User = Depends(require_professional)
):
    """전화번호로 사용자 검색 (환자 등록 전 조회용)"""
    users = db.query(User).filter(User.phone.ilike(f"%{phone}%")).limit(10).all()

    return {
        "items": [
            {
                "id": u.id,
                "name": u.name,
                "phone": u.phone,
                "birth_date": u.birth_date,
                "role": u.role
            }
            for u in users
        ],
        "total": len(users)
    }


@router.get("/{patient_id}/diagnoses")
async def get_patient_diagnosis_history(
    patient_id: int,
    db: Session = Depends(get_db),
    org_ctx: OrganizationContext = Depends(get_organization_context)
):
    """환자 진단 이력 조회"""
    hp = db.query(HospitalPatient).filter(
        HospitalPatient.id == patient_id,
        HospitalPatient.organization_id == org_ctx.organization_id
    ).first()

    if not hp:
        raise HTTPException(404, "환자를 찾을 수 없습니다")

    if not hp.consent_signed:
        raise HTTPException(403, "환자의 동의가 필요합니다")

    patient_user = db.query(User).filter(User.id == hp.patient_user_id).first()

    diagnoses = db.query(UserDiagnosis).filter(
        UserDiagnosis.user_id == hp.patient_user_id
    ).order_by(UserDiagnosis.created_at.desc()).all()

    items = []
    for d in diagnoses:
        entered_by_name = None
        if hasattr(d, 'entered_by') and d.entered_by:
            entered_user = db.query(User).filter(User.id == d.entered_by).first()
            if entered_user:
                entered_by_name = entered_user.name

        items.append({
            "id": d.id,
            "diagnosis_date": d.created_at.date(),
            "results": d.results if hasattr(d, 'results') else {},
            "prescription": d.prescription if hasattr(d, 'prescription') else None,
            "doctor_note": d.doctor_note if hasattr(d, 'doctor_note') else None,
            "entered_by_name": entered_by_name,
            "created_at": d.created_at
        })

    return {
        "patient_id": hp.patient_user_id,
        "patient_name": patient_user.name if patient_user else "Unknown",
        "items": items,
        "total": len(items)
    }
