# Strategic Intel — 시스템 개요

> 내부 경영진 분석 모듈. 외부 사용자 노출 금지.
> 전략·의사결정 문서: [Claude-Opus-bluevlad/services/allergyinsight/plans/strategic-intel-v1-implementation.md](https://github.com/bluevlad/Claude-Opus-bluevlad/blob/main/services/allergyinsight/plans/strategic-intel-v1-implementation.md)

알러지 IVD 진단 키트/시약 분야 4사 (수젠텍 · 녹십자엠에스 · 바디텍메드 · MADx) 의 기술 동향과 경쟁 포지션을 추적, 논문/뉴스 트리거에 대한 회사별 영향 가설을 생성하고 사후 주가 흐름과의 정합성을 1차 검증한다.

---

## 1. 데이터 모델

| 테이블 | 역할 |
|---|---|
| `tech_categories` | Tech Taxonomy v1.1 — 알러지 IVD 키트/시약 10개 카테고리 (multiplex, CRD, singleplex, POC, MAST, BAT, mediator, microfluidics, biosensor, genomics) |
| `company_tech_fits` | Fit Matrix v1 — 회사 × 카테고리 × 점수(0~1) × `effective_from/to` (시점성 보존) |
| `paper_tech_links` | 논문 ↔ 카테고리 다중 라벨 (LLM 분류, conf≥0.50) |
| `news_tech_links` | 뉴스 ↔ 카테고리 다중 라벨 |
| `daily_prices` | 일별 OHLCV (수젠텍 253840 / 녹십자MS 142280 / 바디텍메드 206640) |
| `hypothesis_logs` | 트리거 → 4사 가설 → T+1d/5d/30d abnormal return 검증 |
| `strategic_intel_reports` | 이벤트(\|abnormal_t5d\|≥5%) + 월간 종합 LLM 리포트 (markdown 본문) |

`hypothesis_logs.tech_categories`, `strategic_intel_reports.metrics` 등 JSON 컬럼은 트리거 시점의 라벨/지표를 **스냅샷**으로 보존한다 (분류기 재학습·fit matrix 변경에 의한 사후 흔들림 방지).

---

## 2. 모듈 구조

```
backend/app/
├── database/
│   ├── strategic_intel_models.py      # 7 테이블 ORM
│   └── seed_strategic_intel.py        # Tech Taxonomy v1 + Fit Matrix v1 시드
├── services/strategic_intel/
│   ├── tech_classifier.py             # LLM 다중 라벨 분류기
│   ├── hypothesis_engine.py           # 룰 기반 가설 + 검증기
│   ├── stock_price_service.py         # pykrx 일별 OHLCV 수집
│   └── report_service.py              # 이벤트/월간 리포트 에이전트
├── admin/
│   ├── strategic_intel_routes.py      # /admin/strategic-intel/* (super_admin)
│   └── strategic_intel_schemas.py     # Pydantic 응답 모델
└── ...

backend/scripts/
└── backfill_strategic_intel.py        # 5단계 일괄/선택 실행

frontend/src/apps/admin/pages/
└── StrategicIntelPage.jsx             # 4탭 — 가설/리포트/Matrix/통계
```

---

## 3. 처리 흐름

```
                           ┌──────────────────────────────────┐
                           │  papers / competitor_news (4사)  │
                           └─────────────┬────────────────────┘
                                         ▼
              ┌──────────────────────────────────────────────────┐
   Stage 3    │  TechClassifier (LLM 다중 라벨, conf≥0.50)        │
              │   → paper_tech_links / news_tech_links           │
              └─────────────┬────────────────────────────────────┘
                            ▼
              ┌──────────────────────────────────────────────────┐
   Stage 4    │  HypothesisGenerator                              │
              │   - fit matrix 로드 (trigger_date 시점)           │
              │   - 룰: own_fit/competitor_fit/relevance 임계값   │
              │   - 4사 × 트리거 = hypothesis_logs N건            │
              └─────────────┬────────────────────────────────────┘
                            ▼
              ┌──────────────────────────────────────────────────┐
   Stage 5    │  HypothesisValidator                              │
              │   - daily_prices 조회 (T+1d/5d/30d 영업일)        │
              │   - benchmark 가용 시 abnormal return, 미가용 시   │
              │     raw return 으로 hit_t5d 판정                  │
              │   - validation_status: pending → validated/closed │
              └─────────────┬────────────────────────────────────┘
                            ▼
              ┌──────────────────────────────────────────────────┐
              │  StrategicIntelReportService                      │
              │   - 이벤트: |abnormal_t5d|≥5% 트리거              │
              │   - 월간: 매월 종합 (Tech Pulse / Verdict /       │
              │           Map Shift / Whitespace / Hit Rate)      │
              └──────────────────────────────────────────────────┘
```

각 단계는 **idempotent**: 분류는 `classifier_version` 필터로 미분류 항목만 픽업, 가설은 `(trigger_type, trigger_id, company)` 중복 skip, 검증은 `validation_status` 진행 단계 기준.

---

## 4. 주요 임계값

| 상수 | 값 | 위치 | 의미 |
|---|---|---|---|
| `DEFAULT_MIN_CONFIDENCE` | 0.50 | `tech_classifier.py` | 라벨 저장 최소 신뢰도 |
| `TRIGGER_MIN_CONFIDENCE` | 0.50 | `hypothesis_engine.py` | 가설 트리거 최소 라벨 신뢰도 |
| `HIGH_FIT_THRESHOLD` | 0.60 | 〃 | 회사 핵심 영역 판정선 (positive) |
| `LOW_FIT_THRESHOLD` | 0.30 | 〃 | 회사 미보유 판정선 |
| `COMPETITOR_THREAT_FIT` | 0.70 | 〃 | 경쟁사 위협 판정선 |
| `MIN_RELEVANCE_FOR_THREAT` | 0.15 | 〃 | negative 트리거 최소 자사 fit (무관 영역 위협 제외) |
| `NEUTRAL_BAND` | (-0.15, 0.15) | 〃 | impact_score neutral 정규화 |
| `EVENT_ABNORMAL_THRESHOLD` | 0.05 | `report_service.py` | \|abnormal_t5d\| ≥ 5% 이벤트 리포트 트리거 |

수정 시 [STRATEGIC_INTEL_RUNBOOK.md](../admin/STRATEGIC_INTEL_RUNBOOK.md#임계값-튜닝) 영향 범위 점검.

---

## 5. 외부 의존성

| 의존성 | 용도 | 운영 비고 |
|---|---|---|
| `pykrx` | 한국 3사 일별 OHLCV (primary) | 종목은 pykrx 우선, 실패 시 FDR fallback |
| `FinanceDataReader` | KOSDAQ 종합지수 (primary) + 종목 fallback | pykrx KRX 메타 차단 환경 우회. `daily_prices.source` 컬럼에 실제 사용 소스 기록 |
| LLM (`OllamaService` 추상화, 현재 Gemini 2.5 Flash) | 분류기 + 리포트 생성 | 무료 티어 한도 15 RPM / 1,500 RPD — 백필 페이싱 필수 |
| PostgreSQL | 모든 영속 데이터 | `ON CONFLICT` 기반 upsert (asyncpg/psycopg2) |

---

## 6. 보안·접근 제어

- **API**: 모든 `/admin/strategic-intel/*` 엔드포인트는 `require_super_admin` 종속성으로 보호 (`SUPER_ADMIN_EMAILS` 환경변수)
- **UI**: `/admin/strategic-intel` 진입은 super_admin 세션 필수 (Admin 라우팅에서 가드)
- **리포트 본문**: markdown 그대로 저장, 외부 소비자/일반 admin 노출 금지
- **면책**: 모든 리포트 본문 + UI 상단에 "내부 의사결정 보조용 / 투자 자문 아님" 명시

---

## 7. 관련 문서

| 문서 | 역할 |
|---|---|
| [docs/admin/STRATEGIC_INTEL_RUNBOOK.md](../admin/STRATEGIC_INTEL_RUNBOOK.md) | 운영 절차 (배치 실행·해석·트러블슈팅) |
| [Claude-Opus-bluevlad/services/allergyinsight/plans/strategic-intel-v1-implementation.md](https://github.com/bluevlad/Claude-Opus-bluevlad/blob/main/services/allergyinsight/plans/strategic-intel-v1-implementation.md) | v1 구현 결과 + v2 로드맵 |
| [Claude-Opus-bluevlad/services/allergyinsight/analysis/strategic-intel-fit-matrix-rationale.md](https://github.com/bluevlad/Claude-Opus-bluevlad/blob/main/services/allergyinsight/analysis/strategic-intel-fit-matrix-rationale.md) | 4사 fit 점수 근거 |
| [Claude-Opus-bluevlad/services/allergyinsight/roadmap/PREDICTIVE_ANALYTICS_ROADMAP.md](https://github.com/bluevlad/Claude-Opus-bluevlad/blob/main/services/allergyinsight/roadmap/PREDICTIVE_ANALYTICS_ROADMAP.md) | 상위 예측 분석 로드맵 (Module B 시장 인텔리전스) |
