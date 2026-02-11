# AllergyInsight 프로젝트 규칙

> 상위 `C:/GIT/CLAUDE.md`의 Git-First Workflow를 상속합니다.

## 문서 관리 규칙

### 문서 저장소 위치

프로젝트 문서는 **두 곳**에 분리 관리합니다:

| 구분 | 위치 | 용도 |
|------|------|------|
| **코드 문서** | `AllergyInsight/docs/` | 코드와 함께 버전 관리가 필요한 개발 문서 |
| **프로젝트 문서** | `C:/GIT/Claude-Opus-bluevlad/docs/AllergyInsight/` | 기획, 설계, 로드맵, 아키텍처 등 |

### 문서 참조 규칙

개발 작업 시 **반드시 아래 문서를 먼저 참조**합니다:

```
C:/GIT/Claude-Opus-bluevlad/docs/AllergyInsight/
├── 프로젝트_기획서_v1.0.md            # 프로젝트 기획 및 요구사항
├── PROJECT_WBS.md                     # 작업 분류 체계
├── IMPLEMENTATION.md                  # 전체 구현 상세
├── adr/                               # 아키텍처 결정 기록
├── dev/                               # 아키텍처 분석, 프로세스 문서
├── roadmap/                           # 기능별 로드맵 (7개)
└── wiki/                              # GitHub Wiki 원본
```

### 문서 작성 규칙

구현 중 새로운 문서를 작성할 때 아래 기준으로 저장 위치를 결정합니다:

#### AllergyInsight/docs/ 에 작성 (코드 repo)
- API 변경 이력 (`docs/api/CHANGELOG.md`)
- 개발 환경 설정 변경 (`docs/dev/SETUP.md`)
- 배포 절차 변경 (`docs/dev/DEPLOYMENT.md`)
- 브랜치 워크플로우 변경 (`docs/dev/BRANCH_WORKFLOW.md`)

#### Claude-Opus-bluevlad/docs/AllergyInsight/ 에 작성 (문서 repo)
- 새 기능 로드맵 → `roadmap/FEATURE_NAME_ROADMAP.md`
- 아키텍처 결정 → `adr/NNN-title.md`
- 설계 분석/토론 → `dev/`
- 프로세스 문서 → `dev/`
- Wiki 업데이트 → `wiki/`

### 문서 작성 후 커밋

문서 repo에 작성한 경우, **Claude-Opus-bluevlad repo에도 커밋**해야 합니다:
- 브랜치: `main`
- 커밋 메시지: `docs(AllergyInsight): 문서 설명`
