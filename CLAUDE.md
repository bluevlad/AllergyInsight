# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

> 상위 `C:/GIT/CLAUDE.md`의 Git-First Workflow를 상속합니다.

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
| Auth | python-jose (JWT), passlib (bcrypt), Authlib (OAuth) |
| HTTP Client | httpx, aiohttp, requests |
| RSS | feedparser |
| Config | Pydantic + python-dotenv |
| Testing | pytest, pytest-asyncio |

### Frontend (frontend/)

| 항목 | 기술 |
|------|------|
| Framework | React |

## Setup and Run Commands

```bash
# Backend
cd backend
python -m venv venv
venv\Scripts\activate     # Windows
pip install -r requirements.txt

# Backend 실행
uvicorn app.main:app --reload --port 9040

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
npm run dev
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
GOOGLE_CLIENT_ID=       # Google OAuth
GOOGLE_CLIENT_SECRET=
FRONTEND_URL=           # CORS/OAuth 리다이렉트
BACKEND_URL=
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

### 문서 참조 경로
- 코드 문서: `AllergyInsight/docs/`
- 프로젝트 문서: `C:/GIT/Claude-Opus-bluevlad/docs/AllergyInsight/`
  - 기획서, WBS, IMPLEMENTATION.md, ADR, 로드맵, Wiki

### 문서 작성 규칙
- 코드 관련 (API 변경, 환경설정): `AllergyInsight/docs/`
- 기획/설계/로드맵: `C:/GIT/Claude-Opus-bluevlad/docs/AllergyInsight/`

## Deployment

- **CI/CD**: GitHub Actions (prod 브랜치 push 시 자동 배포)
- **운영 포트**: Frontend 4040, Backend 9040
- **네트워크**: database-network (외부 공유), allergyinsight-network (내부)
- **헬스체크**: http://localhost:9040/api/health

> 로컬 환경 정보는 `CLAUDE.local.md` 참조 (git에 포함되지 않음)
