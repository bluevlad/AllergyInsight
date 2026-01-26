# AllergyInsight

<p align="center">
  <img src="https://img.shields.io/badge/version-2.0.0-blue.svg" alt="Version">
  <img src="https://img.shields.io/badge/license-MIT-green.svg" alt="License">
  <img src="https://img.shields.io/badge/status-Active-success.svg" alt="Status">
</p>

> **SGTi-Allergy Screen PLUS 기반 알러지 진단 및 처방 권고 시스템**

AllergyInsight는 알러지 검사 결과를 분석하여 의료진에게는 근거 기반 처방 권고를, 환자에게는 맞춤형 생활 가이드를 제공하는 통합 헬스케어 플랫폼입니다.

---

## 📋 목차

| 섹션 | 설명 |
|------|------|
| [1. 프로젝트 개요](./1.-Project-Overview) | 비전, 목표, 핵심 가치 |
| [2. 아키텍처](./2.-Architecture) | 시스템 구조, 기술 스택 |
| [3. 도메인 모델](./3.-Domain-Model) | 엔티티, ER 다이어그램 |
| [4. API 명세](./4.-API-Specification) | REST API 문서 |
| [5. 개발 가이드](./5.-Development-Guide) | 환경 설정, 컨벤션 |
| [6. 배포](./6.-Deployment) | CI/CD, 인프라 |
| [7. 로드맵](./7.-Roadmap) | 릴리스 계획, 마일스톤 |
| [8. 사용자 가이드](./8.-User-Guide) | 사용 매뉴얼 |

---

## 🎯 핵심 기능

### Professional Service (의료진 전용)
| 기능 | 설명 |
|------|------|
| **진단 입력** | SGTi-Allergy Screen PLUS 검사 결과 입력 및 관리 |
| **처방 권고** | 알러젠별 회피 식품, 대체 식품, 주의사항 자동 생성 |
| **환자 관리** | 환자 등록, 진단 이력 관리, 동의서 처리 |
| **논문 검색** | PubMed/Semantic Scholar 기반 최신 연구 검색 |
| **Q&A 시스템** | 논문 기반 질의응답 (RAG) |

### Consumer Service (환자용)
| 기능 | 설명 |
|------|------|
| **내 진단 결과** | 검사 결과 조회 및 상세 분석 |
| **식품 가이드** | 회피/대체 식품, 교차반응 정보 |
| **응급 대처** | 아나필락시스 대응, 에피펜 사용법 |
| **생활 관리** | 알러젠별 일상 관리 팁 |
| **키트 등록** | 검사 키트 시리얼/PIN 등록 |

---

## 🏗️ 시스템 구조

```
┌─────────────────────────────────────────────────────────────┐
│                        Client Layer                         │
├────────────────────────┬────────────────────────────────────┤
│   Professional App     │         Consumer App               │
│   /pro/*               │         /app/*                     │
│   (React + Vite)       │         (React + Vite)             │
├────────────────────────┴────────────────────────────────────┤
│                      API Gateway (Nginx)                    │
├─────────────────────────────────────────────────────────────┤
│                      Backend (FastAPI)                      │
├──────────────┬──────────────┬───────────────────────────────┤
│  /api/pro/*  │/api/consumer/*│      /api/* (Core)           │
│  Professional│   Consumer   │   Auth, Allergen, Papers      │
├──────────────┴──────────────┴───────────────────────────────┤
│                     Data Layer                              │
├─────────────────────────┬───────────────────────────────────┤
│     PostgreSQL          │           Redis (Cache)           │
└─────────────────────────┴───────────────────────────────────┘
```

---

## 🛠️ 기술 스택

### Backend
| 기술 | 버전 | 용도 |
|------|------|------|
| Python | 3.11+ | 런타임 |
| FastAPI | 0.100+ | Web Framework |
| SQLAlchemy | 2.0+ | ORM |
| PostgreSQL | 15+ | Database |
| Redis | 7+ | 캐싱 |

### Frontend
| 기술 | 버전 | 용도 |
|------|------|------|
| React | 18+ | UI Framework |
| Vite | 5+ | Build Tool |
| React Router | 6+ | Routing |
| Axios | 1+ | HTTP Client |

### Infrastructure
| 기술 | 용도 |
|------|------|
| Docker | 컨테이너화 |
| Docker Compose | 로컬 개발 환경 |
| GitHub Actions | CI/CD |
| Nginx | 리버스 프록시 |

---

## 🚀 빠른 시작

### 사전 요구사항
- Docker & Docker Compose
- Git

### 실행 방법
```bash
# 1. 저장소 클론
git clone https://github.com/bluevlad/AllergyInsight.git
cd AllergyInsight

# 2. 환경 변수 설정 (선택)
cp .env.example .env

# 3. 서비스 시작
docker-compose up -d

# 4. 접속
# Frontend: http://localhost:4040
# Backend API: http://localhost:9040
```

### 테스트 계정
| 역할 | 이름 | 전화번호 | 접속 PIN |
|------|------|----------|----------|
| 일반 사용자 | 김철수 | 010-9999-8888 | 715302 |
| 의사 | 이의사 | 010-2222-3333 | (별도 문의) |
| 관리자 | 관리자 | 010-1111-2222 | (별도 문의) |

---

## 📊 프로젝트 현황

### 버전 정보
| 버전 | 상태 | 주요 변경사항 |
|------|------|---------------|
| v2.0.0 | **현재** | 서비스 이원화 (Professional/Consumer) |
| v1.1.0 | 완료 | 병원 관리 시스템 추가 |
| v1.0.0 | 완료 | 초기 릴리스 |

### 개발 현황
| Phase | 내용 | 상태 |
|-------|------|------|
| Phase 1 | 서비스 이원화 | ✅ 완료 |
| Phase 2 | 논문 출처 자동 추출 | 🔄 진행중 |
| Phase 3 | 다기관 연동 | 📋 예정 |

---

## 📁 프로젝트 구조

```
AllergyInsight/
├── backend/
│   └── app/
│       ├── api/              # FastAPI 앱
│       ├── core/             # 공통 모듈 (Auth, Allergen)
│       ├── professional/     # 의료진 서비스
│       ├── consumer/         # 환자 서비스
│       ├── database/         # DB 모델
│       └── services/         # 비즈니스 로직
├── frontend/
│   └── src/
│       ├── shared/           # 공통 컴포넌트
│       ├── apps/
│       │   ├── professional/ # 의료진 앱
│       │   └── consumer/     # 환자 앱
│       └── pages/            # 공개 페이지
├── docs/                     # 문서
└── docker-compose.yml
```

---

## 🔗 관련 링크

| 링크 | 설명 |
|------|------|
| [GitHub Repository](https://github.com/bluevlad/AllergyInsight) | 소스 코드 |
| [API Documentation](http://localhost:9040/docs) | Swagger UI |
| [Issue Tracker](https://github.com/bluevlad/AllergyInsight/issues) | 버그 리포트 / 기능 요청 |

---

## 👥 팀

| 역할 | 담당 |
|------|------|
| Project Owner | bluevlad |
| Development | Claude Code (AI Assistant) |

---

## 📄 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다. 자세한 내용은 [LICENSE](../LICENSE) 파일을 참조하세요.

---

<p align="center">
  <sub>© 2024-2026 AllergyInsight. All rights reserved.</sub>
</p>
