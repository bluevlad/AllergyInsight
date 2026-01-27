"""Professional Diagnosis Routes - 진단 입력/관리 API

의료진이 환자의 진단 결과를 입력하고 관리하는 API입니다.
"""
from typing import List, Dict, Any, Optional
from datetime import datetime, date
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from ...database.connection import get_db
from ...database.models import User, UserDiagnosis, DiagnosisKit
from ...database.organization_models import HospitalPatient
from ...core.auth import require_professional
from ...core.allergen import get_allergen_info, ALLERGEN_PRESCRIPTION_DB

router = APIRouter(prefix="/diagnosis", tags=["Professional - Diagnosis"])


# ============================================================================
# Schemas
# ============================================================================

class DiagnosisCreateRequest(BaseModel):
    """진단 결과 입력 요청"""
    patient_user_id: int = Field(..., description="환자 사용자 ID")
    results: Dict[str, int] = Field(..., description="알러젠별 등급 (0-6)")
    diagnosis_date: date = Field(default_factory=date.today, description="진단 날짜")
    doctor_note: Optional[str] = Field(None, description="의사 소견")
    kit_serial: Optional[str] = Field(None, description="진단 키트 시리얼 번호")

class DiagnosisUpdateRequest(BaseModel):
    """진단 결과 수정 요청"""
    results: Optional[Dict[str, int]] = None
    doctor_note: Optional[str] = None

class DiagnosisResponse(BaseModel):
    """진단 결과 응답"""
    id: int
    user_id: int
    results: Dict[str, int]
    diagnosis_date: datetime
    prescription: Optional[Dict[str, Any]] = None
    doctor_note: Optional[str] = None
    entered_by: Optional[int] = None
    entered_by_name: Optional[str] = None
    kit_serial: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# Helper Functions
# ============================================================================

def generate_prescription(results: Dict[str, int]) -> Dict[str, Any]:
    """진단 결과를 기반으로 처방 정보 생성"""
    prescription = {
        "allergens": [],
        "avoid_foods": [],
        "substitutes": [],
        "management_tips": [],
    }

    for allergen_code, grade in results.items():
        if grade == 0:
            continue

        allergen_info = get_allergen_info(allergen_code)
        if not allergen_info:
            continue

        prescription["allergens"].append({
            "code": allergen_code,
            "name": allergen_info.get("name_kr", allergen_code),
            "grade": grade,
            "category": allergen_info.get("category", "unknown"),
        })

        # 식품 알러젠인 경우
        if allergen_info.get("category") == "food":
            if allergen_info.get("avoid_foods"):
                prescription["avoid_foods"].extend([
                    {"allergen": allergen_code, "food": f}
                    for f in allergen_info["avoid_foods"][:5]
                ])
            if allergen_info.get("substitutes"):
                prescription["substitutes"].extend(allergen_info["substitutes"][:3])

        # 흡입 알러젠인 경우
        if allergen_info.get("category") == "inhalant":
            if allergen_info.get("management_tips"):
                prescription["management_tips"].extend(allergen_info["management_tips"][:3])

    return prescription


# ============================================================================
# Endpoints
# ============================================================================

@router.get("/allergen-info")
async def get_allergen_info_endpoint(
    user: User = Depends(require_professional)
):
    """알러젠 정보 목록 조회 (진단 입력용)"""
    return {
        "food": [
            {"code": "peanut", "name_kr": "땅콩", "name_en": "Peanut"},
            {"code": "milk", "name_kr": "우유", "name_en": "Milk"},
            {"code": "egg", "name_kr": "계란", "name_en": "Egg"},
            {"code": "wheat", "name_kr": "밀", "name_en": "Wheat"},
            {"code": "soy", "name_kr": "대두", "name_en": "Soy"},
            {"code": "fish", "name_kr": "생선", "name_en": "Fish"},
            {"code": "shellfish", "name_kr": "갑각류", "name_en": "Shellfish"},
            {"code": "tree_nuts", "name_kr": "견과류", "name_en": "Tree Nuts"},
            {"code": "sesame", "name_kr": "참깨", "name_en": "Sesame"},
        ],
        "inhalant": [
            {"code": "dust_mite", "name_kr": "집먼지진드기", "name_en": "Dust Mite"},
            {"code": "pollen", "name_kr": "꽃가루", "name_en": "Pollen"},
            {"code": "mold", "name_kr": "곰팡이", "name_en": "Mold"},
            {"code": "pet_dander", "name_kr": "반려동물", "name_en": "Pet Dander"},
            {"code": "cockroach", "name_kr": "바퀴벌레", "name_en": "Cockroach"},
            {"code": "latex", "name_kr": "라텍스", "name_en": "Latex"},
            {"code": "bee_venom", "name_kr": "벌독", "name_en": "Bee Venom"},
        ],
        "grades": {
            0: {"label": "음성", "color": "#4CAF50"},
            1: {"label": "약양성", "color": "#8BC34A"},
            2: {"label": "양성", "color": "#FFEB3B"},
            3: {"label": "양성", "color": "#FFC107"},
            4: {"label": "강양성", "color": "#FF9800"},
            5: {"label": "강양성", "color": "#F44336"},
            6: {"label": "최강양성", "color": "#B71C1C"},
        }
    }


@router.post("", response_model=DiagnosisResponse)
async def create_diagnosis(
    data: DiagnosisCreateRequest,
    user: User = Depends(require_professional),
    db: Session = Depends(get_db)
):
    """새로운 진단 결과 입력

    의료진이 환자의 알러지 검사 결과를 시스템에 입력합니다.
    """
    # 환자 사용자 확인
    patient = db.query(User).filter(User.id == data.patient_user_id).first()
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="환자를 찾을 수 없습니다"
        )

    # 결과 값 검증 (0-6)
    for allergen, grade in data.results.items():
        if not isinstance(grade, int) or grade < 0 or grade > 6:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"잘못된 등급 값: {allergen}={grade} (0-6 범위)"
            )

    # 처방 정보 자동 생성
    prescription = generate_prescription(data.results)

    # 키트 ID 조회 (있는 경우)
    kit_id = None
    if data.kit_serial:
        kit = db.query(DiagnosisKit).filter(
            DiagnosisKit.serial_number == data.kit_serial
        ).first()
        if kit:
            kit_id = kit.id

    # 진단 결과 저장
    diagnosis = UserDiagnosis(
        user_id=data.patient_user_id,
        results=data.results,
        diagnosis_date=datetime.combine(data.diagnosis_date, datetime.min.time()),
        prescription=prescription,
        kit_id=kit_id,
    )

    # 추가 필드 설정 (모델에 있는 경우)
    if hasattr(UserDiagnosis, 'doctor_note'):
        diagnosis.doctor_note = data.doctor_note
    if hasattr(UserDiagnosis, 'entered_by'):
        diagnosis.entered_by = user.id

    db.add(diagnosis)
    db.commit()
    db.refresh(diagnosis)

    return DiagnosisResponse(
        id=diagnosis.id,
        user_id=diagnosis.user_id,
        results=diagnosis.results,
        diagnosis_date=diagnosis.diagnosis_date,
        prescription=diagnosis.prescription,
        doctor_note=getattr(diagnosis, 'doctor_note', None),
        entered_by=getattr(diagnosis, 'entered_by', None),
        entered_by_name=user.name,
        kit_serial=data.kit_serial,
        created_at=diagnosis.created_at
    )


@router.get("/{diagnosis_id}", response_model=DiagnosisResponse)
async def get_diagnosis(
    diagnosis_id: int,
    user: User = Depends(require_professional),
    db: Session = Depends(get_db)
):
    """진단 결과 상세 조회"""
    diagnosis = db.query(UserDiagnosis).filter(
        UserDiagnosis.id == diagnosis_id
    ).first()

    if not diagnosis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="진단 결과를 찾을 수 없습니다"
        )

    # 입력자 이름 조회
    entered_by_name = None
    if hasattr(diagnosis, 'entered_by') and diagnosis.entered_by:
        entered_user = db.query(User).filter(User.id == diagnosis.entered_by).first()
        if entered_user:
            entered_by_name = entered_user.name

    # 키트 시리얼 조회
    kit_serial = None
    if diagnosis.kit_id:
        kit = db.query(DiagnosisKit).filter(DiagnosisKit.id == diagnosis.kit_id).first()
        if kit:
            kit_serial = kit.serial_number

    return DiagnosisResponse(
        id=diagnosis.id,
        user_id=diagnosis.user_id,
        results=diagnosis.results,
        diagnosis_date=diagnosis.diagnosis_date,
        prescription=diagnosis.prescription,
        doctor_note=getattr(diagnosis, 'doctor_note', None),
        entered_by=getattr(diagnosis, 'entered_by', None),
        entered_by_name=entered_by_name,
        kit_serial=kit_serial,
        created_at=diagnosis.created_at
    )


@router.put("/{diagnosis_id}", response_model=DiagnosisResponse)
async def update_diagnosis(
    diagnosis_id: int,
    data: DiagnosisUpdateRequest,
    user: User = Depends(require_professional),
    db: Session = Depends(get_db)
):
    """진단 결과 수정"""
    diagnosis = db.query(UserDiagnosis).filter(
        UserDiagnosis.id == diagnosis_id
    ).first()

    if not diagnosis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="진단 결과를 찾을 수 없습니다"
        )

    # 결과 수정
    if data.results is not None:
        for allergen, grade in data.results.items():
            if not isinstance(grade, int) or grade < 0 or grade > 6:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"잘못된 등급 값: {allergen}={grade} (0-6 범위)"
                )
        diagnosis.results = data.results
        diagnosis.prescription = generate_prescription(data.results)

    # 의사 소견 수정
    if data.doctor_note is not None and hasattr(diagnosis, 'doctor_note'):
        diagnosis.doctor_note = data.doctor_note

    db.commit()
    db.refresh(diagnosis)

    # 입력자 이름 조회
    entered_by_name = None
    if hasattr(diagnosis, 'entered_by') and diagnosis.entered_by:
        entered_user = db.query(User).filter(User.id == diagnosis.entered_by).first()
        if entered_user:
            entered_by_name = entered_user.name

    return DiagnosisResponse(
        id=diagnosis.id,
        user_id=diagnosis.user_id,
        results=diagnosis.results,
        diagnosis_date=diagnosis.diagnosis_date,
        prescription=diagnosis.prescription,
        doctor_note=getattr(diagnosis, 'doctor_note', None),
        entered_by=getattr(diagnosis, 'entered_by', None),
        entered_by_name=entered_by_name,
        kit_serial=None,
        created_at=diagnosis.created_at
    )


@router.get("/patient/{patient_id}", response_model=List[DiagnosisResponse])
async def get_patient_diagnoses(
    patient_id: str,
    limit: int = Query(10, ge=1, le=50),
    user: User = Depends(require_professional),
    db: Session = Depends(get_db)
):
    """특정 환자의 진단 이력 조회

    patient_id는 다음 형식을 지원합니다:
    - 정수 (user_id): "2"
    - 환자번호 (patient_number): "P-2026-0001"
    """
    # patient_id가 숫자인지 환자번호인지 판별
    actual_user_id = None

    if patient_id.isdigit():
        # 숫자인 경우 user_id로 직접 사용
        actual_user_id = int(patient_id)
    else:
        # 환자번호인 경우 HospitalPatient에서 user_id 조회
        hp = db.query(HospitalPatient).filter(
            HospitalPatient.patient_number == patient_id
        ).first()
        if hp:
            actual_user_id = hp.patient_user_id
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"환자번호 '{patient_id}'를 찾을 수 없습니다"
            )

    diagnoses = db.query(UserDiagnosis).filter(
        UserDiagnosis.user_id == actual_user_id
    ).order_by(UserDiagnosis.diagnosis_date.desc()).limit(limit).all()

    result = []
    for diag in diagnoses:
        entered_by_name = None
        if hasattr(diag, 'entered_by') and diag.entered_by:
            entered_user = db.query(User).filter(User.id == diag.entered_by).first()
            if entered_user:
                entered_by_name = entered_user.name

        kit_serial = None
        if diag.kit_id:
            kit = db.query(DiagnosisKit).filter(DiagnosisKit.id == diag.kit_id).first()
            if kit:
                kit_serial = kit.serial_number

        result.append(DiagnosisResponse(
            id=diag.id,
            user_id=diag.user_id,
            results=diag.results,
            diagnosis_date=diag.diagnosis_date,
            prescription=diag.prescription,
            doctor_note=getattr(diag, 'doctor_note', None),
            entered_by=getattr(diag, 'entered_by', None),
            entered_by_name=entered_by_name,
            kit_serial=kit_serial,
            created_at=diag.created_at
        ))

    return result
