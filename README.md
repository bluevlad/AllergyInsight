# AllergyInsight

알러지 검사 결과 기반 지능형 정보 시스템

## 소개

AllergyInsight는 알러지 검사 결과를 기반으로 맞춤형 건강 정보를 제공하는 웹 애플리케이션입니다.
- 검사 결과에 따른 예상 증상 및 위험도 안내
- 식이 관리 가이드 (회피 식품, 대체 식품, 교차반응)
- 관련 학술 논문 검색 및 출처 기반 Q&A
- 응급 대처 및 의료 상담 권고

## 빠른 시작

### Docker로 실행 (권장)

```bash
# 저장소 클론
git clone https://github.com/your-repo/AllergyInsight.git
cd AllergyInsight

# 컨테이너 빌드 및 실행
docker-compose up -d --build

# 종료
docker-compose down
```

### 접속 URL

| 서비스 | URL |
|--------|-----|
| **웹 애플리케이션** | http://localhost:4040 |
| API 문서 (Swagger) | http://localhost:9040/docs |
| API 서버 | http://localhost:9040 |

## 테스트 계정

| 구분 | 이름 | 전화번호 | PIN |
|------|------|----------|-----|
| 일반 사용자 | 김철수 | 010-9999-8888 | 715302 |
| 관리자 | 관리자 | 010-1111-2222 | 123456 |

## 주요 화면

| 화면 | 경로 | 설명 |
|------|------|------|
| 로그인 | `/login` | 간편 로그인 (이름 + 전화번호 + PIN) |
| 내 검사 결과 | `/my-diagnosis` | 등록된 알러지 검사 결과 조회 |
| 진단 입력 | `/diagnosis` | 직접 검사 결과 입력 |
| Q&A | `/qa` | 논문 기반 질의응답 |
| 논문 검색 | `/admin/search` | PubMed/Semantic Scholar 통합 검색 (관리자) |
| 논문 목록 | `/admin/papers` | 저장된 논문 관리 (관리자) |

## 지원 알러젠

**식품**: 땅콩, 우유, 계란, 밀, 대두, 생선, 갑각류, 견과류, 참깨

**흡입성**: 집먼지진드기, 꽃가루, 곰팡이, 반려동물, 바퀴벌레, 라텍스, 벌독

## 기술 문서

상세 기술 문서는 아래를 참조하세요:

- [기술 구현 상세](./docs/IMPLEMENTATION.md) - 아키텍처, 기술 스택, API, 프로젝트 구조
- [논문 링크 추출 로드맵](./docs/PAPER_LINK_EXTRACTION_ROADMAP.md) - 자동 추출 고도화 방안
- [백엔드 상세](./backend/README.md) - 백엔드 API 및 서비스
- [프론트엔드 상세](./frontend/README.md) - 프론트엔드 컴포넌트 및 라우팅

## 저작권

```
Copyright (c) 2024-2026 운몽시스템즈 (Unmong Systems). All rights reserved.
```

이 소프트웨어는 운몽시스템즈의 자산이며, 무단 복제 및 상업적 사용이 금지됩니다.
상세 라이선스 조건은 [기술 문서](./docs/IMPLEMENTATION.md#저작권-및-라이선스)를 참조하세요.

## 문의

| 채널 | 연락처 |
|------|--------|
| GitHub Issues | 기술 문의 및 버그 리포트 |
| Email | rainend00@gmail.com |

---

<div align="center">
  <sub>Built by <strong>운몽시스템즈 (Unmong Systems)</strong></sub>
</div>
