# 관리자 시스템 설계 제안서

> 작성일: 2025-01-29
> 버전: 1.0

## 1. 개요

### 1.1 목적
- **super_admin** 역할의 플랫폼 관리자 전용 관리 기능 구현
- 알러젠 마스터 데이터, 논문, 사용자 정보의 중앙 집중 관리

### 1.2 대상 사용자
- 플랫폼 운영자 (super_admin 역할)
- 시스템 관리자

### 1.3 현재 역할 체계

| 역할 | 설명 | 접근 영역 |
|------|------|----------|
| patient | 환자 | /app/* (Consumer) |
| doctor | 의사 | /pro/* (Professional) |
| nurse | 간호사 | /pro/* (Professional) |
| lab_tech | 검사실 기사 | /pro/* (Professional) |
| hospital_admin | 병원 관리자 | /pro/* + 병원 설정 |
| **super_admin** | 플랫폼 관리자 | **/admin/*** (신규) |

---

## 2. 기능 설계

### 2.1 관리자 대시보드

```
/admin/dashboard
├── 시스템 현황 요약
│   ├── 총 사용자 수 (역할별)
│   ├── 총 진단 건수
│   ├── 논문 수집 현황
│   └── 최근 활동 로그
├── 빠른 링크
│   ├── 알러젠 관리
│   ├── 논문 관리
│   ├── 사용자 관리
│   └── 조직(병원) 관리
└── 알림/경고
    ├── 승인 대기 병원
    └── 시스템 오류 로그
```

### 2.2 알러젠 관리

```
/admin/allergens
├── 알러젠 목록 (120종)
│   ├── 카테고리별 필터
│   ├── 검색 (한글/영문/코드)
│   └── 페이지네이션
├── 알러젠 상세/수정
│   ├── 기본 정보 (코드, 이름, 카테고리)
│   ├── 설명 및 교차반응 정보
│   └── 처방 DB 연동 상태
├── 알러젠 추가 (신규)
└── 처방 정보 관리
    ├── 증상 정보
    ├── 회피 식품
    ├── 대체 식품
    └── 교차반응 정보
```

#### API 엔드포인트

| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | `/api/admin/allergens` | 알러젠 목록 조회 |
| GET | `/api/admin/allergens/{code}` | 알러젠 상세 조회 |
| PUT | `/api/admin/allergens/{code}` | 알러젠 수정 |
| POST | `/api/admin/allergens` | 알러젠 추가 |
| DELETE | `/api/admin/allergens/{code}` | 알러젠 삭제 |
| GET | `/api/admin/allergens/{code}/prescription` | 처방 정보 조회 |
| PUT | `/api/admin/allergens/{code}/prescription` | 처방 정보 수정 |
| GET | `/api/admin/allergens/stats` | 알러젠 통계 |

### 2.3 논문 관리

```
/admin/papers
├── 논문 목록
│   ├── 출처별 필터 (PubMed, Semantic Scholar, 수동)
│   ├── 가이드라인 여부
│   ├── 근거 수준 필터
│   └── 검색 (제목, 저자, DOI)
├── 논문 상세/수정
│   ├── 기본 정보 (제목, 저자, 저널, 연도)
│   ├── 초록 및 DOI/PMID
│   ├── 근거 수준 (GRADE)
│   └── 연결된 알러젠/진술문
├── 논문 추가
│   ├── 수동 입력
│   ├── PMID로 자동 가져오기
│   └── DOI로 자동 가져오기
├── 임상 진술문 관리
│   ├── 진술문 목록
│   ├── 진술문 추가/수정
│   └── 논문 연결
└── 논문 수집 작업
    ├── PubMed 검색 실행
    ├── Semantic Scholar 검색 실행
    └── 수집 이력 조회
```

#### API 엔드포인트

| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | `/api/admin/papers` | 논문 목록 조회 |
| GET | `/api/admin/papers/{id}` | 논문 상세 조회 |
| POST | `/api/admin/papers` | 논문 추가 |
| PUT | `/api/admin/papers/{id}` | 논문 수정 |
| DELETE | `/api/admin/papers/{id}` | 논문 삭제 |
| POST | `/api/admin/papers/fetch-pmid` | PMID로 논문 가져오기 |
| POST | `/api/admin/papers/fetch-doi` | DOI로 논문 가져오기 |
| GET | `/api/admin/papers/stats` | 논문 통계 |
| GET | `/api/admin/clinical-statements` | 임상 진술문 목록 |
| POST | `/api/admin/clinical-statements` | 진술문 추가 |
| PUT | `/api/admin/clinical-statements/{id}` | 진술문 수정 |

### 2.4 사용자 관리

```
/admin/users
├── 사용자 목록
│   ├── 역할별 필터
│   ├── 상태별 필터 (활성/비활성)
│   ├── 가입 유형 (Google/Simple)
│   └── 검색 (이름, 이메일, 전화번호)
├── 사용자 상세
│   ├── 기본 정보
│   ├── 역할 변경
│   ├── 활성/비활성 전환
│   ├── 소속 조직 정보
│   └── 진단 이력 (읽기 전용)
├── 역할별 대시보드
│   ├── 환자 (patient) 목록
│   ├── 의사 (doctor) 목록
│   ├── 병원 관리자 (hospital_admin) 목록
│   └── 플랫폼 관리자 (super_admin) 목록
└── 사용자 통계
    ├── 가입 추이
    ├── 역할별 분포
    └── 활동 현황
```

#### API 엔드포인트

| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | `/api/admin/users` | 사용자 목록 조회 |
| GET | `/api/admin/users/{id}` | 사용자 상세 조회 |
| PUT | `/api/admin/users/{id}` | 사용자 수정 |
| PUT | `/api/admin/users/{id}/role` | 역할 변경 |
| PUT | `/api/admin/users/{id}/status` | 상태 변경 |
| GET | `/api/admin/users/stats` | 사용자 통계 |
| GET | `/api/admin/users/{id}/diagnoses` | 진단 이력 조회 |

### 2.5 조직(병원) 관리

```
/admin/organizations
├── 조직 목록
│   ├── 상태별 필터 (승인대기/활성/비활성)
│   ├── 유형별 필터 (병원, 검사기관 등)
│   └── 검색
├── 조직 상세/수정
│   ├── 기본 정보
│   ├── 승인/반려 처리
│   ├── 소속 멤버 목록
│   └── 진단 통계
├── 조직 추가 (수동 등록)
└── 승인 대기 목록
```

#### API 엔드포인트

| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | `/api/admin/organizations` | 조직 목록 |
| GET | `/api/admin/organizations/{id}` | 조직 상세 |
| PUT | `/api/admin/organizations/{id}` | 조직 수정 |
| POST | `/api/admin/organizations/{id}/approve` | 조직 승인 |
| POST | `/api/admin/organizations/{id}/reject` | 조직 반려 |
| GET | `/api/admin/organizations/{id}/members` | 멤버 목록 |
| GET | `/api/admin/organizations/pending` | 승인 대기 목록 |

---

## 3. 기술 설계

### 3.1 백엔드 구조

```
backend/app/admin/
├── __init__.py
├── routes.py              # 메인 라우터
├── schemas.py             # Pydantic 스키마
├── dependencies.py        # 권한 체크 의존성
├── allergen/
│   ├── __init__.py
│   ├── routes.py          # 알러젠 API
│   └── service.py         # 알러젠 서비스
├── paper/
│   ├── __init__.py
│   ├── routes.py          # 논문 API
│   └── service.py         # 논문 서비스
├── user/
│   ├── __init__.py
│   ├── routes.py          # 사용자 API
│   └── service.py         # 사용자 서비스
└── organization/
    ├── __init__.py
    ├── routes.py          # 조직 API
    └── service.py         # 조직 서비스
```

### 3.2 프론트엔드 구조

```
frontend/src/apps/admin/
├── AdminApp.jsx           # 메인 앱
├── index.jsx              # 엔트리
├── components/
│   ├── AdminNav.jsx       # 네비게이션
│   ├── AdminSidebar.jsx   # 사이드바
│   └── StatCard.jsx       # 통계 카드
├── pages/
│   ├── AdminDashboard.jsx
│   ├── AllergenListPage.jsx
│   ├── AllergenDetailPage.jsx
│   ├── PaperListPage.jsx
│   ├── PaperDetailPage.jsx
│   ├── UserListPage.jsx
│   ├── UserDetailPage.jsx
│   ├── OrganizationListPage.jsx
│   └── OrganizationDetailPage.jsx
└── services/
    └── adminApi.js        # API 클라이언트
```

### 3.3 권한 체크

```python
# backend/app/admin/dependencies.py
from fastapi import Depends, HTTPException, status
from ..core.auth.dependencies import get_current_user
from ..database.models import User

async def require_super_admin(
    current_user: User = Depends(get_current_user)
) -> User:
    """super_admin 역할만 접근 허용"""
    if not current_user.is_admin_role():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="관리자 권한이 필요합니다."
        )
    return current_user
```

### 3.4 라우터 등록

```python
# backend/app/api/main.py
from ..admin.routes import router as admin_router

app.include_router(
    admin_router,
    prefix="/api/admin",
    tags=["Admin"]
)
```

---

## 4. 데이터베이스 변경

### 4.1 알러젠 마스터 테이블 (신규)

현재 Python 딕셔너리(`allergen_master.py`)를 DB 테이블로 이전:

```sql
CREATE TABLE allergen_master (
    id SERIAL PRIMARY KEY,
    code VARCHAR(20) UNIQUE NOT NULL,
    name_kr VARCHAR(100) NOT NULL,
    name_en VARCHAR(100) NOT NULL,
    category VARCHAR(30) NOT NULL,
    type VARCHAR(20) NOT NULL,
    description TEXT,
    note TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_allergen_code ON allergen_master(code);
CREATE INDEX idx_allergen_category ON allergen_master(category);
```

### 4.2 처방 정보 테이블 (신규)

현재 Python 딕셔너리(`allergen_prescription_db.py`)를 DB 테이블로 이전:

```sql
CREATE TABLE allergen_prescription (
    id SERIAL PRIMARY KEY,
    allergen_code VARCHAR(20) REFERENCES allergen_master(code),
    -- 증상 정보
    symptoms JSONB,
    -- 회피 식품
    avoidance_foods JSONB,
    -- 숨겨진 알러젠
    hidden_allergens JSONB,
    -- 대체 식품
    alternative_foods JSONB,
    -- 교차반응
    cross_reactions JSONB,
    -- 메타
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

### 4.3 관리자 활동 로그 테이블 (신규)

```sql
CREATE TABLE admin_activity_log (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    action VARCHAR(50) NOT NULL,
    target_type VARCHAR(50),
    target_id VARCHAR(50),
    details JSONB,
    ip_address VARCHAR(45),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_admin_log_user ON admin_activity_log(user_id);
CREATE INDEX idx_admin_log_action ON admin_activity_log(action);
CREATE INDEX idx_admin_log_created ON admin_activity_log(created_at);
```

---

## 5. 구현 우선순위

### Phase 1: 기본 구조 (1주)

| ID | 작업 | 우선순위 |
|----|------|----------|
| A1.1 | Admin 백엔드 모듈 구조 생성 | 필수 |
| A1.2 | super_admin 권한 체크 의존성 | 필수 |
| A1.3 | Admin 프론트엔드 앱 구조 생성 | 필수 |
| A1.4 | 관리자 대시보드 (기본 통계) | 필수 |

### Phase 2: 사용자 관리 (1주)

| ID | 작업 | 우선순위 |
|----|------|----------|
| A2.1 | 사용자 목록 API/UI | 높음 |
| A2.2 | 사용자 상세/수정 API/UI | 높음 |
| A2.3 | 역할 변경 기능 | 높음 |
| A2.4 | 사용자 통계 | 중간 |

### Phase 3: 알러젠 관리 (1~2주)

| ID | 작업 | 우선순위 |
|----|------|----------|
| A3.1 | allergen_master 테이블 생성 및 마이그레이션 | 필수 |
| A3.2 | allergen_prescription 테이블 생성 및 마이그레이션 | 필수 |
| A3.3 | 알러젠 CRUD API | 높음 |
| A3.4 | 알러젠 목록/상세 UI | 높음 |
| A3.5 | 처방 정보 편집 UI | 높음 |

### Phase 4: 논문 관리 (1~2주)

| ID | 작업 | 우선순위 |
|----|------|----------|
| A4.1 | 논문 CRUD API | 높음 |
| A4.2 | 논문 목록/상세 UI | 높음 |
| A4.3 | PMID/DOI 자동 가져오기 | 중간 |
| A4.4 | 임상 진술문 관리 | 중간 |

### Phase 5: 조직 관리 (1주)

| ID | 작업 | 우선순위 |
|----|------|----------|
| A5.1 | 조직 목록/상세 API/UI | 중간 |
| A5.2 | 승인/반려 기능 | 중간 |
| A5.3 | 조직별 통계 | 낮음 |

---

## 6. UI/UX 설계

### 6.1 레이아웃

```
┌─────────────────────────────────────────────────────────┐
│  AllergyInsight Admin            [사용자명] [로그아웃]   │
├──────────┬──────────────────────────────────────────────┤
│          │                                              │
│ 사이드바  │              메인 콘텐츠                     │
│          │                                              │
│ 📊 대시보드 │                                           │
│ 🧬 알러젠  │                                            │
│ 📄 논문   │                                             │
│ 👥 사용자 │                                             │
│ 🏥 조직   │                                             │
│          │                                              │
│ ──────── │                                              │
│ ⚙️ 설정  │                                              │
│          │                                              │
└──────────┴──────────────────────────────────────────────┘
```

### 6.2 색상 테마

| 역할 | 색상 | 용도 |
|------|------|------|
| Primary | #1976D2 (Blue) | 주요 버튼, 링크 |
| Secondary | #424242 (Dark Grey) | 사이드바 |
| Success | #4CAF50 (Green) | 승인, 활성 |
| Warning | #FF9800 (Orange) | 경고, 대기 |
| Error | #F44336 (Red) | 에러, 삭제 |

---

## 7. 접근 URL 체계

| URL | 용도 |
|-----|------|
| `/admin` | 관리자 대시보드 (리다이렉트) |
| `/admin/dashboard` | 대시보드 |
| `/admin/allergens` | 알러젠 목록 |
| `/admin/allergens/:code` | 알러젠 상세 |
| `/admin/papers` | 논문 목록 |
| `/admin/papers/:id` | 논문 상세 |
| `/admin/users` | 사용자 목록 |
| `/admin/users/:id` | 사용자 상세 |
| `/admin/organizations` | 조직 목록 |
| `/admin/organizations/:id` | 조직 상세 |

---

## 8. 보안 고려사항

1. **인증**: JWT 토큰 필수, super_admin 역할 검증
2. **권한**: 모든 API에 `require_super_admin` 의존성 적용
3. **로깅**: 모든 관리자 활동 기록 (admin_activity_log)
4. **민감 정보**: 비밀번호, PIN 해시값 노출 금지
5. **CSRF**: 상태 변경 API에 CSRF 토큰 적용 (선택)
6. **Rate Limiting**: API 호출 제한 (선택)

---

## 9. 예상 일정

| Phase | 기간 | 주요 산출물 |
|-------|------|------------|
| Phase 1 | 1주 | 기본 구조, 대시보드 |
| Phase 2 | 1주 | 사용자 관리 |
| Phase 3 | 1~2주 | 알러젠 관리, DB 마이그레이션 |
| Phase 4 | 1~2주 | 논문 관리 |
| Phase 5 | 1주 | 조직 관리 |
| **총계** | **5~7주** | |

---

## 10. WBS 연동

이 제안서의 작업들을 PROJECT_WBS.md에 추가해야 합니다:

```markdown
### 10. 관리자 시스템 [0%] ⏳

| ID | 작업 | 상태 | 진행율 | 우선순위 |
|----|------|------|--------|----------|
| 10.1 | Admin 모듈 기본 구조 | ⏳ | 0% | 높음 |
| 10.2 | 사용자 관리 기능 | ⏳ | 0% | 높음 |
| 10.3 | 알러젠 DB 마이그레이션 | ⏳ | 0% | 높음 |
| 10.4 | 알러젠 관리 기능 | ⏳ | 0% | 높음 |
| 10.5 | 논문 관리 기능 | ⏳ | 0% | 중간 |
| 10.6 | 조직 관리 기능 | ⏳ | 0% | 중간 |
```
