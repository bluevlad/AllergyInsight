# AllergyInsight 문서 구조

## 개요

코드 저장소에는 **"어떻게(How)"에 해당하는 구현/운영 문서**만 유지합니다.
**"왜(Why)/무엇을(What)"에 해당하는 전략/분석/보안 문서**는 별도 저장소에서 관리합니다.

> 분류 기준: [CLAUDE.md — Documentation Decision Tree](../CLAUDE.md#documentation)
> 이원화 결정: [ADR-003](https://github.com/bluevlad/Claude-Opus-bluevlad/blob/main/docs/AllergyInsight/adr/003-document-dual-repo-strategy.md)

## 이 저장소의 문서 (코드와 함께 관리)

**원칙: 구현 결과 — "어떻게 사용하는가"**

```
docs/
├── README.md                          # 이 파일 (문서 구조 설명)
├── GETTING_STARTED.md                 # 시작 가이드 (설치, 접속, 테스트 계정)
│
├── api/                               # API 관련 문서
│   ├── CHANGELOG.md                   # API 변경 이력
│   └── PAPER_COLLECTION_SOURCES.md    # 데이터 수집 소스
│
├── admin/                             # 운영 빠른 참조 (cheat sheet)
│   └── STRATEGIC_INTEL_RUNBOOK.md     # Strategic Intel — 명령어/스케줄/환경변수만
│                                      # (종합 가이드는 전략 repo)
│
├── dev/                               # 개발자 가이드
│   ├── SETUP.md                       # 개발 환경 설정
│   ├── DEPLOYMENT.md                  # 배포 절차
│   ├── BRANCH_WORKFLOW.md             # 브랜치 전략
│   └── LLM_ARCHITECTURE.md            # LLM 이중화 아키텍처 (구현 관점)
│
└── guides/                            # 기능별 구현 참조 가이드 (신규)
    └── (구현 완료 시 전략 문서의 결과 요약을 여기에 추가)
```

## 전략 저장소 (Claude-Opus-bluevlad/docs/AllergyInsight/)

**원칙: 의사결정과 계획 — "왜 이렇게 하는가, 무엇을 만들 것인가"**

> **GitHub**: [Claude-Opus-bluevlad/docs/AllergyInsight/](https://github.com/bluevlad/Claude-Opus-bluevlad/tree/main/docs/AllergyInsight)

```
AllergyInsight/
├── adr/                               # 아키텍처 결정 기록
│   ├── 001-service-bifurcation.md     #   서비스 이원화 결정
│   ├── 002-llm-dual-provider-architecture.md  # LLM 이중화 결정
│   └── 003-document-dual-repo-strategy.md     # 문서 이원화 전략
│
├── plans/                             # 구현 플랜 (단계, 우선순위, 설계)
│   └── allergen-trend-analysis-plan.md  # 알러젠 트렌드 분석 플랜
│
├── analysis/                          # 비즈니스/기술 분석
│   └── (타당성, 데이터 품질, 비용 분석)
│
├── security/                          # 보안 설계
│   └── (인증 체계, 키 관리, 개인정보)
│
├── roadmap/                           # 중장기 로드맵
│   ├── NEWS_PAPER_UPGRADE_ROADMAP.md  #   뉴스/논문 업그레이드 로드맵
│   ├── ADMIN_SYSTEM_PROPOSAL.md
│   ├── CLINICAL_ACCURACY_ENHANCEMENT.md
│   ├── HOSPITAL_SERVICE_ROADMAP.md
│   ├── MEDICAL_PROFESSIONAL_ENHANCEMENT_PLAN.md
│   ├── PAPER_LINK_EXTRACTION_ROADMAP.md
│   ├── PHYSICIAN_DOCUMENT_SYSTEM.md
│   └── QA_SYSTEM_ENHANCEMENT.md
│
├── dev/                               # 아키텍처 분석/기획 문서
│   ├── BACKEND_ARCHITECTURE_ANALYSIS.md
│   ├── DISCUSS.md
│   └── PATIENT_MANAGEMENT_PROCESS.md
│
└── wiki/                              # 프로젝트 Wiki 문서
    └── ...
```

## 문서 분류 기준 (Decision Tree)

```
1. 보안 정보(키, 계정, 인증 설계) → 전략 저장소 security/
2. 비즈니스 분석(경쟁사, 시장, 비용) → 전략 저장소 analysis/
3. 아키텍처 결정(왜 이 기술을)     → 전략 저장소 adr/
4. 구현 전 계획(무엇을 만들 것인가) → 전략 저장소 plans/
5. 기능 로드맵(중장기 발전 계획)   → 전략 저장소 roadmap/
6. 구현 후 결과(어떻게 사용하는가) → 이 저장소 docs/guides/
7. API 변경사항                    → 이 저장소 docs/api/
```

## 관련 링크

- [프로젝트 README](../README.md)
- [CLAUDE.md — Documentation 규칙](../CLAUDE.md#documentation)
