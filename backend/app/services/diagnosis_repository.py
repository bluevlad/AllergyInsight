"""진단 결과 저장소

진단 결과 및 처방 권고를 저장하고 관리합니다.
현재는 메모리 기반으로 구현되어 있으며,
추후 데이터베이스 연동이 필요합니다.
"""
import uuid
from datetime import datetime
from typing import Optional
from dataclasses import dataclass, field


@dataclass
class StoredDiagnosis:
    """저장된 진단 정보"""
    diagnosis_id: str
    created_at: datetime
    diagnosis_date: Optional[datetime]
    patient_info: dict  # 향후 확장용 (익명화된 정보)
    diagnosis_results: list[dict]  # [{"allergen": "peanut", "grade": 5}, ...]
    prescription_id: Optional[str] = None  # 연결된 처방 ID

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
    prescription_data: dict  # AllergyPrescription.to_dict()

    def to_dict(self) -> dict:
        return {
            "prescription_id": self.prescription_id,
            "diagnosis_id": self.diagnosis_id,
            "created_at": self.created_at.isoformat(),
            "prescription_data": self.prescription_data,
        }


class DiagnosisRepository:
    """
    진단 결과 저장소

    메모리 기반 저장소로, 서버 재시작 시 데이터가 초기화됩니다.
    """

    def __init__(self):
        self._diagnoses: dict[str, StoredDiagnosis] = {}
        self._prescriptions: dict[str, StoredPrescription] = {}

    # =====================
    # 진단 결과 관리
    # =====================

    def save_diagnosis(
        self,
        diagnosis_results: list[dict],
        diagnosis_date: Optional[datetime] = None,
        patient_info: Optional[dict] = None,
    ) -> StoredDiagnosis:
        """
        진단 결과 저장

        Args:
            diagnosis_results: [{"allergen": "peanut", "grade": 5}, ...]
            diagnosis_date: 검사 날짜
            patient_info: 환자 정보 (선택)

        Returns:
            StoredDiagnosis: 저장된 진단 정보
        """
        diagnosis_id = str(uuid.uuid4())

        diagnosis = StoredDiagnosis(
            diagnosis_id=diagnosis_id,
            created_at=datetime.now(),
            diagnosis_date=diagnosis_date,
            patient_info=patient_info or {},
            diagnosis_results=diagnosis_results,
        )

        self._diagnoses[diagnosis_id] = diagnosis
        return diagnosis

    def get_diagnosis(self, diagnosis_id: str) -> Optional[StoredDiagnosis]:
        """진단 결과 조회"""
        return self._diagnoses.get(diagnosis_id)

    def update_diagnosis(
        self,
        diagnosis_id: str,
        diagnosis_results: Optional[list[dict]] = None,
        diagnosis_date: Optional[datetime] = None,
        patient_info: Optional[dict] = None,
    ) -> Optional[StoredDiagnosis]:
        """진단 결과 수정"""
        diagnosis = self._diagnoses.get(diagnosis_id)
        if not diagnosis:
            return None

        if diagnosis_results is not None:
            diagnosis.diagnosis_results = diagnosis_results
        if diagnosis_date is not None:
            diagnosis.diagnosis_date = diagnosis_date
        if patient_info is not None:
            diagnosis.patient_info = patient_info

        return diagnosis

    def delete_diagnosis(self, diagnosis_id: str) -> bool:
        """진단 결과 삭제"""
        if diagnosis_id in self._diagnoses:
            # 연결된 처방도 삭제
            diagnosis = self._diagnoses[diagnosis_id]
            if diagnosis.prescription_id:
                self.delete_prescription(diagnosis.prescription_id)
            del self._diagnoses[diagnosis_id]
            return True
        return False

    def list_diagnoses(
        self,
        limit: int = 50,
        offset: int = 0,
    ) -> list[StoredDiagnosis]:
        """진단 결과 목록 조회"""
        all_diagnoses = sorted(
            self._diagnoses.values(),
            key=lambda d: d.created_at,
            reverse=True,
        )
        return all_diagnoses[offset:offset + limit]

    # =====================
    # 처방 권고 관리
    # =====================

    def save_prescription(
        self,
        diagnosis_id: str,
        prescription_data: dict,
    ) -> Optional[StoredPrescription]:
        """
        처방 권고 저장

        Args:
            diagnosis_id: 연결된 진단 ID
            prescription_data: AllergyPrescription.to_dict() 결과

        Returns:
            StoredPrescription: 저장된 처방 정보
        """
        diagnosis = self._diagnoses.get(diagnosis_id)
        if not diagnosis:
            return None

        prescription_id = prescription_data.get("prescription_id", str(uuid.uuid4()))

        prescription = StoredPrescription(
            prescription_id=prescription_id,
            diagnosis_id=diagnosis_id,
            created_at=datetime.now(),
            prescription_data=prescription_data,
        )

        self._prescriptions[prescription_id] = prescription

        # 진단에 처방 ID 연결
        diagnosis.prescription_id = prescription_id

        return prescription

    def get_prescription(self, prescription_id: str) -> Optional[StoredPrescription]:
        """처방 권고 조회"""
        return self._prescriptions.get(prescription_id)

    def get_prescription_by_diagnosis(self, diagnosis_id: str) -> Optional[StoredPrescription]:
        """진단 ID로 처방 권고 조회"""
        diagnosis = self._diagnoses.get(diagnosis_id)
        if diagnosis and diagnosis.prescription_id:
            return self._prescriptions.get(diagnosis.prescription_id)
        return None

    def delete_prescription(self, prescription_id: str) -> bool:
        """처방 권고 삭제"""
        if prescription_id in self._prescriptions:
            del self._prescriptions[prescription_id]
            return True
        return False

    def list_prescriptions(
        self,
        limit: int = 50,
        offset: int = 0,
    ) -> list[StoredPrescription]:
        """처방 권고 목록 조회"""
        all_prescriptions = sorted(
            self._prescriptions.values(),
            key=lambda p: p.created_at,
            reverse=True,
        )
        return all_prescriptions[offset:offset + limit]

    # =====================
    # 통계
    # =====================

    def get_stats(self) -> dict:
        """저장소 통계"""
        return {
            "total_diagnoses": len(self._diagnoses),
            "total_prescriptions": len(self._prescriptions),
            "diagnoses_with_prescription": sum(
                1 for d in self._diagnoses.values() if d.prescription_id
            ),
        }

    def clear_all(self):
        """모든 데이터 삭제"""
        self._diagnoses.clear()
        self._prescriptions.clear()
