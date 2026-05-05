# Strategic Intel — 빠른 명령어 참조

> 🔒 super_admin 전용. 외부 노출 금지.
>
> 이 페이지는 **빠른 명령어 cheat sheet** 입니다. 시스템 구조 / 임계값 튜닝 /
> 트러블슈팅 / 일상 점검 등 **종합 가이드**는 전략 repo 를 참조하세요.
>
> 📘 **시스템 아키텍처**: [Claude-Opus-bluevlad/services/allergyinsight/dev/STRATEGIC_INTEL_ARCHITECTURE.md](https://github.com/bluevlad/Claude-Opus-bluevlad/blob/main/services/allergyinsight/dev/STRATEGIC_INTEL_ARCHITECTURE.md)
> 📘 **운영 Runbook (종합)**: [Claude-Opus-bluevlad/services/allergyinsight/dev/STRATEGIC_INTEL_RUNBOOK.md](https://github.com/bluevlad/Claude-Opus-bluevlad/blob/main/services/allergyinsight/dev/STRATEGIC_INTEL_RUNBOOK.md)
> 📘 **v2 로드맵 진행**: [Claude-Opus-bluevlad/services/allergyinsight/plans/strategic-intel-v1-implementation.md](https://github.com/bluevlad/Claude-Opus-bluevlad/blob/main/services/allergyinsight/plans/strategic-intel-v1-implementation.md)

---

## 백필 — 10단계 idempotent

```bash
cd backend

# 전체 (기본 — 2025-12-01 ~ 오늘)
python -m scripts.backfill_strategic_intel

# 단계별
python -m scripts.backfill_strategic_intel --only seed
python -m scripts.backfill_strategic_intel --only prices --start 2026-01-01 --end 2026-04-30
python -m scripts.backfill_strategic_intel --only disclosures --start 2026-01-01 --end 2026-04-30
python -m scripts.backfill_strategic_intel --only fda_510k --start 2026-01-01 --end 2026-04-30
python -m scripts.backfill_strategic_intel --only clinical_trials --start 2026-01-01 --end 2026-04-30
python -m scripts.backfill_strategic_intel --only pubmed_ivd --start 2026-01-01 --end 2026-04-30
python -m scripts.backfill_strategic_intel --only classify --max-per-run 1400 --rpm-limit 12
python -m scripts.backfill_strategic_intel --only generate
python -m scripts.backfill_strategic_intel --only validate
python -m scripts.backfill_strategic_intel --only qualitative --qualitative-limit 100 --rpm-limit 12

# 룰 변경 후 가설 재생성
python -m scripts.backfill_strategic_intel --only generate --regenerate
```

---

## 자동 스케줄 (KST)

| Job | 시간 | 내용 |
|---|---|---|
| `strategic_intel_validate` | 매일 06:30 | 가설 시장 검증 |
| `strategic_intel_event_scan` | 매일 09:00 | 이벤트 후보 → 자동 발행 |
| `strategic_intel_daily` | 매일 19:00 | 시세 + 외부 트리거 + 분류 + 가설 + LLM 보강 |
| `strategic_intel_monthly` | 매월 1일 09:30 | 전월 종합 리포트 |

---

## 환경변수

| 변수 | 필수 | 용도 |
|---|---|---|
| `DATABASE_URL` | ✅ | PostgreSQL 연결 |
| `OPENAI_API_KEY` | ✅ | 분류기 + 정성 보강 + 리포트 LLM |
| `SUPER_ADMIN_EMAILS` | ✅ | Strategic Intel 접근 권한 |
| `DART_API_KEY` | 선택 | DART 공시. 미설정 시 graceful skip |
| `PUBMED_API_KEY` | 선택 | PubMed E-utilities rate limit 완화 |

---

## Admin UI

`/admin/strategic-intel` (super_admin 로그인 → 진입 동의 모달 → 5탭: 가설 검증 · 리포트 · Fit Matrix · 통계 · Audit)

상세 절차 / 트러블슈팅 / 임계값 튜닝은 **전략 repo Runbook 참조**.
