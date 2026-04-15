# AllergyInsight 시작 가이드

## 빠른 시작

### Docker로 실행 (권장)

```bash
# 저장소 클론
git clone https://github.com/your-repo/AllergyInsight.git
cd AllergyInsight

# 환경 변수 설정
cp .env.example .env
# .env 파일에 필수 환경 변수를 설정하세요

# 컨테이너 빌드 및 실행
docker compose up -d --build

# 종료
docker compose down
```

### 로컬 개발 환경

```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate  # macOS/Linux
# venv\Scripts\activate   # Windows
pip install -r requirements.txt
uvicorn app.api.main:app --reload --port 9040

# Frontend (별도 터미널)
cd frontend
npm install
npm run dev
```

## 접속 URL

| 서비스 | URL |
|--------|-----|
| 게이트웨이 (메인) | http://localhost:4040/ |
| API 문서 (Swagger) | http://localhost:9040/docs |
| API 서버 | http://localhost:9040 |
| 헬스체크 | http://localhost:9040/api/health |

## 서비스 구조

| 서비스 | 경로 | 설명 | 인증 |
|--------|------|------|------|
| 게이트웨이 | `/` | 서비스 포탈 (비로그인 시 게이트웨이, 로그인 시 역할별 리다이렉트) | 불필요 |
| 일반 사용자 | `/app/*` | 검사 결과 조회 및 맞춤 건강 가이드 | 필요 |
| 주치의 (Professional) | `/pro/*` | 의료진 전용 기능 | 필요 (의료진) |
| 관리자 | `/admin/*` | 플랫폼 관리 및 운영 시스템 | 필요 (관리자) |
| 분석/통계 | `/analytics/*` | 알러젠 트렌드 및 키워드 분석 대시보드 | 불필요 |

## 공개 페이지 (인증 불필요)

| 페이지 | 경로 | 설명 |
|--------|------|------|
| 알러지 리포트 | `/report` | 알러젠 정보 입력 → 맞춤 관리 리포트 |
| AI 상담 | `/ai/consult` | 알러지 관련 논문 기반 AI 질의응답 |
| 알러지 인사이트 | `/ai/insight` | 알러젠별 논문, 뉴스, 트렌드 정보 |
| 뉴스레터 구독 | `/subscribe` | 알러지 최신 뉴스/연구 동향 구독 |
| 구독 관리 | `/subscribe/manage` | 구독 설정 변경 및 해지 |
| 로그인 | `/login` | 간편 로그인 (이름 + 전화번호 + PIN) |
| 관리자 로그인 | `/admin/login` | 관리자 전용 로그인 (Google OAuth) |

## 포트 매핑

| 서비스 | 포트 |
|--------|------|
| Backend API | 9040 |
| Frontend | 4040 |

## 필수 환경 변수

```
DATABASE_URL=               # PostgreSQL 연결 문자열
JWT_SECRET_KEY=             # JWT 서명 키
OPENAI_API_KEY=             # OpenAI API 키
```

상세 환경 변수 목록은 `CLAUDE.md`의 Required Environment Variables 섹션을 참조하세요.

## 지원 알러젠

**식품**: 땅콩, 우유, 계란, 밀, 대두, 생선, 갑각류, 견과류, 참깨

**흡입성**: 집먼지진드기, 꽃가루, 곰팡이, 반려동물, 바퀴벌레, 라텍스, 벌독
