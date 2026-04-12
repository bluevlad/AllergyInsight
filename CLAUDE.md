# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

> 상위 `C:/GIT/CLAUDE.md`의 Git-First Workflow를 상속합니다.
> 도메인/URL/포트 규칙: [Claude-Opus-bluevlad/standards/infrastructure/DOMAIN_MANAGEMENT.md](https://github.com/bluevlad/Claude-Opus-bluevlad/blob/main/standards/infrastructure/DOMAIN_MANAGEMENT.md) — `https://도메인:포트` 사용 금지

## 실행 환경 감지 (SSH 재접속 금지)

- Claude는 현재 호스트에서 직접 실행 중 — **SSH 재접속을 시도하지 말 것**
- `uname -s` = `Darwin` → MacBook 운영환경 (172.30.1.72), docker/docker compose 직접 실행 가능
- `uname -s` 결과가 Windows/MINGW/MSYS → Windows 개발환경 (172.30.1.100)
- Docker 명령은 현재 호스트에서 바로 실행 (별도 SSH 접속 불필요)
- compose 파일 선택: Darwin → `docker-compose.yml` / Windows → `docker-compose.local.yml`

## Project Overview

AllergyInsight - 알러지 연구 논문 검색/분석 플랫폼 (PubMed/Semantic Scholar 검색 → AI 분석 → RAG 기반 Q&A)

## Environment

- **Database**: PostgreSQL (asyncpg + psycopg2, Oracle 문법 금지)
- **Vector DB**: ChromaDB (임베딩 검색)
- **Target Server**: MacBook Docker (172.30.1.72) / Windows 로컬 개발
- **Docker Strategy**: Docker Compose (backend + frontend)
- **Python Version**: 3.10+

## Tech Stack

### Backend (backend/)

| 항목 | 기술 |
|------|------|
| Language | Python 3.10+ |
| Framework | FastAPI 0.109 + Uvicorn |
| ORM | SQLAlchemy 2.0 (async: asyncpg, sync: psycopg2) |
| Database | PostgreSQL |
| Vector DB | ChromaDB |
| AI | OpenAI API (GPT), tiktoken |
| PDF | PyMuPDF, pdfplumber |
| Auth | PyJWT (JWT), passlib (bcrypt), google-auth (ID 토큰 검증) |
| HTTP Client | httpx, aiohttp, requests |
| RSS | feedparser |
| Config | Pydantic + python-dotenv |
| Testing | pytest, pytest-asyncio |

### Frontend (frontend/)

| 항목 | 기술 |
|------|------|
| Language | JavaScript (JSX) |
| Framework | React 18 |
| Build Tool | Vite 5 |
| Router | React Router 6 |
| HTTP Client | Axios |
| Chart | Recharts |
| Testing | Jest + Testing Library |
| Serve | Nginx (Docker) |

## Setup and Run Commands

```bash
# Backend
cd backend
python -m venv venv
venv\Scripts\activate     # Windows
pip install -r requirements.txt

# Backend 실행
uvicorn app.api.main:app --reload --port 9040

# Backend 테스트
pytest
# 또는
python -m pytest tests/

# Docker (전체)
docker compose up -d
docker compose -f docker-compose.dev.yml up -d  # 개발

# Frontend
cd frontend
npm install
npm run dev         # 개발 서버
npm run build       # 프로덕션 빌드
npm run test        # Jest 테스트

# E2E 테스트 (e2e/)
cd e2e
npm install
npm run test        # Playwright 테스트
npm run test:ui     # UI 모드
npm run test:report # 리포트
```

### Port Mapping

| 서비스 | 로컬 | Docker |
|--------|------|--------|
| Backend API | 9040 | 9040:9040 |
| Frontend | (dev port) | 4040:4040 |

## Architecture Overview

```
backend/app/
├── api/            # FastAPI 라우터 (엔드포인트)
├── auth/           # 인증 (JWT, Google OAuth)
├── admin/          # 관리자 기능
├── consumer/       # 소비자 기능
├── core/           # 핵심 비즈니스 로직
├── data/           # 데이터 처리/변환
├── database/       # SQLAlchemy 세션, 마이그레이션
├── hospital/       # 병원 정보 모듈
└── models/         # SQLAlchemy 모델
```

## Do NOT

- Oracle 문법 사용 금지 — PostgreSQL 전용
- .env 파일 커밋 금지
- requirements.txt에 없는 패키지를 설치 없이 import 금지
- pydantic v1 문법과 v2 문법 혼용 금지 (v2 사용)
- 서버 주소, 비밀번호 추측 금지 — 반드시 확인 후 사용
- 운영 Docker 컨테이너 직접 조작 금지 (allergyinsight-backend, allergyinsight-frontend)
- 자격증명(비밀번호, API 키, JWT Secret)을 소스코드에 하드코딩하지 마라
- CORS에 allow_origins=["*"] 사용하지 마라 — 허용 Origin 명시
- API 엔드포인트를 인증 없이 노출하지 마라
- console.log/print로 민감 정보를 출력하지 마라

## Required Environment Variables

```
DATABASE_URL=           # PostgreSQL 연결
JWT_SECRET_KEY=         # JWT 서명 (필수)
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=1440
GOOGLE_CLIENT_ID=       # Google OAuth (ID 토큰 방식, CLIENT_SECRET 불필요)
SUPER_ADMIN_EMAILS=     # Super Admin 이메일 (콤마 구분)
PUBMED_API_KEY=         # PubMed API
PUBMED_EMAIL=
SEMANTIC_SCHOLAR_API_KEY=
OPENAI_API_KEY=         # OpenAI API
```

## Database Notes

- SQL 문법: PostgreSQL 호환만 사용
- 비동기 드라이버: asyncpg
- 동기 드라이버: psycopg2-binary
- 페이지네이션: `LIMIT/OFFSET` 사용

## Documentation

### 문서 이원화 원칙

코드 저장소와 전략 저장소를 분리하여 민감 정보와 지적재산을 보호합니다.

| 저장소 | 역할 | 원칙 |
|--------|------|------|
| `AllergyInsight/docs/` | 구현 문서 | **"어떻게(How)"** — 코드와 함께 버전 관리되는 운영/개발 문서 |
| `Claude-Opus-bluevlad/services/allergyinsight/` | 전략 문서 | **"왜(Why) + 무엇을(What)"** — 의사결정, 분석, 보안, 계획 |

> 📘 **표준 문서**: [SERVICE_FOLDER_STRUCTURE.md](https://github.com/bluevlad/Claude-Opus-bluevlad/blob/main/standards/documentation/SERVICE_FOLDER_STRUCTURE.md) — `services/{project}/` 하위 폴더·파일 표준 (필수/권장/해당 시, 네이밍 규칙, 배치 결정 트리)

### 문서 분류 Decision Tree

문서 작성 시 아래 순서로 위치를 결정합니다:

```
1. 보안 정보(키 관리, 계정 체계, 인증 설계)를 포함하는가?
   → Claude-Opus-bluevlad/services/allergyinsight/security/

2. 비즈니스 분석(경쟁사, 시장, 타당성, 비용)인가?
   → Claude-Opus-bluevlad/services/allergyinsight/analysis/

3. 아키텍처 의사결정(왜 이 기술을 선택했는가)인가?
   → Claude-Opus-bluevlad/services/allergyinsight/adr/

4. 구현 전 계획(무엇을 만들 것인가, 단계별 플랜)인가?
   → Claude-Opus-bluevlad/services/allergyinsight/plans/

5. 기능 로드맵(중장기 발전 계획)인가?
   → Claude-Opus-bluevlad/services/allergyinsight/roadmap/

6. 구현 후 결과(어떻게 사용하는가, 설정값, 엔드포인트)인가?
   → AllergyInsight/docs/

7. API 변경사항인가?
   → AllergyInsight/docs/api/
```

### 문서 간 연결 규칙

- **AllergyInsight → Claude-Opus-bluevlad 참조**: GitHub URL 사용
  ```markdown
  > **설계 문서**: [plans/allergen-trend-analysis-plan.md](https://github.com/bluevlad/Claude-Opus-bluevlad/blob/main/services/allergyinsight/plans/allergen-trend-analysis-plan.md)
  ```
- **Claude-Opus-bluevlad → AllergyInsight 참조**: GitHub URL 사용
  ```markdown
  > **구현 코드**: [backend/app/services/allergen_trend_service.py](https://github.com/bluevlad/AllergyInsight/blob/main/backend/app/services/allergen_trend_service.py)
  ```
- **구현 완료 시**: 양쪽 문서를 동시에 업데이트 (플랜에 구현 상태 표기, 코드 repo에 가이드 추가)

### 문서 저장소 구조

```
Claude-Opus-bluevlad/services/allergyinsight/
├── README.md               # ✅ 필수 — 서비스 메인 문서
├── CLAUDE.service.md       # ✅ 필수 — Claude Code 진입점
├── VERIFICATION_CRITERIA.md # ✅ 필수 — 검증 기준
├── overview.md             # 🟢 권장 — 배경·목적·범위
├── adr/                    # 🟢 권장 — 아키텍처 결정 기록
├── plans/                  # 🟢 권장 — 구현 플랜
├── roadmap/                # 🟢 권장 — 중장기 로드맵
├── analysis/               # 🟢 권장 — 비즈니스/기술 분석
├── security/               # 🟡 해당 시 — 보안 설계
├── dev/                    # 🟡 해당 시 — 전략성 가이드
└── wiki/                   # 🟡 해당 시 — 프로젝트 Wiki
```

> 상세 표준·네이밍 규칙·마이그레이션 가이드는 [SERVICE_FOLDER_STRUCTURE.md](https://github.com/bluevlad/Claude-Opus-bluevlad/blob/main/standards/documentation/SERVICE_FOLDER_STRUCTURE.md) 참조.

## Deployment

- **CI/CD**: GitHub Actions (prod 브랜치 push 시 자동 배포)
- **운영 포트**: Frontend 4040, Backend 9040
- **네트워크**: database-network (외부 공유), allergyinsight-network (내부)
- **헬스체크**: http://localhost:9040/api/health

## Help Page 관리

> 작성 표준: [HELP_PAGE_GUIDE.md](https://github.com/bluevlad/Claude-Opus-bluevlad/blob/main/standards/documentation/HELP_PAGE_GUIDE.md)
> HTML 템플릿: [help-page-template.html](https://github.com/bluevlad/Claude-Opus-bluevlad/blob/main/standards/documentation/templates/help-page-template.html)

- **기능 추가/변경/삭제 시 반드시 헬프 페이지도 함께 업데이트**
- 헬프 파일 위치: `frontend/public/help/`
- 서비스 accent-color: `#8b5cf6` (Violet)
- 대상 가이드 파일:
  - `user-guide.html` — 사용자 처방 대시보드 가이드
  - `admin-guide.html` — 관리자 콘솔 가이드
  - `newsletter-guide.html` — 뉴스레터 구독/발송 가이드
  - `ai-consult-guide.html` — AI 상담 사용자 가이드
  - `analytics-guide.html` — 트렌드 분석 사용자 가이드

> 로컬 환경 정보는 `CLAUDE.local.md` 참조 (git에 포함되지 않음)
