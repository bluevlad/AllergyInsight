# AllergyInsight Backend

FastAPI 기반 백엔드 API 서버

## 기술 스택

| 기술 | 버전 | 용도 |
|------|------|------|
| Python | 3.10+ | 메인 언어 |
| FastAPI | 0.109.0 | REST API 프레임워크 |
| SQLAlchemy | 2.0.25 | ORM |
| PostgreSQL | 15 | 데이터베이스 |
| bcrypt | - | 비밀번호 해싱 |
| python-jose | 3.3.0 | JWT 토큰 |
| authlib | 1.3.0 | OAuth 인증 |

## 프로젝트 구조

```
backend/
├── app/
│   ├── api/
│   │   └── main.py              # FastAPI 앱 진입점
│   ├── auth/                    # 인증 모듈
│   │   ├── config.py            # 인증 설정 (환경변수)
│   │   ├── dependencies.py      # 인증 의존성 (require_auth 등)
│   │   ├── jwt_handler.py       # JWT 생성/검증
│   │   ├── routes.py            # 인증 API 엔드포인트
│   │   ├── schemas.py           # Pydantic 스키마
│   │   └── diagnosis_routes.py  # 진단 결과 API
│   ├── database/                # 데이터베이스 모듈
│   │   ├── connection.py        # DB 연결 설정
│   │   └── models.py            # SQLAlchemy 모델
│   ├── data/
│   │   └── allergen_prescription_db.py  # 알러지 처방 데이터
│   ├── models/                  # 도메인 모델
│   │   ├── paper.py             # 논문 모델
│   │   ├── prescription.py      # 처방 모델
│   │   └── knowledge_base.py    # Q&A 모델
│   ├── services/                # 비즈니스 로직
│   │   ├── pubmed_service.py    # PubMed API
│   │   ├── semantic_scholar_service.py  # Semantic Scholar API
│   │   ├── paper_search_service.py      # 통합 검색
│   │   ├── prescription_engine.py       # 처방 엔진
│   │   ├── qa_engine.py         # Q&A 엔진
│   │   └── ...
│   └── config.py                # 전역 설정
├── Dockerfile
├── requirements.txt
└── README.md
```

## 데이터베이스 모델

### User (사용자)
```python
class User(Base):
    id: int                    # PK
    name: str                  # 이름
    email: str                 # 이메일 (Google OAuth)
    auth_type: str             # 'google' | 'simple'
    google_id: str             # Google OAuth ID
    phone: str                 # 전화번호 (간편 로그인)
    birth_date: date           # 생년월일 (간편 로그인)
    access_pin_hash: str       # 액세스 PIN 해시
    role: str                  # 'user' | 'admin'
    created_at: datetime
    last_login_at: datetime
```

### DiagnosisKit (진단 키트)
```python
class DiagnosisKit(Base):
    id: int                    # PK
    serial_number: str         # SGT-2024-XXXXX-XXXX
    pin_hash: str              # 키트 PIN 해시
    pin_attempts: int          # PIN 실패 횟수 (최대 5회)
    results: JSON              # {"peanut": 3, "milk": 2, ...}
    diagnosis_date: date       # 진단 일자
    is_registered: bool        # 등록 여부
    registered_user_id: int    # FK -> User
    registered_at: datetime
```

### UserDiagnosis (사용자 진단 기록)
```python
class UserDiagnosis(Base):
    id: int                    # PK
    user_id: int               # FK -> User
    kit_id: int                # FK -> DiagnosisKit
    results: JSON              # 진단 결과 복사본
    diagnosis_date: date
    prescription: JSON         # 캐시된 처방 정보
    created_at: datetime
```

## 인증 흐름

### 1. Google OAuth
```
[사용자] → GET /auth/google/login
        → [Google 로그인 페이지]
        → GET /auth/google/callback?code=xxx
        → [JWT 토큰 발급]
        → Redirect /auth/callback?token=xxx
```

### 2. 간편 회원가입
```
[사용자] → POST /auth/simple/register
        {
          "name": "홍길동",
          "phone": "010-1234-5678",    // 또는 birth_date
          "serial_number": "SGT-2024-00001-0001",
          "pin": "123456"
        }
        → [키트 검증 → 사용자 생성 → JWT 발급]
        → Response: { user, access_token, access_pin }
```

### 3. 간편 로그인
```
[사용자] → POST /auth/simple/login
        {
          "name": "홍길동",
          "phone": "010-1234-5678",
          "access_pin": "715302"
        }
        → [사용자 조회 → PIN 검증 → JWT 발급]
        → Response: { user, access_token }
```

## API 엔드포인트

### 인증 API (`/auth`)
| 메서드 | 경로 | 인증 | 설명 |
|--------|------|------|------|
| GET | `/auth/google/login` | - | Google OAuth 시작 |
| GET | `/auth/google/callback` | - | OAuth 콜백 |
| POST | `/auth/simple/register` | - | 간편 회원가입 |
| POST | `/auth/simple/login` | - | 간편 로그인 |
| GET | `/auth/me` | JWT | 현재 사용자 정보 |
| POST | `/auth/logout` | JWT | 로그아웃 |
| POST | `/auth/register-kit` | JWT | 추가 키트 등록 |

### 진단 API (`/api/diagnosis`)
| 메서드 | 경로 | 인증 | 설명 |
|--------|------|------|------|
| GET | `/api/diagnosis/list` | JWT | 내 진단 목록 |
| GET | `/api/diagnosis/{id}` | JWT | 진단 상세 |
| GET | `/api/diagnosis/{id}/prescription` | JWT | 처방 정보 |

### 논문 검색 API (`/api`)
| 메서드 | 경로 | 설명 |
|--------|------|------|
| GET | `/api/health` | 서버 상태 |
| GET | `/api/stats` | 통계 |
| POST | `/api/search` | 논문 검색 |
| GET | `/api/allergens` | 알러지 목록 |
| POST | `/api/qa` | Q&A |

## 로컬 개발 환경

### 1. 가상환경 생성
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. 환경변수 설정
```bash
# .env 파일 생성
DATABASE_URL=postgresql://postgres:password@localhost:5432/allergyinsight
JWT_SECRET_KEY=your-secret-key
GOOGLE_CLIENT_ID=xxx
GOOGLE_CLIENT_SECRET=xxx
```

### 3. 서버 실행
```bash
uvicorn app.api.main:app --reload --port 9040
```

### 4. API 문서 확인
- Swagger UI: http://localhost:9040/docs
- ReDoc: http://localhost:9040/redoc

## Docker 실행

```dockerfile
# Dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["uvicorn", "app.api.main:app", "--host", "0.0.0.0", "--port", "9040"]
```

```bash
docker build -t allergyinsight-backend .
docker run -p 9040:9040 allergyinsight-backend
```

## 테스트

```bash
# 테스트 실행
pytest

# 커버리지 포함
pytest --cov=app
```

---

Copyright (c) 2024-2026 운몽시스템즈 (Unmong Systems). All rights reserved.
