---
title: 도메인 모델 (Domain Model)
---

# 3. 도메인 모델 (Domain Model)

## 3.1 핵심 도메인 개념

### 유비쿼터스 언어 (Ubiquitous Language)

| 용어 (한글) | 용어 (영문) | 정의 |
|-------------|-------------|------|
| 알러젠 | Allergen | 알러지 반응을 유발하는 물질 (예: 땅콩, 우유) |
| 등급 | Grade | 알러젠에 대한 감작 정도 (0-6) |
| 진단 | Diagnosis | 환자의 알러젠별 등급 검사 결과 |
| 처방 권고 | Prescription | 진단 결과에 따른 권고 사항 |
| 회피 식품 | Avoid Foods | 섭취를 피해야 하는 식품 |
| 대체 식품 | Substitutes | 회피 식품 대신 섭취 가능한 식품 |
| 교차반응 | Cross Reactivity | 다른 알러젠에도 반응할 확률 |
| 숨겨진 알러젠 | Hidden Sources | 예상치 못한 곳에 포함된 알러젠 |
| 키트 | Kit | 검사에 사용되는 진단 키트 |
| 임상 진술문 | Clinical Statement | GRADE 근거 기반 의학적 진술 |
| 뉴스레터 | Newsletter | 정기 발송 알러지 관련 뉴스 |
| 트렌드 | Trend | 알러젠별 시간에 따른 연구/뉴스 동향 |

### 도메인 영역

``` mermaid
block-beta
  columns 3
  block:core["Core Domain"]:1
    A["진단 관리"]
    B["처방 엔진"]
    C["알러젠 지식"]
    D["임상 보고서"]
  end
  block:support["Supporting Domain"]:1
    E["환자 관리"]
    F["조직 관리"]
    G["논문 관리"]
    H["키트 관리"]
    I["뉴스 파이프라인"]
    J["뉴스레터"]
    K["트렌드 분석"]
  end
  block:generic["Generic Domain"]:1
    L["사용자 인증"]
    M["파일 저장"]
    N["알림"]
    O["로깅"]
    P["이메일 발송"]
    Q["스케줄링"]
  end
```

---

## 3.2 ER 다이어그램

### 전체 ER 다이어그램

``` mermaid
erDiagram
    User {
        int id PK
        string name
        string email
        string phone
        date birth_date
        string role
        string access_pin
        bool is_active
        datetime created_at
    }

    Organization {
        int id PK
        string name
        string type
        string address
        string phone
        int admin_user_id FK
        string status
        datetime created_at
    }

    UserDiagnosis {
        int id PK
        int user_id FK
        date diagnosis_date
        json results
        json summary
        datetime created_at
    }

    OrganizationMember {
        int id PK
        int org_id FK
        int user_id FK
        string role
        datetime joined_at
    }

    DiagnosisKit {
        int id PK
        string serial_number
        string pin_hash
        string status
        date test_date
        int diagnosis_id FK
        int registered_by
        datetime created_at
    }

    HospitalPatient {
        int id PK
        int org_id FK
        int user_id FK
        string patient_number
        string assigned_doctor
        bool consent_signed
        datetime registered_at
    }

    Paper {
        int id PK
        string title
        string authors
        string journal
        int year
        string doi
        text abstract
        string paper_type
        string evidence_level
        bool is_guideline
        string guideline_org
        datetime created_at
    }

    PaperAllergenLink {
        int id PK
        int paper_id FK
        string allergen_code
        string link_type
        string item_name
        float confidence
        datetime created_at
    }

    ClinicalStatement {
        int id PK
        string statement_en
        string statement_kr
        string allergen_code
        string context
        string evidence_level
        string recommendation
        int paper_id FK
        string source_location
        bool is_active
        datetime created_at
    }

    User ||--o{ UserDiagnosis : "has"
    User ||--o{ OrganizationMember : "belongs to"
    Organization ||--o{ OrganizationMember : "has"
    Organization ||--o{ HospitalPatient : "manages"
    Organization }o--|| User : "admin"
    UserDiagnosis ||--o| DiagnosisKit : "from"
    Paper ||--o{ PaperAllergenLink : "links"
    Paper ||--o{ ClinicalStatement : "sources"
```

### Analytics & News 모델

``` mermaid
erDiagram
    AllergenTrend {
        int id PK
        string allergen_code
        string year_month
        int paper_count
        float mention_ratio
        datetime created_at
    }

    KeywordTrend {
        int id PK
        string keyword
        string year_month
        int paper_count
        float frequency
        datetime created_at
    }

    TreatmentTrend {
        int id PK
        string allergen_code
        string treatment_name
        string treatment_type
        string year_month
        int paper_count
        datetime created_at
    }

    EpidemiologyData {
        int id PK
        string allergen_code
        string data_type
        float value
        string region
        int year
        int source_paper_id
        datetime created_at
    }

    CompetitorNews {
        int id PK
        string title
        string source
        string url
        datetime published_at
        text summary
        float relevance_score
        float importance_score
        json allergen_codes
        int category_id FK
        datetime created_at
    }

    NewsCategory {
        int id PK
        string name
        string description
        datetime created_at
    }

    CompetitorNews }o--|| NewsCategory : "categorized"
```

### Newsletter 모델

``` mermaid
erDiagram
    Subscriber {
        int id PK
        string email
        string name
        json keywords
        bool is_verified
        string verify_code
        string status
        datetime subscribed_at
        datetime unsubscribed_at
        datetime created_at
    }

    Newsletter {
        int id PK
        string subject
        text content_html
        datetime sent_at
        int recipient_count
        datetime created_at
    }

    SchedulerJob {
        int id PK
        string job_type
        string status
        datetime last_run_at
        datetime next_run_at
        json result
        datetime created_at
    }
```

### Activity Logging 모델

``` mermaid
erDiagram
    ActivityLog {
        int id PK
        int user_id FK
        string action
        string resource_type
        string resource_id
        json details
        string ip_address
        string user_agent
        datetime created_at
    }

    User ||--o{ ActivityLog : "generates"
```

### 관계 요약

| 관계 | 설명 |
|------|------|
| User -> UserDiagnosis | 1:N (한 사용자가 여러 진단 보유) |
| User -> OrganizationMember | 1:N (한 사용자가 여러 조직 소속 가능) |
| Organization -> OrganizationMember | 1:N (한 조직에 여러 멤버) |
| Organization -> HospitalPatient | 1:N (한 병원에 여러 환자) |
| UserDiagnosis -> DiagnosisKit | 1:1 (하나의 키트로 하나의 진단) |
| Paper -> PaperAllergenLink | 1:N (한 논문이 여러 알러젠 연결) |
| Paper -> ClinicalStatement | 1:N (한 논문에서 여러 임상 진술문) |
| CompetitorNews -> NewsCategory | N:1 (여러 뉴스가 하나의 카테고리) |
| User -> ActivityLog | 1:N (한 사용자의 여러 활동 기록) |

---

## 3.3 엔티티 명세

### User (사용자)

```python
class User(Base):
    __tablename__ = "users"

    id: int                    # Primary Key
    name: str                  # 이름 (필수)
    email: str | None          # 이메일 (Google OAuth / Email Auth)
    phone: str | None          # 전화번호 (간편 인증 시)
    birth_date: date | None    # 생년월일
    role: UserRole             # 역할 (Enum)
    google_id: str | None      # Google OAuth ID
    access_pin: str | None     # 접속 PIN (해시)
    password_hash: str | None  # 이메일 로그인 비밀번호 (해시)
    is_active: bool            # 활성 상태
    created_at: datetime       # 생성일시
    updated_at: datetime       # 수정일시
```

#### UserRole Enum

| 값 | 설명 | Professional | Consumer | Admin | Public |
|----|------|-------------|----------|-------|--------|
| `patient` | 환자 | :x: | :white_check_mark: | :x: | :white_check_mark: |
| `doctor` | 의사 | :white_check_mark: | :white_check_mark: | :x: | :white_check_mark: |
| `nurse` | 간호사 | :white_check_mark: | :white_check_mark: | :x: | :white_check_mark: |
| `lab_tech` | 검사 기사 | :white_check_mark: (제한) | :white_check_mark: | :x: | :white_check_mark: |
| `hospital_admin` | 병원 관리자 | :white_check_mark: | :white_check_mark: | :white_check_mark: (병원) | :white_check_mark: |
| `admin` | 시스템 관리자 | :white_check_mark: | :white_check_mark: | :white_check_mark: | :white_check_mark: |
| `super_admin` | 슈퍼 관리자 | :white_check_mark: | :white_check_mark: | :white_check_mark: | :white_check_mark: |

### ClinicalStatement (임상 진술문)

```python
class ClinicalStatement(Base):
    __tablename__ = "clinical_statements"

    id: int                        # Primary Key
    statement_en: str              # 영문 원문
    statement_kr: str | None       # 한국어 번역
    allergen_code: str | None      # 알러젠 코드
    context: str                   # cross_reactivity, avoidance, treatment, diagnosis, pathophysiology
    evidence_level: str | None     # GRADE 근거 수준 (A, B, C, D)
    recommendation_grade: str | None # 권고 강도 (1A, 1B, 2A, 2B)
    paper_id: int | None           # 출처 논문 (FK → Paper)
    source_location: str | None    # 출처 위치
    is_active: bool                # 활성 여부
    created_at: datetime           # 생성일시
```

#### GRADE 근거 수준 체계

!!! info "GRADE (Grading of Recommendations Assessment, Development and Evaluation)"

    임상 진술문의 근거 수준은 국제 GRADE 체계를 따릅니다.

| 등급 | 표시 | 의미 | 설명 |
|------|------|------|------|
| A | :material-circle:{ .grade-a } :material-circle:{ .grade-a } :material-circle:{ .grade-a } :material-circle:{ .grade-a } | High | 추가 연구가 결론을 바꿀 가능성 매우 낮음 |
| B | :material-circle:{ .grade-b } :material-circle:{ .grade-b } :material-circle:{ .grade-b } :material-circle-outline: | Moderate | 추가 연구가 결론에 영향을 줄 수 있음 |
| C | :material-circle:{ .grade-c } :material-circle:{ .grade-c } :material-circle-outline: :material-circle-outline: | Low | 추가 연구가 결론을 바꿀 가능성 높음 |
| D | :material-circle:{ .grade-d } :material-circle-outline: :material-circle-outline: :material-circle-outline: | Very Low | 불확실성 매우 높음 |

---

## 3.4 비즈니스 규칙

### 등급 체계 (Grade System)

!!! warning "임상 등급 체계"

    IgE 수치에 따른 등급 분류는 진단 및 처방 권고의 핵심 기준입니다.

| 등급 | IgE 수치 | 임상적 의미 | 권고 수준 |
|------|----------|-------------|----------|
| 0 | < 0.35 | 음성 | 제한 없음 |
| 1 | 0.35 - 0.69 | 경계 | 모니터링 |
| 2 | 0.70 - 3.49 | 약양성 | 주의 섭취 |
| 3 | 3.50 - 17.49 | 양성 | 제한 섭취 |
| 4 | 17.50 - 49.99 | 강양성 | 회피 권고 |
| 5 | 50.00 - 99.99 | 매우 강양성 | 완전 회피 |
| 6 | >= 100.00 | 극강양성 | 완전 회피 + 응급약 휴대 |

### 알러젠 분류

| 카테고리 | 알러젠 |
|----------|--------|
| **식품 (Food)** | 땅콩, 우유, 계란, 밀, 대두, 생선, 갑각류, 견과류, 참깨 |
| **흡입 (Inhalant)** | 집먼지진드기, 고양이, 개, 바퀴벌레, 곰팡이, 꽃가루, 쑥 |

### 뉴스 품질 게이트

!!! tip "환경 변수로 임계값 조정 가능"

    뉴스 수집 시 LLM 평가 점수가 임계값 미만이면 자동 필터링됩니다.

| 기준 | 환경 변수 | 기본값 | 설명 |
|------|----------|--------|------|
| 관련도 | `NEWS_RELEVANCE_THRESHOLD` | 0.3 | LLM 평가 관련도 최소값 |
| 중요도 | `NEWS_IMPORTANCE_THRESHOLD` | 0.2 | LLM 평가 중요도 최소값 |

---

## 3.5 상태 다이어그램

### DiagnosisKit 상태 전이

``` mermaid
stateDiagram-v2
    [*] --> created : 키트 생성
    created --> tested : 검사 수행
    tested --> result_entered : 결과 입력
    result_entered --> registered : 사용자 등록

    created --> expired : 유효기간 초과
    tested --> expired : 유효기간 초과
    result_entered --> expired : 유효기간 초과
```

### Subscriber 상태 전이

``` mermaid
stateDiagram-v2
    [*] --> pending : 이메일 제출 (미인증)
    pending --> active : 인증 코드 확인
    active --> unsubscribed : 구독 해지
```

---

## 3.6 집계 (Aggregates)

### User Aggregate

``` mermaid
graph TD
    subgraph UserAggregate["User Aggregate"]
        User["User<br/><i>Aggregate Root</i>"]
        Diagnoses["Diagnoses"]
        Kit["DiagnosisKit"]
        Activity["Activity Logs"]

        User --> Diagnoses
        Diagnoses --> Kit
        User --> Activity
    end

    style User fill:#4051b5,color:#fff
```

### Analytics Aggregate

``` mermaid
graph TD
    subgraph AnalyticsAggregate["Analytics Aggregate"]
        AllergenTrend["AllergenTrend<br/><i>Aggregate Root</i>"]
        KeywordTrend["KeywordTrend"]
        TreatmentTrend["TreatmentTrend"]
        Epidemiology["EpidemiologyData"]

        AllergenTrend --> KeywordTrend
        AllergenTrend --> TreatmentTrend
        KeywordTrend --> Epidemiology
    end

    style AllergenTrend fill:#4051b5,color:#fff
```

---

[← 아키텍처](architecture.md) | [다음: API 명세 →](api-specification.md)
