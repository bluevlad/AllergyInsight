# 논문 수집 정보 표시 기능

## 개요

관리자 논문 관리 화면에서 각 논문의 **원본 링크**와 **수집 근거**(왜 이 논문이 수집되었는지)를 표시하는 기능.

## 구현 범위

### 1단계: 논문 원본 링크 (완료)

논문 카드에 PubMed/DOI 원본 페이지로 연결되는 링크 버튼 표시.

| 필드 | URL 패턴 | 비고 |
|------|----------|------|
| `pmid` | `https://pubmed.ncbi.nlm.nih.gov/{pmid}` | PubMed 논문 |
| `doi` | `https://doi.org/{doi}` | DOI 논문 |
| `url` | 저장된 URL 그대로 | pmid/doi 없을 때 fallback |

### 2단계: 연결 알레르겐 + 관계유형 (완료)

`PaperAllergenLink` 테이블을 JOIN하여 논문과 연결된 알레르겐 정보를 태그로 표시.

- **알레르겐 이름**: `allergen_master.py`의 `name_kr` 참조
- **관계 유형**: symptom(증상), dietary(식이), cross_reactivity(교차반응), substitute(대체식품), emergency(응급), management(관리), general(일반)
- 유형별 색상 구분 태그로 시각화

### 3단계: 검색 키워드 표시 (완료)

`PaperAllergenLink.note` 필드에서 `"Auto-extracted: {keyword}"` 형태의 자동 추출 키워드를 파싱하여 표시.

### 4단계: SearchHistory 직접 연결 (향후)

현재 `Paper`와 `SearchHistory` 간 직접 FK가 없어 시간대 매칭으로 추정.
향후 `Paper` 테이블에 `search_history_id` 컬럼 추가 시 정확한 수집 이력 추적 가능.

**현재 상태**: `PaperAllergenLink`의 정보만으로 충분한 수집 근거 제공 가능하여 우선순위 낮음.

## 변경 파일

### Backend
| 파일 | 변경 내용 |
|------|----------|
| `backend/app/admin/schemas.py` | `AllergenLinkItem` 스키마 추가, `PaperListItem`에 `pmid`, `doi`, `url`, `allergen_links`, `collection_reason` 필드 추가 |
| `backend/app/admin/routes.py` | `GET /api/admin/papers` 응답에 `PaperAllergenLink` JOIN, `_build_collection_reason()` 헬퍼 함수 추가 |

### Frontend
| 파일 | 변경 내용 |
|------|----------|
| `frontend/src/apps/admin/pages/PapersPage.jsx` | 원본 링크 버튼, 알레르겐 태그, 수집 근거 문구 UI 추가 |

## 수집 근거 표시 형태

```
PubMed 자동 수집 | 대상 알레르겐: 땅콩, 우유 | 관련 유형: 식이, 교차반응 | 검색 키워드: "peanut allergy"
```

## 데이터 흐름

```
스케줄러 (매일 02:00 KST)
  → 알레르겐 로테이션 검색 (16종)
  → Paper 저장 + PaperAllergenLink 연결
  → PaperAllergenLink.note에 "Auto-extracted: {keyword}" 기록

관리자 논문 목록 API
  → Paper + PaperAllergenLink JOIN
  → allergen_master에서 한글명 조회
  → collection_reason 문구 생성
  → 프론트엔드 렌더링
```
