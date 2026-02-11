# AllergyInsight 문서 구조

## 개요

코드 저장소에는 **개발/운영에 직접 필요한 문서**만 유지합니다.
기획서, 로드맵, 아키텍처 분석 등의 문서는 별도 문서 저장소에서 관리합니다.

## 이 저장소의 문서 (코드와 함께 관리)

```
docs/
├── README.md                          # 이 파일 (문서 구조 설명)
├── GETTING_STARTED.md                 # 시작 가이드 (설치, 접속, 테스트 계정)
│
├── api/                               # API 관련 문서
│   ├── CHANGELOG.md                   # API 변경 이력
│   └── PAPER_COLLECTION_SOURCES.md    # 데이터 수집 소스
│
└── dev/                               # 개발자 가이드
    ├── SETUP.md                       # 개발 환경 설정
    ├── DEPLOYMENT.md                  # 배포 절차
    └── BRANCH_WORKFLOW.md             # 브랜치 전략
```

## 문서 저장소 (Claude-Opus-bluevlad/docs/AllergyInsight/)

기획, 설계, 로드맵 등 프로젝트 전략 문서는 아래 저장소에서 관리합니다:

> **위치**: `C:\GIT\Claude-Opus-bluevlad\docs\AllergyInsight\`

```
AllergyInsight/
├── 프로젝트_기획서_v1.0.md            # 프로젝트 기획서
├── PROJECT_WBS.md                     # Work Breakdown Structure
├── IMPLEMENTATION.md                  # 전체 구현 상세 문서
├── SAMPLE_CLINICAL_REPORT_GUIDE.md    # 임상 보고서 가이드
├── SAMPLE_CLINICAL_REPORT_GUIDE.pdf   # 임상 보고서 가이드 (PDF)
│
├── adr/                               # Architecture Decision Records
│   └── 001-service-bifurcation.md
│
├── dev/                               # 아키텍처 분석/기획 문서
│   ├── BACKEND_ARCHITECTURE_ANALYSIS.md
│   ├── DISCUSS.md
│   └── PATIENT_MANAGEMENT_PROCESS.md
│
├── roadmap/                           # 기능별 로드맵
│   ├── ADMIN_SYSTEM_PROPOSAL.md
│   ├── CLINICAL_ACCURACY_ENHANCEMENT.md
│   ├── HOSPITAL_SERVICE_ROADMAP.md
│   ├── MEDICAL_PROFESSIONAL_ENHANCEMENT_PLAN.md
│   ├── PAPER_LINK_EXTRACTION_ROADMAP.md
│   ├── PHYSICIAN_DOCUMENT_SYSTEM.md
│   └── QA_SYSTEM_ENHANCEMENT.md
│
└── wiki/                              # GitHub Wiki 동기화용
    ├── Home.md
    ├── 1.-Project-Overview.md
    ├── 2.-Architecture.md
    ├── 3.-Domain-Model.md
    ├── 4.-API-Specification.md
    ├── 5.-Development-Guide.md
    ├── 6.-Deployment.md
    ├── 7.-Roadmap.md
    └── 8.-User-Guide.md
```

## 문서 분류 기준

| 분류 | 위치 | 기준 |
|------|------|------|
| 개발 가이드 | 이 저장소 `docs/` | 코드 변경과 함께 버전이 바뀌는 문서 |
| API 문서 | 이 저장소 `docs/api/` | API 변경 이력, 데이터 소스 |
| 기획/전략 | 문서 저장소 | 프로젝트 기획서, WBS, 로드맵 |
| 아키텍처 | 문서 저장소 `adr/` | 설계 결정 기록, 아키텍처 분석 |
| Wiki | 문서 저장소 `wiki/` | GitHub Wiki 동기화용 공개 문서 |

## 관련 링크

- [GitHub Wiki](https://github.com/bluevlad/AllergyInsight/wiki)
- [프로젝트 README](../README.md)
