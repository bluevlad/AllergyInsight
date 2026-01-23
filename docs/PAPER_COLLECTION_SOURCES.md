# 알러지 논문 수집 데이터 소스 가이드

## 개요

AllergyInsight 프로젝트에서 알러지 관련 학술 논문을 수집하기 위해 활용 가능한 데이터베이스 및 API를 정리한 문서입니다.

---

## 1. 현재 사용 중인 소스

### 1.1 PubMed / MEDLINE

| 항목 | 내용 |
|------|------|
| **제공** | 미국 국립의학도서관 (NLM) |
| **API URL** | `https://eutils.ncbi.nlm.nih.gov/entrez/eutils` |
| **논문 수** | 3,600만+ |
| **비용** | 무료 |
| **알러지 관련성** | ⭐⭐⭐ 최고 |

**특징**
- 의학/생명과학 논문 최대 데이터베이스
- MeSH(Medical Subject Headings) 용어로 정교한 검색 가능
- API 키 없이 초당 3회, API 키 사용 시 초당 10회 요청 가능

**알러지 검색 쿼리 예시**
```
allergy[MeSH Terms]
hypersensitivity[MeSH Terms]
food allergy[Title/Abstract]
anaphylaxis[MeSH Terms]
```

**API 엔드포인트**
- `esearch.fcgi`: 논문 검색 및 ID 획득
- `efetch.fcgi`: 논문 상세 정보 조회 (XML)
- `einfo.fcgi`: 데이터베이스 정보 조회

**구현 파일**: `backend/app/services/pubmed_service.py`

---

### 1.2 Semantic Scholar

| 항목 | 내용 |
|------|------|
| **제공** | Allen Institute for AI |
| **API URL** | `https://api.semanticscholar.org/graph/v1` |
| **논문 수** | 2억+ |
| **비용** | 무료 (rate limit 있음) |
| **알러지 관련성** | ⭐⭐⭐ |

**특징**
- 오픈액세스 PDF 링크 제공
- 인용 수 및 인용 네트워크 분석
- AI 기반 관련 논문 추천
- 다양한 분야 필터링 지원

**API 엔드포인트**
- `/paper/search`: 논문 검색
- `/paper/{paperId}`: 상세 정보 조회
- `/recommendations/v1/papers/forpaper/{paperId}`: 관련 논문 추천
- `/paper/{paperId}/citations`: 인용 논문 조회

**구현 파일**: `backend/app/services/semantic_scholar_service.py`

---

## 2. 추가 권장 소스 (무료)

### 2.1 Europe PMC

| 항목 | 내용 |
|------|------|
| **제공** | European Bioinformatics Institute (EMBL-EBI) |
| **API URL** | `https://www.ebi.ac.uk/europepmc/webservices/rest` |
| **논문 수** | 4,000만+ |
| **비용** | 무료 |
| **알러지 관련성** | ⭐⭐⭐ |

**특징**
- PubMed + PubMed Central + 유럽 논문 통합
- **전문(Full-text) 무료 제공** (오픈액세스 논문)
- XML, JSON 형식 지원
- 프리프린트 포함

**API 호출 예시**
```bash
# 검색
GET https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=food+allergy&format=json&pageSize=100

# 전문 조회
GET https://www.ebi.ac.uk/europepmc/webservices/rest/{source}/{id}/fullTextXML
```

**장점**
- PubMed 데이터 포함 + 전문 텍스트 제공
- 유럽 연구 자료 추가 확보

---

### 2.2 OpenAlex

| 항목 | 내용 |
|------|------|
| **제공** | OurResearch (비영리) |
| **API URL** | `https://api.openalex.org` |
| **논문 수** | 2.5억+ |
| **비용** | 완전 무료, 제한 없음 |
| **알러지 관련성** | ⭐⭐ |

**특징**
- Microsoft Academic Graph의 후속 프로젝트
- 완전 오픈 데이터, API 키 불필요
- 개념(Concept) 기반 분류 체계
- 저자, 기관, 저널 정보 풍부

**알러지 관련 Concept ID**
- `C71924100`: Allergy
- `C2777710206`: Food allergy
- `C2779770265`: Anaphylaxis

**API 호출 예시**
```bash
# 알러지 개념으로 검색
GET https://api.openalex.org/works?filter=concepts.id:C71924100&per_page=100

# 제목으로 검색
GET https://api.openalex.org/works?filter=title.search:peanut+allergy&per_page=50
```

---

### 2.3 CORE

| 항목 | 내용 |
|------|------|
| **제공** | Open University (영국) |
| **API URL** | `https://api.core.ac.uk/v3` |
| **논문 수** | 2억+ |
| **비용** | 무료 (API 키 필요) |
| **알러지 관련성** | ⭐⭐ |

**특징**
- 오픈액세스 논문 전문(Full-text) 직접 제공
- PDF 다운로드 링크 포함
- 기관 리포지토리 데이터 수집

**API 호출 예시**
```bash
GET https://api.core.ac.uk/v3/search/works?q=food+allergy
Authorization: Bearer {API_KEY}
```

---

### 2.4 Unpaywall

| 항목 | 내용 |
|------|------|
| **제공** | OurResearch |
| **API URL** | `https://api.unpaywall.org/v2` |
| **비용** | 무료 |
| **알러지 관련성** | ⭐⭐ (보조 용도) |

**특징**
- DOI로 무료 PDF 링크 찾기
- 다른 데이터베이스 논문의 PDF 보강 용도
- 간단한 REST API

**API 호출 예시**
```bash
GET https://api.unpaywall.org/v2/10.1016/j.jaci.2020.01.012?email=your@email.com
```

**응답 예시**
```json
{
  "doi": "10.1016/j.jaci.2020.01.012",
  "best_oa_location": {
    "url_for_pdf": "https://...",
    "license": "cc-by"
  }
}
```

---

### 2.5 bioRxiv / medRxiv

| 항목 | 내용 |
|------|------|
| **제공** | Cold Spring Harbor Laboratory |
| **API URL** | `https://api.biorxiv.org/details/[server]/[interval]` |
| **비용** | 무료 |
| **알러지 관련성** | ⭐⭐ |

**특징**
- 생명과학/의학 프리프린트 서버
- 동료 심사 전 최신 연구 확보
- 완전 오픈액세스

**API 호출 예시**
```bash
# 최근 30일 medRxiv 논문
GET https://api.biorxiv.org/details/medrxiv/2024-01-01/2024-01-31

# 특정 DOI 조회
GET https://api.biorxiv.org/details/biorxiv/10.1101/2024.01.01.123456
```

---

### 2.6 ClinicalTrials.gov

| 항목 | 내용 |
|------|------|
| **제공** | NIH (National Institutes of Health) |
| **API URL** | `https://clinicaltrials.gov/api/v2` |
| **비용** | 무료 |
| **알러지 관련성** | ⭐⭐⭐ |

**특징**
- 임상시험 데이터베이스
- 알러지 치료법 효과, 신약 정보
- 진행 중/완료된 임상시험 정보

**API 호출 예시**
```bash
GET https://clinicaltrials.gov/api/v2/studies?query.cond=food+allergy&pageSize=100
```

**활용 방안**
- 알러지 치료법 연구 동향 파악
- 신약 개발 현황 추적

---

### 2.7 CrossRef

| 항목 | 내용 |
|------|------|
| **제공** | CrossRef (비영리) |
| **API URL** | `https://api.crossref.org` |
| **비용** | 무료 |
| **알러지 관련성** | ⭐⭐ (보조 용도) |

**특징**
- DOI 메타데이터 표준
- 인용 관계 정보
- 논문 메타데이터 검증 용도

**API 호출 예시**
```bash
GET https://api.crossref.org/works?query=food+allergy&rows=100
```

---

### 2.8 DOAJ (Directory of Open Access Journals)

| 항목 | 내용 |
|------|------|
| **제공** | Infrastructure Services for Open Access |
| **API URL** | `https://doaj.org/api` |
| **비용** | 무료 |
| **알러지 관련성** | ⭐⭐ |

**특징**
- 오픈액세스 저널 디렉토리
- 신뢰할 수 있는 OA 저널 목록
- 저널 수준 메타데이터

---

### 2.9 WHO IRIS

| 항목 | 내용 |
|------|------|
| **제공** | World Health Organization |
| **API URL** | OAI-PMH 프로토콜 |
| **비용** | 무료 |
| **알러지 관련성** | ⭐⭐ |

**특징**
- WHO 공식 문서 및 가이드라인
- 글로벌 보건 정책 자료

---

## 3. 유료/기관 구독 소스

### 3.1 Scopus

| 항목 | 내용 |
|------|------|
| **제공** | Elsevier |
| **API URL** | `https://api.elsevier.com/content/search/scopus` |
| **논문 수** | 8,400만+ |
| **비용** | 기관 구독 또는 API 구매 |
| **알러지 관련성** | ⭐⭐⭐ |

**특징**
- 가장 큰 초록/인용 데이터베이스
- 인용 분석, h-index, 저자 프로필
- 고급 분석 도구 제공

---

### 3.2 Web of Science

| 항목 | 내용 |
|------|------|
| **제공** | Clarivate Analytics |
| **논문 수** | 1.8억+ |
| **비용** | 기관 구독 필요 |
| **알러지 관련성** | ⭐⭐⭐ |

**특징**
- Impact Factor 원천 데이터
- 인용 네트워크 분석
- 학술 품질 평가 표준

---

### 3.3 Embase

| 항목 | 내용 |
|------|------|
| **제공** | Elsevier |
| **비용** | 기관 구독 필요 |
| **알러지 관련성** | ⭐⭐⭐ |

**특징**
- 약학/의학 특화 데이터베이스
- MEDLINE보다 유럽 저널 coverage 우수
- 약물 관련 연구에 강점

---

### 3.4 Cochrane Library

| 항목 | 내용 |
|------|------|
| **제공** | Cochrane Collaboration |
| **비용** | 일부 무료, 전체 접근 유료 |
| **알러지 관련성** | ⭐⭐⭐ |

**특징**
- 체계적 문헌고찰(Systematic Review) 최고 품질
- 근거 기반 의학의 표준
- 알러지 치료 가이드라인의 근거 자료

---

## 4. 알러지 특화 데이터베이스

| 소스 | 설명 | 접근성 |
|------|------|--------|
| **EAACI Knowledge Hub** | 유럽알러지임상면역학회 자료 | 회원/일부 무료 |
| **AAAAI Resources** | 미국알러지천식면역학회 | 회원/일부 무료 |
| **AllerGen NCE** | 캐나다 알러지 연구 네트워크 | 무료 |
| **WAO Resources** | 세계알러지기구 | 무료 |
| **FARE Research** | Food Allergy Research & Education | 무료 |
| **Allergome** | 알러젠 데이터베이스 | 무료 |
| **WHO/IUIS Allergen** | 공식 알러젠 명명 데이터베이스 | 무료 |

---

## 5. 소스별 비교표

### 5.1 무료 API 비교

| 소스 | 의학 특화 | 전문 제공 | PDF 링크 | API 제한 | 실시간성 |
|------|----------|----------|----------|----------|----------|
| PubMed | ⭐⭐⭐ | ❌ | ❌ | 초당 3-10회 | 일간 업데이트 |
| Semantic Scholar | ⭐⭐ | ❌ | ✅ | 초당 100회 | 주간 업데이트 |
| Europe PMC | ⭐⭐⭐ | ✅ | ✅ | 제한 낮음 | 일간 업데이트 |
| OpenAlex | ⭐ | ❌ | 일부 | 무제한 | 월간 업데이트 |
| CORE | ⭐ | ✅ | ✅ | 일 10,000회 | 주간 업데이트 |
| Unpaywall | - | ❌ | ✅ | 초당 10회 | 실시간 |

### 5.2 데이터 품질 비교

| 소스 | 메타데이터 | 초록 | 키워드 | 인용 정보 |
|------|-----------|------|--------|----------|
| PubMed | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ (MeSH) | ❌ |
| Semantic Scholar | ⭐⭐ | ⭐⭐ | ⭐⭐ | ⭐⭐⭐ |
| Europe PMC | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ | ⭐⭐ |
| OpenAlex | ⭐⭐ | ⭐⭐ | ⭐⭐ (Concepts) | ⭐⭐⭐ |
| Scopus | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ |

---

## 6. 권장 구현 우선순위

### 6.1 1단계 (필수)
- [x] PubMed - 의학 논문 메타데이터 (구현 완료)
- [x] Semantic Scholar - PDF 링크 + 인용 분석 (구현 완료)

### 6.2 2단계 (권장)
- [ ] Europe PMC - 전문(Full-text) 무료 제공
- [ ] OpenAlex - 대규모 메타데이터 보강
- [ ] Unpaywall - PDF 링크 보강

### 6.3 3단계 (선택)
- [ ] ClinicalTrials.gov - 임상시험 데이터
- [ ] bioRxiv/medRxiv - 최신 프리프린트
- [ ] CORE - 추가 전문 텍스트

### 6.4 4단계 (기관 구독 시)
- [ ] Scopus - 인용 분석 강화
- [ ] Cochrane - 체계적 문헌고찰

---

## 7. 통합 아키텍처 제안

```
┌─────────────────────────────────────────────────────────────┐
│                    PaperSearchService                       │
│                      (통합 검색 서비스)                       │
└─────────────────────────────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
        ▼                   ▼                   ▼
┌───────────────┐   ┌───────────────┐   ┌───────────────┐
│    PubMed     │   │   Semantic    │   │   Europe      │
│    Service    │   │   Scholar     │   │   PMC         │
└───────────────┘   └───────────────┘   └───────────────┘
        │                   │                   │
        └───────────────────┼───────────────────┘
                            │
                            ▼
                ┌───────────────────────┐
                │   중복 제거 & 병합     │
                │   (DOI/PMID 기반)     │
                └───────────────────────┘
                            │
            ┌───────────────┼───────────────┐
            │               │               │
            ▼               ▼               ▼
    ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
    │  Unpaywall  │ │   CORE      │ │  OpenAlex   │
    │ (PDF 보강)  │ │ (전문 보강) │ │ (인용 보강) │
    └─────────────┘ └─────────────┘ └─────────────┘
                            │
                            ▼
                ┌───────────────────────┐
                │   자동 링크 추출       │
                │   (알러젠-증상-식품)   │
                └───────────────────────┘
                            │
                            ▼
                ┌───────────────────────┐
                │   데이터베이스 저장    │
                └───────────────────────┘
```

---

## 8. API 키 관리

### 8.1 필요한 API 키

| 소스 | API 키 필요 | 발급 방법 |
|------|------------|----------|
| PubMed | 선택 (권장) | https://www.ncbi.nlm.nih.gov/account/ |
| Semantic Scholar | 선택 | https://www.semanticscholar.org/product/api |
| Europe PMC | 불필요 | - |
| OpenAlex | 불필요 | - |
| CORE | 필수 | https://core.ac.uk/services/api |
| Unpaywall | 불필요 (이메일만) | - |

### 8.2 환경 변수 설정

```bash
# .env 파일
PUBMED_API_KEY=your_pubmed_api_key
PUBMED_EMAIL=your@email.com
SEMANTIC_SCHOLAR_API_KEY=your_s2_api_key
CORE_API_KEY=your_core_api_key
```

---

## 9. 참고 자료

- [PubMed E-utilities Documentation](https://www.ncbi.nlm.nih.gov/books/NBK25501/)
- [Semantic Scholar API Documentation](https://api.semanticscholar.org/api-docs/)
- [Europe PMC REST API](https://europepmc.org/RestfulWebService)
- [OpenAlex Documentation](https://docs.openalex.org/)
- [CORE API Documentation](https://core.ac.uk/documentation/api)
- [Unpaywall API](https://unpaywall.org/products/api)
- [ClinicalTrials.gov API](https://clinicaltrials.gov/data-api/api)

---

## 변경 이력

| 날짜 | 버전 | 변경 내용 |
|------|------|----------|
| 2025-01-23 | 1.0 | 최초 작성 |
