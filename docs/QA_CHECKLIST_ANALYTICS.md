# Analytics 대시보드 QA 체크리스트

> Claude Code Autonomous-QA-Agent가 사용하는 자동 검수 체크리스트

## A. 코드 품질 (10항목)

| ID | 항목 | 검증 방법 |
|----|------|-----------|
| A1 | adminApi.js 엔드포인트가 backend analytics_routes.py의 모든 라우트와 매핑 | Grep으로 양쪽 비교 |
| A2 | import 경로 정확성 (Glob으로 파일 존재 확인) | Glob 각 import 대상 |
| A3 | 각 탭에 loading/error 상태 관리 패턴 존재 | Grep 'setLoading|setError' |
| A4 | 인라인 스타일 패턴 준수 (외부 CSS 파일 없음) | Glob analytics/*.css 없음 |
| A5 | apiClient 경유 호출 (직접 axios/fetch 미사용) | Grep 'import axios|import fetch' |
| A6 | dangerouslySetInnerHTML은 뉴스레터 미리보기만 허용 | Grep dangerouslySetInnerHTML |
| A7 | API 호출 실패 시 에러 상태 표시 | Read 각 탭 catch 블록 |
| A8 | AdminNav에 analytics 메뉴 존재 | Grep '/admin/analytics' in AdminNav |
| A9 | AdminApp에 analytics Route 존재 | Grep 'analytics' in AdminApp |
| A10 | 768px 반응형 미디어 쿼리 존재 | Grep '768px' in AnalyticsPage |

## B. API 연동 (7항목)

| ID | 항목 | Frontend 메서드 | Backend 엔드포인트 |
|----|------|-----------------|-------------------|
| B1 | overview | analytics.overview() | GET /admin/analytics/overview |
| B2 | trend | analytics.trend(code) | GET /admin/analytics/trend/{code} |
| B3 | aggregate | analytics.aggregate() | POST /admin/analytics/aggregate |
| B4 | keywordsOverview | analytics.keywordsOverview() | GET /admin/analytics/keywords/overview |
| B5 | keywordsTrend | analytics.keywordsTrend() | GET /admin/analytics/keywords/trend |
| B6 | keywordsExtract | analytics.keywordsExtract() | POST /admin/analytics/keywords/extract |
| B7 | activityStats | analytics.activityStats() | GET /admin/analytics/activity/stats |

## C. UI/UX (6항목)

| ID | 항목 | 검증 방법 |
|----|------|-----------|
| C1 | 4개 탭 모두 렌더링 (briefing, clinical, market, activity) | Read AnalyticsPage.jsx tabs 배열 |
| C2 | 빈 데이터 상태 graceful 처리 | 각 탭에 빈 상태 메시지 존재 |
| C3 | 차트 ResponsiveContainer 래핑 | Grep ResponsiveContainer |
| C4 | 로딩/에러/빈 상태 표시 | 각 탭에 loading/error/empty 분기 |
| C5 | 탭 전환 정상 동작 | AnalyticsPage useState + 조건부 렌더 |
| C6 | 데이터 재로드 가능 | 각 탭에 새로고침 버튼 존재 |
