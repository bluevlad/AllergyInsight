# AllergyInsight 병원 서비스 확장 로드맵

## 개요

AllergyInsight를 일반 사용자(B2C) 서비스에서 병원/의료기관 대상(B2B) 서비스로 확장하기 위한 개발 로드맵입니다.

---

## 현재 구조 분석

| 항목 | 현재 상태 |
|------|----------|
| **역할 체계** | 2단계 (user, admin) |
| **멀티테넌트** | 미구현 (단일 DB) |
| **인증** | Google OAuth + PIN 기반 |
| **데이터 격리** | 없음 |

---

## 1. 역할(Role) 체계 확장

### 확장된 역할 구조

```
┌─────────────────────────────────────────┐
│ 일반 서비스 (B2C)                        │
├─────────────────────────────────────────┤
│ • patient (환자/일반 사용자)              │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│ 병원 서비스 (B2B)                        │
├─────────────────────────────────────────┤
│ • hospital_admin (병원 관리자)           │
│ • doctor (의사)                          │
│ • nurse (간호사)                         │
│ • lab_tech (검사 담당자)                 │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│ 플랫폼 운영 (System)                     │
├─────────────────────────────────────────┤
│ • super_admin (시스템 관리자)            │
└─────────────────────────────────────────┘
```

### 권한 매트릭스

| 기능 | patient | doctor | nurse | lab_tech | hospital_admin | super_admin |
|------|---------|--------|-------|----------|----------------|-------------|
| 본인 진단 조회 | O | - | - | - | - | O |
| 환자 진단 조회 | X | O | O | O | O | O |
| 진단 입력 | X | O | O | O | X | O |
| 처방 작성 | X | O | X | X | X | O |
| 직원 관리 | X | X | X | X | O | O |
| 병원 통계 | X | O | O | X | O | O |
| 플랫폼 관리 | X | X | X | X | X | O |

---

## 2. 멀티테넌트 구조

### 새로운 데이터베이스 모델

```
┌──────────────────────────────────────────────────┐
│ ORGANIZATIONS (병원/기관)                         │
├──────────────────────────────────────────────────┤
│ id, name, org_type (hospital/clinic/research)    │
│ business_number, license_number                  │
│ address, phone, email                            │
│ subscription_plan, is_active                     │
│ created_at, expires_at                           │
└──────────────────────────────────────────────────┘
           │
           │ 1:N
           ▼
┌──────────────────────────────────────────────────┐
│ ORGANIZATION_MEMBERS (기관 소속 직원)             │
├──────────────────────────────────────────────────┤
│ id, organization_id (FK), user_id (FK)           │
│ role (doctor/nurse/lab_tech/hospital_admin)      │
│ department, employee_number                      │
│ license_number (의사면허 등)                     │
│ joined_at, is_active                             │
└──────────────────────────────────────────────────┘
           │
           │ 1:N
           ▼
┌──────────────────────────────────────────────────┐
│ HOSPITAL_PATIENTS (병원-환자 연결)                │
├──────────────────────────────────────────────────┤
│ id, organization_id, patient_user_id             │
│ patient_number (병원 내 환자번호)                 │
│ consent_signed, consent_date                     │
│ assigned_doctor_id                               │
│ status (active/inactive/transferred)             │
│ created_at, updated_at                           │
└──────────────────────────────────────────────────┘
```

### 데이터 격리 전략

애플리케이션 레벨 필터링 방식 채택:

```python
def get_organization_patients(db, current_user):
    member = get_org_membership(db, current_user.id)
    if not member:
        raise HTTPException(403, "조직에 소속되어 있지 않습니다")

    return db.query(HospitalPatient).filter(
        HospitalPatient.organization_id == member.organization_id
    ).all()
```

---

## 3. 개발 단계별 로드맵

### Phase 1: 기반 구축 ✅ 완료

- [x] 개발 로드맵 문서 작성
- [x] Organization 모델 추가
- [x] OrganizationMember 모델 추가
- [x] HospitalPatient 모델 추가
- [x] UserRole enum 정의 및 역할 체계 확장
- [x] 권한 미들웨어 리팩토링
- [x] Organization CRUD API 구현
- [x] 병원 관리자 가입 플로우 구현

### Phase 2: 핵심 기능 ✅ 완료

- [x] 병원-환자 연결 시스템
- [x] 환자 동의서 관리
- [x] 병원 대시보드 UI
- [x] 환자 목록/검색 기능
- [ ] 진단 워크플로우 (검체 접수 → 결과 입력 → 의사 검토) - 기본 구현 완료, 고도화 예정

### Phase 3: 고급 기능

- [ ] 통계 및 리포트 생성
- [ ] PDF 내보내기
- [ ] SMS/이메일 알림 시스템
- [ ] 결제/구독 시스템

### Phase 4: 확장 및 연동

- [ ] 병원 EMR/HIS 시스템 API 연동
- [ ] 검사 장비 연동 (S-Blot 결과 자동 입력)
- [ ] 다국어 지원

---

## 4. 기술 아키텍처

### 백엔드 구조 변경

```
backend/
├── app/
│   ├── api/main.py
│   ├── auth/
│   │   ├── dependencies.py      # 권한 미들웨어 확장
│   │   └── ...
│   ├── patient/                  # 일반 사용자 기능 (기존)
│   │   └── routes.py
│   ├── hospital/                 # 병원 전용 기능 (신규)
│   │   ├── __init__.py
│   │   ├── routes.py            # 병원 기본 API
│   │   ├── patient_routes.py    # 환자 관리 API
│   │   ├── member_routes.py     # 직원 관리 API
│   │   ├── report_routes.py     # 리포트 API
│   │   └── schemas.py
│   ├── organization/             # 조직 관리 (신규)
│   │   ├── __init__.py
│   │   ├── routes.py
│   │   ├── schemas.py
│   │   └── service.py
│   └── database/
│       └── models.py            # 새 모델 추가
```

### 프론트엔드 구조 변경

```
frontend/src/
├── pages/
│   ├── patient/                  # 기존 일반 사용자
│   │   ├── MyDiagnosisPage.jsx
│   │   └── ...
│   ├── hospital/                 # 병원 전용 (신규)
│   │   ├── HospitalDashboard.jsx
│   │   ├── PatientListPage.jsx
│   │   ├── PatientDetailPage.jsx
│   │   ├── DiagnosisInputPage.jsx
│   │   ├── StaffManagementPage.jsx
│   │   └── ReportsPage.jsx
│   └── admin/                    # 플랫폼 관리자
└── contexts/
    ├── AuthContext.jsx           # 역할 확장
    └── OrganizationContext.jsx   # 조직 컨텍스트 (신규)
```

---

## 5. 보안 및 규정 준수

### 의료 데이터 보안 체크리스트

- [ ] 개인정보보호법 준수
- [ ] 의료법 시행규칙 준수
- [ ] 환자 동의서 관리 시스템
- [ ] 접근 로그 기록 (감사 추적)
- [ ] 데이터 암호화 (저장 시, 전송 시)
- [ ] 세션 타임아웃 강화 (의료 환경)
- [ ] IP 화이트리스트 (병원 전용)

### 감사 로그 요구사항

```
필수 기록 항목:
- 환자 정보 조회 시점 및 조회자
- 진단 결과 입력/수정 이력
- 처방 작성/수정 이력
- 권한 변경 이력
```

---

## 6. API 엔드포인트 설계

### 조직 관리 API

```
POST   /api/organizations              # 조직 생성 (super_admin)
GET    /api/organizations              # 조직 목록 (super_admin)
GET    /api/organizations/{id}         # 조직 상세
PUT    /api/organizations/{id}         # 조직 수정
DELETE /api/organizations/{id}         # 조직 삭제 (soft delete)
```

### 조직 멤버 관리 API

```
POST   /api/organizations/{org_id}/members       # 멤버 추가
GET    /api/organizations/{org_id}/members       # 멤버 목록
PUT    /api/organizations/{org_id}/members/{id}  # 멤버 수정
DELETE /api/organizations/{org_id}/members/{id}  # 멤버 제거
```

### 병원 환자 관리 API

```
POST   /api/hospital/patients                    # 환자 등록
GET    /api/hospital/patients                    # 환자 목록
GET    /api/hospital/patients/{id}               # 환자 상세
PUT    /api/hospital/patients/{id}               # 환자 정보 수정
POST   /api/hospital/patients/{id}/consent       # 동의서 등록
GET    /api/hospital/patients/{id}/diagnoses     # 환자 진단 이력
```

### 병원 진단 관리 API

```
POST   /api/hospital/diagnoses                   # 진단 결과 입력
GET    /api/hospital/diagnoses                   # 진단 목록 (필터링)
GET    /api/hospital/diagnoses/{id}              # 진단 상세
PUT    /api/hospital/diagnoses/{id}/review       # 의사 검토/소견
```

---

## 7. 환자 연결 플로우

```
1. [병원] 환자 기본 정보 입력 (이름, 연락처)
2. [시스템] 환자에게 SMS로 동의서 링크 발송
3. [환자] 모바일에서 동의서 확인 및 서명
4. [시스템] 동의 완료 시 연결 활성화
5. [병원] 환자의 기존 진단 데이터 조회 가능
6. [환자] 병원에서 입력한 새 진단 결과 확인 가능
```

---

## 8. 구독 플랜 (향후)

| 플랜 | 월 요금 | 직원 수 | 환자 수 | 기능 |
|------|--------|--------|--------|------|
| Basic | 50,000원 | 5명 | 500명 | 기본 기능 |
| Professional | 150,000원 | 20명 | 2,000명 | + 리포트, 통계 |
| Enterprise | 별도 협의 | 무제한 | 무제한 | + API 연동, 커스터마이징 |

---

## 변경 이력

| 날짜 | 버전 | 내용 |
|------|------|------|
| 2025-01-25 | 1.0 | 초기 로드맵 작성 |
| 2025-01-25 | 1.1 | Phase 1 완료 - 조직 관리 기반 구축 |
| 2025-01-25 | 1.2 | Phase 2 완료 - 환자 관리 시스템 구현 |
