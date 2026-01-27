# AllergyInsight 브랜치 및 배포 워크플로우

## 개요

개발 환경과 프로덕션 환경을 분리하여 안정적인 배포를 보장합니다.

---

## 환경 구성

| 환경 | 브랜치 | 포트 | Docker Compose | 용도 |
|------|--------|------|----------------|------|
| **Production** | `prod` | 4040, 9040, 5432 | `docker-compose.yml` | 실서비스 |
| **Development** | `master`, `feature/*` | 4041, 9041, 5433 | `docker-compose.dev.yml` | 개발/테스트 |

### 접속 URL

| 환경 | Frontend | Backend API | Swagger Docs |
|------|----------|-------------|--------------|
| Production | http://localhost:4040 | http://localhost:9040 | http://localhost:9040/docs |
| Development | http://localhost:4041 | http://localhost:9041 | http://localhost:9041/docs |

---

## 브랜치 전략

```
feature/xxx ──┬──> master ──────> prod
feature/yyy ──┘    (테스트)      (배포)

[일일 작업]      [통합/테스트]    [프로덕션]
```

### 브랜치 역할

| 브랜치 | 용도 | Docker 환경 | 자동 배포 |
|--------|------|-------------|-----------|
| `feature/*` | 일일 개발 작업 | dev (수동) | X |
| `master` | 통합 브랜치, 테스트 | dev (수동) | X |
| `prod` | 프로덕션 배포 | prod (자동) | O |

---

## 개발 워크플로우

### 1. 새 작업 시작

```bash
# master에서 feature 브랜치 생성
git checkout master
git pull
git checkout -b feature/기능명
```

### 2. 개발 환경에서 테스트

```bash
# 개발용 Docker 실행 (포트 4041, 9041)
docker-compose -f docker-compose.dev.yml up -d --build

# 개발 환경 접속
# Frontend: http://localhost:4041
# Backend:  http://localhost:9041
```

### 3. 작업 완료 후 master에 머지

```bash
# feature 브랜치 커밋
git add .
git commit -m "feat: 기능 설명"

# master로 머지
git checkout master
git merge feature/기능명
git push origin master

# feature 브랜치 삭제 (선택)
git branch -d feature/기능명
```

### 4. 프로덕션 배포 (필요시)

```bash
# master를 prod에 머지
git checkout prod
git merge master
git push origin prod

# GitHub Actions가 자동으로 배포 실행
```

---

## 자동 배포 동작

### GitHub Actions (deploy-prod.yml)

`prod` 브랜치에 push 시 자동 실행:

1. **git pull** - 항상 실행
2. **Docker 재시작 판단** - 변경된 파일 확인
3. **조건부 Docker 재시작**

### Docker 재시작 조건

| 변경된 파일 | Docker 재시작 |
|-------------|---------------|
| `backend/**` | O |
| `frontend/**` | O |
| `docker-compose.yml` | O |
| `Dockerfile*` | O |
| `.env*` | O |
| `docs/**` | X |
| `*.md` | X |
| `.github/**` | X |

---

## 명령어 요약

### 개발 환경

```bash
# 개발 Docker 시작
docker-compose -f docker-compose.dev.yml up -d --build

# 개발 Docker 중지
docker-compose -f docker-compose.dev.yml down

# 개발 Docker 로그
docker-compose -f docker-compose.dev.yml logs -f

# 개발 컨테이너 상태
docker-compose -f docker-compose.dev.yml ps
```

### 프로덕션 환경

```bash
# 프로덕션 Docker 시작 (일반적으로 자동 배포 사용)
docker-compose up -d --build

# 프로덕션 Docker 중지
docker-compose down

# 프로덕션 Docker 로그
docker-compose logs -f

# 프로덕션 컨테이너 상태
docker-compose ps
```

---

## 주의사항

1. **prod 브랜치 직접 수정 금지**
   - 항상 master를 통해 머지

2. **개발 중 prod Docker에 영향 없음**
   - 포트가 분리되어 있음 (4040 vs 4041)

3. **문서만 수정 시 Docker 재시작 안 함**
   - GitHub Actions가 자동 판단

4. **개발 환경 DB는 별도**
   - prod: `allergyinsight` (5432)
   - dev: `allergyinsight_dev` (5433)

---

## 변경 이력

| 날짜 | 버전 | 내용 |
|------|------|------|
| 2025-01-27 | 1.0 | 초기 작성 |
