# AllergyInsight 의료 전문가용 고도화 계획

## 개요

### 서비스 목적
- **대상**: 의료관련자 (의사, 간호사, 임상병리사 등)
- **목표**: 키트 검사(SGTi-Allergy Screen PLUS)를 진행한 환자에게 근거 기반 처방 권고 제공
- **핵심 가치**: 학술 논문 기반의 신뢰할 수 있는 의사결정 지원

### 현재 구현 상태 요약

| 영역 | 구현율 | 상태 |
|------|--------|------|
| 인증 시스템 | 100% | 완료 |
| 진단 결과 관리 | 90% | 완료 |
| 처방 권고 엔진 | 85% | 거의 완료 |
| 논문 검색 | 80% | 완료 |
| 논문 관리 UI | 40% | 부분 구현 |
| 의료 전문가 기능 | 20% | 고도화 필요 |

---

## 1. 사용자 역할 체계 고도화

### 1.1 현재 역할 구조
```
현재: user / admin (2단계)
```

### 1.2 제안 역할 구조 (현재 구현됨)
```
┌─────────────────────────────────────────────────────────────┐
│                     역할 계층 구조                           │
├─────────────────────────────────────────────────────────────┤
│  super_admin    │ 시스템 관리자 (논문 검증, 사용자 관리)      │
│  hospital_admin │ 병원 관리자 (직원 관리, 병원 설정)          │
│  doctor         │ 의사 (처방 작성, 환자 관리, 전체 기능)      │
│  nurse          │ 간호사 (환자 가이드, 제한된 처방 조회)      │
│  lab_tech       │ 임상병리사 (키트 결과 입력, 검사 관리)      │
│  patient        │ 환자 (본인 결과 조회, 가이드 열람)          │
└─────────────────────────────────────────────────────────────┘

※ 약사(pharmacist) 역할은 현재 타겟 고객이 아니므로 제외
  → 향후 약국 연계 서비스 확장 시 추가 검토
```

### 1.3 데이터베이스 스키마 변경

```sql
-- 의료 전문가 프로필 테이블
CREATE TABLE medical_professionals (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    license_number VARCHAR(50) NOT NULL,       -- 면허번호
    license_type VARCHAR(30) NOT NULL,          -- 의사/간호사/약사 등
    specialty VARCHAR(100),                     -- 전문분야 (알러지내과 등)
    institution VARCHAR(200),                   -- 소속 기관
    institution_code VARCHAR(50),               -- 요양기관번호
    is_verified BOOLEAN DEFAULT FALSE,          -- 면허 검증 여부
    verified_at TIMESTAMP,
    verified_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 환자 테이블 (의료진이 관리)
CREATE TABLE patients (
    id SERIAL PRIMARY KEY,
    chart_number VARCHAR(50),                   -- 차트번호
    name VARCHAR(100) NOT NULL,
    birth_date DATE NOT NULL,
    gender VARCHAR(10),
    phone VARCHAR(20),
    emergency_contact VARCHAR(20),
    medical_history TEXT,                       -- 과거력 (JSON)
    current_medications TEXT,                   -- 현재 복용약 (JSON)
    created_by INTEGER REFERENCES users(id),    -- 등록한 의료진
    institution_code VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP
);

-- 처방 기록 테이블
CREATE TABLE prescription_records (
    id SERIAL PRIMARY KEY,
    patient_id INTEGER REFERENCES patients(id),
    diagnosis_id INTEGER REFERENCES user_diagnoses(id),
    prescriber_id INTEGER REFERENCES users(id), -- 처방 의료진
    prescription_data JSONB NOT NULL,           -- 처방 내용
    clinical_notes TEXT,                        -- 임상 소견
    recommendations TEXT,                       -- 권고사항
    follow_up_date DATE,                        -- 추적관찰일
    status VARCHAR(30) DEFAULT 'active',        -- active/completed/cancelled
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP
);

-- 처방 이력 (감사 로그)
CREATE TABLE prescription_audit_log (
    id SERIAL PRIMARY KEY,
    prescription_id INTEGER REFERENCES prescription_records(id),
    action VARCHAR(30) NOT NULL,                -- create/update/view/print
    actor_id INTEGER REFERENCES users(id),
    actor_role VARCHAR(30),
    changes JSONB,
    ip_address VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 1.4 권한 매트릭스 (현재 구현됨)

| 기능 | super_admin | hospital_admin | doctor | nurse | lab_tech | patient |
|------|-------------|----------------|--------|-------|----------|---------|
| 환자 등록 | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ |
| 키트 결과 입력 | ✅ | ❌ | ✅ | ✅ | ✅ | ❌ |
| 처방 작성 | ✅ | ❌ | ✅ | ❌ | ❌ | ❌ |
| 처방 조회 | ✅ | ✅ | ✅ | ✅ | ✅ | 본인만 |
| 처방 수정 | ✅ | ❌ | 본인만 | ❌ | ❌ | ❌ |
| 환자 가이드 출력 | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ |
| 논문 검색 | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ |
| 논문 관리 | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| 직원 관리 | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| 통계 조회 | ✅ | ✅ | ✅ | 제한 | 제한 | ❌ |

---

## 2. 의료 전문가 전용 기능

### 2.1 처방 작성 워크플로우

```
┌─────────────────────────────────────────────────────────────┐
│                    처방 작성 워크플로우                       │
└─────────────────────────────────────────────────────────────┘

[1. 환자 선택/등록]
    │
    ├─ 기존 환자 검색 (차트번호, 이름, 생년월일)
    └─ 신규 환자 등록
           │
           ▼
[2. 키트 결과 입력/조회]
    │
    ├─ 키트 시리얼 번호로 자동 연동
    ├─ 수동 결과 입력 (16종 알러젠)
    └─ 이전 검사 결과 비교
           │
           ▼
[3. AI 처방 권고 생성]
    │
    ├─ 자동 위험도 분석
    ├─ 논문 기반 권고사항
    ├─ 교차반응 경고
    └─ 약물 상호작용 확인
           │
           ▼
[4. 의료진 검토 및 수정]
    │
    ├─ 권고안 수정/추가
    ├─ 임상 소견 작성
    └─ 추적관찰 일정 설정
           │
           ▼
[5. 처방 확정 및 출력]
    │
    ├─ 전자서명
    ├─ 처방전 출력 (PDF)
    └─ 환자 가이드 출력
```

### 2.2 처방 권고 엔진 고도화

#### 현재 구현된 처방 항목
- ✅ 음식 섭취 제한 (FoodRestriction)
- ✅ 예상 증상 (SymptomPrediction)
- ✅ 교차반응 경고 (CrossReactivityAlert)
- ✅ 응급 가이드라인 (EmergencyGuideline)

#### 추가 제안 처방 항목

```python
# 1. 약물 처방 권고
class MedicationRecommendation:
    medication_type: str          # 항히스타민제, 에피네프린, 스테로이드 등
    generic_name: str             # 일반명
    brand_examples: List[str]     # 상품명 예시
    dosage_guideline: str         # 용량 가이드
    indication: str               # 적응증
    contraindications: List[str]  # 금기사항
    precautions: List[str]        # 주의사항
    evidence_level: str           # 근거수준 (A/B/C/D)
    citations: List[Citation]     # 참고문헌

# 2. 검사 권고
class TestRecommendation:
    test_name: str                # 검사명
    test_code: str                # 검사코드
    purpose: str                  # 검사 목적
    timing: str                   # 검사 시기
    preparation: str              # 준비사항
    priority: str                 # urgent/routine/optional

# 3. 전문의 의뢰 권고
class ReferralRecommendation:
    specialty: str                # 의뢰 진료과
    urgency: str                  # 긴급도
    reason: str                   # 의뢰 사유
    suggested_tests: List[str]    # 권장 검사

# 4. 생활 관리 권고
class LifestyleRecommendation:
    category: str                 # 환경관리, 운동, 스트레스 등
    recommendations: List[str]
    avoid_situations: List[str]
    monitoring_items: List[str]

# 5. 추적관찰 계획
class FollowUpPlan:
    next_visit: str               # 다음 방문 시기
    monitoring_parameters: List[str]  # 모니터링 항목
    warning_signs: List[str]      # 주의 증상
    when_to_seek_help: List[str]  # 즉시 내원 필요 상황
```

### 2.3 근거수준 표시 시스템

```
┌─────────────────────────────────────────────────────────────┐
│                    근거수준 (Evidence Level)                 │
├─────────────────────────────────────────────────────────────┤
│  Level A │ 다수의 RCT 또는 메타분석에 기반한 권고            │
│  Level B │ 단일 RCT 또는 대규모 비무작위 연구                │
│  Level C │ 전문가 합의 또는 소규모 연구                      │
│  Level D │ 전문가 의견 또는 사례 보고                        │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                    권고등급 (Recommendation Grade)           │
├─────────────────────────────────────────────────────────────┤
│  Grade I   │ 강력히 권고 (이득 >> 위험)                      │
│  Grade IIa │ 권고 (이득 > 위험)                              │
│  Grade IIb │ 고려 가능 (이득 ≥ 위험)                         │
│  Grade III │ 권고하지 않음 (이득 < 위험)                     │
└─────────────────────────────────────────────────────────────┘
```

### 2.4 임상 의사결정 지원 (CDS) 기능

```python
# 임상 의사결정 지원 알림
class ClinicalAlert:
    alert_type: str       # warning/caution/info
    category: str         # drug_interaction/contraindication/allergy_cross
    message: str
    severity: str         # critical/high/moderate/low
    action_required: str
    citations: List[Citation]

# 약물 상호작용 체크
def check_drug_interactions(
    current_medications: List[str],
    allergen_results: Dict[str, int]
) -> List[ClinicalAlert]:
    """
    현재 복용약과 알러지 결과를 기반으로 상호작용 체크
    예: 아스피린 복용 + NSAID 교차반응 알러지
    """
    pass

# 금기사항 체크
def check_contraindications(
    patient: Patient,
    prescription: Prescription
) -> List[ClinicalAlert]:
    """
    환자 정보와 처방 내용의 금기사항 체크
    예: 임산부 + 특정 약물, 신장질환 + 용량 조절
    """
    pass
```

---

## 3. 환자 관리 시스템

### 3.1 환자 대시보드

```
┌─────────────────────────────────────────────────────────────┐
│                     환자 대시보드                            │
├─────────────────────────────────────────────────────────────┤
│  [검색창] 차트번호/이름/생년월일 검색                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ 오늘의 환자 목록                                     │   │
│  │ ┌─────┬────────┬────────┬─────────┬───────────┐    │   │
│  │ │차트 │ 이름   │ 검사일  │ 양성항원 │ 상태      │    │   │
│  │ ├─────┼────────┼────────┼─────────┼───────────┤    │   │
│  │ │001  │ 김OO   │ 01-23  │ 5개     │ 처방대기  │    │   │
│  │ │002  │ 이OO   │ 01-23  │ 3개     │ 처방완료  │    │   │
│  │ └─────┴────────┴────────┴─────────┴───────────┘    │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─────────────────────┐ ┌─────────────────────────────┐   │
│  │ 위험 환자 알림       │ │ 추적관찰 필요 환자          │   │
│  │ • 김OO: 아나필락시스 │ │ • 박OO: 01-30 예정          │   │
│  │   위험 (땅콩 6등급)  │ │ • 최OO: 02-05 예정          │   │
│  └─────────────────────┘ └─────────────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 3.2 환자 상세 화면

```
┌─────────────────────────────────────────────────────────────┐
│  환자: 김철수 (M/35)              차트번호: 2024-001234     │
├─────────────────────────────────────────────────────────────┤
│  [기본정보] [검사이력] [처방이력] [가이드출력]               │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ■ 최근 검사 결과 (2026-01-23)                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  위험도: ████████████░░░░ HIGH                      │   │
│  │                                                      │   │
│  │  양성 알러젠 (5개):                                  │   │
│  │  ┌──────────┬───────┬─────────────────────────┐     │   │
│  │  │ 알러젠   │ 등급  │ 주요 증상 위험          │     │   │
│  │  ├──────────┼───────┼─────────────────────────┤     │   │
│  │  │ 땅콩     │ ⬛⬛⬛⬛⬛⬛ 6 │ 아나필락시스 고위험   │     │   │
│  │  │ 우유     │ ⬛⬛⬛░░░ 3 │ 소화기 증상          │     │   │
│  │  │ 계란     │ ⬛⬛░░░░ 2 │ 피부 증상            │     │   │
│  │  │ 집먼지   │ ⬛⬛⬛⬛░░ 4 │ 호흡기 증상          │     │   │
│  │  │ 꽃가루   │ ⬛⬛░░░░ 2 │ 비염, 결막염         │     │   │
│  │  └──────────┴───────┴─────────────────────────┘     │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ■ 이전 검사와 비교                                        │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  [차트: 등급 변화 추이 그래프]                        │   │
│  │  땅콩: 4 → 5 → 6 (↑ 악화)                           │   │
│  │  우유: 4 → 3 → 3 (→ 유지)                           │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  [처방 작성하기]  [환자 가이드 출력]  [전문의 의뢰]         │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 3.3 검사 결과 추이 분석

```python
class DiagnosisTrendAnalysis:
    """검사 결과 추이 분석"""

    def analyze_trend(
        self,
        patient_id: int,
        allergen: str
    ) -> TrendResult:
        """
        특정 알러젠의 등급 변화 추이 분석
        Returns:
            - trend: improving/stable/worsening
            - grade_history: [(date, grade), ...]
            - prediction: 예상 변화
            - recommendation: 추가 검사/관리 권고
        """
        pass

    def compare_diagnoses(
        self,
        diagnosis_id_1: int,
        diagnosis_id_2: int
    ) -> ComparisonResult:
        """
        두 검사 결과 비교
        Returns:
            - new_positives: 새로 양성된 항원
            - resolved: 음성으로 전환된 항원
            - grade_changes: 등급 변화
            - clinical_significance: 임상적 의의
        """
        pass
```

---

## 4. 논문 기반 근거 시스템 고도화

### 4.1 논문 관리 확장

```sql
-- 논문 테이블 확장
ALTER TABLE papers ADD COLUMN
    study_type VARCHAR(50),           -- RCT, cohort, case-control, etc.
    sample_size INTEGER,              -- 연구 대상 수
    population VARCHAR(100),          -- 연구 대상 (성인/소아/임산부 등)
    evidence_level VARCHAR(10),       -- A/B/C/D
    quality_score INTEGER,            -- 논문 품질 점수 (0-100)
    clinical_relevance VARCHAR(20),   -- high/medium/low
    last_reviewed_at TIMESTAMP,
    reviewed_by INTEGER REFERENCES users(id);

-- 가이드라인 테이블
CREATE TABLE clinical_guidelines (
    id SERIAL PRIMARY KEY,
    title VARCHAR(500) NOT NULL,
    organization VARCHAR(200),        -- EAACI, AAAAI, WAO 등
    publication_year INTEGER,
    version VARCHAR(20),
    url VARCHAR(500),
    summary TEXT,
    key_recommendations JSONB,        -- 주요 권고사항
    allergens_covered JSONB,          -- 다루는 알러젠
    is_current BOOLEAN DEFAULT TRUE,
    superseded_by INTEGER REFERENCES clinical_guidelines(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 가이드라인-처방 매핑
CREATE TABLE guideline_prescription_mapping (
    id SERIAL PRIMARY KEY,
    guideline_id INTEGER REFERENCES clinical_guidelines(id),
    allergen_code VARCHAR(30),
    grade_range VARCHAR(20),          -- "1-2", "3-4", "5-6"
    recommendation_type VARCHAR(50),
    recommendation_text TEXT,
    evidence_level VARCHAR(10),
    recommendation_grade VARCHAR(10)
);
```

### 4.2 권고사항 출처 표시 강화

```
┌─────────────────────────────────────────────────────────────┐
│  권고사항: 땅콩 완전 회피 필요                               │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  근거수준: Level A  |  권고등급: Grade I (강력히 권고)       │
│                                                             │
│  참고문헌:                                                  │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ [1] EAACI Guidelines on Allergen Immunotherapy      │   │
│  │     Pajno GB, et al. Allergy. 2022;77(2):348-370   │   │
│  │     PMID: 34536223 | IF: 14.71 | 인용: 234회       │   │
│  │     → "Grade 5-6 peanut allergy requires strict    │   │
│  │        avoidance and epinephrine prescription"      │   │
│  ├─────────────────────────────────────────────────────┤   │
│  │ [2] Food Allergy Management Guidelines 2024        │   │
│  │     AAAAI/ACAAI Joint Task Force                   │   │
│  │     J Allergy Clin Immunol. 2024;153(1):15-28     │   │
│  │     → "Severe peanut allergy: absolute avoidance"  │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  [전문 보기]  [PDF 다운로드]  [PubMed 링크]                 │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 4.3 실시간 논문 업데이트 알림

```python
class PaperUpdateNotification:
    """새로운 관련 논문 발행 알림"""

    async def check_new_publications(
        self,
        allergens: List[str],
        last_check: datetime
    ) -> List[NewPaperAlert]:
        """
        지정된 알러젠 관련 신규 논문 확인
        - PubMed 신규 발행 확인
        - 주요 가이드라인 업데이트 확인
        - Impact Factor 상위 저널 우선
        """
        pass

    async def notify_guideline_update(
        self,
        guideline: ClinicalGuideline
    ) -> None:
        """
        가이드라인 업데이트 시 관련 의료진에게 알림
        """
        pass
```

---

## 5. 보고서 및 출력 기능

### 5.1 처방전 템플릿

```
┌─────────────────────────────────────────────────────────────┐
│                    알러지 검사 결과 및 처방                   │
│                                                             │
│  ═══════════════════════════════════════════════════════   │
│                                                             │
│  ■ 환자 정보                                                │
│  성명: 김철수          생년월일: 1990-05-15                 │
│  차트번호: 2024-001234  검사일: 2026-01-23                  │
│                                                             │
│  ■ 검사 결과 요약                                           │
│  검사명: SGTi-Allergy Screen PLUS (16종)                   │
│  양성 항원: 5개 / 16개                                      │
│  최고 등급: 6등급 (땅콩)                                    │
│  종합 위험도: HIGH                                          │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ 알러젠      │ 등급 │ sIgE (kU/L) │ 판정           │   │
│  ├─────────────┼──────┼─────────────┼────────────────┤   │
│  │ 땅콩        │  6   │   >100      │ 강양성 ⚠️     │   │
│  │ 우유        │  3   │   3.5-17.4  │ 양성          │   │
│  │ 계란        │  2   │   0.7-3.4   │ 약양성        │   │
│  │ 집먼지진드기 │  4   │   17.5-49.9 │ 양성          │   │
│  │ 꽃가루      │  2   │   0.7-3.4   │ 약양성        │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ■ 처방 및 권고사항                                         │
│                                                             │
│  1. 응급 처치                                               │
│     • 에피네프린 자가주사기(에피펜) 처방 및 휴대 필수        │
│     • 아나필락시스 응급 대처법 교육 완료                     │
│                                                             │
│  2. 식이 관리                                               │
│     • 땅콩 및 땅콩 함유 식품 완전 회피                       │
│     • 견과류 교차반응 주의 (호두, 아몬드 등)                 │
│     • 외식 시 알러지 정보 반드시 확인                        │
│                                                             │
│  3. 약물 처방                                               │
│     • 항히스타민제: 세티리진 10mg 1일 1회                   │
│     • 에피네프린 자가주사기 0.3mg 1개                       │
│                                                             │
│  4. 추적 관찰                                               │
│     • 6개월 후 재검사 권장                                  │
│     • 증상 발생 시 즉시 내원                                │
│                                                             │
│  ═══════════════════════════════════════════════════════   │
│                                                             │
│  처방일: 2026-01-23                                         │
│  처방의: 홍길동 (알러지내과 전문의)                          │
│  의료기관: OO대학교병원 알러지내과                          │
│                                                             │
│                              [서명]                         │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 5.2 환자용 가이드 출력

```
┌─────────────────────────────────────────────────────────────┐
│              나의 알러지 관리 가이드                         │
│                                                             │
│  김철수님을 위한 맞춤 가이드                 2026-01-23     │
│                                                             │
│  ═══════════════════════════════════════════════════════   │
│                                                             │
│  ⚠️ 주의해야 할 알러젠                                      │
│                                                             │
│  🥜 땅콩 (위험등급: 매우 높음)                              │
│  ─────────────────────────────────────                      │
│  피해야 할 음식:                                            │
│  • 땅콩버터, 땅콩가루, 땅콩기름                             │
│  • 사탕, 초콜릿, 과자류 (성분 확인 필수)                    │
│  • 아시아 요리 (태국, 베트남, 중국식)                       │
│                                                             │
│  숨겨진 땅콩 주의:                                          │
│  • 소스류 (사테이소스, 몰레소스)                            │
│  • 샐러드 드레싱, 마리네이드                                │
│  • 에너지바, 그래놀라                                       │
│                                                             │
│  라벨에서 확인할 단어:                                      │
│  peanut, groundnut, arachis oil, 땅콩, 낙화생              │
│                                                             │
│  🥛 우유 (위험등급: 중간)                                   │
│  ─────────────────────────────────────                      │
│  피해야 할 음식:                                            │
│  • 우유, 치즈, 버터, 요거트, 아이스크림                     │
│  • 크림소스, 베샤멜소스                                     │
│                                                             │
│  대체식품:                                                  │
│  • 두유, 아몬드밀크, 귀리우유, 코코넛밀크                   │
│  • 비건 치즈, 코코넛 요거트                                 │
│                                                             │
│  ═══════════════════════════════════════════════════════   │
│                                                             │
│  🚨 응급 상황 대처법                                        │
│                                                             │
│  아나필락시스 증상:                                         │
│  • 전신 두드러기, 얼굴/목 부종                              │
│  • 호흡곤란, 쌕쌕거림                                       │
│  • 어지러움, 의식저하                                       │
│                                                             │
│  즉시 해야 할 일:                                           │
│  1. 에피펜 허벅지에 주사                                    │
│  2. 119 신고                                                │
│  3. 편평한 자세로 눕기 (다리 올리기)                        │
│  4. 병원 도착까지 2차 주사 준비                             │
│                                                             │
│  ═══════════════════════════════════════════════════════   │
│                                                             │
│  📅 다음 방문 예정일: 2026-07-23                            │
│  📞 응급 연락처: OO대학교병원 응급실 02-XXX-XXXX           │
│  👨‍⚕️ 담당의: 홍길동 (알러지내과)                            │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 5.3 보고서 생성 API

```python
# 보고서 생성 서비스
class ReportGenerationService:

    async def generate_prescription_report(
        self,
        prescription_id: int,
        format: str = "pdf",  # pdf, docx, html
        language: str = "ko"
    ) -> bytes:
        """처방전 생성"""
        pass

    async def generate_patient_guide(
        self,
        diagnosis_id: int,
        format: str = "pdf",
        include_images: bool = True,
        language: str = "ko"
    ) -> bytes:
        """환자용 가이드 생성"""
        pass

    async def generate_referral_letter(
        self,
        patient_id: int,
        referral_to: str,
        reason: str
    ) -> bytes:
        """전문의 의뢰서 생성"""
        pass

    async def generate_statistics_report(
        self,
        institution_code: str,
        date_range: Tuple[date, date],
        report_type: str  # daily, weekly, monthly
    ) -> bytes:
        """기관별 통계 보고서 생성"""
        pass
```

---

## 6. 보안 및 규정 준수

### 6.1 의료 정보 보안 (HIPAA/개인정보보호법 준수)

```python
# 보안 설정
class SecurityConfig:
    # 데이터 암호화
    ENCRYPTION_AT_REST = True           # 저장 데이터 암호화
    ENCRYPTION_IN_TRANSIT = True        # 전송 데이터 암호화 (TLS 1.3)

    # 접근 제어
    SESSION_TIMEOUT_MINUTES = 30        # 세션 타임아웃
    MAX_LOGIN_ATTEMPTS = 5              # 최대 로그인 시도
    LOCKOUT_DURATION_MINUTES = 30       # 계정 잠금 시간

    # 감사 로그
    AUDIT_LOG_ENABLED = True            # 모든 접근 기록
    AUDIT_LOG_RETENTION_DAYS = 365 * 5  # 5년 보관

    # 데이터 마스킹
    MASK_PATIENT_NAME = True            # 환자명 마스킹
    MASK_PHONE_NUMBER = True            # 전화번호 마스킹
```

### 6.2 감사 로그 시스템

```sql
-- 감사 로그 테이블
CREATE TABLE audit_logs (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    user_id INTEGER REFERENCES users(id),
    user_role VARCHAR(30),
    action VARCHAR(50) NOT NULL,          -- login, logout, view, create, update, delete, print
    resource_type VARCHAR(50),            -- patient, diagnosis, prescription, paper
    resource_id INTEGER,
    details JSONB,                        -- 상세 정보 (변경 전/후)
    ip_address VARCHAR(50),
    user_agent TEXT,
    success BOOLEAN DEFAULT TRUE,
    error_message TEXT
);

-- 인덱스
CREATE INDEX idx_audit_logs_user ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_timestamp ON audit_logs(timestamp);
CREATE INDEX idx_audit_logs_action ON audit_logs(action);
CREATE INDEX idx_audit_logs_resource ON audit_logs(resource_type, resource_id);
```

### 6.3 데이터 접근 권한

```python
# 데이터 접근 정책
class DataAccessPolicy:

    def can_access_patient(
        self,
        user: User,
        patient: Patient
    ) -> bool:
        """환자 정보 접근 권한 확인"""
        # 같은 기관 소속만 접근 가능
        if user.institution_code != patient.institution_code:
            return False

        # 역할별 접근 권한
        if user.role in ['doctor', 'nurse', 'lab_tech']:
            return True

        # 환자 본인
        if user.role == 'patient' and user.patient_id == patient.id:
            return True

        return False

    def can_modify_prescription(
        self,
        user: User,
        prescription: Prescription
    ) -> bool:
        """처방 수정 권한 확인"""
        # 의사만 가능
        if user.role != 'doctor':
            return False

        # 본인이 작성한 처방만
        if prescription.prescriber_id != user.id:
            return False

        # 24시간 이내만
        if prescription.created_at < datetime.now() - timedelta(hours=24):
            return False

        return True
```

---

## 7. API 확장

### 7.1 새로운 API 엔드포인트

```python
# 환자 관리 API
@router.post("/patients")
async def create_patient(patient: PatientCreate, user: User = Depends(require_role(['doctor', 'nurse', 'lab_tech']))):
    """환자 등록"""

@router.get("/patients/{patient_id}")
async def get_patient(patient_id: int, user: User = Depends(require_auth)):
    """환자 정보 조회"""

@router.get("/patients/{patient_id}/diagnoses")
async def get_patient_diagnoses(patient_id: int, user: User = Depends(require_auth)):
    """환자의 검사 이력"""

@router.get("/patients/{patient_id}/prescriptions")
async def get_patient_prescriptions(patient_id: int, user: User = Depends(require_auth)):
    """환자의 처방 이력"""

@router.get("/patients/{patient_id}/trend")
async def get_patient_trend(patient_id: int, allergen: str, user: User = Depends(require_auth)):
    """특정 알러젠 추이 분석"""

# 처방 관리 API
@router.post("/prescriptions")
async def create_prescription(prescription: PrescriptionCreate, user: User = Depends(require_role(['doctor']))):
    """처방 작성"""

@router.put("/prescriptions/{prescription_id}")
async def update_prescription(prescription_id: int, updates: PrescriptionUpdate, user: User = Depends(require_role(['doctor']))):
    """처방 수정"""

@router.post("/prescriptions/{prescription_id}/sign")
async def sign_prescription(prescription_id: int, user: User = Depends(require_role(['doctor']))):
    """처방 전자서명"""

# 보고서 API
@router.get("/reports/prescription/{prescription_id}")
async def generate_prescription_report(prescription_id: int, format: str = "pdf", user: User = Depends(require_auth)):
    """처방전 PDF 생성"""

@router.get("/reports/patient-guide/{diagnosis_id}")
async def generate_patient_guide(diagnosis_id: int, format: str = "pdf", user: User = Depends(require_auth)):
    """환자 가이드 PDF 생성"""

# 통계 API
@router.get("/statistics/institution")
async def get_institution_statistics(date_from: date, date_to: date, user: User = Depends(require_role(['doctor', 'admin']))):
    """기관별 통계"""

@router.get("/statistics/allergen-distribution")
async def get_allergen_distribution(date_from: date, date_to: date, user: User = Depends(require_role(['doctor', 'admin']))):
    """알러젠별 분포 통계"""

# CDS API
@router.post("/cds/check-interactions")
async def check_drug_interactions(request: InteractionCheckRequest, user: User = Depends(require_role(['doctor', 'pharmacist']))):
    """약물 상호작용 체크"""

@router.post("/cds/alerts")
async def get_clinical_alerts(diagnosis_id: int, medications: List[str], user: User = Depends(require_role(['doctor']))):
    """임상 경고 조회"""
```

### 7.2 API 응답 표준화

```python
# 표준 응답 형식
class ApiResponse(Generic[T]):
    success: bool
    data: Optional[T]
    error: Optional[ErrorDetail]
    meta: Optional[MetaInfo]

class ErrorDetail:
    code: str
    message: str
    details: Optional[Dict]

class MetaInfo:
    timestamp: datetime
    request_id: str
    pagination: Optional[PaginationInfo]
    evidence_summary: Optional[EvidenceSummary]  # 의료 API용

class EvidenceSummary:
    total_citations: int
    evidence_levels: Dict[str, int]  # {"A": 3, "B": 2, "C": 1}
    guideline_sources: List[str]
```

---

## 8. 프론트엔드 확장

### 8.1 새로운 페이지 구성

```
/medical                    # 의료진 메인 대시보드
/medical/patients           # 환자 목록
/medical/patients/:id       # 환자 상세
/medical/patients/:id/new-diagnosis  # 새 검사 등록
/medical/prescriptions      # 처방 목록
/medical/prescriptions/new  # 처방 작성
/medical/prescriptions/:id  # 처방 상세/수정
/medical/reports            # 보고서 생성
/medical/statistics         # 통계 대시보드

/admin/users                # 사용자 관리 (super_admin)
/admin/professionals        # 의료진 인증 관리
/admin/papers               # 논문 관리
/admin/guidelines           # 가이드라인 관리
```

### 8.2 UI 컴포넌트

```jsx
// 핵심 컴포넌트
<PatientSearch />           // 환자 검색
<DiagnosisInput />          // 검사 결과 입력
<AllergenGradeChart />      // 등급 시각화
<TrendChart />              // 추이 그래프
<PrescriptionEditor />      // 처방 편집기
<EvidencePanel />           // 근거 패널
<ClinicalAlertBanner />     // 임상 경고
<ReportPreview />           // 보고서 미리보기
<SignaturePad />            // 전자서명
```

---

## 9. 구현 로드맵

### ✅ 완료된 항목

| 항목 | 상태 | 완료일 |
|------|------|--------|
| 역할 시스템 구현 (6개 역할) | ✅ 완료 | 2025-01-25 |
| 조직/멤버 관리 시스템 | ✅ 완료 | 2025-01-25 |
| 병원-환자 연결 시스템 | ✅ 완료 | 2025-01-25 |
| 임상 보고서 시스템 Phase 1 | ✅ 완료 | 2025-01-26 |
| GRADE 기반 근거 수준 표시 | ✅ 완료 | 2025-01-26 |

### 🎯 단기 목표 (2~4주)

| 작업 | 우선순위 |
|------|----------|
| PDF 리포트 출력 (임상 보고서, 환자 가이드) | 높음 |
| ICD-10 진단 코드 자동 매핑 개선 | 높음 |
| 의사 소견 입력 UI 개선 | 높음 |
| 테스트 코드 작성 (pytest, jest) | 필수 |
| API 에러 핸들링 및 로깅 개선 | 필수 |

### 📅 중기 목표 (1~2개월)

| 작업 | 우선순위 |
|------|----------|
| 병원별 통계 리포트 | 중간 |
| SMS/이메일 알림 시스템 | 중간 |
| PubMed 논문 자동 검증 | 중간 |
| Consumer 앱 UI/UX 개선 | 중간 |

### 📆 장기 목표 (3개월+)

| 작업 | 비고 |
|------|------|
| 검사 결과 자동 연동 | batch job 또는 API 방식 |
| 다국어 지원 (영어) | 글로벌 확장 시 |
| 결제/구독 시스템 | 고객사 확보 후 |

---

## 10. 기술 스택 추가 제안

### 10.1 백엔드 추가

```
# PDF 생성
WeasyPrint 또는 ReportLab

# 작업 큐 (배치 처리)
Celery + Redis

# 캐싱
Redis

# 검색 엔진 (논문 검색 고도화)
Elasticsearch 또는 Meilisearch

# 모니터링
Sentry (에러 추적)
Prometheus + Grafana (메트릭)
```

### 10.2 프론트엔드 추가

```
# 상태 관리
React Query (서버 상태)
Zustand (클라이언트 상태)

# UI 컴포넌트
Radix UI 또는 shadcn/ui

# 차트
Chart.js 또는 Visx

# PDF 뷰어
react-pdf

# 전자서명
signature_pad
```

---

## 11. 결론

### 현재 상태
AllergyInsight는 **핵심 기능의 80%가 구현된 상태**로, 의료 전문가용 고도화를 위한 탄탄한 기반을 갖추고 있습니다.

### 고도화 핵심 방향
1. **역할 기반 접근 제어**: 의사, 간호사, 임상병리사 등 세분화된 권한
2. **환자 관리 시스템**: 차트 기반 환자 관리, 검사 이력 추적
3. **처방 워크플로우**: AI 권고 → 의료진 검토 → 전자서명 → 출력
4. **근거 기반 의사결정**: 논문/가이드라인 기반 권고, 근거수준 표시
5. **보안 및 규정 준수**: 감사 로그, 데이터 암호화, 접근 제어

### 예상 효과
- 의료진의 처방 의사결정 시간 단축
- 근거 기반 일관된 처방 권고
- 환자 교육 자료 자동화
- 의료 과실 위험 감소
- 규정 준수 용이

---

## 변경 이력

| 날짜 | 버전 | 변경 내용 |
|------|------|----------|
| 2025-01-23 | 1.0 | 최초 작성 |
| 2025-01-27 | 1.1 | 약사 역할 제외, 구현 완료 항목 표시, 우선순위 재정리 |
