# AllergyInsight Frontend

React + Vite 기반 프론트엔드 애플리케이션

## 기술 스택

| 기술 | 버전 | 용도 |
|------|------|------|
| React | 18.2.0 | UI 프레임워크 |
| Vite | 5.4.2 | 빌드 도구 |
| React Router | 6.22.0 | 라우팅 |
| Recharts | 2.12.0 | 차트 시각화 |
| Axios | 1.6.7 | HTTP 클라이언트 |

## 프로젝트 구조

```
frontend/
├── src/
│   ├── contexts/
│   │   └── AuthContext.jsx      # 인증 상태 관리 (Context API)
│   ├── pages/
│   │   ├── LoginPage.jsx        # 로그인/회원가입 페이지
│   │   ├── AuthCallback.jsx     # OAuth 콜백 처리
│   │   ├── MyDiagnosisPage.jsx  # 내 진단 결과 (사용자)
│   │   ├── Dashboard.jsx        # 대시보드 (관리자)
│   │   ├── SearchPage.jsx       # 논문 검색
│   │   ├── QAPage.jsx           # Q&A
│   │   ├── PapersPage.jsx       # 논문 목록
│   │   ├── DiagnosisPage.jsx    # 진단 결과 입력
│   │   └── PrescriptionPage.jsx # 처방 정보
│   ├── services/
│   │   └── api.js               # API 클라이언트 (Axios)
│   ├── App.jsx                  # 메인 앱 (라우팅 정의)
│   ├── main.jsx                 # 엔트리 포인트
│   └── index.css                # 전역 스타일
├── public/
├── Dockerfile
├── package.json
├── vite.config.js
└── README.md
```

## 라우팅 구조

### 공개 라우트
| 경로 | 컴포넌트 | 설명 |
|------|----------|------|
| `/login` | LoginPage | 로그인/회원가입 |
| `/auth/callback` | AuthCallback | OAuth 콜백 처리 |

### 사용자 라우트 (로그인 필요)
| 경로 | 컴포넌트 | 설명 |
|------|----------|------|
| `/` | MyDiagnosisPage | 내 진단 결과 |
| `/diagnosis` | DiagnosisPage | 진단 결과 입력 |
| `/prescription` | PrescriptionPage | 처방 정보 |
| `/qa` | QAPage | Q&A |

### 관리자 라우트
| 경로 | 컴포넌트 | 설명 |
|------|----------|------|
| `/admin` | Dashboard | 관리자 대시보드 |
| `/admin/search` | SearchPage | 논문 검색 |
| `/admin/papers` | PapersPage | 논문 목록 |

## 인증 시스템

### AuthContext
```jsx
// 제공하는 값
{
  user,           // 현재 사용자 정보
  token,          // JWT 토큰
  isAuthenticated,// 로그인 여부
  isLoading,      // 로딩 상태
  login,          // 로그인 함수
  logout,         // 로그아웃 함수
  setToken,       // 토큰 설정 함수
}
```

### 사용 예시
```jsx
import { useAuth } from '../contexts/AuthContext';

function MyComponent() {
  const { user, isAuthenticated, logout } = useAuth();

  if (!isAuthenticated) {
    return <Navigate to="/login" />;
  }

  return <div>안녕하세요, {user.name}님</div>;
}
```

## API 클라이언트

### 기본 설정
```javascript
// services/api.js
const api = axios.create({
  baseURL: 'http://localhost:9040',
  timeout: 30000,
});

// JWT 토큰 자동 첨부
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});
```

### API 함수
```javascript
// 인증
authApi.googleLogin()           // Google OAuth 시작
authApi.simpleRegister(data)    // 간편 회원가입
authApi.simpleLogin(data)       // 간편 로그인
authApi.getMe()                 // 현재 사용자 정보

// 진단
diagnosisApi.getList()          // 내 진단 목록
diagnosisApi.getDetail(id)      // 진단 상세
diagnosisApi.getPrescription(id)// 처방 정보

// 논문 검색
searchApi.search(params)        // 논문 검색
searchApi.getAllergens()        // 알러지 목록
qaApi.ask(question)             // Q&A
```

## 컴포넌트 설명

### LoginPage
- Google OAuth 로그인 버튼
- 간편 로그인 (이름 + 전화번호/생년월일 + PIN)
- 간편 회원가입 (이름 + 전화번호/생년월일 + 키트 시리얼 + 키트 PIN)

### MyDiagnosisPage
- 사용자의 진단 결과 목록
- 각 알러지 항목별 등급 표시 (0-6)
- 처방 정보 연결

### Dashboard (관리자)
- 시스템 통계 (논문 수, 검색 수, 사용자 수)
- 알러지별 논문 수집 현황 차트
- 최근 활동 로그

## 로컬 개발 환경

### 1. 의존성 설치
```bash
cd frontend
npm install
```

### 2. 환경변수 설정
```bash
# .env 파일 생성 (필요시)
VITE_API_URL=http://localhost:9040
```

### 3. 개발 서버 실행
```bash
npm run dev
```

### 4. 빌드
```bash
npm run build
```

### 5. 프리뷰
```bash
npm run preview
```

## Docker 실행

```dockerfile
# Dockerfile
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 4040
CMD ["nginx", "-g", "daemon off;"]
```

```bash
docker build -t allergyinsight-frontend .
docker run -p 4040:4040 allergyinsight-frontend
```

## 스타일 가이드

### 색상 팔레트
```css
:root {
  --primary: #4f46e5;      /* 인디고 */
  --primary-hover: #4338ca;
  --success: #10b981;      /* 에메랄드 */
  --warning: #f59e0b;      /* 앰버 */
  --danger: #ef4444;       /* 레드 */
  --gray-50: #f9fafb;
  --gray-100: #f3f4f6;
  --gray-900: #111827;
}
```

### 알러지 등급 색상
| 등급 | 의미 | 색상 |
|------|------|------|
| 0 | 음성 | #10b981 (green) |
| 1 | 약양성 | #84cc16 (lime) |
| 2 | 양성 | #eab308 (yellow) |
| 3 | 중등도 양성 | #f97316 (orange) |
| 4 | 강양성 | #ef4444 (red) |
| 5-6 | 매우 강양성 | #dc2626 (dark red) |

---

Copyright (c) 2024-2026 운몽시스템즈 (Unmong Systems). All rights reserved.
