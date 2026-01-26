"""Consumer Kit Routes - 키트 등록 API

알러지 검사 키트 등록 기능을 제공합니다.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from datetime import datetime

from ...database.connection import get_db
from ...database.models import User, UserDiagnosis, DiagnosisKit
from ...core.auth import require_consumer

router = APIRouter(prefix="/kit", tags=["Consumer - Kit"])


# ============================================================================
# Schemas
# ============================================================================

class KitRegisterRequest(BaseModel):
    """키트 등록 요청"""
    serial_number: str = Field(..., min_length=8, max_length=20)
    pin: str = Field(..., min_length=4, max_length=6)


class KitRegisterResponse(BaseModel):
    """키트 등록 응답"""
    success: bool
    message: str
    diagnosis_id: int = None
    diagnosis_date: datetime = None


# ============================================================================
# Endpoints
# ============================================================================

@router.post("/register", response_model=KitRegisterResponse)
async def register_kit(
    request: KitRegisterRequest,
    user: User = Depends(require_consumer),
    db: Session = Depends(get_db)
):
    """알러지 검사 키트 등록

    시리얼 번호와 PIN으로 키트를 등록하고 진단 결과를 연결합니다.
    """
    # 키트 조회
    kit = db.query(DiagnosisKit).filter(
        DiagnosisKit.serial_number == request.serial_number
    ).first()

    if not kit:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="키트 시리얼 번호를 찾을 수 없습니다"
        )

    # PIN 검증
    if kit.pin != request.pin:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="PIN이 일치하지 않습니다"
        )

    # 이미 등록된 키트인지 확인
    if kit.is_registered:
        # 이미 현재 사용자가 등록한 키트인 경우
        existing_diagnosis = db.query(UserDiagnosis).filter(
            UserDiagnosis.kit_id == kit.id,
            UserDiagnosis.user_id == user.id
        ).first()

        if existing_diagnosis:
            return KitRegisterResponse(
                success=True,
                message="이미 등록된 키트입니다",
                diagnosis_id=existing_diagnosis.id,
                diagnosis_date=existing_diagnosis.diagnosis_date
            )

        # 다른 사용자가 등록한 키트인 경우
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="이미 다른 사용자에게 등록된 키트입니다"
        )

    # 키트에 진단 결과가 있는지 확인
    if not kit.results:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="아직 검사 결과가 입력되지 않은 키트입니다"
        )

    # 진단 결과 생성
    diagnosis = UserDiagnosis(
        user_id=user.id,
        kit_id=kit.id,
        results=kit.results,
        diagnosis_date=kit.test_date or datetime.utcnow(),
        prescription=None,  # 별도 처리 필요
    )
    db.add(diagnosis)

    # 키트 상태 업데이트
    kit.is_registered = True
    kit.registered_user_id = user.id
    kit.registered_at = datetime.utcnow()

    db.commit()
    db.refresh(diagnosis)

    return KitRegisterResponse(
        success=True,
        message="키트가 성공적으로 등록되었습니다",
        diagnosis_id=diagnosis.id,
        diagnosis_date=diagnosis.diagnosis_date
    )


@router.get("/status/{serial_number}")
async def check_kit_status(
    serial_number: str,
    user: User = Depends(require_consumer),
    db: Session = Depends(get_db)
):
    """키트 상태 확인"""
    kit = db.query(DiagnosisKit).filter(
        DiagnosisKit.serial_number == serial_number
    ).first()

    if not kit:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="키트를 찾을 수 없습니다"
        )

    # 현재 사용자의 키트인지 확인
    if kit.is_registered and kit.registered_user_id != user.id:
        return {
            "serial_number": serial_number,
            "status": "registered_to_other",
            "message": "다른 사용자에게 등록된 키트입니다",
        }

    return {
        "serial_number": serial_number,
        "status": "registered" if kit.is_registered else ("ready" if kit.results else "pending"),
        "is_registered": kit.is_registered,
        "has_results": kit.results is not None,
        "test_date": kit.test_date,
        "message": (
            "이미 등록된 키트입니다" if kit.is_registered
            else ("등록 가능합니다" if kit.results else "검사 결과 대기 중입니다")
        ),
    }


@router.get("/my-kits")
async def get_my_kits(
    user: User = Depends(require_consumer),
    db: Session = Depends(get_db)
):
    """내 키트 목록 조회"""
    kits = db.query(DiagnosisKit).filter(
        DiagnosisKit.registered_user_id == user.id
    ).order_by(DiagnosisKit.registered_at.desc()).all()

    result = []
    for kit in kits:
        diagnosis = db.query(UserDiagnosis).filter(
            UserDiagnosis.kit_id == kit.id,
            UserDiagnosis.user_id == user.id
        ).first()

        result.append({
            "serial_number": kit.serial_number,
            "test_date": kit.test_date,
            "registered_at": kit.registered_at,
            "diagnosis_id": diagnosis.id if diagnosis else None,
            "diagnosis_date": diagnosis.diagnosis_date if diagnosis else None,
        })

    return {"items": result, "total": len(result)}
