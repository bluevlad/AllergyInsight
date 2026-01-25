# Hospital module - Phase 2
from .routes import router
from .schemas import (
    HospitalPatientCreate,
    HospitalPatientCreateNew,
    HospitalPatientUpdate,
    HospitalPatientResponse,
    HospitalPatientListResponse,
    PatientConsentRequest,
    PatientConsentResponse,
    PatientDiagnosisResponse,
    PatientDiagnosisListResponse,
    PatientDiagnosisCreate,
    HospitalDashboardStats,
    DoctorPatientStats,
)

__all__ = [
    "router",
    "HospitalPatientCreate",
    "HospitalPatientCreateNew",
    "HospitalPatientUpdate",
    "HospitalPatientResponse",
    "HospitalPatientListResponse",
    "PatientConsentRequest",
    "PatientConsentResponse",
    "PatientDiagnosisResponse",
    "PatientDiagnosisListResponse",
    "PatientDiagnosisCreate",
    "HospitalDashboardStats",
    "DoctorPatientStats",
]
