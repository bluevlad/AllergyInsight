# 병원 환자 관리 프로세스

## 개요

AllergyInsight에서 병원이 환자를 등록하고 관리하는 프로세스를 정의합니다.

---

## 1. 환자 등록 흐름

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   환자 등록      │────▶│   동의서 서명    │────▶│   담당의사 배정  │
│ (pending_consent)│     │     (active)     │     │    (active)     │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

### 1.1 환자 상태 (HospitalPatientStatus)

| 상태 | 설명 | 조건 |
|------|------|------|
| `pending_consent` | 동의 대기 | 환자 등록 직후, 동의서 미서명 |
| `active` | 활성 | 동의서 서명 완료, 정상 관리 중 |
| `inactive` | 비활성 | 치료 종료 또는 일시 중단 |
| `discharged` | 퇴원 | 병원 관계 종료 |

---

## 2. API 엔드포인트

### 2.1 환자 등록

#### 기존 사용자 등록
```http
POST /api/hospital/patients
Authorization: Bearer {token}
Content-Type: application/json

{
  "patient_user_id": 2,
  "patient_number": "P-2026-0001",
  "assigned_doctor_id": null
}
```

#### 신규 환자 등록 (사용자 생성 포함)
```http
POST /api/hospital/patients/new
Authorization: Bearer {token}
Content-Type: application/json

{
  "name": "홍길동",
  "phone": "010-1234-5678",
  "birth_date": "1990-01-15",
  "patient_number": "P-2026-0002",
  "assigned_doctor_id": null
}
```

### 2.2 환자 정보 수정 (담당의사 배정 포함)

```http
PUT /api/hospital/patients/{patient_id}
Authorization: Bearer {token}
Content-Type: application/json

{
  "patient_number": "P-2026-0001",
  "assigned_doctor_id": 1,
  "status": "active"
}
```

### 2.3 환자 동의서 서명

```http
POST /api/hospital/patients/{patient_id}/consent
Authorization: Bearer {token}  # 환자 본인 토큰
Content-Type: application/json

{
  "consent_agreed": true
}
```

### 2.4 환자 목록 조회

```http
GET /api/hospital/patients?status=active&assigned_doctor_id=1&page=1&page_size=20
Authorization: Bearer {token}
```

### 2.5 환자 상세 조회

```http
GET /api/hospital/patients/{patient_id}
Authorization: Bearer {token}
```

---

## 3. 담당의사 배정 프로세스

### 3.1 전제 조건

1. 의사가 해당 조직(병원)의 `OrganizationMember`로 등록되어 있어야 함
2. 의사의 역할(`role`)이 `doctor`이어야 함
3. 환자가 같은 조직에 `HospitalPatient`로 등록되어 있어야 함

### 3.2 배정 방법

#### 방법 1: 환자 등록 시 배정
```json
// POST /api/hospital/patients
{
  "patient_user_id": 2,
  "assigned_doctor_id": 1  // OrganizationMember.id
}
```

#### 방법 2: 기존 환자에게 배정
```json
// PUT /api/hospital/patients/{patient_id}
{
  "assigned_doctor_id": 1  // OrganizationMember.id
}
```

#### 방법 3: 직접 DB 수정 (관리자)
```sql
UPDATE hospital_patients
SET assigned_doctor_id = (
    SELECT om.id FROM organization_members om
    JOIN users u ON om.user_id = u.id
    WHERE u.name = '이의사' AND om.organization_id = 1
)
WHERE id = 1;
```

### 3.3 담당의사 조회

```sql
SELECT
    hp.id,
    u.name AS patient_name,
    doc.name AS doctor_name
FROM hospital_patients hp
JOIN users u ON hp.patient_user_id = u.id
LEFT JOIN organization_members om ON hp.assigned_doctor_id = om.id
LEFT JOIN users doc ON om.user_id = doc.id;
```

---

## 4. 데이터베이스 스키마

### 4.1 HospitalPatient 테이블

```sql
CREATE TABLE hospital_patients (
    id SERIAL PRIMARY KEY,
    organization_id INTEGER REFERENCES organizations(id),
    patient_user_id INTEGER REFERENCES users(id),
    patient_number VARCHAR(50),
    consent_signed BOOLEAN DEFAULT FALSE,
    consent_date TIMESTAMP,
    consent_document_url VARCHAR(500),
    assigned_doctor_id INTEGER REFERENCES organization_members(id),
    status VARCHAR(20) DEFAULT 'pending_consent',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP
);
```

### 4.2 OrganizationMember 테이블

```sql
CREATE TABLE organization_members (
    id SERIAL PRIMARY KEY,
    organization_id INTEGER REFERENCES organizations(id),
    user_id INTEGER REFERENCES users(id),
    role VARCHAR(20),  -- 'doctor', 'nurse', 'lab_tech', 'hospital_admin'
    is_active BOOLEAN DEFAULT TRUE,
    joined_at TIMESTAMP DEFAULT NOW()
);
```

---

## 5. 권한 체계

| 역할 | 환자 등록 | 환자 조회 | 담당의사 배정 | 동의서 서명 |
|------|----------|----------|--------------|------------|
| `doctor` | ✅ | ✅ | ✅ | ❌ |
| `nurse` | ✅ | ✅ | ❌ | ❌ |
| `lab_tech` | ❌ | ✅ (제한적) | ❌ | ❌ |
| `hospital_admin` | ✅ | ✅ | ✅ | ❌ |
| `patient` | ❌ | 본인만 | ❌ | ✅ (본인) |

---

## 6. 사용 예시

### 6.1 김철수 환자를 이의사에게 배정하는 전체 과정

```bash
# 1. 환자 등록 (병원 직원이 수행)
curl -X POST http://localhost:9040/api/hospital/patients \
  -H "Authorization: Bearer {staff_token}" \
  -H "Content-Type: application/json" \
  -d '{"patient_user_id": 2}'

# 2. 환자 동의서 서명 (환자 본인이 수행)
curl -X POST http://localhost:9040/api/hospital/patients/1/consent \
  -H "Authorization: Bearer {patient_token}" \
  -H "Content-Type: application/json" \
  -d '{"consent_agreed": true}'

# 3. 담당의사 배정 (의사 또는 관리자가 수행)
curl -X PUT http://localhost:9040/api/hospital/patients/1 \
  -H "Authorization: Bearer {doctor_token}" \
  -H "Content-Type: application/json" \
  -d '{"assigned_doctor_id": 1, "patient_number": "P-2026-0001"}'
```

---

## 7. 대시보드에서 확인

의사 대시보드 (`/pro/dashboard`)에서 다음 정보 확인 가능:

- **총 환자 수**: 담당 환자 전체
- **활성 환자 수**: `status = 'active'`인 환자
- **동의 대기 환자 수**: `status = 'pending_consent'`인 환자
- **최근 등록 환자 목록**: 최근 5명
- **최근 진단 목록**: 최근 5건

---

## 변경 이력

| 날짜 | 버전 | 내용 |
|------|------|------|
| 2026-01-26 | 1.0 | 최초 작성 |
