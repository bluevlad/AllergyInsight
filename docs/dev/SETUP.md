# 개발 환경 설정

## 필수 요구사항

| 도구 | 최소 버전 | 권장 버전 | 용도 |
|------|----------|----------|------|
| Git | 2.30+ | 최신 | 버전 관리 |
| Docker | 20.10+ | 최신 | 컨테이너 |
| Docker Compose | 2.0+ | 최신 | 컨테이너 오케스트레이션 |
| Node.js | 18+ | 20 LTS | Frontend 개발 |
| Python | 3.11+ | 3.11 | Backend 개발 |
| VS Code | - | 최신 | IDE (권장) |

## 저장소 클론

```bash
git clone https://github.com/bluevlad/AllergyInsight.git
cd AllergyInsight
```

## Docker로 실행 (권장)

```bash
# 전체 서비스 빌드 및 실행
docker-compose up -d --build

# 로그 확인
docker-compose logs -f

# 서비스 중지
docker-compose down
```

## 로컬 개발 환경 (Docker 없이)

### Backend

```bash
cd backend

# 가상 환경 생성 및 활성화
python -m venv .venv

# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

# 의존성 설치
pip install -r requirements.txt

# 환경 변수 설정
cp .env.example .env

# 서버 실행
uvicorn app.api.main:app --reload --port 9040
```

### Frontend

```bash
cd frontend

# 의존성 설치
npm install

# 개발 서버 실행
npm run dev
```

## 환경 변수

### Backend (.env)

```env
# Database
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/allergyinsight

# JWT
JWT_SECRET_KEY=your-secret-key-change-in-production
JWT_ALGORITHM=HS256
JWT_EXPIRE_HOURS=24

# Google OAuth (선택)
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
```

### Frontend (.env)

```env
VITE_API_URL=http://localhost:9040
```

## 접속 URL

| 서비스 | URL | 설명 |
|--------|-----|------|
| Frontend | http://localhost:4040 | React 앱 |
| Professional | http://localhost:4040/pro | 의료진 서비스 |
| Consumer | http://localhost:4040/app | 환자 서비스 |
| Backend API | http://localhost:9040 | FastAPI |
| API Docs | http://localhost:9040/docs | Swagger UI |

## 테스트 환경

```bash
# 테스트 환경 실행 (포트 분리)
docker-compose -f docker-compose.test.yml up -d --build

# 테스트 환경 URL
# Frontend: http://localhost:4041
# Backend: http://localhost:9041
# Database: localhost:5433
```

## VS Code 권장 설정

### 확장 프로그램

- Python
- Pylance
- ESLint
- Prettier
- Docker
- GitLens

### 디버깅 설정

`.vscode/launch.json`:
```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "FastAPI",
      "type": "python",
      "request": "launch",
      "module": "uvicorn",
      "args": ["app.api.main:app", "--reload", "--port", "9040"],
      "cwd": "${workspaceFolder}/backend"
    }
  ]
}
```

## 문제 해결

### 포트 충돌

```bash
# 사용 중인 포트 확인
netstat -an | findstr 4040
netstat -an | findstr 9040

# Docker 컨테이너 확인
docker ps
```

### 데이터베이스 연결 오류

```bash
# DB 컨테이너 상태 확인
docker-compose ps db

# DB 접속 테스트
docker exec -it allergyinsight-db-1 psql -U postgres -d allergyinsight
```

### 의존성 설치 오류

```bash
# npm 캐시 삭제
npm cache clean --force
rm -rf node_modules
npm install

# pip 캐시 삭제
pip cache purge
pip install -r requirements.txt
```
