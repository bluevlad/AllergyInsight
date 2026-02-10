# AllergyInsight 시작 가이드

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

## 접속 URL

| 서비스 | URL |
|--------|-----|
| **웹 애플리케이션** | http://insight.unmong.com:4040/ |
| API 문서 (Swagger) | http://localhost:9040/docs |
| API 서버 | http://localhost:9040 |
| **일반사용자** | http://insight.unmong.com:4040/app |
| **주치의** | http://insight.unmong.com:4040/pro |
| **관리자** | http://insight.unmong.com:4040/admin |

## 테스트 계정

|  구분  | 이름  |    전화번호     |   PIN  |
|-------|-------|---------------|--------|
| 사용자 | 김철수 | 010-9999-8888 | 715302 |
| 주치의 | 이의사 | 010-2222-3333 | 111111 |
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
