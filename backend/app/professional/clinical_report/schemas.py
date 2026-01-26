"""Clinical Report Schemas"""
from typing import List, Optional, Dict, Any
from datetime import date, datetime
from pydantic import BaseModel, Field


class CitationSchema(BaseModel):
    """논문 인용 정보"""
    paper_id: int
    pmid: Optional[str] = None
    title: str
    authors: Optional[str] = None
    journal: Optional[str] = None
    year: Optional[int] = None
    url: Optional[str] = None
    evidence_level: Optional[str] = None
    is_guideline: bool = False
    guideline_org: Optional[str] = None


class ClinicalStatementSchema(BaseModel):
    """임상 진술문"""
    id: int
    statement_en: str
    statement_kr: Optional[str] = None
    context: str
    evidence_level: Optional[str] = None
    recommendation_grade: Optional[str] = None
    grade_display: Optional[str] = None  # ⊕⊕⊕⊕
    evidence_label: Optional[str] = None  # "High", "Moderate", etc.
    source_location: Optional[str] = None
    citation: Optional[CitationSchema] = None


class AllergenDiagnosisSchema(BaseModel):
    """개별 알러젠 진단 정보"""
    allergen_code: str
    allergen_name_kr: str
    allergen_name_en: str
    grade: int
    grade_class: str  # Class 0-6
    grade_interpretation: str  # "Negative", "Low", "Moderate", "High", "Very High"
    clinical_significance: str  # "음성", "약양성", "양성", "강양성" 등


class CrossReactivitySchema(BaseModel):
    """교차반응 정보"""
    related_allergens: List[str]
    mechanism: Optional[str] = None
    statements: List[ClinicalStatementSchema] = []


class ClinicalAssessmentSchema(BaseModel):
    """임상 평가 (Assessment)"""
    primary_allergens: List[str]  # 주요 감작 항원
    risk_level: str  # "High", "Moderate", "Low"
    anaphylaxis_risk: bool
    cross_reactivity_concerns: List[CrossReactivitySchema] = []
    clinical_statements: List[ClinicalStatementSchema] = []


class ManagementPlanSchema(BaseModel):
    """관리 계획 (Plan)"""
    avoidance_items: List[str]
    hidden_allergens: List[str]
    substitutes: List[str]
    emergency_plan: bool
    follow_up_recommended: bool
    statements: List[ClinicalStatementSchema] = []


class PatientInfoSchema(BaseModel):
    """환자 정보"""
    patient_id: int
    name: str
    birth_date: Optional[date] = None
    age: Optional[int] = None


class DiagnosisInfoSchema(BaseModel):
    """진단 정보"""
    diagnosis_id: int
    kit_serial: Optional[str] = None
    diagnosis_date: date
    positive_count: int
    total_tested: int


class ClinicalReportResponse(BaseModel):
    """임상 보고서 응답 (의사 전용)

    병원 의사용 프로그램과 연동 가능한 API 형식
    """
    # 메타 정보
    report_generated_at: datetime
    report_version: str = "1.0"

    # 환자 정보
    patient: PatientInfoSchema

    # 진단 정보
    diagnosis: DiagnosisInfoSchema

    # 개별 알러젠 결과 (Objective)
    allergen_results: List[AllergenDiagnosisSchema]

    # 임상 평가 (Assessment)
    assessment: ClinicalAssessmentSchema

    # 관리 계획 (Plan)
    management: ManagementPlanSchema

    # 전체 인용 목록
    references: List[CitationSchema] = []

    # ICD-10 코드 (진단 코드)
    icd10_codes: List[str] = []


class ClinicalReportRequest(BaseModel):
    """임상 보고서 요청"""
    patient_id: Optional[int] = None
    kit_serial_number: Optional[str] = None
    diagnosis_id: Optional[int] = None

    class Config:
        json_schema_extra = {
            "example": {
                "patient_id": 1,
                "kit_serial_number": "SGT-2024-TEST1-0001"
            }
        }
