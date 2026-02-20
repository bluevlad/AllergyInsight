"""Professional Dashboard Routes - 대시보드 API

의료진을 위한 대시보드 통계 및 현황 정보를 제공합니다.
"""
from typing import List, Optional
from datetime import datetime, date, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from pydantic import BaseModel

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
from ...core.allergen import ALLERGEN_NAMES_KR

router = APIRouter(prefix="/dashboard", tags=["Professional - Dashboard"])


# ============================================================================
# Schemas
# ============================================================================

class DashboardStats(BaseModel):
    """대시보드 통계"""
    total_patients: int
    active_patients: int
    pending_consent: int
    today_diagnoses: int
    this_week_diagnoses: int
    this_month_diagnoses: int
    recent_patients: List[dict]
    recent_diagnoses: List[dict]

class DoctorStats(BaseModel):
    """의사별 통계"""
    doctor_id: int
    doctor_name: str
    total_patients: int
    this_month_diagnoses: int

class AllergenStats(BaseModel):
    """알러젠별 통계"""
    allergen_code: str
    allergen_name: str
    positive_count: int
    high_risk_count: int
    percentage: float


# ============================================================================
# Endpoints
# ============================================================================

@router.get("/stats", response_model=DashboardStats)
async def get_dashboard_stats(
    db: Session = Depends(get_db),
    org_ctx: OrganizationContext = Depends(get_organization_context)
):
    """병원 대시보드 통계"""
    org_id = org_ctx.organization_id
    today = date.today()
    week_start = today - timedelta(days=today.weekday())
    month_start = today.replace(day=1)

    # admin은 조직 소속 없이도 전체 데이터 조회
    org_filter = [HospitalPatient.organization_id == org_id] if org_id else []

    # 환자 통계
    total_patients = db.query(HospitalPatient).filter(
        *org_filter
    ).count()

    active_patients = db.query(HospitalPatient).filter(
        *org_filter,
        HospitalPatient.status == HospitalPatientStatus.ACTIVE
    ).count()

    pending_consent = db.query(HospitalPatient).filter(
        *org_filter,
        HospitalPatient.status == HospitalPatientStatus.PENDING_CONSENT
    ).count()

    # 병원 환자들의 user_id 서브쿼리
    patient_user_ids = db.query(HospitalPatient.patient_user_id).filter(
        *org_filter
    ).subquery()

    # 진단 통계
    today_diagnoses = db.query(UserDiagnosis).filter(
        UserDiagnosis.user_id.in_(patient_user_ids),
        func.date(UserDiagnosis.created_at) == today
    ).count()

    this_week_diagnoses = db.query(UserDiagnosis).filter(
        UserDiagnosis.user_id.in_(patient_user_ids),
        UserDiagnosis.created_at >= datetime.combine(week_start, datetime.min.time())
    ).count()

    this_month_diagnoses = db.query(UserDiagnosis).filter(
        UserDiagnosis.user_id.in_(patient_user_ids),
        UserDiagnosis.created_at >= datetime.combine(month_start, datetime.min.time())
    ).count()

    # 최근 등록 환자 (5명)
    recent_patients_query = db.query(HospitalPatient).filter(
        *org_filter
    ).order_by(HospitalPatient.created_at.desc()).limit(5).all()

    # 배치 로딩: 최근 환자 + 진단의 user_id를 한 번에 조회
    recent_patient_user_ids = [hp.patient_user_id for hp in recent_patients_query]

    # 최근 진단 (5건)
    recent_diagnoses_query = db.query(UserDiagnosis).filter(
        UserDiagnosis.user_id.in_(patient_user_ids)
    ).order_by(UserDiagnosis.created_at.desc()).limit(5).all()

    recent_diag_user_ids = [d.user_id for d in recent_diagnoses_query]

    # 한 번에 사용자 조회
    all_user_ids = set(recent_patient_user_ids + recent_diag_user_ids)
    users_map = {}
    if all_user_ids:
        users = db.query(User).filter(User.id.in_(all_user_ids)).all()
        users_map = {u.id: u for u in users}

    recent_patients = []
    for hp in recent_patients_query:
        patient_user = users_map.get(hp.patient_user_id)
        recent_patients.append({
            "id": hp.id,
            "patient_name": patient_user.name if patient_user else "Unknown",
            "patient_number": hp.patient_number,
            "status": hp.status.value if hasattr(hp.status, 'value') else hp.status,
            "created_at": hp.created_at.isoformat()
        })

    recent_diagnoses = []
    for d in recent_diagnoses_query:
        patient_user = users_map.get(d.user_id)
        positive_count = sum(1 for v in d.results.values() if v > 0) if d.results else 0
        recent_diagnoses.append({
            "id": d.id,
            "patient_name": patient_user.name if patient_user else "Unknown",
            "positive_count": positive_count,
            "diagnosis_date": d.created_at.date().isoformat(),
            "created_at": d.created_at.isoformat()
        })

    return DashboardStats(
        total_patients=total_patients,
        active_patients=active_patients,
        pending_consent=pending_consent,
        today_diagnoses=today_diagnoses,
        this_week_diagnoses=this_week_diagnoses,
        this_month_diagnoses=this_month_diagnoses,
        recent_patients=recent_patients,
        recent_diagnoses=recent_diagnoses
    )


@router.get("/doctors", response_model=List[DoctorStats])
async def get_doctor_stats(
    db: Session = Depends(get_db),
    org_ctx: OrganizationContext = Depends(get_organization_context)
):
    """의사별 환자/진단 통계"""
    org_id = org_ctx.organization_id
    today = date.today()
    month_start = today.replace(day=1)

    org_filter = [OrganizationMember.organization_id == org_id] if org_id else []

    doctors = db.query(OrganizationMember).filter(
        *org_filter,
        OrganizationMember.role == "doctor",
        OrganizationMember.is_active == True
    ).all()

    if not doctors:
        return []

    # 배치 로딩: 의사 사용자 정보
    doc_user_ids = [doc.user_id for doc in doctors]
    doc_users = db.query(User).filter(User.id.in_(doc_user_ids)).all()
    doc_user_map = {u.id: u.name for u in doc_users}

    # 배치 로딩: 의사별 담당 환자 수 (한 쿼리)
    doc_ids = [doc.id for doc in doctors]
    patient_counts = db.query(
        HospitalPatient.assigned_doctor_id,
        func.count(HospitalPatient.id)
    ).filter(
        HospitalPatient.assigned_doctor_id.in_(doc_ids),
        HospitalPatient.status == HospitalPatientStatus.ACTIVE
    ).group_by(HospitalPatient.assigned_doctor_id).all()
    patient_count_map = dict(patient_counts)

    # 배치 로딩: 의사별 이번 달 진단 수
    # 먼저 의사별 환자 목록
    doc_patient_rows = db.query(
        HospitalPatient.assigned_doctor_id,
        HospitalPatient.patient_user_id
    ).filter(
        HospitalPatient.assigned_doctor_id.in_(doc_ids)
    ).all()

    doc_to_patients = {}
    all_patient_uids = set()
    for did, puid in doc_patient_rows:
        doc_to_patients.setdefault(did, set()).add(puid)
        all_patient_uids.add(puid)

    # 이번 달 진단 수 (환자별)
    month_diag_counts = {}
    if all_patient_uids:
        rows = db.query(
            UserDiagnosis.user_id,
            func.count(UserDiagnosis.id)
        ).filter(
            UserDiagnosis.user_id.in_(all_patient_uids),
            UserDiagnosis.created_at >= datetime.combine(month_start, datetime.min.time())
        ).group_by(UserDiagnosis.user_id).all()
        month_diag_counts = dict(rows)

    result = []
    for doc in doctors:
        patient_uids = doc_to_patients.get(doc.id, set())
        month_diagnoses = sum(month_diag_counts.get(uid, 0) for uid in patient_uids)

        result.append(DoctorStats(
            doctor_id=doc.id,
            doctor_name=doc_user_map.get(doc.user_id, "Unknown"),
            total_patients=patient_count_map.get(doc.id, 0),
            this_month_diagnoses=month_diagnoses
        ))

    return result


@router.get("/allergens", response_model=List[AllergenStats])
async def get_allergen_stats(
    period: str = Query("month", regex="^(week|month|year|all)$"),
    db: Session = Depends(get_db),
    org_ctx: OrganizationContext = Depends(get_organization_context)
):
    """알러젠별 통계 (양성 비율)"""
    org_id = org_ctx.organization_id
    today = date.today()

    # 기간 설정
    if period == "week":
        start_date = today - timedelta(days=7)
    elif period == "month":
        start_date = today.replace(day=1)
    elif period == "year":
        start_date = today.replace(month=1, day=1)
    else:
        start_date = None

    # 병원 환자들의 user_id
    org_filter = [HospitalPatient.organization_id == org_id] if org_id else []
    patient_user_ids = db.query(HospitalPatient.patient_user_id).filter(
        *org_filter
    ).subquery()

    # 진단 데이터 조회
    query = db.query(UserDiagnosis).filter(
        UserDiagnosis.user_id.in_(patient_user_ids)
    )
    if start_date:
        query = query.filter(
            UserDiagnosis.created_at >= datetime.combine(start_date, datetime.min.time())
        )

    diagnoses = query.all()
    total_diagnoses = len(diagnoses)

    if total_diagnoses == 0:
        return []

    # 알러젠별 통계 계산
    allergen_counts = {}
    for diag in diagnoses:
        if not diag.results:
            continue
        for allergen, grade in diag.results.items():
            if allergen not in allergen_counts:
                allergen_counts[allergen] = {"positive": 0, "high_risk": 0}
            if grade > 0:
                allergen_counts[allergen]["positive"] += 1
            if grade >= 4:
                allergen_counts[allergen]["high_risk"] += 1

    result = []
    for allergen, counts in allergen_counts.items():
        result.append(AllergenStats(
            allergen_code=allergen,
            allergen_name=ALLERGEN_NAMES_KR.get(allergen, allergen),
            positive_count=counts["positive"],
            high_risk_count=counts["high_risk"],
            percentage=round((counts["positive"] / total_diagnoses) * 100, 1)
        ))

    # 양성 비율 순으로 정렬
    result.sort(key=lambda x: x.positive_count, reverse=True)

    return result


@router.get("/organization")
async def get_organization_info(
    db: Session = Depends(get_db),
    org_ctx: OrganizationContext = Depends(get_organization_context)
):
    """현재 조직 정보"""
    if not org_ctx.organization_id:
        # admin은 조직 소속이 없을 수 있음
        return {"id": None, "name": "전체 (관리자)", "org_type": None, "member_count": 0, "role_counts": {}, "created_at": None}

    org = db.query(Organization).filter(
        Organization.id == org_ctx.organization_id
    ).first()

    if not org:
        raise HTTPException(404, "조직을 찾을 수 없습니다")

    # 멤버 수
    member_count = db.query(OrganizationMember).filter(
        OrganizationMember.organization_id == org.id,
        OrganizationMember.is_active == True
    ).count()

    # 역할별 멤버 수
    role_counts = {}
    members = db.query(OrganizationMember).filter(
        OrganizationMember.organization_id == org.id,
        OrganizationMember.is_active == True
    ).all()

    for m in members:
        role_counts[m.role] = role_counts.get(m.role, 0) + 1

    return {
        "id": org.id,
        "name": org.name,
        "org_type": org.org_type,
        "status": org.status,
        "member_count": member_count,
        "role_counts": role_counts,
        "created_at": org.created_at.isoformat()
    }
