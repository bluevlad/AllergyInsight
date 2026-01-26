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
    include_stats: bool = False
) -> PatientResponse:
    """HospitalPatient를 PatientResponse로 변환"""
    patient_user = db.query(User).filter(User.id == hp.patient_user_id).first()

    # 담당 의사 정보
    doctor_name = None
    if hp.assigned_doctor_id:
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
    base_query = db.query(HospitalPatient).filter(
        HospitalPatient.organization_id == org_ctx.organization_id
    )

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

    items = [build_patient_response(p, db, include_stats=True) for p in patients]

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
