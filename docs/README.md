# AllergyInsight 문서 구조

## 디렉토리 구조

```
docs/
├── README.md              # 이 파일 (문서 구조 설명)
├── IMPLEMENTATION.md      # 전체 구현 상세 문서
│
├── adr/                   # Architecture Decision Records
│   └── (설계 결정 기록)
│
├── api/                   # API 관련 문서
│   └── PAPER_COLLECTION_SOURCES.md
│
├── dev/                   # 개발자 가이드
│   └── DEPLOYMENT.md
│
├── roadmap/               # 로드맵 및 계획 문서
│   ├── HOSPITAL_SERVICE_ROADMAP.md
│   ├── MEDICAL_PROFESSIONAL_ENHANCEMENT_PLAN.md
│   └── PAPER_LINK_EXTRACTION_ROADMAP.md
│
└── wiki/                  # GitHub Wiki 동기화용
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

## 디렉토리 설명

| 디렉토리 | 용도 | 대상 |
|----------|------|------|
| `adr/` | 아키텍처 결정 기록 (Architecture Decision Records) | 개발자 |
| `api/` | API 변경 이력, 외부 연동 문서 | 개발자 |
| `dev/` | 개발 환경 설정, 배포, 트러블슈팅 | 개발자 |
| `roadmap/` | 기능별 로드맵, 구현 계획 | 개발자/PM |
| `wiki/` | GitHub Wiki 동기화 (공개 문서) | 모든 사용자 |

## 문서 작성 가이드

### 언제 어디에 작성할까?

| 상황 | 위치 | 예시 |
|------|------|------|
| 새 기능 설계 결정 | `adr/` | `adr/003-push-notification.md` |
| API 변경/추가 | `api/` | `api/CHANGELOG.md` |
| 개발 환경 변경 | `dev/` | `dev/LOCAL_SETUP.md` |
| 기능 로드맵 | `roadmap/` | `roadmap/FEATURE_X_PLAN.md` |
| 사용자 가이드 | `wiki/` | Wiki에서 직접 편집 권장 |

### ADR (Architecture Decision Records) 작성법

파일명: `adr/NNN-title.md`

```markdown
# NNN. 제목

## 상태
Proposed | Accepted | Deprecated | Superseded

## 컨텍스트
어떤 문제/상황인가?

## 결정
무엇을 결정했는가?

## 결과
이 결정으로 인한 영향은?
```

### 로드맵 문서 작성법

파일명: `roadmap/FEATURE_NAME_ROADMAP.md`

```markdown
# Feature Name 로드맵

## 개요
기능 설명

## Phase 1: ...
- [ ] Task 1
- [ ] Task 2

## Phase 2: ...

## 변경 이력
| 날짜 | 변경 내용 |
|------|----------|
```

## Wiki 동기화

`wiki/` 폴더의 내용은 GitHub Wiki와 동기화됩니다.

```bash
# Wiki 저장소 클론
git clone https://github.com/bluevlad/AllergyInsight.wiki.git

# 변경사항 복사
cp docs/wiki/* ../AllergyInsight.wiki/

# 커밋 및 푸시
cd ../AllergyInsight.wiki
git add . && git commit -m "docs: update wiki" && git push
```

## 관련 링크

- [GitHub Wiki](https://github.com/bluevlad/AllergyInsight/wiki)
- [프로젝트 README](../README.md)
