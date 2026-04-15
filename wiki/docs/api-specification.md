---
title: API 명세 (API Specification)
---

# 4. API 명세 (API Specification)

## 4.1 API 설계 원칙

### RESTful 원칙

| 원칙 | 적용 |
|------|------|
| **리소스 기반** | URL은 리소스를 나타냄 (`/api/pro/patients`) |
| **HTTP 메서드** | GET(조회), POST(생성), PUT(수정), DELETE(삭제) |
| **상태 코드** | 200(성공), 201(생성), 400(요청오류), 401(인증필요), 403(권한없음), 404(없음), 500(서버오류) |
| **JSON 형식** | 요청/응답 본문은 JSON |

### API 버전

- **현재 버전**: v3.0.0
- **Base URL**: `/api`
- **Swagger UI**: `/docs`

!!! tip "Swagger UI"

    개발 환경에서 `http://localhost:9040/docs` 로 접속하면 전체 API를 탐색하고 테스트할 수 있습니다.

### API Prefix 체계

| Prefix | 대상 | 인증 | 설명 |
|--------|------|------|------|
| `/api/auth/*` | 인증 | 일부 | 로그인, 회원가입, 토큰 관리 |
| `/api/pro/*` | 의료진 | 필수 | Professional 서비스 |
| `/api/consumer/*` | 환자 | 필수 | Consumer 서비스 |
| `/api/admin/*` | 관리자 | 필수 (super_admin) | Admin 콘솔 |
| `/api/public/analytics/*` | 공개 | 불필요 | 트렌드 분석 (읽기 전용) |
| `/api/ai/consult/*` | 공개 | 불필요 | AI 상담 |
| `/api/ai/insight/*` | 공개 | 불필요 | AI 인사이트 |
| `/api/subscribe/*` | 공개 | 불필요 | 뉴스레터 구독 |
| `/api/report/*` | 공개 | 불필요 | 알러지 리포트 |
| `/api/clinicaltrials/*` | 공개 | 불필요 | 임상시험 검색 |

---

## 4.2 인증/인가 (Authentication)

### 인증 API

#### Google OAuth 로그인 (ID 토큰 방식)

```http
POST /api/auth/google/verify
Content-Type: application/json

{
  "id_token": "eyJ..."
}
```

#### 간편 회원가입 (키트 기반)

```http
POST /api/auth/simple/register
Content-Type: application/json

{
  "name": "홍길동",
  "phone": "010-1234-5678",
  "serial_number": "SGT-2024-XXXXX",
  "pin": "123456"
}
```

#### 간편 로그인

```http
POST /api/auth/simple/login
Content-Type: application/json

{
  "name": "홍길동",
  "phone": "010-1234-5678",
  "access_pin": "715302"
}
```

#### 이메일 로그인

```http
POST /api/auth/email/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "password123"
}
```

#### Admin 로그인

```http
POST /api/auth/admin/login
Content-Type: application/json

{
  "name": "관리자",
  "access_pin": "123456"
}
```

#### 현재 사용자 정보

```http
GET /api/auth/me
Authorization: Bearer {token}
```

---

## 4.3 인증 필수 API

=== "Professional API (`/api/pro/*`)"

    ### 진단 관리

    | 메서드 | 경로 | 설명 |
    |--------|------|------|
    | `GET` | `/api/pro/diagnosis` | 진단 목록 |
    | `GET` | `/api/pro/diagnosis/{id}` | 진단 상세 |
    | `POST` | `/api/pro/diagnosis` | 진단 입력 |
    | `PUT` | `/api/pro/diagnosis/{id}` | 진단 수정 |

    ### 환자 관리

    | 메서드 | 경로 | 설명 |
    |--------|------|------|
    | `GET` | `/api/pro/patients` | 환자 목록 |
    | `POST` | `/api/pro/patients` | 환자 등록 |
    | `GET` | `/api/pro/patients/{id}` | 환자 상세 |
    | `PUT` | `/api/pro/patients/{id}` | 환자 수정 |

    ### 연구 (Research)

    | 메서드 | 경로 | 설명 |
    |--------|------|------|
    | `GET` | `/api/pro/research/papers` | 논문 검색 |
    | `POST` | `/api/pro/research/qa` | Q&A 질문 |
    | `GET` | `/api/pro/research/qa` | Q&A 조회 |

    ### 임상 보고서

    | 메서드 | 경로 | 설명 |
    |--------|------|------|
    | `GET` | `/api/pro/clinical-report` | 임상 보고서 조회 |
    | `POST` | `/api/pro/clinical-report` | 임상 보고서 생성 |
    | `GET` | `/api/pro/clinical-report/{patientId}` | 환자별 보고서 |
    | `GET` | `/api/pro/clinical-report/statements` | 임상 진술문 조회 |
    | `GET` | `/api/pro/clinical-report/guidelines` | 가이드라인 목록 |

    ### 대시보드

    | 메서드 | 경로 | 설명 |
    |--------|------|------|
    | `GET` | `/api/pro/dashboard` | 대시보드 통계 |

=== "Consumer API (`/api/consumer/*`)"

    ### 내 진단

    | 메서드 | 경로 | 설명 |
    |--------|------|------|
    | `GET` | `/api/consumer/my/diagnoses` | 내 진단 목록 |
    | `GET` | `/api/consumer/my/diagnoses/{id}` | 진단 상세 |

    ### 가이드

    | 메서드 | 경로 | 설명 |
    |--------|------|------|
    | `GET` | `/api/consumer/guide/food` | 식품 가이드 |
    | `GET` | `/api/consumer/guide/lifestyle` | 생활 관리 |
    | `GET` | `/api/consumer/guide/emergency` | 응급 대처 |

    ### 키트

    | 메서드 | 경로 | 설명 |
    |--------|------|------|
    | `POST` | `/api/consumer/kit/register` | 키트 등록 |

=== "Admin API (`/api/admin/*`)"

    !!! warning "super_admin 역할 필수"

        Admin API는 `super_admin` 역할을 가진 사용자만 접근할 수 있습니다.

    ### 대시보드

    | 메서드 | 경로 | 설명 |
    |--------|------|------|
    | `GET` | `/api/admin/dashboard` | 플랫폼 통계 대시보드 |

    ### 사용자 관리

    | 메서드 | 경로 | 설명 |
    |--------|------|------|
    | `GET` | `/api/admin/users` | 사용자 목록 (페이지네이션, 필터) |
    | `GET` | `/api/admin/users/{id}` | 사용자 상세 |
    | `PUT` | `/api/admin/users/{id}` | 사용자 정보 수정 |
    | `PUT` | `/api/admin/users/{id}/role` | 역할 변경 |
    | `GET` | `/api/admin/users/stats/summary` | 사용자 통계 |

    ### 알러젠 관리

    | 메서드 | 경로 | 설명 |
    |--------|------|------|
    | `GET` | `/api/admin/allergens` | 알러젠 목록 |
    | `GET` | `/api/admin/allergens/{code}` | 알러젠 상세 |
    | `POST` | `/api/admin/allergens` | 알러젠 생성 |
    | `PUT` | `/api/admin/allergens/{code}` | 알러젠 수정 |
    | `DELETE` | `/api/admin/allergens/{code}` | 알러젠 삭제 (soft) |
    | `POST` | `/api/admin/allergens/{code}/restore` | 알러젠 복원 |

    ### 논문 관리

    | 메서드 | 경로 | 설명 |
    |--------|------|------|
    | `GET` | `/api/admin/papers` | 논문 목록 (페이지네이션) |

    ### 조직 관리

    | 메서드 | 경로 | 설명 |
    |--------|------|------|
    | `GET` | `/api/admin/organizations` | 조직 목록 |
    | `POST` | `/api/admin/organizations/{id}/approve` | 조직 승인 |
    | `POST` | `/api/admin/organizations/{id}/reject` | 조직 거절 |

    ### 구독자 관리

    | 메서드 | 경로 | 설명 |
    |--------|------|------|
    | `GET` | `/api/admin/subscribers` | 구독자 목록 |
    | `GET` | `/api/admin/subscribers/stats` | 구독자 통계 |
    | `GET` | `/api/admin/subscribers/{id}` | 구독자 상세 |
    | `PUT` | `/api/admin/subscribers/{id}` | 구독자 수정 |
    | `DELETE` | `/api/admin/subscribers/{id}` | 구독자 삭제 |

    ### 뉴스 관리

    | 메서드 | 경로 | 설명 |
    |--------|------|------|
    | `GET` | `/api/admin/news` | 뉴스 목록 |
    | `POST` | `/api/admin/news/import` | 뉴스 수동 가져오기 |
    | `PUT` | `/api/admin/news/{id}` | 뉴스 수정 |

    ### 분석 관리

    | 메서드 | 경로 | 설명 |
    |--------|------|------|
    | `POST` | `/api/admin/analytics/aggregate` | 월간 집계 실행 |
    | `GET` | `/api/admin/analytics/overview` | 분석 개요 |
    | `GET` | `/api/admin/analytics/trend/{allergen_code}` | 알러젠별 트렌드 |
    | `POST` | `/api/admin/analytics/keywords/extract` | 키워드 추출 |
    | `GET` | `/api/admin/analytics/keywords/overview` | 키워드 개요 |
    | `POST` | `/api/admin/analytics/paper-trend/aggregate` | 논문 트렌드 집계 |
    | `POST` | `/api/admin/analytics/treatments/extract` | 치료법 추출 |
    | `POST` | `/api/admin/analytics/epidemiology/extract` | 역학 데이터 추출 |
    | `GET` | `/api/admin/analytics/activity/stats` | 활동 통계 |

---

## 4.4 공개 API (인증 불필요)

=== "Analytics API (`/api/public/analytics/*`)"

    !!! note "읽기 전용"

        Public Analytics API는 인증 없이 접근 가능한 읽기 전용 API입니다.

    ### 기본 분석

    | 메서드 | 경로 | 설명 |
    |--------|------|------|
    | `GET` | `/api/public/analytics/overview` | 분석 개요 |
    | `GET` | `/api/public/analytics/summary` | 플랫폼 요약 |
    | `GET` | `/api/public/analytics/papers/stats` | 논문 수집 통계 |

    ### 키워드 트렌드

    | 메서드 | 경로 | 설명 |
    |--------|------|------|
    | `GET` | `/api/public/analytics/keywords/overview` | 키워드 개요 |
    | `GET` | `/api/public/analytics/keywords/trend` | 키워드 추세 |

    ### 알러젠 트렌드 (논문 기반)

    | 메서드 | 경로 | 설명 |
    |--------|------|------|
    | `GET` | `/api/public/analytics/allergen-trend/overview` | 논문 기반 트렌드 개요 |
    | `GET` | `/api/public/analytics/allergen-trend/ranking` | 상승/하락 알러젠 |
    | `GET` | `/api/public/analytics/allergen-trend/{allergen_code}` | 알러젠별 논문 트렌드 |

    ### 알러젠 트렌드 (뉴스 기반)

    | 메서드 | 경로 | 설명 |
    |--------|------|------|
    | `GET` | `/api/public/analytics/news-allergen/overview` | 뉴스 알러젠 개요 |
    | `GET` | `/api/public/analytics/news-allergen/{allergen_code}` | 뉴스 알러젠 트렌드 |
    | `GET` | `/api/public/analytics/news/recent` | 최근 뉴스 |

    ### 종합 트렌드

    | 메서드 | 경로 | 설명 |
    |--------|------|------|
    | `GET` | `/api/public/analytics/allergen-comprehensive/{allergen_code}` | 종합 트렌드 |

    ### 치료법

    | 메서드 | 경로 | 설명 |
    |--------|------|------|
    | `GET` | `/api/public/analytics/treatments/overview` | 치료법 개요 |
    | `GET` | `/api/public/analytics/treatments/emerging` | 신흥 치료법 |
    | `GET` | `/api/public/analytics/treatments/{allergen_code}` | 알러젠별 치료법 |

    ### 역학 데이터

    | 메서드 | 경로 | 설명 |
    |--------|------|------|
    | `GET` | `/api/public/analytics/epidemiology/overview` | 역학 개요 |
    | `GET` | `/api/public/analytics/epidemiology/{allergen_code}` | 알러젠별 역학 |

    ### 인사이트

    | 메서드 | 경로 | 설명 |
    |--------|------|------|
    | `GET` | `/api/public/analytics/insights` | 인사이트 보고서 목록 |
    | `GET` | `/api/public/analytics/insights/allergens` | 인사이트 가능 알러젠 |
    | `GET` | `/api/public/analytics/insights/{report_id}` | 인사이트 상세 |

=== "AI Portal API"

    ### AI 상담 (`/api/ai/consult/*`)

    !!! info "Rate Limit: 10/min"

        AI 상담 API는 과도한 사용 방지를 위해 분당 10회로 제한됩니다.

    | 메서드 | 경로 | 설명 |
    |--------|------|------|
    | `POST` | `/api/ai/consult/ask` | 질문 (RAG + 키워드 fallback) |
    | `POST` | `/api/ai/consult/ask/rag` | RAG 전용 질문 |
    | `GET` | `/api/ai/consult/questions/{allergen}` | 사전 정의 질문 |
    | `GET` | `/api/ai/consult/allergens` | 상담 가능 알러젠 |
    | `GET` | `/api/ai/consult/rag/stats` | RAG 인덱스 통계 |
    | `POST` | `/api/ai/consult/rag/index` | RAG 인덱싱 트리거 |

    ### AI 인사이트 (`/api/ai/insight/*`)

    | 메서드 | 경로 | 설명 |
    |--------|------|------|
    | `GET` | `/api/ai/insight/overview` | 인사이트 개요 |
    | `GET` | `/api/ai/insight/allergen/{allergen_code}` | 알러젠별 상세 |
    | `GET` | `/api/ai/insight/news` | 알러지 뉴스 |
    | `GET` | `/api/ai/insight/trends` | 알러지 트렌드 |

=== "기타 Public API"

    ### 뉴스레터 구독 (`/api/subscribe/*`)

    | 메서드 | 경로 | 설명 |
    |--------|------|------|
    | `POST` | `/api/subscribe` | 구독 신청 |
    | `POST` | `/api/subscribe/verify` | 이메일 인증 |
    | `GET` | `/api/subscribe/status` | 구독 상태 확인 |
    | `POST` | `/api/subscribe/unsubscribe` | 구독 해지 |
    | `PUT` | `/api/subscribe/keywords` | 관심 키워드 변경 |
    | `POST` | `/api/subscribe/resend-verification` | 인증 코드 재발송 |

    ### 알러지 리포트 (`/api/report/*`)

    | 메서드 | 경로 | 설명 |
    |--------|------|------|
    | `POST` | `/api/report/generate` | 알러지 리포트 생성 (stateless) |

    ### 임상시험 (`/api/clinicaltrials/*`)

    | 메서드 | 경로 | 설명 |
    |--------|------|------|
    | `GET` | `/api/clinicaltrials/search` | 임상시험 검색 |
    | `GET` | `/api/clinicaltrials/study/{nct_id}` | 임상시험 상세 |
    | `GET` | `/api/clinicaltrials/recruiting` | 모집 중 임상시험 |

---

## 4.5 에러 코드 및 처리

### HTTP 상태 코드

| 코드 | 의미 | 설명 |
|------|------|------|
| 200 | OK | 요청 성공 |
| 201 | Created | 리소스 생성 성공 |
| 400 | Bad Request | 잘못된 요청 |
| 401 | Unauthorized | 인증 필요 |
| 403 | Forbidden | 권한 없음 |
| 404 | Not Found | 리소스 없음 |
| 422 | Unprocessable Entity | 검증 실패 |
| 429 | Too Many Requests | Rate Limit 초과 |
| 500 | Internal Server Error | 서버 오류 |

### Rate Limiting

!!! warning "Rate Limit 정책"

    과도한 API 호출 방지를 위해 엔드포인트 그룹별로 Rate Limit이 적용됩니다.

| API 그룹 | 제한 |
|----------|------|
| 기본 | 60/min |
| 검색 (`/api/search`) | 30/min |
| AI 상담 (`/api/ai/consult/ask`) | 10/min |
| 진단/처방 생성 | 10/min |
| 통계 초기화 | 3/min |

---

## 4.6 API 테스트

### Swagger UI

- URL: `http://localhost:9040/docs`
- 인증: Authorize 버튼 -> Bearer Token 입력

### 테스트 예시 (cURL)

```bash
# 간편 로그인
curl -X POST http://localhost:9040/api/auth/simple/login \
  -H "Content-Type: application/json" \
  -d '{"name":"김철수","phone":"010-9999-8888","access_pin":"715302"}'

# AI 상담 (인증 불필요)
curl -X POST http://localhost:9040/api/ai/consult/ask \
  -H "Content-Type: application/json" \
  -d '{"question":"땅콩 알러지가 있으면 어떤 음식을 피해야 하나요?"}'

# 종합 트렌드 조회 (인증 불필요)
curl http://localhost:9040/api/public/analytics/allergen-comprehensive/peanut
```

---

[← 도메인 모델](domain-model.md) | [다음: 개발 가이드 →](development-guide.md)
