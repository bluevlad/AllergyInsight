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

    # 병원 환자들의 user_id 서브쿼리
    patient_user_ids = db.query(HospitalPatient.patient_user_id).filter(
        HospitalPatient.organization_id == org_id
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
        HospitalPatient.organization_id == org_id
    ).order_by(HospitalPatient.created_at.desc()).limit(5).all()

    recent_patients = []
    for hp in recent_patients_query:
        patient_user = db.query(User).filter(User.id == hp.patient_user_id).first()
        recent_patients.append({
            "id": hp.id,
            "patient_name": patient_user.name if patient_user else "Unknown",
            "patient_number": hp.patient_number,
            "status": hp.status.value if hasattr(hp.status, 'value') else hp.status,
            "created_at": hp.created_at.isoformat()
        })

    # 최근 진단 (5건)
    recent_diagnoses_query = db.query(UserDiagnosis).filter(
        UserDiagnosis.user_id.in_(patient_user_ids)
    ).order_by(UserDiagnosis.created_at.desc()).limit(5).all()

    recent_diagnoses = []
    for d in recent_diagnoses_query:
        patient_user = db.query(User).filter(User.id == d.user_id).first()
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

        # 담당 환자들의 이번 달 진단 수
        patient_user_ids = db.query(HospitalPatient.patient_user_id).filter(
            HospitalPatient.organization_id == org_id,
            HospitalPatient.assigned_doctor_id == doc.id
        ).subquery()

        month_diagnoses = db.query(UserDiagnosis).filter(
            UserDiagnosis.user_id.in_(patient_user_ids),
            UserDiagnosis.created_at >= datetime.combine(month_start, datetime.min.time())
        ).count()

        result.append(DoctorStats(
            doctor_id=doc.id,
            doctor_name=doc_user.name if doc_user else "Unknown",
            total_patients=patient_count,
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
    patient_user_ids = db.query(HospitalPatient.patient_user_id).filter(
        HospitalPatient.organization_id == org_id
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
    allergen_names = {
        "peanut": "땅콩", "milk": "우유", "egg": "계란",
        "wheat": "밀", "soy": "대두", "fish": "생선",
        "shellfish": "갑각류", "tree_nuts": "견과류", "sesame": "참깨",
        "dust_mite": "집먼지진드기", "pollen": "꽃가루",
        "mold": "곰팡이", "pet_dander": "반려동물",
        "cockroach": "바퀴벌레", "latex": "라텍스", "bee_venom": "벌독"
    }

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
            allergen_name=allergen_names.get(allergen, allergen),
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
        "is_approved": org.is_approved,
        "member_count": member_count,
        "role_counts": role_counts,
        "created_at": org.created_at.isoformat()
    }
