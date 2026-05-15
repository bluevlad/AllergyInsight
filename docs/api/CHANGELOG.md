# API 변경 이력

## [2.1.1] - 2026-05-15

### Added
- 알러젠 직접 뉴스 수집 파이프라인 (`allergen-trend-followup-plan` §2)
  - `CompetitorNewsService.search_allergen_news()` / `collect_allergen_news()`
  - `AllergenMaster.name_kr / name_en` 기반 검색 키워드 빌더 (`allergen_news_keywords.py`)
  - 매주 일요일 06:30 KST `job_allergen_news_collection` 스케줄러 잡
- `NewsAllergenLink` write-time deterministic 태깅 — 검색 시점 `allergen_code` 가 결정되어 LLM 추정 없이 즉시 링크 생성

### Why
- 기존 종합 트렌드 뉴스 섹션이 0건이었던 문제 (경쟁사 뉴스만 알러젠 태깅) 해소

---

## [2.1.0] - 2026-03-16

### Added
- LLM 이중화 프로바이더 구조 (Gemini 2.5 Flash + 로컬 MLX)
- 뉴스 관련성 필터 (`relevance_score`, `is_relevant`)
- 뉴스레터 품질 게이트 (관련성/중요도/요약 검증)
- 뉴스 AI 분석 통합 프롬프트 (기사당 1회 호출로 4항목 동시 분석)
- 관리자 메뉴에 뉴스레터/구독자 관리 추가

### Changed
- `OllamaService`: 용도별 LLM 프로바이더 분리 (`NEWS_LLM_PROVIDER`, `RAG_LLM_PROVIDER`)
- `analyze_article()`: 통합 프롬프트 방식으로 API 효율화
- `_get_today_articles()`: 관련성/중요도/요약 품질 필터 적용

---

## [2.0.0] - 2025-01

### Breaking Changes
- API prefix 변경: 서비스별 분리
  - `/api/pro/*` - Professional API
  - `/api/consumer/*` - Consumer API
- 기존 `/api/admin/*`, `/api/hospital/*` 엔드포인트 제거

### Added

#### Professional API (`/api/pro/*`)
| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | `/pro/dashboard/stats` | 대시보드 통계 |
| POST | `/pro/diagnosis` | 진단 입력 |
| GET | `/pro/diagnosis/{id}` | 진단 조회 |
| GET | `/pro/diagnosis/{id}/prescription` | 처방 권고 조회 |
| GET | `/pro/patients` | 환자 목록 |
| POST | `/pro/patients` | 환자 등록 |
| GET | `/pro/patients/{id}` | 환자 상세 |
| GET | `/pro/patients/{id}/diagnoses` | 환자 진단 이력 |
| POST | `/pro/research/search` | 논문 검색 |
| POST | `/pro/research/qa` | Q&A |

#### Consumer API (`/api/consumer/*`)
| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | `/consumer/my/diagnoses` | 내 진단 목록 |
| GET | `/consumer/my/diagnoses/latest` | 최신 진단 |
| GET | `/consumer/my/diagnoses/{id}` | 진단 상세 |
| GET | `/consumer/my/diagnoses/{id}/guide` | 환자 가이드 |
| GET | `/consumer/guide/foods` | 식품 가이드 |
| GET | `/consumer/guide/lifestyle` | 생활 관리 가이드 |
| GET | `/consumer/emergency/guidelines` | 응급 대처 가이드 |
| POST | `/consumer/kit/register` | 키트 등록 |

### Deprecated
- 없음

### Removed
- `/api/admin/*` - `/api/pro/*`로 통합
- `/api/hospital/*` - `/api/pro/*`로 통합

---

## [1.5.0] - 2024-12

### Added
- 조직 관리 API (`/api/organizations/*`)
- 병원 환자 관리 API (`/api/hospital/*`)

---

## [1.0.0] - 2024-11

### Added
- 인증 API (`/api/auth/*`)
- 진단 API (`/api/diagnosis/*`)
- 알러젠 API (`/api/allergens/*`)
- 논문 API (`/api/papers/*`)
