---
title: 개발 가이드 (Development Guide)
---

# 개발 가이드 (Development Guide)

## 5.1 개발 환경 설정

### 필수 요구사항

| 도구 | 최소 버전 | 권장 버전 | 용도 |
|------|----------|----------|------|
| Git | 2.30+ | 최신 | 버전 관리 |
| Docker | 20.10+ | 최신 | 컨테이너 |
| Docker Compose | 2.0+ | 최신 | 컨테이너 오케스트레이션 |
| Node.js | 18+ | 20 LTS | Frontend 개발 |
| Python | 3.10+ | 3.10 | Backend 개발 |

### 저장소 클론

```bash
git clone https://github.com/bluevlad/AllergyInsight.git
cd AllergyInsight
```

### Docker로 실행 (권장)

!!! tip "Docker 사용을 권장합니다"
    전체 서비스를 한 번에 실행할 수 있어 가장 간편합니다.

```bash
# 전체 서비스 빌드 및 실행
docker compose up -d --build

# 로그 확인
docker compose logs -f

# 서비스 중지
docker compose down
```

### 로컬 개발 환경 (Docker 없이)

=== "Backend"

    ```bash
    cd backend

    # 가상 환경 생성
    python -m venv venv
    ```

    === "Windows"

        ```bash
        venv\Scripts\activate
        ```

    === "macOS/Linux"

        ```bash
        source venv/bin/activate
        ```

    ```bash
    # 의존성 설치
    pip install -r requirements.txt

    # 환경 변수 설정
    cp .env.example .env

    # 서버 실행
    uvicorn app.api.main:app --reload --port 9040
    ```

=== "Frontend"

    ```bash
    cd frontend

    # 의존성 설치
    npm install

    # 개발 서버 실행
    npm run dev
    ```

### 환경 변수

#### Backend (.env) — 필수

!!! danger "보안 주의"
    `.env` 파일은 절대 Git에 커밋하지 마십시오. `JWT_SECRET_KEY`와 데이터베이스 비밀번호는 반드시 운영 환경에서 변경해야 합니다.

```env
# Database (외부 PostgreSQL 사용)
DATABASE_URL=postgresql://allergyinsight_svc:password@localhost:5432/allergyinsight

# JWT
JWT_SECRET_KEY=your-secret-key-change-in-production
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=1440

# Google OAuth (ID 토큰 방식 - CLIENT_SECRET 불필요)
GOOGLE_CLIENT_ID=your-google-client-id
SUPER_ADMIN_EMAILS=admin@example.com
```

#### Backend (.env) — 선택

```env
# Paper Search APIs
PUBMED_API_KEY=
PUBMED_EMAIL=
SEMANTIC_SCHOLAR_API_KEY=
CORE_API_KEY=
OPENAI_API_KEY=

# AI - Gemini
GEMINI_API_KEY=
NEWS_LLM_PROVIDER=gemini
RAG_LLM_PROVIDER=gemini

# AI - Local LLM
LLM_API_URL=http://localhost:11435/v1
LLM_MODEL=mlx-community/EXAONE-3.5-7.8B-Instruct-4bit

# Scheduler
ENABLE_SCHEDULER=false
CRAWL_HOUR=7
CRAWL_MINUTE=0
SEND_HOUR=8
SEND_MINUTE=0

# Email (뉴스레터)
GMAIL_ADDRESS=
GMAIL_APP_PASSWORD=

# Subscription
SUBSCRIPTION_BASE_URL=https://allergy.unmong.com/subscribe

# News quality gate
NEWS_RELEVANCE_THRESHOLD=0.3
NEWS_IMPORTANCE_THRESHOLD=0.2
```

---

## 5.2 코딩 컨벤션

### Python (Backend)

#### 스타일 가이드

!!! note "핵심 규칙"
    - **PEP 8** 준수
    - **Pydantic v2** 사용 (v1 문법 혼용 금지)
    - **PostgreSQL** 전용 SQL (Oracle 문법 금지)

#### 네이밍 규칙

```python
# 클래스: PascalCase
class UserDiagnosis:
    pass

# 함수/변수: snake_case
def get_patient_by_id(patient_id: int) -> Patient:
    user_name = "홍길동"

# 상수: UPPER_SNAKE_CASE
MAX_GRADE = 6
DEFAULT_PAGE_SIZE = 20

# Private: 앞에 언더스코어
def _calculate_risk_level(grade: int) -> str:
    pass
```

#### 파일 구조 (Import 순서)

```python
# 1. Standard library imports
import os
from datetime import datetime
from typing import Optional

# 2. Third-party imports
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

# 3. Local imports
from ..database.models import User, UserDiagnosis
from ..core.auth.dependencies import get_current_user
from .schemas import DiagnosisCreate, DiagnosisResponse
```

### JavaScript/React (Frontend)

#### 네이밍 규칙

```javascript
// 컴포넌트: PascalCase
function DiagnosisCard({ diagnosis }) { }

// 함수/변수: camelCase
const patientName = "홍길동";
function calculateRiskLevel(grade) { }

// 상수: UPPER_SNAKE_CASE
const MAX_GRADE = 6;

// 파일명
// 컴포넌트: PascalCase.jsx
// 유틸/서비스: camelCase.js
```

---

## 5.3 Git 브랜치 전략

### 브랜치 구조

```mermaid
graph TD
    PROD[prod<br/>production - 자동 배포] --> MAIN[main<br/>stable]
    PROD --> HOTFIX[hotfix/critical-auth-bug]
    MAIN --> FEAT1[feature/add-emergency-guide]
    MAIN --> FEAT2[feature/analytics-dashboard]
    MAIN --> FIX[fix/login-redirect-issue]
    MAIN --> REFACTOR[refactor/api-structure]
```

### 브랜치 명명 규칙

| 유형 | 형식 | 예시 |
|------|------|------|
| 기능 | `feature/{기능명}` | `feature/add-emergency-guide` |
| 버그 수정 | `fix/{이슈명}` | `fix/login-redirect-issue` |
| 리팩토링 | `refactor/{대상}` | `refactor/api-structure` |
| 문서 | `docs/{문서명}` | `docs/api-specification` |
| 긴급 수정 | `hotfix/{이슈명}` | `hotfix/critical-auth-bug` |

### 커밋 메시지 규칙

```
<type>(<scope>): <subject>

<body>

<footer>
```

#### Type

| Type | 설명 |
|------|------|
| `feat` | 새로운 기능 |
| `fix` | 버그 수정 |
| `docs` | 문서 변경 |
| `style` | 코드 포맷팅 (로직 변경 없음) |
| `refactor` | 리팩토링 |
| `test` | 테스트 추가/수정 |
| `chore` | 빌드, 설정 변경 |
| `ci` | CI/CD 관련 변경 |

### 배포 흐름

```mermaid
graph LR
    F[feature/*] -->|PR + Review| M[main]
    M -->|PR + merge| P[prod]
    P -->|자동 배포| S[Production Server]
```

---

## 5.4 테스트

=== "Backend"

    ```bash
    cd backend
    pytest -v
    # 또는
    python -m pytest tests/
    ```

=== "Frontend"

    ```bash
    cd frontend
    npm test
    npm run test:coverage
    ```

=== "E2E"

    ```bash
    cd e2e
    npm install
    npm run test        # Playwright 테스트
    npm run test:ui     # UI 모드
    npm run test:report # 리포트
    ```

---

## 5.5 디버깅

### Docker 로그 확인

```bash
# 전체 로그
docker compose logs

# 특정 서비스
docker compose logs backend
docker compose logs scheduler

# 실시간 로그
docker compose logs -f backend

# 최근 100줄
docker compose logs --tail=100 backend
```

### 개발 도구

| 도구 | 용도 |
|------|------|
| **Swagger UI** | `http://localhost:9040/docs` — API 테스트 |
| **pgAdmin / DBeaver** | PostgreSQL GUI |

---

## 5.6 금지 사항 (Do NOT)

!!! danger "반드시 준수해야 하는 금지 사항"

    - Oracle 문법 사용 금지 — PostgreSQL 전용
    - `.env` 파일 커밋 금지
    - `requirements.txt`에 없는 패키지를 설치 없이 import 금지
    - Pydantic v1 문법과 v2 문법 혼용 금지 (v2 사용)
    - 서버 주소, 비밀번호 추측 금지 — 반드시 확인 후 사용
    - 운영 Docker 컨테이너 직접 조작 금지
    - 자격증명을 소스코드에 하드코딩하지 말 것
    - CORS에 `allow_origins=["*"]` 사용 금지 — 허용 Origin 명시
    - API 엔드포인트를 인증 없이 노출하지 말 것 (Public API 제외)
    - `console.log`/`print`로 민감 정보를 출력하지 말 것

---

[← API 명세](api-specification.md) | [배포 가이드 →](deployment.md)
