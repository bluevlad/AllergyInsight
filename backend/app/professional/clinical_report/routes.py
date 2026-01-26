"""Clinical Report API Routes - 의사 전용 임상 보고서 API

병원 의사용 프로그램과 연동 가능하도록 설계된 API
- patient_id 또는 kit_serial_number로 조회 가능
- GRADE 기반 근거 수준 표시
- 논문 인용 포함
"""
from datetime import datetime, date
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ...database import get_db, User, DiagnosisKit, UserDiagnosis, Paper
from ...database.clinical_models import ClinicalStatement
from ...core.auth.dependencies import require_professional
from ...data.allergen_prescription_db import get_allergen_info
from .schemas import (
    ClinicalReportResponse,
    ClinicalReportRequest,
    PatientInfoSchema,
    DiagnosisInfoSchema,
    AllergenDiagnosisSchema,
    ClinicalAssessmentSchema,
    ManagementPlanSchema,
    CrossReactivitySchema,
    ClinicalStatementSchema,
    CitationSchema,
)

router = APIRouter(prefix="/clinical-report", tags=["Clinical Report"])


def get_grade_interpretation(grade: int) -> tuple[str, str]:
    """등급에 따른 해석 반환 (class, interpretation)"""
    interpretations = {
        0: ("Class 0", "Negative"),
        1: ("Class 1", "Low"),
        2: ("Class 2", "Moderate"),
        3: ("Class 3", "High"),
        4: ("Class 4", "Very High"),
        5: ("Class 5", "Very High"),
        6: ("Class 6", "Very High"),
    }
    return interpretations.get(grade, ("Unknown", "Unknown"))


def get_clinical_significance(grade: int) -> str:
    """등급에 따른 임상적 의의"""
    if grade == 0:
        return "음성 - 감작 미확인"
    elif grade == 1:
        return "약양성 - 감작 가능성 있음, 임상 증상과 대조 필요"
    elif grade == 2:
        return "양성 - 감작 확인, 증상 유발 가능"
    elif grade == 3:
        return "중등도 양성 - 감작 확인, 회피 권장"
    elif grade >= 4:
        return "강양성 - 고위험, 엄격한 회피 필수"
    return "판정 불가"


def build_citation(paper: Paper) -> CitationSchema:
    """Paper 객체에서 Citation 스키마 생성"""
    return CitationSchema(
        paper_id=paper.id,
        pmid=paper.pmid,
        title=paper.title,
        authors=paper.authors,
        journal=paper.journal,
        year=paper.year,
        url=paper.url,
        evidence_level=paper.evidence_level,
        is_guideline=paper.is_guideline or False,
        guideline_org=paper.guideline_org,
    )


def build_clinical_statement(stmt: ClinicalStatement) -> ClinicalStatementSchema:
    """ClinicalStatement 객체에서 스키마 생성"""
    citation = None
    if stmt.paper:
        citation = build_citation(stmt.paper)

    return ClinicalStatementSchema(
        id=stmt.id,
        statement_en=stmt.statement_en,
        statement_kr=stmt.statement_kr,
        context=stmt.context,
        evidence_level=stmt.evidence_level,
        recommendation_grade=stmt.recommendation_grade,
        grade_display=stmt.get_grade_display(),
        evidence_label=stmt.get_evidence_label(),
        source_location=stmt.source_location,
        citation=citation,
    )


def get_icd10_codes(positive_allergens: List[str]) -> List[str]:
    """양성 알러젠에 따른 ICD-10 코드 반환"""
    # ICD-10-CM 코드 매핑
    codes = []

    # 식품 알러지 기본 코드
    food_allergens = ["peanut", "milk", "egg", "wheat", "soy", "fish", "shrimp", "crab", "buckwheat"]
    inhalant_allergens = ["dust_mite", "cat", "dog", "cockroach", "mugwort", "ragweed", "mold"]

    has_food = any(a in food_allergens for a in positive_allergens)
    has_inhalant = any(a in inhalant_allergens for a in positive_allergens)

    if has_food:
        codes.append("T78.1")  # Other adverse food reactions, not elsewhere classified

    if "peanut" in positive_allergens:
        codes.append("Z91.010")  # Allergy status to peanuts

    if "milk" in positive_allergens:
        codes.append("Z91.011")  # Allergy status to milk products

    if "egg" in positive_allergens:
        codes.append("Z91.012")  # Allergy status to eggs

    if "shrimp" in positive_allergens or "crab" in positive_allergens:
        codes.append("Z91.013")  # Allergy status to seafood

    if has_inhalant:
        codes.append("J30.89")  # Other allergic rhinitis

    if "dust_mite" in positive_allergens:
        codes.append("J30.81")  # Allergic rhinitis due to animal (cat) (dog) hair and dander

    return codes


@router.get(
    "",
    response_model=ClinicalReportResponse,
    summary="임상 보고서 조회 (의사 전용)",
    description="""
환자 정보 또는 키트 시리얼 번호로 임상 보고서를 조회합니다.

## 조회 방법
- `patient_id`: 환자 ID로 최신 진단 결과 조회
- `kit_serial_number`: 진단 키트 시리얼 번호로 조회
- `diagnosis_id`: 특정 진단 ID로 조회

최소 하나의 파라미터가 필요합니다.

## 응답 구조
- SOAP Note 형식 (Subjective, Objective, Assessment, Plan)
- GRADE 기반 근거 수준 표시
- 논문 인용 포함
- ICD-10 진단 코드 포함
    """,
)
async def get_clinical_report(
    patient_id: Optional[int] = Query(None, description="환자 ID"),
    kit_serial_number: Optional[str] = Query(None, description="진단 키트 시리얼 번호"),
    diagnosis_id: Optional[int] = Query(None, description="특정 진단 ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_professional),
) -> ClinicalReportResponse:
    """임상 보고서 생성"""

    # 최소 하나의 파라미터 필요
    if not any([patient_id, kit_serial_number, diagnosis_id]):
        raise HTTPException(
            status_code=400,
            detail="patient_id, kit_serial_number, 또는 diagnosis_id 중 하나가 필요합니다.",
        )

    # 진단 데이터 조회
    diagnosis: Optional[UserDiagnosis] = None
    user: Optional[User] = None
    kit: Optional[DiagnosisKit] = None

    if diagnosis_id:
        diagnosis = db.query(UserDiagnosis).filter(UserDiagnosis.id == diagnosis_id).first()
        if diagnosis:
            user = diagnosis.user
            kit = diagnosis.kit
    elif kit_serial_number:
        kit = db.query(DiagnosisKit).filter(DiagnosisKit.serial_number == kit_serial_number).first()
        if kit and kit.is_registered:
            user = kit.registered_user
            diagnosis = (
                db.query(UserDiagnosis)
                .filter(UserDiagnosis.kit_id == kit.id)
                .order_by(UserDiagnosis.created_at.desc())
                .first()
            )
    elif patient_id:
        user = db.query(User).filter(User.id == patient_id).first()
        if user:
            diagnosis = (
                db.query(UserDiagnosis)
                .filter(UserDiagnosis.user_id == patient_id)
                .order_by(UserDiagnosis.diagnosis_date.desc())
                .first()
            )
            if diagnosis:
                kit = diagnosis.kit

    # 데이터 검증
    if not user:
        raise HTTPException(status_code=404, detail="환자를 찾을 수 없습니다.")
    if not diagnosis:
        raise HTTPException(status_code=404, detail="진단 결과를 찾을 수 없습니다.")

    # 결과 데이터 파싱
    results = diagnosis.results or {}

    # 알러젠 결과 빌드
    allergen_results: List[AllergenDiagnosisSchema] = []
    positive_allergens: List[str] = []

    for allergen_code, grade in results.items():
        grade_int = int(grade) if grade else 0
        allergen_info = get_allergen_info(allergen_code)

        if allergen_info:
            name_kr = allergen_info.get("name_kr", allergen_code)
            name_en = allergen_info.get("name_en", allergen_code)
        else:
            name_kr = allergen_code
            name_en = allergen_code

        grade_class, interpretation = get_grade_interpretation(grade_int)

        allergen_results.append(
            AllergenDiagnosisSchema(
                allergen_code=allergen_code,
                allergen_name_kr=name_kr,
                allergen_name_en=name_en,
                grade=grade_int,
                grade_class=grade_class,
                grade_interpretation=interpretation,
                clinical_significance=get_clinical_significance(grade_int),
            )
        )

        if grade_int > 0:
            positive_allergens.append(allergen_code)

    # 양성 알러젠 기준 임상 진술문 조회
    allergen_statements = (
        db.query(ClinicalStatement)
        .filter(
            ClinicalStatement.is_active == True,
            ClinicalStatement.allergen_code.in_(positive_allergens + ["general"]),
        )
        .all()
    )

    # 컨텍스트별 진술문 분류
    assessment_statements = [
        build_clinical_statement(s)
        for s in allergen_statements
        if s.context in ["diagnosis", "pathophysiology", "cross_reactivity"]
    ]
    management_statements = [
        build_clinical_statement(s)
        for s in allergen_statements
        if s.context in ["avoidance", "treatment"]
    ]

    # 교차반응 정보 빌드
    cross_reactivities: List[CrossReactivitySchema] = []
    cross_statements = [s for s in allergen_statements if s.context == "cross_reactivity"]

    # 갑각류 교차반응
    if "shrimp" in positive_allergens or "crab" in positive_allergens:
        cross_reactivities.append(
            CrossReactivitySchema(
                related_allergens=["새우", "게", "랍스터", "집먼지진드기"],
                mechanism="트로포미오신 공유 (80% 서열 상동성)",
                statements=[
                    build_clinical_statement(s)
                    for s in cross_statements
                    if s.allergen_code in ["shrimp", "crab", "dust_mite"]
                ],
            )
        )

    # 땅콩-견과류 교차반응
    if "peanut" in positive_allergens:
        cross_reactivities.append(
            CrossReactivitySchema(
                related_allergens=["땅콩", "호두", "아몬드", "캐슈넛"],
                mechanism="저장 단백질 교차반응 (30-40% 임상적 연관)",
                statements=[
                    build_clinical_statement(s)
                    for s in cross_statements
                    if s.allergen_code == "peanut"
                ],
            )
        )

    # 위험도 평가
    max_grade = max((r.grade for r in allergen_results), default=0)
    high_risk_allergens = ["peanut", "shrimp", "crab", "fish", "buckwheat"]
    has_high_risk = any(a in positive_allergens for a in high_risk_allergens)

    if max_grade >= 4 or has_high_risk:
        risk_level = "High"
        anaphylaxis_risk = True
    elif max_grade >= 3:
        risk_level = "Moderate"
        anaphylaxis_risk = len([a for a in positive_allergens if a in high_risk_allergens]) > 0
    else:
        risk_level = "Low"
        anaphylaxis_risk = False

    # 관리 계획 빌드
    avoidance_items: List[str] = []
    hidden_allergens: List[str] = []
    substitutes: List[str] = []

    for allergen_code in positive_allergens:
        allergen_info = get_allergen_info(allergen_code)
        if allergen_info:
            avoidance_items.extend(allergen_info.get("avoid_foods", [])[:3])
            hidden_allergens.extend(allergen_info.get("hidden_sources", [])[:3])
            for sub in allergen_info.get("substitutes", [])[:2]:
                if isinstance(sub, dict):
                    substitutes.extend(sub.get("alternatives", [])[:2])

    # 중복 제거
    avoidance_items = list(dict.fromkeys(avoidance_items))[:10]
    hidden_allergens = list(dict.fromkeys(hidden_allergens))[:10]
    substitutes = list(dict.fromkeys(substitutes))[:10]

    # 인용 목록 빌드 (중복 제거)
    all_papers = set()
    for stmt in allergen_statements:
        if stmt.paper:
            all_papers.add(stmt.paper)

    references = [build_citation(p) for p in all_papers]

    # 환자 나이 계산
    age = None
    if user.birth_date:
        today = date.today()
        age = today.year - user.birth_date.year
        if today.month < user.birth_date.month or (
            today.month == user.birth_date.month and today.day < user.birth_date.day
        ):
            age -= 1

    # 응답 생성
    return ClinicalReportResponse(
        report_generated_at=datetime.utcnow(),
        report_version="1.0",
        patient=PatientInfoSchema(
            patient_id=user.id,
            name=user.name,
            birth_date=user.birth_date,
            age=age,
        ),
        diagnosis=DiagnosisInfoSchema(
            diagnosis_id=diagnosis.id,
            kit_serial=kit.serial_number if kit else None,
            diagnosis_date=diagnosis.diagnosis_date,
            positive_count=len(positive_allergens),
            total_tested=len(results),
        ),
        allergen_results=sorted(allergen_results, key=lambda x: -x.grade),
        assessment=ClinicalAssessmentSchema(
            primary_allergens=positive_allergens,
            risk_level=risk_level,
            anaphylaxis_risk=anaphylaxis_risk,
            cross_reactivity_concerns=cross_reactivities,
            clinical_statements=assessment_statements,
        ),
        management=ManagementPlanSchema(
            avoidance_items=avoidance_items,
            hidden_allergens=hidden_allergens,
            substitutes=substitutes,
            emergency_plan=anaphylaxis_risk,
            follow_up_recommended=max_grade >= 3,
            statements=management_statements,
        ),
        references=references,
        icd10_codes=get_icd10_codes(positive_allergens),
    )


@router.get(
    "/statements",
    response_model=List[ClinicalStatementSchema],
    summary="임상 진술문 조회",
    description="알러젠 코드 또는 컨텍스트로 임상 진술문을 조회합니다.",
)
async def get_clinical_statements(
    allergen_code: Optional[str] = Query(None, description="알러젠 코드 (예: shrimp, peanut)"),
    context: Optional[str] = Query(
        None,
        description="컨텍스트 (cross_reactivity, avoidance, treatment, diagnosis, pathophysiology)",
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_professional),
) -> List[ClinicalStatementSchema]:
    """임상 진술문 조회"""
    query = db.query(ClinicalStatement).filter(ClinicalStatement.is_active == True)

    if allergen_code:
        query = query.filter(ClinicalStatement.allergen_code == allergen_code)

    if context:
        query = query.filter(ClinicalStatement.context == context)

    statements = query.all()

    return [build_clinical_statement(stmt) for stmt in statements]


@router.get(
    "/guidelines",
    response_model=List[CitationSchema],
    summary="가이드라인 목록 조회",
    description="EAACI, AAAAI, WAO 등 공인 가이드라인 목록을 조회합니다.",
)
async def get_guidelines(
    organization: Optional[str] = Query(None, description="기관 코드 (EAACI, AAAAI, WAO)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_professional),
) -> List[CitationSchema]:
    """가이드라인 목록 조회"""
    query = db.query(Paper).filter(Paper.is_guideline == True)

    if organization:
        query = query.filter(Paper.guideline_org == organization)

    papers = query.order_by(Paper.year.desc()).all()

    return [build_citation(p) for p in papers]
