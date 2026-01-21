# AllergyInsight 기술 구현 문서

이 문서는 AllergyInsight 프로젝트의 기술적 구현 상세를 다룹니다.

---

## 시스템 아키텍처

```
┌─────────────────────────────────────────────────────────────┐
│                        Frontend                              │
│                   (React + Vite, Port 4040)                  │
├─────────────────────────────────────────────────────────────┤
│  Login │ Dashboard │ Search │ Q&A │ MyDiagnosis │ Papers    │
└──────────────────────────┬──────────────────────────────────┘
                           │ HTTP/REST API + JWT Auth
┌──────────────────────────▼──────────────────────────────────┐
│                     Backend API                              │
│                 (FastAPI, Port 9040)                         │
├─────────────────────────────────────────────────────────────┤
│  /auth/*  │  /api/stats  │  /api/search  │  /api/diagnosis  │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│                      Services                                │
├────────────┬────────────┬────────────┬────────────┬─────────┤
│  Auth      │  PubMed    │  Semantic  │  Paper     │  Batch  │
│  (OAuth/PIN)│  Service   │  Scholar   │  Extractor │ Process │
└────────────┴────────────┴────────────┴────────────┴─────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│                   Data Layer                                 │
├─────────────────────────┬───────────────────────────────────┤
│  PostgreSQL (Port 5432) │  External APIs (PubMed, S2)       │
│  Users, Kits, Diagnoses │  NIH/NCBI, Allen Institute        │
└─────────────────────────┴───────────────────────────────────┘
```

---

## 기술 스택

### Backend

| 기술 | 버전 | 용도 |
|------|------|------|
| Python | 3.10+ | 메인 언어 |
| FastAPI | 0.109.0 | REST API 프레임워크 |
| Uvicorn | 0.27.0 | ASGI 서버 |
| SQLAlchemy | 2.0.25 | ORM |
| PostgreSQL | 15 | 관계형 데이터베이스 |
| bcrypt | - | 비밀번호 해싱 |
| python-jose | 3.3.0 | JWT 토큰 |
| authlib | 1.3.0 | OAuth 인증 |
| Pydantic | 2.5.3 | 데이터 검증 |

### Frontend

| 기술 | 버전 | 용도 |
|------|------|------|
| React | 18.2.0 | UI 프레임워크 |
| Vite | 5.4.2 | 빌드 도구 |
| React Router | 6.22.0 | 라우팅 |
| Recharts | 2.12.0 | 차트 시각화 |
| Axios | 1.6.7 | HTTP 클라이언트 |

### Infrastructure

| 기술 | 버전 | 용도 |
|------|------|------|
| Docker | - | 컨테이너화 |
| Docker Compose | - | 멀티 컨테이너 관리 |
| PostgreSQL | 15-alpine | 데이터베이스 |

---

## 프로젝트 구조

```
AllergyInsight/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── main.py              # FastAPI 애플리케이션
│   │   ├── auth/                    # 인증 모듈
│   │   │   ├── routes.py            # 인증 라우트
│   │   │   ├── schemas.py           # Pydantic 스키마
│   │   │   ├── jwt_handler.py       # JWT 처리
│   │   │   ├── dependencies.py      # 인증 의존성
│   │   │   ├── diagnosis_routes.py  # 진단 라우트
│   │   │   └── paper_routes.py      # 논문 관리 라우트
│   │   ├── database/                # 데이터베이스 모듈
│   │   │   ├── connection.py        # DB 연결
│   │   │   ├── models.py            # SQLAlchemy 모델
│   │   │   └── seed_papers.py       # 샘플 논문 데이터
│   │   ├── data/
│   │   │   ├── allergen_prescription_db.py  # 알러젠 처방 정보
│   │   │   └── paper_keywords.py    # 논문 키워드 사전
│   │   ├── models/
│   │   │   └── paper.py             # 도메인 모델
│   │   └── services/
│   │       ├── pubmed_service.py    # PubMed API
│   │       ├── semantic_scholar_service.py  # Semantic Scholar API
│   │       ├── paper_search_service.py      # 통합 검색
│   │       └── paper_link_extractor.py      # 키워드 자동 추출
│   ├── Dockerfile
│   ├── requirements.txt
│   └── README.md
├── frontend/
│   ├── src/
│   │   ├── contexts/
│   │   │   └── AuthContext.jsx      # 인증 상태 관리
│   │   ├── pages/
│   │   │   ├── LoginPage.jsx        # 로그인 페이지
│   │   │   ├── MyDiagnosisPage.jsx  # 내 진단 결과
│   │   │   ├── DiagnosisPage.jsx    # 진단 입력
│   │   │   ├── Dashboard.jsx        # 대시보드
│   │   │   ├── SearchPage.jsx       # 논문 검색
│   │   │   ├── PapersPage.jsx       # 논문 목록
│   │   │   └── QAPage.jsx           # Q&A
│   │   ├── services/
│   │   │   └── api.js               # API 클라이언트
│   │   └── App.jsx                  # 메인 앱 (라우팅)
│   ├── Dockerfile
│   ├── package.json
│   └── README.md
├── docs/
│   ├── IMPLEMENTATION.md            # 기술 구현 문서 (이 문서)
│   └── PAPER_LINK_EXTRACTION_ROADMAP.md  # 논문 링크 추출 고도화
├── docker-compose.yml               # Docker 멀티 컨테이너 설정
├── .env.example                     # 환경변수 예시
└── README.md                        # 프로젝트 개요
```

---

## API 엔드포인트

### 인증 (Authentication)

| 메서드 | 경로 | 설명 |
|--------|------|------|
| GET | `/auth/google/login` | Google OAuth 로그인 |
| GET | `/auth/google/callback` | Google OAuth 콜백 |
| POST | `/auth/simple/register` | 간편 회원가입 |
| POST | `/auth/simple/login` | 간편 로그인 |
| GET | `/auth/me` | 현재 사용자 정보 |
| POST | `/auth/register-kit` | 진단 키트 등록 |

### 진단 (Diagnosis)

| 메서드 | 경로 | 설명 |
|--------|------|------|
| GET | `/api/diagnosis/my` | 내 진단 목록 |
| GET | `/api/diagnosis/my/{id}` | 진단 상세 |
| GET | `/api/diagnosis/my/{id}/patient-guide` | 환자 가이드 (증상, 식이, 응급) |
| GET | `/api/diagnosis/allergen-info` | 알러젠 정보 |
| POST | `/api/admin/diagnosis` | 진단 결과 입력 (관리자) |

### 논문 (Papers)

| 메서드 | 경로 | 설명 |
|--------|------|------|
| POST | `/api/papers` | 논문 저장 (자동 링크 추출) |
| GET | `/api/papers` | 논문 목록 (필터링, 페이징) |
| GET | `/api/papers/{id}` | 논문 상세 |
| POST | `/api/papers/{id}/extract-links` | 기존 논문 링크 추출 |
| POST | `/api/papers/extract-links/batch` | 일괄 링크 추출 |
| GET | `/api/papers/citations/{allergen}` | 알러젠별 출처 |
| GET | `/api/papers/citations/by-specific-item` | 특정 항목별 출처 |

### 검색 (Search)

| 메서드 | 경로 | 설명 |
|--------|------|------|
| POST | `/api/search` | 논문 검색 (PubMed + Semantic Scholar) |
| GET | `/api/allergens` | 알러지 항원 목록 |

### Q&A

| 메서드 | 경로 | 설명 |
|--------|------|------|
| POST | `/api/qa` | 질문-답변 |
| GET | `/api/qa/questions/{allergen}` | 사전 정의 질문 |

### 통계

| 메서드 | 경로 | 설명 |
|--------|------|------|
| GET | `/api/health` | 서버 상태 |
| GET | `/api/stats` | 전체 통계 |
| GET | `/api/stats/summary` | 대시보드용 요약 |

> 전체 API 문서는 http://localhost:9040/docs 에서 확인

---

## 데이터베이스 스키마

### Users

| 컬럼 | 타입 | 설명 |
|------|------|------|
| id | SERIAL | PK |
| name | VARCHAR(100) | 사용자 이름 |
| email | VARCHAR(255) | 이메일 (OAuth) |
| phone | VARCHAR(20) | 전화번호 (간편 로그인) |
| auth_type | VARCHAR(20) | 인증 유형 (google/simple) |
| role | VARCHAR(20) | 역할 (user/admin) |
| access_pin_hash | VARCHAR(255) | PIN 해시 |
| is_active | BOOLEAN | 활성 상태 |

### UserDiagnosis

| 컬럼 | 타입 | 설명 |
|------|------|------|
| id | SERIAL | PK |
| user_id | INTEGER | FK → Users |
| kit_id | INTEGER | FK → DiagnosisKit |
| results | JSONB | 알러젠별 등급 (0-6) |
| prescription | JSONB | 처방 권고 |
| diagnosis_date | DATE | 검사 날짜 |

### Paper

| 컬럼 | 타입 | 설명 |
|------|------|------|
| id | SERIAL | PK |
| pmid | VARCHAR(20) | PubMed ID |
| doi | VARCHAR(100) | DOI |
| title | TEXT | 제목 (영문) |
| title_kr | TEXT | 제목 (한글) |
| abstract | TEXT | 초록 |
| authors | TEXT | 저자 |
| journal | VARCHAR(255) | 저널명 |
| year | INTEGER | 출판연도 |
| paper_type | VARCHAR(50) | 논문 유형 |
| is_verified | BOOLEAN | 검증 여부 |

### PaperAllergenLink

| 컬럼 | 타입 | 설명 |
|------|------|------|
| id | SERIAL | PK |
| paper_id | INTEGER | FK → Paper |
| allergen_code | VARCHAR(50) | 알러젠 코드 |
| link_type | VARCHAR(50) | 링크 유형 (symptom/dietary/...) |
| specific_item | VARCHAR(200) | 구체적 항목 (한글) |
| relevance_score | INTEGER | 관련도 점수 (0-100) |

---

## 환경변수

| 변수명 | 설명 | 기본값 |
|--------|------|--------|
| `DATABASE_URL` | PostgreSQL 연결 문자열 | - |
| `JWT_SECRET_KEY` | JWT 서명 키 | - |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | 토큰 만료 시간 | 60 |
| `GOOGLE_CLIENT_ID` | Google OAuth 클라이언트 ID | - |
| `GOOGLE_CLIENT_SECRET` | Google OAuth 시크릿 | - |
| `FRONTEND_URL` | 프론트엔드 URL | http://localhost:4040 |
| `BACKEND_URL` | 백엔드 URL | http://localhost:9040 |
| `PUBMED_API_KEY` | PubMed API 키 (선택) | - |
| `SEMANTIC_SCHOLAR_API_KEY` | Semantic Scholar API 키 (선택) | - |

---

## 로컬 개발 환경

### 사전 요구사항

- Python 3.10+
- Node.js 18+
- PostgreSQL 15+
- Docker & Docker Compose (선택)

### 백엔드 실행

```bash
cd backend
pip install -r requirements.txt
uvicorn app.api.main:app --reload --port 9040
```

### 프론트엔드 실행

```bash
cd frontend
npm install
npm run dev
```

### Docker Compose 실행

```bash
docker-compose up -d --build
docker-compose logs -f
docker-compose down
```

---

## 주요 기능 구현

### 1. 논문 링크 자동 추출

논문 저장 시 Abstract에서 키워드를 분석하여 알러젠-항목 연결을 자동 생성합니다.

**관련 파일:**
- `backend/app/data/paper_keywords.py` - 키워드 사전
- `backend/app/services/paper_link_extractor.py` - 추출 서비스

**추출 흐름:**
```
논문 Abstract → 키워드 매칭 → PaperAllergenLink 생성
                              ├── allergen_code
                              ├── link_type (symptom/dietary/...)
                              ├── specific_item (한글)
                              └── relevance_score
```

고도화 방안은 [PAPER_LINK_EXTRACTION_ROADMAP.md](./PAPER_LINK_EXTRACTION_ROADMAP.md) 참조

### 2. 환자 가이드 (Patient Guide)

진단 결과에 따라 환자 맞춤형 정보를 제공합니다.

**구성:**
- 증상/위험도: 고위험(4-6등급), 주의(2-3등급), 경미(1등급)
- 식이 관리: 회피 식품, 숨겨진 알러젠, 교차반응, 대체 식품
- 응급/의료: 아나필락시스 대처, 에피펜 사용법, 의료 상담 권고
- 출처: 각 항목별 관련 논문 링크

### 3. 인증 시스템

**간편 로그인:**
- 이름 + 전화번호 + 6자리 PIN
- bcrypt 해싱
- JWT 토큰 발급

**Google OAuth:**
- authlib 기반 OAuth 2.0
- 프로필 정보 자동 등록

---

## 개발 현황

### Phase 1: 핵심 기능 (완료)
- [x] PubMed / Semantic Scholar 논문 검색
- [x] Q&A 시스템
- [x] 웹 대시보드

### Phase 2: 인증 및 인프라 (완료)
- [x] Docker 컨테이너화
- [x] PostgreSQL 데이터베이스
- [x] 사용자 인증 시스템 (Google OAuth + 간편 로그인)
- [x] 진단 키트 등록 시스템
- [x] JWT 기반 인증

### Phase 3: 환자 가이드 (완료)
- [x] 증상/위험도 안내
- [x] 식이 관리 가이드
- [x] 논문 출처 연결
- [x] 키워드 기반 자동 추출

### Phase 4: AI 기능 강화 (예정)
- [ ] ChromaDB 벡터 데이터베이스 연동
- [ ] OpenAI/Claude API 연동 RAG 구현
- [ ] MeSH Terms 기반 추출
- [ ] LLM 기반 정밀 추출

### Phase 5: 추가 기능 (예정)
- [ ] 검색 이력 저장 (DB)
- [ ] 논문 북마크 동기화
- [ ] 알림 시스템
- [ ] Redis 캐시 서버
- [ ] CI/CD 파이프라인

---

## 저작권 및 라이선스

<div align="center">
  <h3>운몽시스템즈 (Unmong Systems)</h3>
</div>

### Copyright

```
Copyright (c) 2024-2026 운몽시스템즈 (Unmong Systems). All rights reserved.
```

### 라이선스 조건

이 소프트웨어 및 관련 문서 파일("소프트웨어")에 대한 모든 권리는 **운몽시스템즈 (Unmong Systems)**에 있습니다.

#### 허용 사항
- 개인적, 비상업적 목적의 학습 및 연구 사용
- 교육 목적의 참고 자료로 활용
- 운몽시스템즈의 서면 승인을 받은 경우의 사용

#### 금지 사항
- 소프트웨어의 무단 복제, 수정, 배포
- 상업적 목적의 사용 또는 판매
- 소프트웨어의 역공학, 디컴파일, 분해
- 저작권 표시 및 라이선스 정보의 제거 또는 수정

#### 면책 조항

이 소프트웨어는 "있는 그대로" 제공되며, 명시적이든 묵시적이든 어떠한 종류의 보증도 제공하지 않습니다. 상품성, 특정 목적에의 적합성, 비침해에 대한 보증을 포함하되 이에 국한되지 않습니다. 어떠한 경우에도 저작권자는 소프트웨어 사용으로 인해 발생하는 어떠한 손해에 대해서도 책임을 지지 않습니다.

### 제3자 라이선스

이 프로젝트는 다음의 오픈소스 라이브러리를 사용합니다:

| 라이브러리 | 라이선스 | 용도 |
|-----------|---------|------|
| FastAPI | MIT | Backend API 프레임워크 |
| React | MIT | Frontend UI 프레임워크 |
| Vite | MIT | Frontend 빌드 도구 |
| Recharts | MIT | 차트 시각화 |
| Axios | MIT | HTTP 클라이언트 |
| BeautifulSoup4 | MIT | HTML/XML 파싱 |
| Pydantic | MIT | 데이터 검증 |
| SQLAlchemy | MIT | ORM |

각 라이브러리의 라이선스 조건은 해당 프로젝트의 LICENSE 파일을 참조하세요.
