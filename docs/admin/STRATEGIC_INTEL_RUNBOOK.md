# Strategic Intel — 운영 Runbook

> 내부 경영진 분석 모듈. super_admin 전용.
> 시스템 구조: [docs/architecture/STRATEGIC_INTEL_OVERVIEW.md](../architecture/STRATEGIC_INTEL_OVERVIEW.md)

본 문서는 백필/재실행/해석/장애 대응 절차를 다룬다.

---

## 1. 백필 스크립트 — 5단계

`backend/scripts/backfill_strategic_intel.py` 가 단일 진입점. 각 단계 idempotent.

| Stage | 내용 | 입력 | 출력 |
|---|---|---|---|
| `seed` | Tech Taxonomy + Fit Matrix v1 시드 | (constants) | `tech_categories`, `company_tech_fits` |
| `prices` | 일별 OHLCV + market_cap 백필 | pykrx + FDR | `daily_prices` |
| `classify` | papers/news LLM 라벨링 | LLM | `paper_tech_links`, `news_tech_links` |
| `generate` | 라벨된 트리거 → 4사 가설 | (룰) | `hypothesis_logs` |
| `validate` | 가설 → T+1d/5d/30d abnormal return + 보조 시그널 | `daily_prices` | `hypothesis_logs.*_return` + `hit_t5d` + `volume_zscore_t1d` |
| `qualitative` | 가설 → LLM 정성 보강 (Phase B) | LLM + fit context | `hypothesis_logs.qualitative_*` |

### 1.1 전체 실행 (기본 — 2025-12-01부터 오늘까지)

```bash
cd backend
python -m scripts.backfill_strategic_intel
```

### 1.2 특정 단계만

```bash
python -m scripts.backfill_strategic_intel --only seed
python -m scripts.backfill_strategic_intel --only prices --start 2026-01-01 --end 2026-04-30
python -m scripts.backfill_strategic_intel --only classify --max-per-run 1400 --rpm-limit 12
python -m scripts.backfill_strategic_intel --only generate
python -m scripts.backfill_strategic_intel --only validate
python -m scripts.backfill_strategic_intel --only qualitative --qualitative-limit 100 --rpm-limit 12
```

### 1.3 단계 제외

```bash
python -m scripts.backfill_strategic_intel --skip seed prices
```

### 1.4 가설 재생성 (룰 변경 후)

```bash
# 기존 가설 삭제 후 재생성 — 임계값 조정·negative 룰 보강 등 룰 변경 시 사용
python -m scripts.backfill_strategic_intel --only generate --regenerate
python -m scripts.backfill_strategic_intel --only validate
```

### 1.5 분류기 한도 페이싱

Gemini 2.5 Flash 무료 티어 (15 RPM / 1,500 RPD) 안에서:

| 옵션 | 기본값 | 의미 |
|---|---|---|
| `--max-per-run` | 1400 | 이번 실행에서 처리할 *총* 항목 수 상한 (RPD 1,500 안전 마진) |
| `--rpm-limit` | 12 | 분당 호출 상한 (15 RPM 안전 마진, 호출 간 ≥5초) |
| `--target` | all | `papers` / `news` / `all` (분리 실행 가능) |

한도 도달 시 graceful exit. 다음 날 재실행하면 `classifier_version` 필터로 미분류 항목만 픽업.

---

## 2. Admin UI — `/admin/strategic-intel`

super_admin 로그인 후 접속. 4탭:

| 탭 | 역할 |
|---|---|
| 가설 검증 | 회사/방향/상태/적중 필터 + 페이지네이션, 행 클릭 시 상세 + 가설 본문 + T+5d 검증치 |
| 리포트 | 이벤트/월간 리포트 목록 + 마크다운 본문 렌더링, 수동 발행 버튼 |
| Fit Matrix | 4사 × 10 카테고리 표 (effective_on 일자 변경 가능) |
| 통계 | 회사별/방향별 적중률, Tech Pulse (트리거 빈도) |

이벤트 리포트 수동 발행: 가설 상세 → "이벤트 리포트 생성" → POST `/admin/strategic-intel/reports/event/{id}`.
월간 리포트 수동 발행: 리포트 탭 → "월간 발행" → POST `/admin/strategic-intel/reports/monthly` (year, month).

---

## 3. 임계값 튜닝

[STRATEGIC_INTEL_OVERVIEW.md §4](../architecture/STRATEGIC_INTEL_OVERVIEW.md) 의 상수를 변경할 때 영향 범위:

| 상수 | 변경 시 재실행 필요 |
|---|---|
| `DEFAULT_MIN_CONFIDENCE` | 분류 → 가설 → 검증 (사실상 전체) |
| `TRIGGER_MIN_CONFIDENCE` | 가설 → 검증 |
| `HIGH_FIT_THRESHOLD` / `LOW_FIT_THRESHOLD` / `COMPETITOR_THREAT_FIT` / `MIN_RELEVANCE_FOR_THREAT` / `NEUTRAL_BAND` | 가설 (`--regenerate`) → 검증 |
| `EVENT_ABNORMAL_THRESHOLD` | 이벤트 리포트 발행 후보만 영향, DB 재처리 불필요 |

**Fit Matrix 변경**:
- `effective_to` 를 채우고 새 row 를 `effective_from` = 변경일로 추가 → 기존 가설은 스냅샷이 보존되어 흔들리지 않음
- 신규 트리거부터 새 fit 적용

---

## 4. 트러블슈팅

### 4.1 분류기에서 `UniqueViolation` 발생

LLM 응답 dedupe 가드(`tech_classifier._parse_response`)와 세션 손상 가드(`classify_and_save_*` 의 `db.rollback()`) 가 도입됨 (commit `c5cf952`). 추가 발생 시 로그에서 `paper_id` / `news_id` 확인 후 분류기 버전 업.

### 4.2 KOSDAQ 종합지수 수집 실패

pykrx KRX 메타 fetch 가 차단된 환경에서는 **FinanceDataReader 가 자동 fallback** (`fdr_symbol="KQ11"`, `primary_source="fdr"`). 두 소스 모두 실패 시 종목 자체 raw return 으로 hit 판정. 적재된 row 의 `daily_prices.source` 컬럼에서 실제 사용된 소스 확인 가능 ('pykrx' | 'fdr').

FDR 도 차단되면:
1. 일시적: 다른 거래일에 재시도 (휴장/일시장애)
2. 지속적: `TRACKED_TICKERS` 의 KOSDAQ 항목 `primary_source` 를 변경하거나 별도 소스 어댑터 추가

### 4.3 가설 미생성

확인 순서:
1. 분류 라벨이 conf ≥ 0.50 으로 저장되었는지 — `paper_tech_links` / `news_tech_links` 조회
2. 트리거 일자 시점에 `company_tech_fits` 가 활성인지 — `effective_from <= trigger_date < effective_to`
3. 룰 임계값이 너무 보수적이지 않은지 — 디버그 로그 활성화 후 `_build_company_impact` 의 own_weighted/competitor_weighted 출력 확인

### 4.4 검증 결과 NULL

`daily_prices` 에 trigger_date + offset 만큼의 거래일이 적재되지 않은 경우. `--only prices --start <trigger_date> --end <today>` 재실행.

### 4.5 가설이 너무 많이 생성됨 (관련도 낮은 negative 다수)

`MIN_RELEVANCE_FOR_THREAT` 임계값 검토 (commit `5629d63`에서 0.15 도입). 추가 룰 보강 후 `--regenerate` 로 재생성.

---

## 5. 일상 운영 체크리스트

자동 스케줄 (KST, `app/scheduler/scheduler_service.py`):

| Job ID | 시간 | 내용 |
|---|---|---|
| `strategic_intel_validate` | 매일 06:30 | pending/partial 가설 → T+1d/5d/30d abnormal return 검증 (batch 500) |
| `strategic_intel_event_scan` | 매일 09:00 | 검증 완료 가설 중 \|abnormal_t5d\|≥5% → 이벤트 리포트 자동 발행 (최근 60일 내) |
| `strategic_intel_daily` | 매일 19:00 (장마감 후) | 최근 4일 시세 + 30일 미분류 항목 분류 (max 400/run, RPM 12) + 가설 생성 + LLM 정성 보강 (max 80/run) |
| `strategic_intel_monthly` | 매월 1일 09:30 | 전월 종합 리포트 자동 발행 |

배치 실패 / 수동 재실행:
- 백필 스크립트 (`backfill_strategic_intel.py --only ...`) 또는
- 스케줄러 admin API: `run_strategic_intel_daily_once` / `run_strategic_intel_validate_once` / `run_strategic_intel_event_scan_once` / `run_strategic_intel_monthly_once`

수기로 점검:
| 주기 | 작업 |
|---|---|
| 주 | 미적중 가설 클러스터 점검 (Stats 탭) |
| 월 | 발행된 월간 리포트 검토 (Admin UI) |
| 분기 | Fit Matrix 재검토 — 회사 신제품 출시·전략 변경 반영 (`effective_from` 갱신) |

---

## 6. 데이터 보관 정책

| 데이터 | 보관 |
|---|---|
| `hypothesis_logs` | 영구 (사후 분석·룰 캘리브레이션 기반) |
| `strategic_intel_reports` | 영구 |
| `daily_prices` | 영구 (외부 fetch 불가 시점 대비) |
| `paper_tech_links` / `news_tech_links` | 영구 (재학습 시 비교 baseline) |

분류기/생성기 재학습 시 `classifier_version` / `generator_version` 으로 신·구 버전 공존 가능.

---

## 7. 외부 노출 금지 원칙

- 본 모듈의 가설·리포트는 **내부 경영 의사결정 보조용**. 투자 자문 아님.
- API/DB 의 어떤 응답도 일반 사용자 페이지·뉴스레터·외부 통합에 사용하지 말 것.
- 리포트 본문에 면책 (`DISCLAIMER`) 자동 포함됨 — 추출·복사 시에도 면책 같이 유지.
