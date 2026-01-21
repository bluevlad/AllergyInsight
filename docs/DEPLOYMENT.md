# AllergyInsight 배포 가이드

이 문서는 AllergyInsight 프로젝트의 배포 환경 및 방법을 설명합니다.

---

## 배포 아키텍처

```
┌─────────────────────────────────────────────────────────────────┐
│                        GitHub Repository                         │
│                   bluevlad/AllergyInsight                        │
├─────────────┬─────────────┬─────────────────────────────────────┤
│   master    │   develop   │              prod                    │
│  (안정 버전) │  (개발 버전) │          (운영 배포)                 │
└─────────────┴─────────────┴──────────────┬──────────────────────┘
                                           │ push
                                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                     GitHub Actions                               │
│                  deploy-prod.yml 워크플로우                       │
└──────────────────────────┬──────────────────────────────────────┘
                           │ trigger
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Self-hosted Runner                             │
│              allergyinsight-runner (Windows)                     │
│                    C:\actions-runner\allergyinsight              │
└──────────────────────────┬──────────────────────────────────────┘
                           │ docker-compose
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Docker Containers                            │
├─────────────────┬─────────────────┬─────────────────────────────┤
│  allergyinsight │  allergyinsight │      allergyinsight         │
│     -frontend   │     -backend    │          -db                │
│    (Port 4040)  │   (Port 9040)   │      (Port 5432)            │
└─────────────────┴─────────────────┴─────────────────────────────┘
```

---

## 브랜치 전략

| 브랜치 | 용도 | 배포 |
|--------|------|------|
| `master` | 안정 버전, 릴리즈 준비 | - |
| `develop` | 개발 통합 브랜치 | - |
| `prod` | 운영 배포 브랜치 | 자동 배포 |
| `feature/*` | 기능 개발 | - |

### 배포 흐름

```
feature/* → develop → master → prod
                                 │
                                 └→ 자동 배포 (GitHub Actions)
```

---

## GitHub Actions 워크플로우

### 파일 위치
`.github/workflows/deploy-prod.yml`

### 트리거 조건
- `prod` 브랜치에 push 시 자동 실행

### 실행 단계

| 순서 | 단계 | 설명 |
|------|------|------|
| 1 | Configure git safe directory | Git 권한 설정 |
| 2 | Pull latest changes | 최신 코드 pull |
| 3 | Stop existing containers | 기존 컨테이너 중지 |
| 4 | Build and start containers | 새 컨테이너 빌드 및 시작 |
| 5 | Wait for services | 서비스 시작 대기 (30초) |
| 6 | Health check | Backend 헬스체크 |
| 7 | Show container status | 컨테이너 상태 출력 |

---

## Self-hosted Runner

### 설치 정보

| 항목 | 값 |
|------|-----|
| Runner 이름 | `allergyinsight-runner` |
| 설치 경로 | `C:\actions-runner\allergyinsight` |
| 서비스 이름 | `actions.runner.AllergyInsight` |
| 라벨 | `self-hosted`, `Windows`, `X64` |

### 서비스 관리

```powershell
# 상태 확인
Get-Service -Name 'actions.runner.AllergyInsight'

# 시작
Start-Service -Name 'actions.runner.AllergyInsight'

# 중지
Stop-Service -Name 'actions.runner.AllergyInsight'

# 재시작
Restart-Service -Name 'actions.runner.AllergyInsight'
```

### Runner 재설정 (필요시)

```powershell
# 1. 서비스 중지 및 삭제
Stop-Service -Name 'actions.runner.AllergyInsight'
sc.exe delete 'actions.runner.AllergyInsight'

# 2. Runner 제거
cd C:\actions-runner\allergyinsight
.\config.cmd remove --token <TOKEN>

# 3. 새 토큰 발급 (gh CLI)
gh api repos/bluevlad/AllergyInsight/actions/runners/registration-token -X POST --jq '.token'

# 4. Runner 재설정
.\config.cmd --url https://github.com/bluevlad/AllergyInsight --token <NEW_TOKEN> --name allergyinsight-runner --labels Windows,self-hosted --work _work --unattended

# 5. 서비스 등록
sc.exe create 'actions.runner.AllergyInsight' binPath='C:\actions-runner\allergyinsight\bin\RunnerService.exe' start=delayed-auto
Start-Service -Name 'actions.runner.AllergyInsight'
```

---

## Docker 컨테이너

### 컨테이너 목록

| 컨테이너 | 이미지 | 포트 | 역할 |
|---------|--------|------|------|
| allergyinsight-db | postgres:15-alpine | 5432 | PostgreSQL 데이터베이스 |
| allergyinsight-backend | 자체 빌드 | 9040 | FastAPI 백엔드 |
| allergyinsight-frontend | 자체 빌드 | 4040 | React 프론트엔드 |

### Docker 명령어

```bash
# 컨테이너 상태 확인
docker-compose ps

# 로그 확인
docker-compose logs -f
docker-compose logs -f backend

# 컨테이너 재시작
docker-compose restart

# 전체 재배포
docker-compose down
docker-compose up -d --build

# 특정 서비스만 재빌드
docker-compose up -d --build backend
```

### 볼륨

| 볼륨 | 용도 |
|------|------|
| `postgres_data` | PostgreSQL 데이터 영속화 |
| `backend_downloads` | 논문 다운로드 파일 |

---

## 환경변수

### 필수 환경변수

프로젝트 루트에 `.env` 파일 생성:

```env
# Database
DB_PASSWORD=your-secure-password

# JWT
JWT_SECRET_KEY=your-jwt-secret-key

# Google OAuth (선택)
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret

# URLs
FRONTEND_URL=http://localhost:4040
BACKEND_URL=http://localhost:9040
```

### API 키 (선택)

```env
# PubMed API
PUBMED_API_KEY=your-pubmed-api-key
PUBMED_EMAIL=your-email@example.com

# Semantic Scholar API
SEMANTIC_SCHOLAR_API_KEY=your-semantic-scholar-api-key

# OpenAI API (향후 RAG 기능용)
OPENAI_API_KEY=your-openai-api-key
```

---

## 수동 배포 방법

### 1. prod 브랜치로 머지

```bash
# master의 변경사항을 prod에 머지
git checkout prod
git merge master
git push
```

### 2. GitHub Actions 확인

- URL: https://github.com/bluevlad/AllergyInsight/actions
- 워크플로우 실행 상태 확인

### 3. 배포 결과 확인

```bash
# 컨테이너 상태
docker ps

# 헬스체크
curl http://localhost:9040/api/health

# 프론트엔드 접속
start http://localhost:4040
```

---

## 접속 URL

| 서비스 | URL |
|--------|-----|
| Frontend | http://localhost:4040 |
| Backend API | http://localhost:9040 |
| API 문서 (Swagger) | http://localhost:9040/docs |
| GitHub Actions | https://github.com/bluevlad/AllergyInsight/actions |

---

## 트러블슈팅

### Runner가 offline 상태일 때

```powershell
# 서비스 상태 확인
Get-Service -Name 'actions.runner.AllergyInsight'

# 서비스 재시작
Restart-Service -Name 'actions.runner.AllergyInsight'

# GitHub에서 상태 확인
gh api repos/bluevlad/AllergyInsight/actions/runners --jq '.runners[]'
```

### Docker 권한 오류

```powershell
# NETWORK SERVICE를 docker-users 그룹에 추가
net localgroup docker-users "NT AUTHORITY\NETWORK SERVICE" /add
```

### Git safe directory 오류

```powershell
git config --global --add safe.directory C:/GIT/AllergyInsight
```

### 컨테이너 빌드 실패

```bash
# 캐시 없이 재빌드
docker-compose build --no-cache

# 이미지 정리 후 재빌드
docker system prune -f
docker-compose up -d --build
```

---

## 버전 이력

| 날짜 | 변경 내용 |
|------|----------|
| 2026-01-21 | 초기 배포 환경 구축 (GitHub Actions + Self-hosted Runner) |
