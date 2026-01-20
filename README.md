# AllergyInsight

알러지 검사 결과 기반 지능형 정보 시스템 - RAG(Retrieval-Augmented Generation) 기반 논문 검색 및 Q&A 플랫폼

## 프로젝트 개요

AllergyInsight는 알러지 검사 결과를 기반으로 관련 학술 논문을 검색하고, 논문 내용을 바탕으로 질문에 답변하는 지능형 시스템입니다. PubMed와 Semantic Scholar API를 활용하여 최신 연구 논문을 수집하고, 출처가 명확한 정보를 제공합니다.

## 주요 기능

### 1. 논문 검색 시스템
- **PubMed API 연동**: NIH E-utilities를 통한 의학 논문 검색
- **Semantic Scholar API 연동**: AI 기반 학술 검색 엔진 활용
- **통합 검색**: 두 소스의 결과를 DOI 기반으로 중복 제거 후 병합
- **PDF 다운로드**: 오픈 액세스 논문 PDF 자동 다운로드

### 2. 점진적 논문 수집
- **배치 처리**: 대량 알러지 항원(최대 120개)에 대한 단계적 수집
- **우선순위 기반**: 고등급 알러지 항원 우선 처리
- **캐싱 시스템**: 24시간 TTL 캐시로 API 호출 최소화
- **진행률 추적**: 실시간 수집 진행 상황 모니터링

### 3. Q&A 시스템
- **논문 기반 답변**: 수집된 논문 내용을 기반으로 질문에 답변
- **출처 표시**: 모든 답변에 DOI/PubMed 링크 포함
- **신뢰도 표시**: 답변의 신뢰도 점수 제공
- **사전 정의 질문**: 증상, 위험성, 교차반응, 치료 관련 빠른 질문

### 4. 웹 대시보드
- **통계 현황**: 총 검색 수, 수집된 논문 수, Q&A 질문 수
- **알러지별 수집 현황**: 차트로 시각화
- **최근 검색 이력**: 검색 활동 로그
- **논문 상세 정보**: 초록, 저자, 키워드, 외부 링크

## 시스템 아키텍처

```
┌─────────────────────────────────────────────────────────────┐
│                        Frontend                              │
│                   (React + Vite, Port 4040)                  │
├─────────────────────────────────────────────────────────────┤
│  Dashboard  │  Search Page  │  Q&A Page  │  Papers Page     │
└──────────────────────────┬──────────────────────────────────┘
                           │ HTTP/REST API
┌──────────────────────────▼──────────────────────────────────┐
│                     Backend API                              │
│                 (FastAPI, Port 9040)                         │
├─────────────────────────────────────────────────────────────┤
│  /api/stats     │  /api/search  │  /api/qa  │  /api/allergens│
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│                      Services                                │
├────────────────┬────────────────┬────────────────┬──────────┤
│  PubMed        │  Semantic      │  Knowledge     │  Batch   │
│  Service       │  Scholar       │  Extractor     │  Processor│
└────────────────┴────────────────┴────────────────┴──────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│                   External APIs                              │
├─────────────────────────┬───────────────────────────────────┤
│  PubMed E-utilities     │  Semantic Scholar API             │
│  (NIH/NCBI)             │  (Allen Institute for AI)         │
└─────────────────────────┴───────────────────────────────────┘
```

## 기술 스택

### Backend
| 기술 | 버전 | 용도 |
|------|------|------|
| Python | 3.10+ | 메인 언어 |
| FastAPI | 0.109.0 | REST API 프레임워크 |
| Uvicorn | 0.27.0 | ASGI 서버 |
| Requests | 2.31.0 | HTTP 클라이언트 |
| aiohttp | 3.9.1 | 비동기 HTTP |
| BeautifulSoup4 | 4.12.3 | XML/HTML 파싱 |
| Pydantic | 2.5.3 | 데이터 검증 |

### Frontend
| 기술 | 버전 | 용도 |
|------|------|------|
| React | 18.2.0 | UI 프레임워크 |
| Vite | 5.4.2 | 빌드 도구 |
| React Router | 6.22.0 | 라우팅 |
| Recharts | 2.12.0 | 차트 시각화 |
| Axios | 1.6.7 | HTTP 클라이언트 |

## 프로젝트 구조

```
AllergyInsight/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── main.py              # FastAPI 애플리케이션
│   │   ├── models/
│   │   │   ├── paper.py             # 논문 데이터 모델
│   │   │   └── knowledge_base.py    # Q&A 관련 모델
│   │   └── services/
│   │       ├── pubmed_service.py    # PubMed API 클라이언트
│   │       ├── semantic_scholar_service.py  # S2 API 클라이언트
│   │       ├── paper_search_service.py      # 통합 검색 서비스
│   │       ├── pdf_service.py       # PDF 처리
│   │       ├── batch_processor.py   # 배치 처리
│   │       ├── progressive_loader.py # 점진적 로딩
│   │       ├── knowledge_extractor.py # 지식 추출
│   │       ├── qa_engine.py         # Q&A 엔진
│   │       └── symptom_qa_interface.py # Q&A 인터페이스
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   │   ├── Dashboard.jsx        # 대시보드 페이지
│   │   │   ├── SearchPage.jsx       # 논문 검색 페이지
│   │   │   ├── QAPage.jsx           # Q&A 페이지
│   │   │   └── PapersPage.jsx       # 논문 목록 페이지
│   │   ├── services/
│   │   │   └── api.js               # API 클라이언트
│   │   ├── App.jsx                  # 메인 앱 컴포넌트
│   │   ├── main.jsx                 # 엔트리 포인트
│   │   └── index.css                # 전역 스타일
│   ├── package.json
│   └── vite.config.js
├── run_dev.bat                      # 개발 서버 실행 스크립트
├── .gitignore
└── README.md
```

## API 엔드포인트

### 통계
| 메서드 | 경로 | 설명 |
|--------|------|------|
| GET | `/api/health` | 서버 상태 확인 |
| GET | `/api/stats` | 전체 통계 |
| GET | `/api/stats/summary` | 대시보드용 요약 통계 |

### 논문 검색
| 메서드 | 경로 | 설명 |
|--------|------|------|
| POST | `/api/search` | 논문 검색 |
| GET | `/api/allergens` | 알러지 항원 목록 |
| POST | `/api/batch/search` | 배치 검색 시작 |
| GET | `/api/batch/status/{job_id}` | 배치 상태 조회 |

### Q&A
| 메서드 | 경로 | 설명 |
|--------|------|------|
| POST | `/api/qa` | 질문-답변 |
| GET | `/api/qa/questions/{allergen}` | 사전 정의 질문 목록 |

## 실행 방법

### 1. 의존성 설치

```powershell
# 백엔드 의존성
cd C:\GIT\AllergyInsight\backend
pip install -r requirements.txt

# 프론트엔드 의존성
cd C:\GIT\AllergyInsight\frontend
npm install
```

### 2. 서버 실행

**방법 1: 배치 파일 사용 (Windows)**
```powershell
C:\GIT\AllergyInsight\run_dev.bat
```

**방법 2: 수동 실행**

터미널 1 (백엔드):
```powershell
cd C:\GIT\AllergyInsight\backend
uvicorn app.api.main:app --reload --port 9040
```

터미널 2 (프론트엔드):
```powershell
cd C:\GIT\AllergyInsight\frontend
npm run dev
```

### 3. 접속

| 서비스 | URL |
|--------|-----|
| 대시보드 | http://localhost:4040 |
| API 문서 | http://localhost:9040/docs |
| API 서버 | http://localhost:9040 |

## 화면 구성

### 1. 대시보드 (/)
- 총 검색 수, 수집된 논문 수, Q&A 질문 수 카드
- 알러지 항원별 수집 현황 바 차트
- 최근 검색 이력 테이블
- 캐시 상태 정보

### 2. 논문 검색 (/search)
- 알러지 항원 선택 드롭다운
- 검색 옵션 (교차반응 포함, 결과 수)
- PubMed + Semantic Scholar 통합 검색 결과
- 논문 정보 테이블 (제목, 저자, 연도, 출처)

### 3. Q&A (/qa)
- 알러지 항원 선택
- 빠른 질문 버튼 (증상, 위험성, 교차반응, 치료)
- 채팅 형식 Q&A 인터페이스
- 출처(Citation) 및 DOI 링크
- 신뢰도 점수 표시

### 4. 논문 목록 (/papers)
- 키워드 검색
- 저장된 논문 목록
- 논문 상세 정보 (초록, 저자, 키워드)
- DOI/PubMed/PDF 외부 링크

## 지원 알러지 항원

### 식품 알러지 (Food)
| 영문명 | 한글명 |
|--------|--------|
| peanut | 땅콩 |
| milk | 우유 |
| egg | 계란 |
| wheat | 밀 |
| soy | 대두 |
| fish | 생선 |
| shellfish | 갑각류 |
| tree_nuts | 견과류 |
| sesame | 참깨 |

### 흡입성 알러지 (Inhalant)
| 영문명 | 한글명 |
|--------|--------|
| dust_mite | 집먼지진드기 |
| pollen | 꽃가루 |
| mold | 곰팡이 |
| pet_dander | 반려동물 비듬 |
| cockroach | 바퀴벌레 |

## 향후 개발 계획

### Phase 2: AI 기능 강화
- [ ] ChromaDB 벡터 데이터베이스 연동
- [ ] OpenAI/Claude API 연동 RAG 구현
- [ ] 논문 전문 임베딩 및 의미 검색

### Phase 3: 기능 확장
- [ ] 사용자 인증 시스템
- [ ] 검색 이력 저장 (DB)
- [ ] 논문 북마크 동기화
- [ ] 알림 시스템

### Phase 4: 운영 환경
- [ ] Docker 컨테이너화
- [ ] PostgreSQL 데이터베이스
- [ ] Redis 캐시 서버
- [ ] CI/CD 파이프라인

---

## 저작권 및 라이선스

<div align="center">
  <img src="unmon_192-192.png" alt="Unmong Systems Logo" width="120" height="120">
  <h3>운몽시스템즈 (Unmong Systems)</h3>
</div>

### Copyright

```
Copyright (c) 2024-2026 운몽시스템즈 (Unmong Systems). All rights reserved.
```

### 라이선스 조건

이 소프트웨어 및 관련 문서 파일("소프트웨어")에 대한 모든 권리는 **운몽시스템즈 (Unmong Systems)**에 있습니다.

#### 허용 사항
- 개인적, 비상업적 목적의 학습 및 연구 사용
- 교육 목적의 참고 자료로 활용
- 운몽시스템즈의 서면 승인을 받은 경우의 사용

#### 금지 사항
- 소프트웨어의 무단 복제, 수정, 배포
- 상업적 목적의 사용 또는 판매
- 소프트웨어의 역공학, 디컴파일, 분해
- 저작권 표시 및 라이선스 정보의 제거 또는 수정

#### 면책 조항

이 소프트웨어는 "있는 그대로" 제공되며, 명시적이든 묵시적이든 어떠한 종류의 보증도 제공하지 않습니다.
상품성, 특정 목적에의 적합성, 비침해에 대한 보증을 포함하되 이에 국한되지 않습니다.
어떠한 경우에도 저작권자는 소프트웨어 사용으로 인해 발생하는 어떠한 손해에 대해서도 책임을 지지 않습니다.

### 제3자 라이선스

이 프로젝트는 다음의 오픈소스 라이브러리를 사용합니다:

| 라이브러리 | 라이선스 | 용도 |
|-----------|---------|------|
| FastAPI | MIT | Backend API 프레임워크 |
| React | MIT | Frontend UI 프레임워크 |
| Vite | MIT | Frontend 빌드 도구 |
| Recharts | MIT | 차트 시각화 |
| Axios | MIT | HTTP 클라이언트 |
| BeautifulSoup4 | MIT | HTML/XML 파싱 |
| Pydantic | MIT | 데이터 검증 |

각 라이브러리의 라이선스 조건은 해당 프로젝트의 LICENSE 파일을 참조하세요.

---

## 문의

<div align="center">

**운몽시스템즈 (Unmong Systems)**

프로젝트 관련 문의사항은 아래 채널을 통해 연락해주세요.

| 채널 | 연락처 |
|------|--------|
| GitHub Issues | 기술 문의 및 버그 리포트 |
| Email | rainend00@gmail.com |

</div>

---

<div align="center">
  <sub>Built with by <strong>운몽시스템즈 (Unmong Systems)</strong></sub>
</div>
