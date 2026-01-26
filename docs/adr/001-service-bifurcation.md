# 001. 서비스 이원화 (Professional / Consumer)

## 상태
Accepted

## 날짜
2025-01

## 컨텍스트

AllergyInsight 서비스는 두 가지 사용자 그룹을 대상으로 합니다:

1. **의료진 (Professional)**: 진단 입력, 처방 생성, 환자 관리, 논문 검색
2. **환자 (Consumer)**: 진단 결과 조회, 식품 가이드, 응급 대처

기존에는 단일 앱에서 역할 기반으로 UI를 분기했으나, 다음 문제가 발생했습니다:

- 코드 복잡도 증가
- 각 사용자 그룹에 맞지 않는 UX
- 독립적인 기능 확장의 어려움

## 고려한 대안

### 대안 1: 역할 기반 UI 분기 (기존 방식)
- 장점: 단일 코드베이스 유지
- 단점: 복잡도 증가, UX 타협

### 대안 2: 완전 분리 (별도 앱)
- 장점: 완전한 독립성
- 단점: 코드 중복, 유지보수 비용 증가

### 대안 3: URL 기반 분기 (하이브리드) ✅ 선택
- 장점: 공통 코드 공유 + 독립적 UI
- 단점: 초기 구조 변경 비용

## 결정

**URL 기반 서비스 분기** 방식을 채택합니다.

### Frontend
```
/pro/*     → Professional App (의료진)
/app/*     → Consumer App (환자)
```

### Backend API
```
/api/pro/*       → Professional API
/api/consumer/*  → Consumer API
```

### 디렉토리 구조
```
backend/
├── core/           # 공통 (인증, 알러젠 DB)
├── professional/   # 의료진 전용
└── consumer/       # 환자 전용

frontend/
├── shared/         # 공통 컴포넌트
└── apps/
    ├── professional/
    └── consumer/
```

## 결과

### 긍정적
- 각 사용자 그룹에 최적화된 UX 제공 가능
- 독립적인 기능 개발 및 배포 가능
- 코드 구조 명확화

### 부정적
- 초기 마이그레이션 작업 필요
- 공통 코드 변경 시 양쪽 영향 고려 필요

### 향후 확장
- 도메인 분리: `pro.allergyinsight.com`, `app.allergyinsight.com`
- 독립 배포: 별도 Docker 이미지로 분리 가능

## 관련 문서
- [2. Architecture (Wiki)](../wiki/2.-Architecture.md)
- [서비스 이원화 계획 (Plan)](../../.claude/plans/prancy-meandering-pixel.md)
