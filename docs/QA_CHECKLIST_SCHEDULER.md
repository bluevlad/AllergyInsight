# 스케줄러 QA 체크리스트

> Claude Code Autonomous-QA-Agent가 사용하는 자동 검수 체크리스트

## A. 코드 품질 (8항목)

| ID | 항목 | 검증 방법 |
|----|------|-----------|
| A1 | NewsSchedulerService.start()에서 5개 작업 등록 호출 | Grep 'add_paper_search_job\|add_korean_translation_job\|add_crawl_job\|add_send_job\|add_insight_job' in scheduler_service.py |
| A2 | timezone="Asia/Seoul" 설정 | Grep 'Asia/Seoul' in scheduler_service.py |
| A3 | misfire_grace_time ≥ 3600 | Read scheduler_service.py에서 misfire_grace_time 값 확인 |
| A4 | job_daily_paper_search import 경로 유효성 | Glob 'backend/app/services/scheduler_jobs.py' 존재 확인 |
| A5 | job_korean_translation import 경로 유효성 | Grep 'def job_korean_translation' in scheduler_jobs.py |
| A6 | 각 작업에 replace_existing=True 설정 | Grep 'replace_existing=True' in scheduler_service.py (5개) |
| A7 | 각 작업에 고유 id 부여 | Grep 'id="daily_paper_search"\|id="korean_translation"\|id="news_crawl"\|id="news_send"\|id="insight_report"' |
| A8 | run_*_once 즉시실행 메서드 존재 (5개) | Grep 'def run_paper_search_once\|def run_korean_translation_once\|def run_crawl_once\|def run_send_once\|def run_insight_once' |

## B. 환경설정 - docker-compose.yml (6항목)

| ID | 항목 | 검증 방법 |
|----|------|-----------|
| B1 | scheduler 서비스에 PUBMED_API_KEY 전달 | Grep 'PUBMED_API_KEY' in docker-compose.yml scheduler 섹션 |
| B2 | scheduler 서비스에 PUBMED_EMAIL 전달 | Grep 'PUBMED_EMAIL' in docker-compose.yml scheduler 섹션 |
| B3 | scheduler 서비스에 SEMANTIC_SCHOLAR_API_KEY 전달 | Grep 'SEMANTIC_SCHOLAR_API_KEY' in docker-compose.yml scheduler 섹션 |
| B4 | scheduler 서비스에 OPENAI_API_KEY 전달 | Grep 'OPENAI_API_KEY' in docker-compose.yml scheduler 섹션 |
| B5 | scheduler 서비스에 DATABASE_URL 전달 | Grep 'DATABASE_URL' in docker-compose.yml scheduler 섹션 |
| B6 | scheduler 서비스에 ENABLE_SCHEDULER=true | Grep 'ENABLE_SCHEDULER=true' in docker-compose.yml scheduler 섹션 |

## C. 스케줄 시간 정합성 (5항목)

| ID | 항목 | 검증 방법 |
|----|------|-----------|
| C1 | 논문 검색: 매일 02:00 KST | Read add_paper_search_job 기본값 hour=2, minute=0 |
| C2 | 한국어 번역: 매일 04:00 KST | Read add_korean_translation_job 기본값 hour=4, minute=0 |
| C3 | 뉴스 수집: 환경변수 기반 (기본 07:00) | Read add_crawl_job 기본값 hour=7, minute=0 |
| C4 | 뉴스레터 발송: 환경변수 기반 (기본 08:00) | Read add_send_job 기본값 hour=8, minute=0 |
| C5 | 인사이트 리포트: 매월 1일 03:00 | Read add_insight_job CronTrigger(day=1, hour=3, minute=0) |

## D. 작업 간 의존성/충돌 (3항목)

| ID | 항목 | 검증 방법 |
|----|------|-----------|
| D1 | 작업 시간 겹침 없음 (02:00, 04:00, 07:00, 08:00 모두 다름) | Read start() 메서드에서 시간 교차 확인 |
| D2 | max_instances=1로 동시 실행 방지 | Grep 'max_instances.*1' in scheduler_service.py |
| D3 | coalesce=True로 밀린 작업 단일 실행 | Grep 'coalesce.*True' in scheduler_service.py |
