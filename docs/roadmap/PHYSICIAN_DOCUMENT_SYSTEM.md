# 의사 전용 의료 문서 시스템 구현 계획

## 개요

AllergyInsight Professional 서비스에 **의사 전용 임상 문서 시스템**을 구현합니다.
- 의료 전문용어 사용 (환자 비공개)
- GRADE 기반 근거 수준 표시
- 신뢰도 높은 논문 인용 체계

---

## 1. 시스템 구조

### 1.1 문서 유형

| 문서 | 용도 | 대상 | 공개 범위 |
|------|------|------|-----------|
| Clinical Assessment Report | 검사 결과 임상 해석 | 의사 | 의료진 전용 |
| Clinical Decision Support | 의사결정 지원 알고리즘 | 의사 | 의료진 전용 |
| Treatment Protocol | 치료 계획/처방 | 의사 | 의료진 전용 |
| Internal Notes (SOAP) | 진료 기록 | 의사 | 담당의 전용 |
| Patient Guide | 환자 교육 자료 | 환자 | Phase 2 (차후) |

### 1.2 권한 체계

```
의사 전용 문서 접근 권한:
├── Clinical Assessment Report → doctor, nurse, lab_tech
├── Clinical Decision Support  → doctor only
├── Treatment Protocol         → doctor only
├── Internal Notes             → attending physician only
└── Patient Guide              → Phase 2 (doctor, nurse, patient)
```

---

## 2. 데이터베이스 스키마

### 2.1 신규 테이블

#### ClinicalStatement (임상 진술문)

```sql
CREATE TABLE clinical_statements (
    id SERIAL PRIMARY KEY,

    -- 진술문 내용
    statement_en TEXT NOT NULL,           -- 영문 원문
    statement_kr TEXT,                    -- 한국어 번역

    -- 적용 범위
    allergen_code VARCHAR(30),            -- 'shrimp', 'peanut', 'general'
    context VARCHAR(50) NOT NULL,         -- 'cross_reactivity', 'avoidance', 'treatment', 'diagnosis'

    -- 근거 수준 (GRADE)
    evidence_level VARCHAR(10),           -- 'A', 'B', 'C', 'D'
    recommendation_grade VARCHAR(10),     -- '1A', '1B', '2A', '2B'

    -- 출처
    paper_id INTEGER REFERENCES papers(id),
    source_location VARCHAR(100),         -- "Results, p.198"

    -- 메타데이터
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    created_by INTEGER REFERENCES users(id)
);

CREATE INDEX idx_clinical_statements_allergen ON clinical_statements(allergen_code);
CREATE INDEX idx_clinical_statements_context ON clinical_statements(context);
```

#### DiagnosisClinicalNote (진단별 임상 노트)

```sql
CREATE TABLE diagnosis_clinical_notes (
    id SERIAL PRIMARY KEY,
    diagnosis_id INTEGER REFERENCES user_diagnoses(id) NOT NULL,

    -- 임상 해석 (암호화 저장)
    clinical_interpretation TEXT,
    differential_diagnosis JSONB,

    -- 위험도 평가
    risk_score INTEGER,                   -- 0-10
    risk_factors JSONB,
    anaphylaxis_risk VARCHAR(20),         -- 'low', 'moderate', 'high', 'critical'

    -- 치료 계획
    treatment_protocol JSONB,
    medication_orders JSONB,
    follow_up_plan JSONB,

    -- 의사 내부 메모 (환자 열람 불가)
    physician_notes TEXT,

    -- ICD-10 코드
    icd10_codes JSONB,

    -- 메타데이터
    documented_by INTEGER REFERENCES users(id),
    reviewed_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP
);

CREATE INDEX idx_diagnosis_clinical_notes_diagnosis ON diagnosis_clinical_notes(diagnosis_id);
```

#### DiagnosisEvidence (진단-근거 연결)

```sql
CREATE TABLE diagnosis_evidence (
    id SERIAL PRIMARY KEY,
    diagnosis_id INTEGER REFERENCES user_diagnoses(id),
    statement_id INTEGER REFERENCES clinical_statements(id),

    -- 적용 섹션
    applied_section VARCHAR(50),          -- 'interpretation', 'recommendation'

    -- 연결 방식
    is_auto_linked BOOLEAN DEFAULT TRUE,

    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_diagnosis_evidence_diagnosis ON diagnosis_evidence(diagnosis_id);
```

### 2.2 기존 테이블 확장

#### papers 테이블 확장

```sql
ALTER TABLE papers ADD COLUMN evidence_level VARCHAR(10);
ALTER TABLE papers ADD COLUMN recommendation_strength VARCHAR(20);
ALTER TABLE papers ADD COLUMN is_guideline BOOLEAN DEFAULT FALSE;
ALTER TABLE papers ADD COLUMN guideline_org VARCHAR(50);
ALTER TABLE papers ADD COLUMN key_statements JSONB;
ALTER TABLE papers ADD COLUMN verified_by INTEGER REFERENCES users(id);
ALTER TABLE papers ADD COLUMN verified_at TIMESTAMP;
```

---

## 3. API 설계

### 3.1 엔드포인트 구조

```
/api/pro/diagnosis/{id}/
├── GET  /clinical-report        # 임상 평가 보고서
├── GET  /decision-support       # 의사결정 지원 패널
├── GET  /treatment-protocol     # 치료 프로토콜
├── GET  /internal-notes         # 내부 메모 조회
├── POST /internal-notes         # 내부 메모 저장
├── GET  /evidence               # 관련 근거 목록
└── GET  /icd10-suggestions      # ICD-10 코드 제안

/api/pro/statements/
├── GET  /                       # 진술문 목록 (필터링)
├── GET  /{id}                   # 진술문 상세
└── GET  /by-allergen/{code}     # 알러젠별 진술문

/api/pro/papers/
├── GET  /guidelines             # 가이드라인 목록
├── GET  /{pmid}/verify          # PubMed 검증
└── POST /import                 # 논문 가져오기 (PMID)
```

### 3.2 응답 스키마

#### Clinical Report Response

```python
class ClinicalReportResponse(BaseModel):
    patient_id: str
    test_date: date
    panel: str

    # 요약
    summary: ClinicalSummary

    # 검사 결과
    food_allergens: List[AllergenResult]
    inhalant_allergens: List[AllergenResult]

    # 임상 해석 (근거 포함)
    interpretations: List[ClinicalInterpretation]

    # 감별진단
    differential_considerations: List[str]

    # 추가 검사 권고
    recommended_workup: List[RecommendedTest]

    # ICD-10 코드
    icd10_codes: ICD10Codes

    # 참고문헌
    references: List[Reference]


class ClinicalInterpretation(BaseModel):
    allergen_group: str                    # "Crustacean", "Legume"
    clinical_statement: str                # 임상 해석 문장
    statements_with_evidence: List[EvidenceStatement]
    recommendations: List[Recommendation]


class EvidenceStatement(BaseModel):
    text: str                              # 진술문 내용
    text_kr: str                           # 한국어
    evidence_level: str                    # 'A', 'B', 'C', 'D'
    grade_display: str                     # '⊕⊕⊕◯'
    recommendation_grade: Optional[str]    # '1A', '2B'
    source: ReferenceShort                 # 출처 요약


class Reference(BaseModel):
    ref_number: int                        # [1], [2]
    authors: str                           # "Faber MA, et al."
    title: str
    journal: str
    year: int
    pmid: Optional[str]
    doi: Optional[str]
    evidence_level: str
    paper_type: str                        # 'guideline', 'review', 'research'
    key_findings: List[str]                # 핵심 발견사항
```

---

## 4. 핵심 데이터 시드

### 4.1 가이드라인 논문

```python
GUIDELINE_PAPERS = [
    {
        "pmid": "39473345",
        "title": "EAACI guidelines on the management of IgE-mediated food allergy",
        "authors": "Santos AF, Riggioni C, Agache I, et al.",
        "journal": "Allergy",
        "year": 2025,
        "paper_type": "guideline",
        "guideline_org": "EAACI",
        "evidence_level": "A",
        "is_guideline": True,
    },
    {
        "pmid": "39560049",
        "title": "AAAAI-EAACI PRACTALL: Standardizing oral food challenges-2024 Update",
        "authors": "Sampson HA, van Wijk RG, et al.",
        "journal": "Pediatr Allergy Immunol",
        "year": 2024,
        "paper_type": "guideline",
        "guideline_org": "AAAAI/EAACI",
        "evidence_level": "A",
        "is_guideline": True,
    },
    {
        "pmid": "28027402",
        "title": "Shellfish allergens: tropomyosin and beyond",
        "authors": "Faber MA, Pascal M, et al.",
        "journal": "Allergy",
        "year": 2017,
        "paper_type": "review",
        "evidence_level": "B",
    },
]
```

### 4.2 임상 진술문

```python
CLINICAL_STATEMENTS = [
    # 갑각류/트로포미오신
    {
        "statement_en": "Tropomyosin is the major allergen in shellfish allergy, with IgE reactivity in 82% of shrimp-sensitive individuals.",
        "statement_kr": "트로포미오신은 갑각류 알레르기의 주요 알레르겐으로, 새우 감작 환자의 82%에서 IgE 반응성을 보인다.",
        "allergen_code": "shrimp",
        "context": "pathophysiology",
        "evidence_level": "B",
        "paper_pmid": "28027402",
        "source_location": "Introduction, p.194",
    },
    {
        "statement_en": "Cross-reactivity between crustaceans is high (>75%) due to conserved tropomyosin epitopes.",
        "statement_kr": "갑각류 간 교차반응성은 트로포미오신 에피토프 보존으로 인해 75% 이상으로 높다.",
        "allergen_code": "shrimp",
        "context": "cross_reactivity",
        "evidence_level": "B",
        "recommendation_grade": "1B",
        "paper_pmid": "28027402",
        "source_location": "Discussion, p.200",
    },

    # 아나필락시스/AAI
    {
        "statement_en": "Patients and caregivers must be empowered to identify anaphylaxis and correctly administer adrenaline using an AAI device. Two devices are recommended.",
        "statement_kr": "환자와 보호자는 아나필락시스를 인지하고 AAI를 올바르게 투여할 수 있어야 한다. 2개의 장치 보유를 권고한다.",
        "allergen_code": "general",
        "context": "treatment",
        "evidence_level": "A",
        "recommendation_grade": "1A",
        "paper_pmid": "39473345",
        "source_location": "Recommendations, Section 4.2",
    },
    {
        "statement_en": "Strict avoidance of the culprit food is recommended for patients with confirmed IgE-mediated food allergy.",
        "statement_kr": "IgE 매개 식품 알레르기가 확인된 환자에게는 원인 식품의 엄격한 회피를 권고한다.",
        "allergen_code": "general",
        "context": "management",
        "evidence_level": "A",
        "recommendation_grade": "1A",
        "paper_pmid": "39473345",
        "source_location": "Recommendations, Section 3.1",
    },

    # 진단
    {
        "statement_en": "Skin prick test and/or specific IgE are first line tests; oral food challenges can be done at any point of the diagnostic process.",
        "statement_kr": "피부단자검사와/또는 특이 IgE는 1차 검사이며, 경구유발검사는 진단 과정 어느 시점에서든 시행 가능하다.",
        "allergen_code": "general",
        "context": "diagnosis",
        "evidence_level": "A",
        "recommendation_grade": "1A",
        "paper_pmid": "39473345",
        "source_location": "Diagnostic Algorithm",
    },

    # 땅콩
    {
        "statement_en": "Component-resolved diagnostics using Ara h 2 improves diagnostic accuracy for peanut allergy and predicts reaction severity.",
        "statement_kr": "Ara h 2를 이용한 성분분석검사(CRD)는 땅콩 알레르기 진단 정확도를 높이고 반응 중증도를 예측한다.",
        "allergen_code": "peanut",
        "context": "diagnosis",
        "evidence_level": "B",
        "paper_pmid": "25841549",
        "source_location": "Conclusions",
    },

    # 집먼지진드기-갑각류 교차반응
    {
        "statement_en": "House dust mite sensitized patients may show asymptomatic shellfish sIgE positivity due to tropomyosin cross-reactivity. Clinical correlation is essential.",
        "statement_kr": "집먼지진드기 감작 환자는 트로포미오신 교차반응으로 무증상 갑각류 sIgE 양성을 보일 수 있다. 임상적 상관관계 확인이 필수적이다.",
        "allergen_code": "dust_mite",
        "context": "cross_reactivity",
        "evidence_level": "B",
        "paper_pmid": "8939159",
        "source_location": "Results",
    },
]
```

---

## 5. 의료 용어 사전

### 5.1 검사 결과 용어

| 코드 | 의료 용어 (EN) | 의료 용어 (KR) | 환자용 (Phase 2) |
|------|---------------|---------------|-----------------|
| `class_0` | Negative (<0.35 kU/L) | 음성 | 정상 |
| `class_1` | Low positive (0.35-0.7) | 약양성 | 약간 반응 |
| `class_2` | Weak positive (0.7-3.5) | 약양성 | 경미한 반응 |
| `class_3` | Moderate positive (3.5-17.5) | 중등도 양성 | 주의 필요 |
| `class_4` | Positive (17.5-50) | 양성 | 높음 |
| `class_5` | Strong positive (50-100) | 강양성 | 매우 높음 |
| `class_6` | Very strong positive (>100) | 강양성 | 매우 높음 |

### 5.2 진단 용어

| 코드 | 의료 용어 | 약어 |
|------|----------|------|
| `sige` | Allergen-specific IgE | sIgE |
| `spt` | Skin prick test | SPT |
| `ofc` | Oral food challenge | OFC |
| `crd` | Component-resolved diagnostics | CRD |
| `aai` | Adrenaline auto-injector | AAI |
| `fdeia` | Food-dependent exercise-induced anaphylaxis | FDEIA |

### 5.3 ICD-10 매핑

```python
ICD10_MAPPING = {
    "shrimp": {
        "allergy_status": "Z91.013",
        "anaphylaxis": "T78.02XA",
        "urticaria": "L50.0",
    },
    "peanut": {
        "allergy_status": "Z91.010",
        "anaphylaxis": "T78.01XA",
    },
    "milk": {
        "allergy_status": "Z91.011",
        "anaphylaxis": "T78.07XA",
    },
    "egg": {
        "allergy_status": "Z91.012",
        "anaphylaxis": "T78.09XA",
    },
    "dust_mite": {
        "rhinitis": "J30.89",
    },
}
```

---

## 6. 구현 단계

### Phase 1: 핵심 기능 ✅ 완료 (2025-01-26)

#### 1-A: 데이터베이스 확장 ✅

- [x] papers 테이블 컬럼 추가 (evidence_level, is_guideline, guideline_org)
- [x] clinical_statements 테이블 생성
- [ ] diagnosis_clinical_notes 테이블 생성 (Phase 2로 이동)
- [ ] diagnosis_evidence 테이블 생성 (Phase 2로 이동)
- [x] 인덱스 생성

#### 1-B: 시드 데이터 ✅

- [x] 가이드라인 논문 시드 (EAACI, AAAAI, WAO - 5개)
- [x] 핵심 임상 진술문 시드 (14개)
- [x] ICD-10 매핑 (코드에 내장)

#### 1-C: Backend API ✅

- [x] `GET /api/pro/clinical-report` (patient_id, kit_serial_number, diagnosis_id 지원)
- [x] `GET /api/pro/clinical-report/statements` (알러젠별/컨텍스트별 진술문 조회)
- [x] `GET /api/pro/clinical-report/guidelines` (가이드라인 목록)
- [x] 권한 미들웨어 적용 (require_professional)

#### 1-D: Frontend UI ✅

- [x] ClinicalReportPage.jsx 생성
- [x] ClinicalStatement 컴포넌트 (인용 표시)
- [x] GradeBadge 컴포넌트 (⊕⊕⊕◯)
- [x] Citation 컴포넌트
- [x] ProNav에 임상보고서 메뉴 추가

### Phase 2: 고급 기능 (2주)

#### 2-A: PubMed 연동 (3일)

- [ ] PubMedService 구현
- [ ] 논문 정보 자동 조회 API
- [ ] 논문 검증 기능

#### 2-B: 임상 노트 기능 (4일)

- [ ] `POST /api/pro/diagnosis/{id}/internal-notes`
- [ ] SOAP 노트 입력 폼
- [ ] 암호화 저장

#### 2-C: 치료 프로토콜 (3일)

- [ ] Treatment Protocol 페이지
- [ ] 약물 처방 템플릿
- [ ] PDF 출력 기능

#### 2-D: ICD-10 지원 (2일)

- [ ] ICD-10 코드 자동 제안
- [ ] 코드 검색 기능

### Phase 3: 확장 (차후)

- [ ] 논문 관리 Admin UI
- [ ] 진술문 추가/편집 기능
- [ ] 다국어 지원 확장
- [ ] 환자용 문서 생성 (Patient Guide)

---

## 7. 파일 구조

### Backend

```
backend/app/
├── professional/
│   ├── clinical/
│   │   ├── __init__.py
│   │   ├── routes.py           # 임상 보고서 API
│   │   ├── schemas.py          # Pydantic 스키마
│   │   └── services.py         # 비즈니스 로직
│   ├── evidence/
│   │   ├── __init__.py
│   │   ├── routes.py           # 근거/인용 API
│   │   └── schemas.py
│   └── notes/
│       ├── __init__.py
│       ├── routes.py           # SOAP 노트 API
│       └── schemas.py
├── database/
│   ├── models.py               # 기존 + 신규 모델
│   ├── seed_guidelines.py      # 가이드라인 시드
│   └── seed_statements.py      # 진술문 시드
├── services/
│   └── pubmed_service.py       # PubMed API 연동
└── data/
    ├── icd10_mapping.py        # ICD-10 매핑
    └── medical_terms.py        # 의료 용어 사전
```

### Frontend

```
frontend/src/apps/professional/
├── pages/
│   ├── ClinicalReportPage.jsx      # 임상 보고서
│   ├── DecisionSupportPage.jsx     # 의사결정 지원
│   └── TreatmentProtocolPage.jsx   # 치료 프로토콜
├── components/
│   ├── clinical/
│   │   ├── ClinicalSummary.jsx
│   │   ├── AllergenResultTable.jsx
│   │   ├── InterpretationCard.jsx
│   │   └── DifferentialList.jsx
│   ├── evidence/
│   │   ├── EvidenceStatement.jsx   # 근거 진술문
│   │   ├── GradeBadge.jsx          # ⊕⊕⊕◯ 배지
│   │   ├── ReferenceCard.jsx       # 참고문헌 카드
│   │   └── EvidenceLegend.jsx      # 범례
│   └── protocol/
│       ├── MedicationOrder.jsx
│       └── FollowUpPlan.jsx
└── services/
    └── clinicalApi.js              # API 클라이언트
```

---

## 8. 참고 자료

### 가이드라인 출처

- [EAACI Management Guidelines 2025](https://pubmed.ncbi.nlm.nih.gov/39473345/)
- [EAACI Diagnosis Guidelines 2025](https://onlinelibrary.wiley.com/doi/10.1111/all.16321)
- [AAAAI-EAACI PRACTALL 2024](https://pubmed.ncbi.nlm.nih.gov/39560049/)
- [WAO Anaphylaxis Guidelines 2020](https://pubmed.ncbi.nlm.nih.gov/32698591/)

### 기술 참고

- [GRADE Framework](https://www.gradeworkinggroup.org/)
- [NCBI PubMed API](https://www.ncbi.nlm.nih.gov/home/develop/api/)
- [ICD-10-CM Codes](https://www.icd10data.com/)

---

## 변경 이력

| 버전 | 일자 | 내용 |
|------|------|------|
| 1.0 | 2025-01-26 | 초안 작성 |
