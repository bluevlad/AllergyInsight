# API 변경 이력

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
