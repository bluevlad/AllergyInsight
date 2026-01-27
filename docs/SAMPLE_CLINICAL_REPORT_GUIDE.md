# AllergyInsight 임상보고서 샘플 가이드

> **문서 목적**: 의료진 및 진단테스터 생산업체 담당자를 위한 AllergyInsight 서비스 소개
> **버전**: 1.0
> **최종 수정일**: 2025-01-27

---

## 목차

1. [서비스 개요](#1-서비스-개요)
2. [GRADE 근거 수준 체계](#2-grade-근거-수준-체계)
3. [임상 진술문 시스템](#3-임상-진술문-시스템)
4. [샘플 진단 결과](#4-샘플-진단-결과)
5. [임상보고서 생성 예시](#5-임상보고서-생성-예시)
6. [시스템 연동 가이드](#6-시스템-연동-가이드)

---

## 1. 서비스 개요

### 1.1 AllergyInsight란?

AllergyInsight는 알레르기 검사 결과를 기반으로 **근거 중심의 맞춤형 임상 정보**를 제공하는 의료 지원 시스템입니다.

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  진단 키트      │────▶│  AllergyInsight │────▶│  임상 보고서    │
│  검사 결과      │     │  분석 엔진      │     │  (GRADE 기반)   │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                               │
                               ▼
                    ┌─────────────────────────┐
                    │ 근거 기반 임상 진술문   │
                    │ + 국제 가이드라인 참조  │
                    └─────────────────────────┘
```

### 1.2 주요 기능

| 기능 | 설명 | 대상 |
|------|------|------|
| **임상 보고서 생성** | GRADE 기반 근거 수준이 포함된 임상 문서 | 의료진 |
| **환자 가이드** | 이해하기 쉬운 생활 관리 지침 | 환자 |
| **처방 권고** | 알러젠별 회피 식품, 대체 식품 정보 | 의료진/환자 |
| **교차반응 분석** | 관련 알러젠 교차반응 위험도 평가 | 의료진 |
| **논문 검색** | PubMed/Semantic Scholar 연동 | 의료진/연구자 |

### 1.3 지원 알러젠 (16종)

#### 식품 알러젠 (9종)
| 코드 | 한글명 | 영문명 |
|------|--------|--------|
| peanut | 땅콩 | Peanut |
| milk | 우유 | Milk |
| egg | 계란 | Egg |
| wheat | 밀 | Wheat |
| soy | 대두 | Soy |
| fish | 생선 | Fish |
| shellfish | 갑각류 | Shellfish |
| tree_nuts | 견과류 | Tree Nuts |
| sesame | 참깨 | Sesame |

#### 흡입성 알러젠 (7종)
| 코드 | 한글명 | 영문명 |
|------|--------|--------|
| dust_mite | 집먼지진드기 | Dust Mite |
| pollen | 꽃가루 | Pollen |
| mold | 곰팡이 | Mold |
| pet_dander | 반려동물 | Pet Dander |
| cockroach | 바퀴벌레 | Cockroach |
| latex | 라텍스 | Latex |
| bee_venom | 벌독 | Bee Venom |

---

## 2. GRADE 근거 수준 체계

AllergyInsight는 국제적으로 인정받는 **GRADE (Grading of Recommendations Assessment, Development and Evaluation)** 체계를 사용합니다.

### 2.1 근거 수준 (Evidence Level)

| 등급 | 표시 | 영문 | 의미 |
|------|------|------|------|
| **A** | ⊕⊕⊕⊕ | High | 추가 연구가 효과 추정치의 신뢰도를 변경할 가능성이 **매우 낮음** |
| **B** | ⊕⊕⊕◯ | Moderate | 추가 연구가 효과 추정치의 신뢰도에 **중요한 영향**을 미칠 수 있음 |
| **C** | ⊕⊕◯◯ | Low | 추가 연구가 효과 추정치의 신뢰도에 중요한 영향을 미칠 **가능성이 높음** |
| **D** | ⊕◯◯◯ | Very Low | 효과 추정치가 **불확실함** |

### 2.2 권고 강도 (Recommendation Grade)

| 등급 | 권고 강도 | 근거 수준 | 임상적 해석 |
|------|----------|----------|------------|
| **1A** | 강력 권고 | 높은 근거 | 대부분의 환자에게 적용 권장 |
| **1B** | 강력 권고 | 중간 근거 | 대부분의 환자에게 적용 가능 |
| **2A** | 약한 권고 | 높은 근거 | 환자 상황에 따라 선택적 적용 |
| **2B** | 약한 권고 | 중간 근거 | 개별화된 의사결정 필요 |

### 2.3 GRADE 표시 예시

```
┌────────────────────────────────────────────────────────────────┐
│ ⊕⊕⊕⊕ 1A  에피네프린은 아나필락시스의 일차 치료제이며         │
│           인지 즉시 투여해야 한다.                              │
│           [EAACI Guidelines 2022]                               │
└────────────────────────────────────────────────────────────────┘
```

---

## 3. 임상 진술문 시스템

### 3.1 진술문 구조

```
┌─────────────────────────────────────────────────────────────────┐
│                    Clinical Statement                            │
├─────────────────────────────────────────────────────────────────┤
│  statement_kr: 한국어 진술문                                     │
│  statement_en: 영문 원문 (학술 논문 기반)                        │
├─────────────────────────────────────────────────────────────────┤
│  allergen_code: 적용 알러젠 (shrimp, peanut, milk, general)      │
│  context: 맥락 (diagnosis, treatment, avoidance, etc.)           │
├─────────────────────────────────────────────────────────────────┤
│  evidence_level: A/B/C/D (GRADE 근거 수준)                       │
│  recommendation_grade: 1A/1B/2A/2B (권고 강도)                   │
├─────────────────────────────────────────────────────────────────┤
│  paper: 출처 논문 (PMID, DOI, 저널 정보)                         │
│  source_location: 논문 내 위치 (예: "Results, p.198")            │
└─────────────────────────────────────────────────────────────────┘
```

### 3.2 맥락(Context) 분류

| 맥락 | 영문 | 설명 | 보고서 위치 |
|------|------|------|------------|
| **diagnosis** | Diagnosis | 진단 기준, 검사 해석 | 임상 평가 |
| **pathophysiology** | Pathophysiology | 병태생리, 면역 기전 | 임상 평가 |
| **cross_reactivity** | Cross-reactivity | 교차반응 정보 | 임상 평가 |
| **avoidance** | Avoidance | 회피 지침 | 관리 계획 |
| **treatment** | Treatment | 치료 지침 | 관리 계획 |

### 3.3 참조 가이드라인

| 기관 | 가이드라인 | 연도 | 근거수준 |
|------|-----------|------|---------|
| **EAACI** | Anaphylaxis Guidelines (2021 update) | 2022 | A |
| **AAAAI/ACAAI** | Practice parameter update: Food allergy | 2020 | A |
| **WAO** | World Allergy Organization Anaphylaxis Guidance | 2020 | A |

> **EAACI**: European Academy of Allergy and Clinical Immunology
> **AAAAI**: American Academy of Allergy, Asthma & Immunology
> **WAO**: World Allergy Organization

---

## 4. 샘플 진단 결과

### 4.1 환자 정보

| 항목 | 값 |
|------|-----|
| 환자번호 | P-2026-0001 |
| 환자명 | 김철수 |
| 검사일 | 2026-01-26 |
| 검사 키트 | SGTi-Allergy Screen PLUS |

### 4.2 검사 결과 (원시 데이터)

```json
{
  "peanut": 3,
  "milk": 2,
  "egg": 1,
  "wheat": 0,
  "soy": 0,
  "fish": 0,
  "shellfish": 4,
  "tree_nuts": 2,
  "sesame": 0,
  "dust_mite": 3,
  "pollen": 1,
  "mold": 0,
  "pet_dander": 0,
  "cockroach": 0,
  "latex": 0,
  "bee_venom": 0
}
```

### 4.3 등급 해석표

| 등급 | Class | 해석 | 임상적 의의 |
|------|-------|------|------------|
| 0 | Class 0 | 음성 (Negative) | 감작 미확인 |
| 1 | Class 1 | 약양성 (Low) | 감작 가능성 있음, 임상 증상과 대조 필요 |
| 2 | Class 2 | 양성 (Moderate) | 감작 확인, 증상 유발 가능 |
| 3 | Class 3 | 중등도 양성 (High) | 감작 확인, 회피 권장 |
| 4-6 | Class 4-6 | 강양성 (Very High) | 고위험, 엄격한 회피 필수 |

### 4.4 검사 결과 요약

#### 양성 알러젠 (7종)

| 알러젠 | 등급 | Class | 해석 | 위험도 |
|--------|------|-------|------|--------|
| **shellfish** (갑각류) | 4 | Class 4 | Very High | 🔴 고위험 |
| **peanut** (땅콩) | 3 | Class 3 | High | 🔴 고위험 |
| **dust_mite** (집먼지진드기) | 3 | Class 3 | High | 🟠 중위험 |
| **milk** (우유) | 2 | Class 2 | Moderate | 🟡 주의 |
| **tree_nuts** (견과류) | 2 | Class 2 | Moderate | 🟡 주의 |
| **egg** (계란) | 1 | Class 1 | Low | 🟢 경미 |
| **pollen** (꽃가루) | 1 | Class 1 | Low | 🟢 경미 |

#### 음성 알러젠 (9종)

wheat, soy, fish, sesame, mold, pet_dander, cockroach, latex, bee_venom

---

## 5. 임상보고서 생성 예시

### 5.1 환자 정보 섹션

```
┌─────────────────────────────────────────────────────────────────┐
│                    알레르기 임상 보고서                          │
│         Clinical Allergy Assessment Report (Physician Only)      │
├─────────────────────────────────────────────────────────────────┤
│ 환자명: 김철수                    환자번호: P-2026-0001          │
│ 검사일: 2026-01-26               양성 항원: 7 / 16              │
│ 위험도: High                     아나필락시스 위험: 있음         │
└─────────────────────────────────────────────────────────────────┘
```

### 5.2 진단 코드 (ICD-10)

김철수 환자에게 적용되는 ICD-10 코드:

| 코드 | 설명 |
|------|------|
| T78.1 | Other adverse food reactions, not elsewhere classified |
| Z91.010 | Allergy status to peanuts |
| Z91.013 | Allergy status to seafood |
| J30.89 | Other allergic rhinitis |

### 5.3 임상 평가 (Assessment)

#### 5.3.1 주요 양성 알러젠

| 알러젠 | 등급 | Class | 임상적 의의 |
|--------|------|-------|------------|
| 갑각류 (Shellfish) | 4 | Class 4 (Very High) | 고위험, 엄격한 회피 필수 |
| 땅콩 (Peanut) | 3 | Class 3 (High) | 감작 확인, 회피 권장 |
| 집먼지진드기 (Dust Mite) | 3 | Class 3 (High) | 감작 확인, 회피 권장 |

#### 5.3.2 적용 임상 진술문

**갑각류 관련 진술문:**

| GRADE | 진술문 | 출처 |
|-------|--------|------|
| ⊕⊕⊕⊕ 1A | 트로포미오신은 갑각류(새우, 게, 랍스터) 및 연체류 간의 교차반응을 일으키는 주요 pan-allergen이다. | Shellfish allergy: Tropomyosin as a major allergen |
| ⊕⊕⊕⊕ 1A | 확진된 새우 알레르기 및 트로포미오신 감작 양성 환자에게는 모든 갑각류의 엄격한 회피가 권장된다. | AAAAI Practice parameter (2020) |
| ⊕⊕⊕◯ 1B | 새우 알레르기 환자는 다른 갑각류 및 집먼지진드기와의 교차반응 여부를 평가해야 한다. | Shellfish allergy: Tropomyosin |
| ⊕⊕⊕◯ 2B | 트로포미오신(rPen a 1)에 대한 sIgE ≥0.35 kU/L는 갑각류에 대한 임상적 반응성을 시사한다. | Shellfish allergy: Tropomyosin |

**땅콩 관련 진술문:**

| GRADE | 진술문 | 출처 |
|-------|--------|------|
| ⊕⊕⊕⊕ 1A | Ara h 2에 대한 sIgE ≥0.35 kU/L는 임상적 땅콩 알레르기 예측에 높은 특이도(>95%)를 보인다. | AAAAI Practice parameter (2020) |
| ⊕⊕⊕◯ 1B | 땅콩 알레르기는 식물학적으로 관련이 없음에도 불구하고 30-40%의 환자에서 견과류와 임상적 교차반응을 보인다. | Cross-reactivity among peanut and tree nuts |
| ⊕⊕⊕◯ 1B | 땅콩 알레르기 환자는 견과류 감작 여부를 평가받고, 임상 병력에 따라 개별 견과류 회피에 대한 조언을 받아야 한다. | Cross-reactivity among peanut and tree nuts |

**우유 관련 진술문:**

| GRADE | 진술문 | 출처 |
|-------|--------|------|
| ⊕⊕⊕⊕ 1A | 우유 알레르기(CMA)는 영아기에 가장 흔한 식품 알레르기이며, 대부분의 아동은 5세까지 내성을 획득한다. | AAAAI Practice parameter (2020) |
| ⊕⊕⊕⊕ 1A | 고도 가수분해 분유(eHF)는 모유 수유가 아닌 영아의 CMA 관리에 일차적으로 권장된다. | AAAAI Practice parameter (2020) |

**집먼지진드기 관련 진술문:**

| GRADE | 진술문 | 출처 |
|-------|--------|------|
| ⊕⊕⊕◯ 2B | 집먼지진드기 트로포미오신은 새우 트로포미오신과 80%의 서열 상동성을 보여 교차감작 가능성이 있다. | Shellfish allergy: Tropomyosin |

#### 5.3.3 교차반응 주의

```
┌─────────────────────────────────────────────────────────────────┐
│  ⚠️ 교차반응 경고                                               │
├─────────────────────────────────────────────────────────────────┤
│  갑각류 + 집먼지진드기 동시 양성                                 │
│                                                                  │
│  관련 알러젠: 새우, 게, 랍스터, 집먼지진드기                     │
│  기전: 트로포미오신 공유 (80% 서열 상동성)                       │
│  임상적 의의: 갑각류 섭취 시 증상 악화 가능성                    │
├─────────────────────────────────────────────────────────────────┤
│  땅콩 + 견과류 동시 양성                                         │
│                                                                  │
│  관련 알러젠: 땅콩, 호두, 아몬드, 캐슈넛                         │
│  기전: 저장 단백질 교차반응 (30-40% 임상적 연관)                 │
│  임상적 의의: 개별 견과류 회피 여부 평가 필요                    │
└─────────────────────────────────────────────────────────────────┘
```

### 5.4 관리 계획 (Management Plan)

#### 5.4.1 회피 식품

| 알러젠 | 회피 식품 |
|--------|----------|
| 갑각류 | 새우, 게, 랍스터, 가재, 크릴새우 |
| 땅콩 | 땅콩버터, 땅콩오일, 사테소스 |
| 견과류 | 호두, 아몬드, 캐슈넛, 피스타치오 |
| 우유 | 우유, 치즈, 요거트, 버터, 크림 |
| 계란 | 계란, 마요네즈, 머랭, 일부 빵류 |

#### 5.4.2 숨겨진 알러젠 주의

- 갑각류: 피쉬소스, 굴소스, XO소스, 해물 육수
- 땅콩: 아시아 요리, 아프리카 요리, 에너지바
- 우유: 카제인, 유청, 락토스프리 제품(단백질 포함)

#### 5.4.3 대체 식품

| 알러젠 | 대체 식품 |
|--------|----------|
| 우유 | 두유, 오트밀크, 아몬드밀크 (견과류 알러지 없는 경우) |
| 계란 | 두부 스크램블, 치아씨드, 아쿠아파바 |

#### 5.4.4 응급 치료 계획

**아나필락시스 위험: 있음** (갑각류, 땅콩 고위험 양성)

| GRADE | 권고사항 | 출처 |
|-------|---------|------|
| ⊕⊕⊕⊕ 1A | 에피네프린은 아나필락시스의 일차 치료제이며 인지 즉시 투여해야 한다. | EAACI Guidelines 2022 |
| ⊕⊕⊕⊕ 1A | 아나필락시스 위험이 있는 환자에게는 최소 2개의 에피네프린 자가주사기를 처방하고 올바른 사용법을 교육해야 한다. | EAACI Guidelines 2022 |
| ⊕⊕⊕◯ 1B | 이상성 아나필락시스는 최대 20%의 경우에서 발생하며, 치료 후 4-6시간 관찰이 권장된다. | WAO Guidance 2020 |

---

## 6. 시스템 연동 가이드

### 6.1 API 연동 (진단 장비 제조사용)

#### 6.1.1 진단 결과 전송

```http
POST /api/pro/diagnosis
Authorization: Bearer {token}
Content-Type: application/json

{
  "patient_user_id": 2,
  "results": {
    "peanut": 3,
    "milk": 2,
    "egg": 1,
    "shellfish": 4,
    ...
  },
  "diagnosis_date": "2026-01-26",
  "kit_serial": "SGT-2026-00001-0001"
}
```

#### 6.1.2 임상보고서 조회

```http
GET /api/pro/clinical-report?patient_id=P-2026-0001
Authorization: Bearer {token}
```

또는

```http
GET /api/pro/clinical-report?diagnosis_id=4
Authorization: Bearer {token}
```

### 6.2 응답 데이터 구조

```json
{
  "report_generated_at": "2026-01-27T08:00:00Z",
  "report_version": "1.0",
  "patient": {
    "patient_id": 2,
    "name": "김철수",
    "birth_date": null,
    "age": null
  },
  "diagnosis": {
    "diagnosis_id": 4,
    "kit_serial": "SGT-2026-00001-0001",
    "diagnosis_date": "2026-01-26",
    "positive_count": 7,
    "total_tested": 16
  },
  "allergen_results": [
    {
      "allergen_code": "shellfish",
      "allergen_name_kr": "갑각류",
      "allergen_name_en": "Shellfish",
      "grade": 4,
      "grade_class": "Class 4",
      "grade_interpretation": "Very High",
      "clinical_significance": "강양성 - 고위험, 엄격한 회피 필수"
    },
    ...
  ],
  "assessment": {
    "primary_allergens": ["shellfish", "peanut", "dust_mite", ...],
    "risk_level": "High",
    "anaphylaxis_risk": true,
    "cross_reactivity_concerns": [...],
    "clinical_statements": [...]
  },
  "management": {
    "avoidance_items": [...],
    "hidden_allergens": [...],
    "substitutes": [...],
    "emergency_plan": true,
    "follow_up_recommended": true,
    "statements": [...]
  },
  "references": [...],
  "icd10_codes": ["T78.1", "Z91.010", "Z91.013", "J30.89"]
}
```

### 6.3 연동 체크리스트

#### 진단 장비 제조사

- [ ] API 인증 토큰 발급
- [ ] 진단 결과 JSON 형식 맞춤
- [ ] 키트 시리얼 번호 체계 협의
- [ ] 에러 핸들링 구현
- [ ] 테스트 환경 검증

#### 의료기관

- [ ] 사용자 계정 등록 (의사, 간호사, 검사기사)
- [ ] 환자 등록 워크플로우 설정
- [ ] 임상보고서 출력 설정
- [ ] EMR 연동 검토 (선택)

---

## 부록 A: 용어 정의

| 용어 | 정의 |
|------|------|
| **GRADE** | Grading of Recommendations Assessment, Development and Evaluation - 국제 근거 수준 평가 체계 |
| **sIgE** | Specific Immunoglobulin E - 특이 면역글로불린 E |
| **트로포미오신** | Tropomyosin - 갑각류의 주요 알러젠 단백질 |
| **교차반응** | Cross-reactivity - 구조적으로 유사한 단백질에 대한 면역 반응 |
| **아나필락시스** | Anaphylaxis - 급성 전신 알레르기 반응 |
| **eHF** | extensively Hydrolyzed Formula - 고도 가수분해 분유 |

## 부록 B: 참고 문헌

1. EAACI guidelines: Anaphylaxis (2021 update). Allergy. 2022
2. AAAAI/ACAAI Practice parameter update: Food allergy. J Allergy Clin Immunol. 2020
3. World Allergy Organization Anaphylaxis Guidance 2020. World Allergy Organ J. 2020
4. Shellfish allergy: Tropomyosin as a major allergen. Clin Rev Allergy Immunol. 2021
5. Cross-reactivity among peanut and tree nuts. Ann Allergy Asthma Immunol. 2019

---

## 문의처

| 구분 | 연락처 |
|------|--------|
| 기술 지원 | tech-support@allergyinsight.com |
| 영업 문의 | sales@allergyinsight.com |
| 의료 자문 | medical@allergyinsight.com |

---

> **면책 조항**: 본 문서의 임상 정보는 의료 전문가의 판단을 대체하지 않습니다.
> 모든 임상 결정은 담당 의료진의 전문적 판단에 따라 이루어져야 합니다.
