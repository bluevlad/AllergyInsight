"""Hospital Routes - Phase 2: 병원-환자 관리 API"""
from datetime import datetime, date, timezone
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_

from ..database import get_db
from ..database.models import User, UserDiagnosis
from ..database.organization_models import (
    Organization, OrganizationMember, HospitalPatient,
    HospitalPatientStatus, UserRole
)
from ..auth.dependencies import (
    require_auth, require_hospital_staff,
    OrganizationContext, get_organization_context
)
from .schemas import (
    HospitalPatientCreate, HospitalPatientCreateNew,
    HospitalPatientUpdate, HospitalPatientResponse,
    HospitalPatientListResponse,
    PatientConsentRequest, PatientConsentResponse,
    PatientSearchRequest, PatientDiagnosisResponse,
    PatientDiagnosisListResponse, PatientDiagnosisCreate,
    HospitalDashboardStats, DoctorPatientStats
)

router = APIRouter(prefix="/hospital", tags=["Hospital"])


# ===== Helper Functions =====

def get_patient_response(
    hp: HospitalPatient,
    db: Session,
    include_stats: bool = False
) -> HospitalPatientResponse:
    """HospitalPatient를 Response로 변환"""
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

    return HospitalPatientResponse(
        id=hp.id,
        organization_id=hp.organization_id,
        patient_user_id=hp.patient_user_id,
        patient_number=hp.patient_number,
        consent_signed=hp.consent_signed,
        consent_date=hp.consent_date,
        status=hp.status,
        created_at=hp.created_at,
        updated_at=hp.updated_at,
        patient_name=patient_user.name if patient_user else None,
        patient_phone=patient_user.phone if patient_user else None,
        patient_birth_date=patient_user.birth_date if patient_user else None,
        assigned_doctor_id=hp.assigned_doctor_id,
        assigned_doctor_name=doctor_name,
        diagnosis_count=diagnosis_count,
        last_diagnosis_date=last_diagnosis_date
    )


# ===== Patient Management Endpoints =====

@router.get("/patients", response_model=HospitalPatientListResponse)
async def list_hospital_patients(
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

    # 필터링
    if status:
        base_query = base_query.filter(HospitalPatient.status == status)

    if assigned_doctor_id:
        base_query = base_query.filter(HospitalPatient.assigned_doctor_id == assigned_doctor_id)

    # 검색어 처리 (이름, 전화번호, 환자번호)
    if query:
        # 환자번호로 직접 검색
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

    items = [get_patient_response(p, db, include_stats=True) for p in patients]

    return HospitalPatientListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size
    )


@router.post("/patients", response_model=HospitalPatientResponse)
async def register_existing_patient(
    data: HospitalPatientCreate,
    db: Session = Depends(get_db),
    org_ctx: OrganizationContext = Depends(get_organization_context)
):
    """기존 사용자를 병원 환자로 등록"""
    # 환자 사용자 확인
    patient_user = db.query(User).filter(User.id == data.patient_user_id).first()
    if not patient_user:
        raise HTTPException(404, "환자 사용자를 찾을 수 없습니다")

    # 이미 등록된 환자인지 확인
    existing = db.query(HospitalPatient).filter(
        HospitalPatient.organization_id == org_ctx.organization_id,
        HospitalPatient.patient_user_id == data.patient_user_id
    ).first()

    if existing:
        raise HTTPException(400, "이미 등록된 환자입니다")

    # 담당 의사 확인
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

    return get_patient_response(hp, db)


@router.post("/patients/new", response_model=HospitalPatientResponse)
async def register_new_patient(
    data: HospitalPatientCreateNew,
    db: Session = Depends(get_db),
    org_ctx: OrganizationContext = Depends(get_organization_context)
):
    """신규 사용자 생성 및 병원 환자 등록"""
    import secrets

    # 전화번호로 기존 사용자 확인
    existing_user = db.query(User).filter(User.phone == data.phone).first()
    if existing_user:
        raise HTTPException(
            400,
            "해당 전화번호로 등록된 사용자가 있습니다. 기존 환자 등록 API를 사용하세요."
        )

    # 신규 사용자 생성
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
    db.flush()  # ID 생성

    # 병원 환자 등록
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

    return get_patient_response(hp, db)


@router.get("/patients/{patient_id}", response_model=HospitalPatientResponse)
async def get_hospital_patient(
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

    return get_patient_response(hp, db, include_stats=True)


@router.put("/patients/{patient_id}", response_model=HospitalPatientResponse)
async def update_hospital_patient(
    patient_id: int,
    data: HospitalPatientUpdate,
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

    hp.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(hp)

    return get_patient_response(hp, db)


# ===== Patient Consent Endpoints =====

@router.post("/patients/{patient_id}/consent", response_model=PatientConsentResponse)
async def sign_patient_consent(
    patient_id: int,
    data: PatientConsentRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_auth)
):
    """환자 동의서 서명 (환자 본인이 서명)"""
    hp = db.query(HospitalPatient).filter(
        HospitalPatient.id == patient_id,
        HospitalPatient.patient_user_id == current_user.id
    ).first()

    if not hp:
        raise HTTPException(404, "해당 병원 연결 정보를 찾을 수 없습니다")

    if hp.consent_signed:
        raise HTTPException(400, "이미 동의서가 서명되었습니다")

    if not data.consent_agreed:
        return PatientConsentResponse(
            hospital_patient_id=hp.id,
            consent_signed=False,
            consent_date=None,
            status=hp.status,
            message="동의가 거부되었습니다"
        )

    hp.consent_signed = True
    hp.consent_date = datetime.now(timezone.utc)
    hp.status = HospitalPatientStatus.ACTIVE
    hp.updated_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(hp)

    return PatientConsentResponse(
        hospital_patient_id=hp.id,
        consent_signed=True,
        consent_date=hp.consent_date,
        status=hp.status,
        message="동의서가 성공적으로 서명되었습니다"
    )


@router.get("/my-hospitals")
async def get_my_hospital_connections(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_auth)
):
    """환자의 병원 연결 목록 조회"""
    connections = db.query(HospitalPatient).filter(
        HospitalPatient.patient_user_id == current_user.id
    ).all()

    result = []
    for hp in connections:
        org = db.query(Organization).filter(Organization.id == hp.organization_id).first()
        result.append({
            "hospital_patient_id": hp.id,
            "organization_id": hp.organization_id,
            "organization_name": org.name if org else None,
            "patient_number": hp.patient_number,
            "consent_signed": hp.consent_signed,
            "consent_date": hp.consent_date,
            "status": hp.status.value if hasattr(hp.status, 'value') else hp.status,
            "created_at": hp.created_at
        })

    return {"items": result, "total": len(result)}


# ===== Patient Diagnosis Endpoints =====

@router.get("/patients/{patient_id}/diagnoses", response_model=PatientDiagnosisListResponse)
async def get_patient_diagnoses(
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

        items.append(PatientDiagnosisResponse(
            id=d.id,
            diagnosis_date=d.created_at.date(),
            results=d.results if hasattr(d, 'results') else {},
            prescription=d.prescription if hasattr(d, 'prescription') else None,
            doctor_note=d.doctor_note if hasattr(d, 'doctor_note') else None,
            entered_by_name=entered_by_name,
            created_at=d.created_at
        ))

    return PatientDiagnosisListResponse(
        patient_id=hp.patient_user_id,
        patient_name=patient_user.name if patient_user else "Unknown",
        items=items,
        total=len(items)
    )


@router.post("/patients/{patient_id}/diagnoses", response_model=PatientDiagnosisResponse)
async def create_patient_diagnosis(
    patient_id: int,
    data: PatientDiagnosisCreate,
    db: Session = Depends(get_db),
    org_ctx: OrganizationContext = Depends(get_organization_context)
):
    """환자 진단 결과 입력 (병원 직원)"""
    if not org_ctx.can_edit_diagnosis():
        raise HTTPException(403, "진단 입력 권한이 없습니다")

    hp = db.query(HospitalPatient).filter(
        HospitalPatient.id == patient_id,
        HospitalPatient.organization_id == org_ctx.organization_id
    ).first()

    if not hp:
        raise HTTPException(404, "환자를 찾을 수 없습니다")

    if not hp.consent_signed:
        raise HTTPException(403, "환자의 동의가 필요합니다")

    # UserDiagnosis 생성 - 기존 모델 구조에 맞춤
    new_diagnosis = UserDiagnosis(
        user_id=hp.patient_user_id,
        results=data.results,
        created_at=datetime.combine(data.diagnosis_date, datetime.min.time())
    )

    # 추가 필드가 있으면 설정
    if hasattr(UserDiagnosis, 'doctor_note'):
        new_diagnosis.doctor_note = data.doctor_note
    if hasattr(UserDiagnosis, 'entered_by'):
        new_diagnosis.entered_by = org_ctx.user.id

    db.add(new_diagnosis)
    db.commit()
    db.refresh(new_diagnosis)

    return PatientDiagnosisResponse(
        id=new_diagnosis.id,
        diagnosis_date=data.diagnosis_date,
        results=new_diagnosis.results,
        prescription=None,
        doctor_note=data.doctor_note,
        entered_by_name=org_ctx.user.name,
        created_at=new_diagnosis.created_at
    )


# ===== Dashboard Endpoints =====

@router.get("/dashboard", response_model=HospitalDashboardStats)
async def get_hospital_dashboard(
    db: Session = Depends(get_db),
    org_ctx: OrganizationContext = Depends(get_organization_context)
):
    """병원 대시보드 통계"""
    org_id = org_ctx.organization_id
    today = date.today()

    # 환자 통계
    total_patients = db.query(HospitalPatient).filter(
        HospitalPatient.organization_id == org_id
    ).count()

    active_patients = db.query(HospitalPatient).filter(
        HospitalPatient.organization_id == org_id,
        HospitalPatient.status == HospitalPatientStatus.ACTIVE
    ).count()

    pending_consent = db.query(HospitalPatient).filter(
        HospitalPatient.organization_id == org_id,
        HospitalPatient.status == HospitalPatientStatus.PENDING_CONSENT
    ).count()

    # 진단 통계 - 병원 환자들의 진단만
    patient_user_ids = db.query(HospitalPatient.patient_user_id).filter(
        HospitalPatient.organization_id == org_id
    ).subquery()

    today_diagnoses = db.query(UserDiagnosis).filter(
        UserDiagnosis.user_id.in_(patient_user_ids),
        func.date(UserDiagnosis.created_at) == today
    ).count()

    # 이번 달 진단
    first_day_of_month = today.replace(day=1)
    this_month_diagnoses = db.query(UserDiagnosis).filter(
        UserDiagnosis.user_id.in_(patient_user_ids),
        UserDiagnosis.created_at >= first_day_of_month
    ).count()

    # 최근 환자 (5명)
    recent_patients_query = db.query(HospitalPatient).filter(
        HospitalPatient.organization_id == org_id
    ).order_by(HospitalPatient.created_at.desc()).limit(5).all()

    recent_patients = [get_patient_response(p, db) for p in recent_patients_query]

    # 최근 진단 (5건)
    recent_diagnoses_query = db.query(UserDiagnosis).filter(
        UserDiagnosis.user_id.in_(patient_user_ids)
    ).order_by(UserDiagnosis.created_at.desc()).limit(5).all()

    recent_diagnoses = []
    for d in recent_diagnoses_query:
        recent_diagnoses.append(PatientDiagnosisResponse(
            id=d.id,
            diagnosis_date=d.created_at.date(),
            results=d.results if hasattr(d, 'results') else {},
            prescription=d.prescription if hasattr(d, 'prescription') else None,
            doctor_note=d.doctor_note if hasattr(d, 'doctor_note') else None,
            entered_by_name=None,
            created_at=d.created_at
        ))

    return HospitalDashboardStats(
        total_patients=total_patients,
        active_patients=active_patients,
        pending_consent=pending_consent,
        today_diagnoses=today_diagnoses,
        this_month_diagnoses=this_month_diagnoses,
        recent_patients=recent_patients,
        recent_diagnoses=recent_diagnoses
    )


@router.get("/doctors/stats", response_model=List[DoctorPatientStats])
async def get_doctor_stats(
    db: Session = Depends(get_db),
    org_ctx: OrganizationContext = Depends(get_organization_context)
):
    """의사별 환자 통계"""
    org_id = org_ctx.organization_id
    today = date.today()
    first_day_of_month = today.replace(day=1)

    # 조직의 의사 목록
    doctors = db.query(OrganizationMember).filter(
        OrganizationMember.organization_id == org_id,
        OrganizationMember.role == "doctor",
        OrganizationMember.is_active == True
    ).all()

    result = []
    for doc in doctors:
        doc_user = db.query(User).filter(User.id == doc.user_id).first()

        # 담당 환자 수
        patient_count = db.query(HospitalPatient).filter(
            HospitalPatient.organization_id == org_id,
            HospitalPatient.assigned_doctor_id == doc.id,
            HospitalPatient.status == HospitalPatientStatus.ACTIVE
        ).count()

        # 이번 달 진단 수 (담당 환자)
        patient_user_ids = db.query(HospitalPatient.patient_user_id).filter(
            HospitalPatient.organization_id == org_id,
            HospitalPatient.assigned_doctor_id == doc.id
        ).subquery()

        month_diagnoses = db.query(UserDiagnosis).filter(
            UserDiagnosis.user_id.in_(patient_user_ids),
            UserDiagnosis.created_at >= first_day_of_month
        ).count()

        result.append(DoctorPatientStats(
            doctor_id=doc.id,
            doctor_name=doc_user.name if doc_user else "Unknown",
            total_patients=patient_count,
            this_month_diagnoses=month_diagnoses
        ))

    return result
