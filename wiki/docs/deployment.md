---
title: 배포 가이드 (Deployment Guide)
---

# 배포 가이드 (Deployment Guide)

## 6.1 배포 환경

### 환경 구성

| 환경 | 용도 | 브랜치 | 배포 |
|------|------|--------|------|
| **Local** | 개발 | feature/* | 수동 |
| **Production** | 운영 | prod | GitHub Actions 자동 배포 |

### 인프라 구성

```mermaid
graph TB
    subgraph Production Server - MacBook Docker 172.30.1.72
        FE[Frontend<br/>Nginx :4040]
        BE[Backend<br/>FastAPI :9040]
        SC[Scheduler<br/>background]

        FE --> NET[allergyinsight-network]
        BE --> NET
        SC --> NET

        BE --> DB_NET[database-network]
        SC --> DB_NET
    end

    DB_NET --> PG[(PostgreSQL<br/>shared)]
```

---

## 6.2 Docker 배포

### docker-compose.yml (운영)

!!! note "운영 환경 구성"
    환경 변수는 `.env` 파일에서 관리되며, 민감한 정보는 절대 소스 코드에 포함하지 않습니다.

```yaml
services:
  backend:
    build: ./backend
    container_name: allergyinsight-backend
    ports: ["9040:9040"]
    environment:
      - TZ=Asia/Seoul
      - DATABASE_URL=postgresql://allergyinsight_svc:${DB_PASSWORD}@postgresql:5432/allergyinsight
      - JWT_SECRET_KEY=${JWT_SECRET_KEY}
      - JWT_ALGORITHM=HS256
      - JWT_EXPIRE_MINUTES=1440
      - GOOGLE_CLIENT_ID=${GOOGLE_CLIENT_ID:-}
      - SUPER_ADMIN_EMAILS=${SUPER_ADMIN_EMAILS:-}
      - PUBMED_API_KEY=${PUBMED_API_KEY:-}
      - SEMANTIC_SCHOLAR_API_KEY=${SEMANTIC_SCHOLAR_API_KEY:-}
      - OPENAI_API_KEY=${OPENAI_API_KEY:-}
      - GEMINI_API_KEY=${GEMINI_API_KEY:-}
      - NEWS_LLM_PROVIDER=${NEWS_LLM_PROVIDER:-gemini}
      - RAG_LLM_PROVIDER=${RAG_LLM_PROVIDER:-gemini}
      - LLM_API_URL=${LLM_API_URL:-http://host.docker.internal:11435/v1}
      - LLM_MODEL=${LLM_MODEL:-mlx-community/EXAONE-3.5-7.8B-Instruct-4bit}
      - ENABLE_SCHEDULER=${ENABLE_SCHEDULER:-false}
      - GMAIL_ADDRESS=${GMAIL_ADDRESS:-}
      - GMAIL_APP_PASSWORD=${GMAIL_APP_PASSWORD:-}
    volumes:
      - backend_downloads:/app/downloads
      - chromadb_data:/app/data/chromadb
    networks: [database-network, allergyinsight-network]
    restart: always
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:9040/api/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  scheduler:
    build: ./backend
    container_name: allergyinsight-scheduler
    command: ["python", "-m", "app.scheduler.cli"]
    environment:
      - TZ=Asia/Seoul
      - DATABASE_URL=postgresql://allergyinsight_svc:${DB_PASSWORD}@postgresql:5432/allergyinsight
      - ENABLE_SCHEDULER=true
      - CRAWL_HOUR=${CRAWL_HOUR:-7}
      - SEND_HOUR=${SEND_HOUR:-8}
      - GEMINI_API_KEY=${GEMINI_API_KEY:-}
      - GMAIL_ADDRESS=${GMAIL_ADDRESS:-}
      - GMAIL_APP_PASSWORD=${GMAIL_APP_PASSWORD:-}
    depends_on: [backend]
    networks: [database-network, allergyinsight-network]
    restart: always

  frontend:
    build:
      context: ./frontend
      args:
        - VITE_GOOGLE_CLIENT_ID=${GOOGLE_CLIENT_ID:-}
    container_name: allergyinsight-frontend
    ports: ["4040:4040"]
    depends_on: [backend]
    networks: [allergyinsight-network]
    restart: always

networks:
  database-network:
    external: true
  allergyinsight-network:
    driver: bridge

volumes:
  backend_downloads:
  chromadb_data:
```

### 컨테이너 설명

| 컨테이너 | 역할 | 이미지 | 포트 |
|----------|------|--------|------|
| `allergyinsight-backend` | FastAPI API 서버 | backend/ | 9040 |
| `allergyinsight-scheduler` | 뉴스/뉴스레터 스케줄러 | backend/ (command override) | - |
| `allergyinsight-frontend` | Nginx + React SPA | frontend/ | 4040 |

### 배포 명령어

```bash
# 전체 빌드 및 실행
docker compose up -d --build

# 특정 서비스만 재빌드
docker compose up -d --build backend

# 로그 확인
docker compose logs -f

# 서비스 중지
docker compose down
```

---

## 6.3 CI/CD 파이프라인

### GitHub Actions 워크플로우

!!! note "자동 배포 트리거"
    `prod` 브랜치에 push 시 GitHub Actions가 자동으로 배포를 수행합니다.

```yaml title=".github/workflows/deploy-prod.yml"
name: Deploy to Production

on:
  push:
    branches: [prod]

jobs:
  deploy:
    runs-on: [self-hosted, macOS]
    steps:
      - name: Pull Latest Code
        run: |
          cd /Users/rainend/GIT/AllergyInsight
          git fetch origin
          git reset --hard origin/prod

      - name: Check if Docker Restart Needed
        # backend/, frontend/, docker-compose.yml 변경 시에만 재시작

      - name: Stop and Rebuild (if needed)
        run: |
          docker compose down
          docker compose up -d --build

      - name: Health Check
        run: |
          sleep 30
          curl -f http://localhost:9040/api/health
```

### 배포 흐름

```mermaid
graph LR
    A[1. main → prod PR 생성 + 머지] --> B[2. GitHub Actions 트리거]
    B --> C[3. Self-hosted Runner가 코드 풀]
    C --> D[4. 변경된 서비스만 Docker 재빌드]
    D --> E[5. 헬스체크<br/>/api/health 확인]
    E --> F[6. 완료]
```

---

## 6.4 네트워크 구성

| 네트워크 | 타입 | 용도 |
|----------|------|------|
| `database-network` | external | PostgreSQL 공유 (다른 프로젝트와 공유) |
| `allergyinsight-network` | bridge | 내부 서비스 간 통신 |

### 포트 매핑

| 서비스 | 호스트 포트 | 컨테이너 포트 |
|--------|-----------|-------------|
| Frontend (Nginx) | 4040 | 4040 |
| Backend (FastAPI) | 9040 | 9040 |
| Scheduler | - | - (백그라운드) |

---

## 6.5 데이터 관리

### 볼륨

| 볼륨 | 용도 |
|------|------|
| `backend_downloads` | 논문 PDF 다운로드 |
| `chromadb_data` | ChromaDB 벡터 데이터 |

### 데이터베이스

!!! note "외부 공유 PostgreSQL"
    PostgreSQL은 **외부 공유 컨테이너**를 사용합니다 (`database-network`).

- DB 이름: `allergyinsight`
- DB 사용자: `allergyinsight_svc`

### 시드 데이터

!!! tip "자동 시드"
    앱 시작 시 아래 시드 함수가 자동으로 실행됩니다.

- `seed_users()` — 테스트 사용자 생성
- `seed_allergens()` — 알러젠 마스터 데이터 시딩

---

## 6.6 모니터링

### 헬스 체크 엔드포인트

```
GET /api/health
```

```json title="Response"
{
  "status": "healthy",
  "timestamp": "2026-03-25T10:30:00+09:00"
}
```

### Docker 컨테이너 모니터링

```bash
# 컨테이너 상태
docker ps

# 리소스 사용량
docker stats

# 특정 서비스 로그
docker compose logs backend --since="1h"
docker compose logs scheduler --since="1h"
```

---

## 6.7 트러블슈팅

### 일반적인 문제

#### 1. 컨테이너 시작 실패

```bash
docker compose logs backend
```

!!! warning "일반적인 원인"
    - **DB 연결 실패**: `DATABASE_URL`, `DB_PASSWORD` 확인
    - **포트 충돌**: `lsof -i :9040`으로 확인
    - **이미지 빌드 오류**: `docker compose build --no-cache`로 재빌드

#### 2. 스케줄러 작동 안 함

```bash
docker compose logs scheduler
```

!!! warning "확인 사항"
    - `ENABLE_SCHEDULER=true` 설정 여부
    - `GMAIL_ADDRESS`, `GMAIL_APP_PASSWORD` 설정 여부
    - `GEMINI_API_KEY` 설정 여부

#### 3. Nginx 프록시 타임아웃

!!! tip "타임아웃 해결"
    Nginx 설정에서 타임아웃/버퍼링 설정을 확인하세요. 대용량 응답 시 `proxy_buffering`, `proxy_read_timeout` 값을 조정합니다.

### 롤백 절차

!!! warning "롤백 시 주의"
    롤백 후 반드시 헬스체크를 수행하여 서비스 상태를 확인하세요.

```bash
# 1. 이전 버전으로 롤백
git checkout HEAD~1
docker compose up -d --build

# 2. 상태 확인
curl http://localhost:9040/api/health
```

---

## 6.8 보안 체크리스트

!!! danger "배포 전 반드시 확인"

    - [ ] `JWT_SECRET_KEY` 변경 (운영 환경)
    - [ ] `DB_PASSWORD` 강력한 비밀번호 설정
    - [ ] CORS 설정 확인 (허용 Origin 명시)
    - [ ] `SUPER_ADMIN_EMAILS` 설정
    - [ ] 로그에 민감 정보 미포함
    - [ ] `.env` 파일 gitignore 확인

---

[← 개발 가이드](development-guide.md) | [로드맵 →](roadmap.md)
