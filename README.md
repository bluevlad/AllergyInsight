# AllergyInsight

알러지 검사 결과 기반 지능형 정보 시스템

## 소개

AllergyInsight는 알러지 검사 결과를 기반으로 맞춤형 건강 정보를 제공하는 웹 애플리케이션입니다.
- 검사 결과에 따른 예상 증상 및 위험도 안내
- 식이 관리 가이드 (회피 식품, 대체 식품, 교차반응)
- 관련 학술 논문 검색 및 출처 기반 Q&A
- 응급 대처 및 의료 상담 권고

## 기술 스택

### Backend

| 기술 | 용도 |
|------|------|
| Python 3.10+ | 메인 언어 |
| FastAPI | REST API 프레임워크 |
| SQLAlchemy | ORM |
| PostgreSQL 15 | 관계형 데이터베이스 |

### Frontend

| 기술 | 용도 |
|------|------|
| React 18 | UI 프레임워크 |
| Vite | 빌드 도구 |
| React Router | 라우팅 |
| Recharts | 차트 시각화 |
| Axios | HTTP 클라이언트 |

### Infrastructure

| 기술 | 용도 |
|------|------|
| Docker / Docker Compose | 컨테이너화 및 오케스트레이션 |

## 문서

- [시작 가이드](./docs/GETTING_STARTED.md) - 설치, 접속 URL, 테스트 계정, 주요 화면
- [기술 구현 상세](./docs/IMPLEMENTATION.md) - 아키텍처, API, 프로젝트 구조
- [백엔드 상세](./backend/README.md) - 백엔드 API 및 서비스
- [프론트엔드 상세](./frontend/README.md) - 프론트엔드 컴포넌트 및 라우팅
