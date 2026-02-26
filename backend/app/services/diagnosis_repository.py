"""진단 결과 저장소

진단 결과 및 처방 권고를 저장하고 관리합니다.
SQLAlchemy 기반 데이터베이스 저장소입니다.
"""
import uuid
from datetime import datetime
from typing import Optional
from dataclasses import dataclass, field

from sqlalchemy import Column, Integer, String, DateTime, JSON, ForeignKey, Index
from sqlalchemy.orm import Session

from ..database.connection import Base, SessionLocal


# =====================
# DB 모델
# =====================

class StoredDiagnosisModel(Base):
    """진단 결과 DB 모델"""
    __tablename__ = "stored_diagnoses"

    id = Column(Integer, primary_key=True, index=True)
    diagnosis_id = Column(String(36), unique=True, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    diagnosis_date = Column(DateTime, nullable=True)
    patient_info = Column(JSON, default=dict)
    diagnosis_results = Column(JSON, nullable=False)
    prescription_id = Column(String(36), nullable=True)

    __table_args__ = (
        Index('idx_stored_diagnoses_created', 'created_at'),
    )


class StoredPrescriptionModel(Base):
    """처방 권고 DB 모델"""
    __tablename__ = "stored_prescriptions"

    id = Column(Integer, primary_key=True, index=True)
    prescription_id = Column(String(36), unique=True, nullable=False, index=True)
    diagnosis_id = Column(String(36), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    prescription_data = Column(JSON, nullable=False)


# =====================
# 데이터 클래스 (API 응답용 - 기존 호환)
# =====================

@dataclass
class StoredDiagnosis:
    """저장된 진단 정보"""
    diagnosis_id: str
    created_at: datetime
    diagnosis_date: Optional[datetime]
    patient_info: dict
    diagnosis_results: list[dict]
    prescription_id: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "diagnosis_id": self.diagnosis_id,
            "created_at": self.created_at.isoformat(),
            "diagnosis_date": self.diagnosis_date.isoformat() if self.diagnosis_date else None,
            "patient_info": self.patient_info,
            "diagnosis_results": self.diagnosis_results,
            "prescription_id": self.prescription_id,
        }


@dataclass
class StoredPrescription:
    """저장된 처방 정보"""
    prescription_id: str
    diagnosis_id: str
    created_at: datetime
    prescription_data: dict

    def to_dict(self) -> dict:
        return {
            "prescription_id": self.prescription_id,
            "diagnosis_id": self.diagnosis_id,
            "created_at": self.created_at.isoformat(),
            "prescription_data": self.prescription_data,
        }


def _model_to_diagnosis(m: StoredDiagnosisModel) -> StoredDiagnosis:
    return StoredDiagnosis(
        diagnosis_id=m.diagnosis_id,
        created_at=m.created_at,
        diagnosis_date=m.diagnosis_date,
        patient_info=m.patient_info or {},
        diagnosis_results=m.diagnosis_results or [],
        prescription_id=m.prescription_id,
    )


def _model_to_prescription(m: StoredPrescriptionModel) -> StoredPrescription:
    return StoredPrescription(
        prescription_id=m.prescription_id,
        diagnosis_id=m.diagnosis_id,
        created_at=m.created_at,
        prescription_data=m.prescription_data or {},
    )


class DiagnosisRepository:
    """
    진단 결과 저장소

    SQLAlchemy 기반 데이터베이스 저장소입니다.
    """

    # =====================
    # 진단 결과 관리
    # =====================

    def save_diagnosis(
        self,
        diagnosis_results: list[dict],
        diagnosis_date: Optional[datetime] = None,
        patient_info: Optional[dict] = None,
    ) -> StoredDiagnosis:
        diagnosis_id = str(uuid.uuid4())
        db = SessionLocal()
        try:
            model = StoredDiagnosisModel(
                diagnosis_id=diagnosis_id,
                diagnosis_date=diagnosis_date,
                patient_info=patient_info or {},
                diagnosis_results=diagnosis_results,
            )
            db.add(model)
            db.commit()
            db.refresh(model)
            return _model_to_diagnosis(model)
        finally:
            db.close()

    def get_diagnosis(self, diagnosis_id: str) -> Optional[StoredDiagnosis]:
        db = SessionLocal()
        try:
            model = db.query(StoredDiagnosisModel).filter(
                StoredDiagnosisModel.diagnosis_id == diagnosis_id
            ).first()
            return _model_to_diagnosis(model) if model else None
        finally:
            db.close()

    def update_diagnosis(
        self,
        diagnosis_id: str,
        diagnosis_results: Optional[list[dict]] = None,
        diagnosis_date: Optional[datetime] = None,
        patient_info: Optional[dict] = None,
    ) -> Optional[StoredDiagnosis]:
        db = SessionLocal()
        try:
            model = db.query(StoredDiagnosisModel).filter(
                StoredDiagnosisModel.diagnosis_id == diagnosis_id
            ).first()
            if not model:
                return None
            if diagnosis_results is not None:
                model.diagnosis_results = diagnosis_results
            if diagnosis_date is not None:
                model.diagnosis_date = diagnosis_date
            if patient_info is not None:
                model.patient_info = patient_info
            db.commit()
            db.refresh(model)
            return _model_to_diagnosis(model)
        finally:
            db.close()

    def delete_diagnosis(self, diagnosis_id: str) -> bool:
        db = SessionLocal()
        try:
            model = db.query(StoredDiagnosisModel).filter(
                StoredDiagnosisModel.diagnosis_id == diagnosis_id
            ).first()
            if not model:
                return False
            # 연결된 처방도 삭제
            if model.prescription_id:
                db.query(StoredPrescriptionModel).filter(
                    StoredPrescriptionModel.prescription_id == model.prescription_id
                ).delete()
            db.delete(model)
            db.commit()
            return True
        finally:
            db.close()

    def list_diagnoses(
        self,
        limit: int = 50,
        offset: int = 0,
    ) -> list[StoredDiagnosis]:
        db = SessionLocal()
        try:
            models = db.query(StoredDiagnosisModel).order_by(
                StoredDiagnosisModel.created_at.desc()
            ).offset(offset).limit(limit).all()
            return [_model_to_diagnosis(m) for m in models]
        finally:
            db.close()

    # =====================
    # 처방 권고 관리
    # =====================

    def save_prescription(
        self,
        diagnosis_id: str,
        prescription_data: dict,
    ) -> Optional[StoredPrescription]:
        db = SessionLocal()
        try:
            diag = db.query(StoredDiagnosisModel).filter(
                StoredDiagnosisModel.diagnosis_id == diagnosis_id
            ).first()
            if not diag:
                return None

            prescription_id = prescription_data.get("prescription_id", str(uuid.uuid4()))

            model = StoredPrescriptionModel(
                prescription_id=prescription_id,
                diagnosis_id=diagnosis_id,
                prescription_data=prescription_data,
            )
            db.add(model)

            # 진단에 처방 ID 연결
            diag.prescription_id = prescription_id
            db.commit()
            db.refresh(model)
            return _model_to_prescription(model)
        finally:
            db.close()

    def get_prescription(self, prescription_id: str) -> Optional[StoredPrescription]:
        db = SessionLocal()
        try:
            model = db.query(StoredPrescriptionModel).filter(
                StoredPrescriptionModel.prescription_id == prescription_id
            ).first()
            return _model_to_prescription(model) if model else None
        finally:
            db.close()

    def get_prescription_by_diagnosis(self, diagnosis_id: str) -> Optional[StoredPrescription]:
        db = SessionLocal()
        try:
            diag = db.query(StoredDiagnosisModel).filter(
                StoredDiagnosisModel.diagnosis_id == diagnosis_id
            ).first()
            if not diag or not diag.prescription_id:
                return None
            model = db.query(StoredPrescriptionModel).filter(
                StoredPrescriptionModel.prescription_id == diag.prescription_id
            ).first()
            return _model_to_prescription(model) if model else None
        finally:
            db.close()

    def delete_prescription(self, prescription_id: str) -> bool:
        db = SessionLocal()
        try:
            deleted = db.query(StoredPrescriptionModel).filter(
                StoredPrescriptionModel.prescription_id == prescription_id
            ).delete()
            db.commit()
            return deleted > 0
        finally:
            db.close()

    def list_prescriptions(
        self,
        limit: int = 50,
        offset: int = 0,
    ) -> list[StoredPrescription]:
        db = SessionLocal()
        try:
            models = db.query(StoredPrescriptionModel).order_by(
                StoredPrescriptionModel.created_at.desc()
            ).offset(offset).limit(limit).all()
            return [_model_to_prescription(m) for m in models]
        finally:
            db.close()

    # =====================
    # 통계
    # =====================

    def get_stats(self) -> dict:
        db = SessionLocal()
        try:
            total_diag = db.query(StoredDiagnosisModel).count()
            total_presc = db.query(StoredPrescriptionModel).count()
            with_presc = db.query(StoredDiagnosisModel).filter(
                StoredDiagnosisModel.prescription_id.isnot(None)
            ).count()
            return {
                "total_diagnoses": total_diag,
                "total_prescriptions": total_presc,
                "diagnoses_with_prescription": with_presc,
            }
        finally:
            db.close()

    def clear_all(self):
        """모든 데이터 삭제"""
        db = SessionLocal()
        try:
            db.query(StoredPrescriptionModel).delete()
            db.query(StoredDiagnosisModel).delete()
            db.commit()
        finally:
            db.close()
