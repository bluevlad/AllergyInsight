# 임상 정확도 향상 시스템 설계

> **문서 목적**: 환자 자가 보고와 진단 키트 결과 비교를 통한 임상 정확도 향상 방안
> **버전**: 1.0
> **작성일**: 2025-01-27

---

## 1. 개요

### 1.1 현재 상황

```
┌─────────────────┐                    ┌─────────────────┐
│  진단 키트      │────────────────────▶│  임상 보고서    │
│  (Lab Result)   │                    │  (단방향)       │
└─────────────────┘                    └─────────────────┘
```

현재 시스템은 진단 키트 결과만을 기반으로 임상 보고서를 생성합니다.
환자의 실제 반응 경험이 반영되지 않아 **임상적 관련성(Clinical Relevance)** 평가가 제한적입니다.

### 1.2 목표 시스템

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  환자 자가보고  │────▶│                 │────▶│  정확도 향상    │
│  (Pre/Post)     │     │  비교 분석 엔진 │     │  임상 보고서    │
└─────────────────┘     │                 │     └─────────────────┘
                        │                 │
┌─────────────────┐     │                 │     ┌─────────────────┐
│  진단 키트      │────▶│                 │────▶│  통계/패턴 DB   │
│  (Lab Result)   │     └─────────────────┘     │  (학습 데이터)  │
└─────────────────┘                             └─────────────────┘
```

---

## 2. 환자 자가 보고 시스템

### 2.1 수집 시점

| 시점 | 목적 | 수집 내용 |
|------|------|----------|
| **검사 전 (Pre-Test)** | 병력 파악 | 과거 반응 이력, 의심 알러젠, 증상 패턴 |
| **검사 후 (Post-Test)** | 결과 검증 | 실제 노출 시 반응, 증상 일치 여부 |
| **추적 관찰 (Follow-up)** | 장기 검증 | 회피 후 증상 변화, 재노출 반응 |

### 2.2 Pre-Test 설문 구조

```
┌─────────────────────────────────────────────────────────────────┐
│                    검사 전 알러지 병력 설문                      │
├─────────────────────────────────────────────────────────────────┤
│ 1. 알러지 반응 경험이 있는 음식/물질을 선택해주세요              │
│    □ 새우/게/랍스터    □ 땅콩    □ 우유    □ 계란              │
│    □ 밀    □ 견과류    □ 생선    □ 기타: _________             │
├─────────────────────────────────────────────────────────────────┤
│ 2. 각 항목에 대해 반응 정도를 선택해주세요                       │
│                                                                  │
│    새우: ○없음 ○경미(가려움) ○중간(두드러기) ○심함(호흡곤란)    │
│    땅콩: ○없음 ○경미(가려움) ○중간(두드러기) ○심함(호흡곤란)    │
│    ...                                                           │
├─────────────────────────────────────────────────────────────────┤
│ 3. 반응이 나타나기까지 걸린 시간                                 │
│    ○즉시(30분 이내) ○1-2시간 ○수시간 후 ○다음날               │
├─────────────────────────────────────────────────────────────────┤
│ 4. 아나필락시스 경험 여부                                        │
│    ○없음 ○있음 (에피네프린 사용: ○예 ○아니오)                  │
├─────────────────────────────────────────────────────────────────┤
│ 5. 가족력                                                        │
│    □ 부모 알러지 병력    □ 형제 알러지 병력    □ 없음           │
└─────────────────────────────────────────────────────────────────┘
```

### 2.3 Post-Test 확인 설문

```
┌─────────────────────────────────────────────────────────────────┐
│                 검사 결과 확인 설문 (3개월 후)                   │
├─────────────────────────────────────────────────────────────────┤
│ 검사에서 양성으로 나온 항목에 대해 확인해주세요                  │
│                                                                  │
│ [갑각류 - Class 4 양성]                                          │
│ Q. 검사 후 갑각류를 드신 적이 있나요?                            │
│    ○예 ○아니오(회피 중)                                         │
│                                                                  │
│ Q. (예 선택시) 어떤 반응이 있었나요?                             │
│    ○반응 없음  ○경미한 반응  ○중간 반응  ○심한 반응            │
│                                                                  │
│ Q. 결과와 본인 경험이 일치한다고 느끼시나요?                     │
│    ○매우 일치  ○대체로 일치  ○잘 모르겠음  ○일치하지 않음      │
├─────────────────────────────────────────────────────────────────┤
│ [땅콩 - Class 3 양성]                                            │
│ Q. 검사 후 땅콩을 드신 적이 있나요?                              │
│    ...                                                           │
└─────────────────────────────────────────────────────────────────┘
```

---

## 3. 데이터베이스 설계

### 3.1 새로운 테이블

```sql
-- 환자 자가 보고 (검사 전)
CREATE TABLE patient_symptom_history (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    allergen_code VARCHAR(50) NOT NULL,

    -- 반응 경험
    has_reaction BOOLEAN DEFAULT FALSE,
    reaction_severity VARCHAR(20),  -- none, mild, moderate, severe
    reaction_type TEXT[],           -- ['itching', 'hives', 'swelling', 'breathing', 'anaphylaxis']
    onset_time VARCHAR(20),         -- immediate, 1-2hours, delayed, next_day

    -- 추가 정보
    last_exposure_date DATE,
    frequency VARCHAR(20),          -- once, occasional, frequent
    confidence_level VARCHAR(20),   -- certain, likely, uncertain

    -- 메타
    reported_at TIMESTAMP DEFAULT NOW(),
    reported_by VARCHAR(20)         -- patient, guardian, doctor
);

-- 환자 자가 보고 (검사 후 추적)
CREATE TABLE patient_followup_report (
    id SERIAL PRIMARY KEY,
    diagnosis_id INTEGER REFERENCES user_diagnosis(id),
    user_id INTEGER REFERENCES users(id),
    allergen_code VARCHAR(50) NOT NULL,

    -- 검사 결과
    test_grade INTEGER,             -- 0-6

    -- 실제 경험
    exposed_after_test BOOLEAN,
    actual_reaction_severity VARCHAR(20),  -- none, mild, moderate, severe
    reaction_matched BOOLEAN,              -- 검사 결과와 일치 여부
    patient_agreement VARCHAR(20),         -- strongly_agree, agree, neutral, disagree

    -- 상세
    exposure_date DATE,
    notes TEXT,

    -- 메타
    followup_date TIMESTAMP DEFAULT NOW(),
    followup_period_days INTEGER           -- 검사 후 며칠 경과
);

-- 정확도 통계 (집계 테이블)
CREATE TABLE accuracy_statistics (
    id SERIAL PRIMARY KEY,
    allergen_code VARCHAR(50) NOT NULL,
    test_grade INTEGER NOT NULL,

    -- 통계
    total_cases INTEGER DEFAULT 0,
    true_positive INTEGER DEFAULT 0,      -- 양성 + 실제 반응 있음
    false_positive INTEGER DEFAULT 0,     -- 양성 + 실제 반응 없음
    true_negative INTEGER DEFAULT 0,      -- 음성 + 실제 반응 없음
    false_negative INTEGER DEFAULT 0,     -- 음성 + 실제 반응 있음

    -- 계산된 지표
    sensitivity DECIMAL(5,4),             -- 민감도
    specificity DECIMAL(5,4),             -- 특이도
    ppv DECIMAL(5,4),                     -- 양성예측도
    npv DECIMAL(5,4),                     -- 음성예측도

    -- 업데이트
    last_calculated TIMESTAMP,
    sample_size INTEGER
);
```

### 3.2 ER 다이어그램

```
┌──────────────────┐     ┌──────────────────┐     ┌──────────────────┐
│ patient_symptom  │     │   user_diagnosis │     │ patient_followup │
│    _history      │     │                  │     │    _report       │
├──────────────────┤     ├──────────────────┤     ├──────────────────┤
│ user_id ─────────┼──┐  │ id ──────────────┼──┐  │ diagnosis_id ────┤
│ allergen_code    │  │  │ user_id          │  │  │ user_id          │
│ has_reaction     │  │  │ results (JSON)   │  └──│ allergen_code    │
│ reaction_severity│  │  │ diagnosis_date   │     │ test_grade       │
│ reaction_type[]  │  │  │ prescription     │     │ actual_reaction  │
│ onset_time       │  │  └──────────────────┘     │ reaction_matched │
│ confidence_level │  │           │               │ patient_agreement│
└──────────────────┘  │           │               └──────────────────┘
         │            │           │                        │
         │            │           │                        │
         ▼            ▼           ▼                        ▼
┌──────────────────────────────────────────────────────────────────┐
│                      accuracy_statistics                          │
├──────────────────────────────────────────────────────────────────┤
│ allergen_code | test_grade | TP | FP | TN | FN | sensitivity     │
└──────────────────────────────────────────────────────────────────┘
```

---

## 4. 비교 분석 알고리즘

### 4.1 일치도 분류

```python
def classify_concordance(test_grade: int, patient_reaction: str) -> str:
    """
    검사 결과와 환자 반응 일치도 분류

    Returns:
        - concordant_positive: 양성 + 반응 있음 (True Positive)
        - concordant_negative: 음성 + 반응 없음 (True Negative)
        - discordant_fp: 양성 + 반응 없음 (False Positive, 과진단)
        - discordant_fn: 음성 + 반응 있음 (False Negative, 과소진단)
    """
    is_test_positive = test_grade >= 2  # Class 2 이상을 양성으로
    has_clinical_reaction = patient_reaction in ['mild', 'moderate', 'severe']

    if is_test_positive and has_clinical_reaction:
        return 'concordant_positive'
    elif not is_test_positive and not has_clinical_reaction:
        return 'concordant_negative'
    elif is_test_positive and not has_clinical_reaction:
        return 'discordant_fp'  # 검사만 양성
    else:
        return 'discordant_fn'  # 증상만 있음
```

### 4.2 임상적 관련성 점수 (Clinical Relevance Score)

```python
def calculate_clinical_relevance_score(
    test_grade: int,
    patient_history: dict,
    followup_data: dict = None
) -> dict:
    """
    임상적 관련성 점수 계산

    점수 범위: 0-100
    - 0-30: 낮은 관련성 (검사 결과 신뢰도 낮음)
    - 31-60: 중간 관련성 (추가 확인 필요)
    - 61-80: 높은 관련성 (대체로 신뢰)
    - 81-100: 매우 높은 관련성 (높은 신뢰도)
    """
    score = 50  # 기본 점수
    factors = []

    # 1. 검사 등급 가중치
    grade_weight = {0: -20, 1: -10, 2: 0, 3: 10, 4: 20, 5: 25, 6: 30}
    score += grade_weight.get(test_grade, 0)

    # 2. 환자 병력 일치도
    if patient_history.get('has_reaction'):
        if patient_history.get('reaction_severity') == 'severe':
            score += 20
            factors.append('심한 반응 병력')
        elif patient_history.get('reaction_severity') == 'moderate':
            score += 15
            factors.append('중등도 반응 병력')
        elif patient_history.get('reaction_severity') == 'mild':
            score += 10
            factors.append('경미한 반응 병력')
    else:
        if test_grade >= 3:
            score -= 15  # 양성인데 병력 없음
            factors.append('양성이나 반응 병력 없음')

    # 3. 반응 시간 패턴 (즉시형이 IgE 매개 가능성 높음)
    if patient_history.get('onset_time') == 'immediate':
        score += 10
        factors.append('즉시형 반응')

    # 4. 환자 확신도
    confidence = patient_history.get('confidence_level')
    if confidence == 'certain':
        score += 10
    elif confidence == 'uncertain':
        score -= 5

    # 5. 추적 관찰 데이터 반영
    if followup_data:
        if followup_data.get('reaction_matched'):
            score += 15
            factors.append('추적 관찰에서 일치 확인')
        else:
            score -= 10
            factors.append('추적 관찰에서 불일치')

    # 점수 범위 조정
    score = max(0, min(100, score))

    return {
        'score': score,
        'level': get_relevance_level(score),
        'factors': factors,
        'recommendation': get_recommendation(score, test_grade)
    }

def get_relevance_level(score: int) -> str:
    if score >= 81:
        return 'very_high'
    elif score >= 61:
        return 'high'
    elif score >= 31:
        return 'moderate'
    else:
        return 'low'

def get_recommendation(score: int, test_grade: int) -> str:
    if score >= 81:
        return '검사 결과와 임상 소견이 일치합니다. 해당 알러젠 회피를 권장합니다.'
    elif score >= 61:
        return '검사 결과가 임상 소견을 지지합니다. 회피 후 증상 변화를 관찰하세요.'
    elif score >= 31:
        if test_grade >= 3:
            return '검사 양성이나 임상 소견 불충분. 경구유발시험(OFC) 고려하세요.'
        else:
            return '경계 결과. 증상 재발 시 재평가가 필요합니다.'
    else:
        return '검사 결과와 임상 소견 불일치. 위양성 가능성 있으며 OFC를 권장합니다.'
```

### 4.3 보고서 적용 예시

```
┌─────────────────────────────────────────────────────────────────┐
│  갑각류 (Shellfish) - Class 4                                   │
├─────────────────────────────────────────────────────────────────┤
│  검사 결과: Class 4 (Very High)                                 │
│  환자 보고: 심한 반응 (두드러기, 호흡곤란)                      │
│  반응 시간: 즉시형 (30분 이내)                                  │
│  환자 확신도: 확실함                                            │
├─────────────────────────────────────────────────────────────────┤
│  ▶ 임상적 관련성 점수: 95/100 (매우 높음)                       │
│                                                                  │
│  분석 요인:                                                      │
│  ✓ 높은 검사 등급 (+20)                                         │
│  ✓ 심한 반응 병력 (+20)                                         │
│  ✓ 즉시형 반응 패턴 (+10)                                       │
│  ✓ 환자 확신도 높음 (+10)                                       │
├─────────────────────────────────────────────────────────────────┤
│  권고: 검사 결과와 임상 소견이 일치합니다.                      │
│        해당 알러젠의 엄격한 회피를 권장합니다.                   │
│        에피네프린 자가주사기 처방을 고려하세요.                  │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│  견과류 (Tree Nuts) - Class 2                                   │
├─────────────────────────────────────────────────────────────────┤
│  검사 결과: Class 2 (Moderate)                                  │
│  환자 보고: 반응 없음                                           │
│  반응 시간: 해당 없음                                           │
│  환자 확신도: 확실함 (평소 섭취함)                              │
├─────────────────────────────────────────────────────────────────┤
│  ▶ 임상적 관련성 점수: 35/100 (중간)                            │
│                                                                  │
│  분석 요인:                                                      │
│  ⚠ 양성이나 반응 병력 없음 (-15)                                │
│  ✓ 환자 확신도 높음 (+10)                                       │
├─────────────────────────────────────────────────────────────────┤
│  권고: 검사 양성이나 임상 소견 불충분.                          │
│        경구유발시험(OFC)을 통한 확인을 고려하세요.              │
│        무증상 감작(asymptomatic sensitization) 가능성 있음.     │
└─────────────────────────────────────────────────────────────────┘
```

---

## 5. 정확도 향상 피드백 루프

### 5.1 집계 통계 활용

```python
def update_accuracy_statistics(allergen_code: str, test_grade: int):
    """
    축적된 데이터로 정확도 지표 재계산
    """
    stats = db.query(AccuracyStatistics).filter(
        allergen_code=allergen_code,
        test_grade=test_grade
    ).first()

    if stats.total_cases >= 30:  # 최소 표본 크기
        # 민감도 = TP / (TP + FN)
        stats.sensitivity = stats.true_positive / (stats.true_positive + stats.false_negative)

        # 특이도 = TN / (TN + FP)
        stats.specificity = stats.true_negative / (stats.true_negative + stats.false_positive)

        # 양성예측도 = TP / (TP + FP)
        stats.ppv = stats.true_positive / (stats.true_positive + stats.false_positive)

        # 음성예측도 = TN / (TN + FN)
        stats.npv = stats.true_negative / (stats.true_negative + stats.false_negative)
```

### 5.2 진단 임계값 최적화

축적된 데이터를 기반으로 알러젠별 최적 진단 임계값(cutoff) 도출:

```
┌────────────────────────────────────────────────────────────────────┐
│  알러젠별 진단 성능 통계 (N=500)                                   │
├─────────────┬────────┬────────┬────────┬────────┬─────────────────┤
│ 알러젠      │ Grade  │ 민감도 │ 특이도 │ PPV    │ 권장 조치       │
├─────────────┼────────┼────────┼────────┼────────┼─────────────────┤
│ shellfish   │ ≥3     │ 92%    │ 85%    │ 88%    │ 신뢰 가능       │
│ shellfish   │ ≥2     │ 95%    │ 72%    │ 78%    │ 과진단 주의     │
├─────────────┼────────┼────────┼────────┼────────┼─────────────────┤
│ peanut      │ ≥3     │ 88%    │ 90%    │ 91%    │ 신뢰 가능       │
│ peanut      │ ≥2     │ 93%    │ 78%    │ 82%    │ OFC 권장        │
├─────────────┼────────┼────────┼────────┼────────┼─────────────────┤
│ milk        │ ≥3     │ 75%    │ 88%    │ 70%    │ OFC 권장        │
│ milk        │ ≥2     │ 85%    │ 65%    │ 55%    │ 과진단 높음     │
└─────────────┴────────┴────────┴────────┴────────┴─────────────────┘
```

### 5.3 개인화 모델

```python
def get_personalized_interpretation(
    user_id: int,
    allergen_code: str,
    test_grade: int
) -> dict:
    """
    환자 개인 이력 기반 맞춤 해석
    """
    # 1. 환자의 과거 검사-반응 이력 조회
    history = get_patient_history(user_id, allergen_code)

    # 2. 동일 알러젠 집단 통계 조회
    population_stats = get_population_stats(allergen_code, test_grade)

    # 3. 개인 패턴 vs 집단 패턴 비교
    personal_pattern = analyze_personal_pattern(history)

    return {
        'standard_interpretation': population_stats.interpretation,
        'personalized_interpretation': personal_pattern.interpretation,
        'confidence': calculate_confidence(history, population_stats),
        'recommendation': generate_personalized_recommendation(
            test_grade, history, population_stats
        )
    }
```

---

## 6. 구현 로드맵

### Phase 1: 데이터 수집 기반 (2주)

| 작업 | 설명 | 우선순위 |
|------|------|---------|
| DB 스키마 추가 | patient_symptom_history, patient_followup_report 테이블 | 필수 |
| Pre-Test 설문 API | 검사 전 병력 수집 API | 필수 |
| Pre-Test 설문 UI | 환자용 병력 입력 화면 | 필수 |
| 의사 병력 입력 UI | 상담 내용 기록 화면 | 필수 |

### Phase 2: 비교 분석 엔진 (2주)

| 작업 | 설명 | 우선순위 |
|------|------|---------|
| 일치도 분류 로직 | concordance 분류 알고리즘 | 필수 |
| 임상적 관련성 점수 | Clinical Relevance Score 계산 | 필수 |
| 보고서 통합 | 임상보고서에 관련성 점수 추가 | 필수 |
| 불일치 경고 | 검사-병력 불일치 시 알림 | 높음 |

### Phase 3: 추적 관찰 시스템 (2주)

| 작업 | 설명 | 우선순위 |
|------|------|---------|
| Follow-up 설문 API | 검사 후 추적 API | 필수 |
| 자동 알림 시스템 | 3개월 후 추적 설문 알림 | 높음 |
| Follow-up 결과 반영 | 관련성 점수 재계산 | 필수 |

### Phase 4: 통계 및 학습 (3주)

| 작업 | 설명 | 우선순위 |
|------|------|---------|
| accuracy_statistics 집계 | 일/주/월 배치 집계 | 높음 |
| 대시보드 | 의사/관리자용 정확도 통계 화면 | 중간 |
| 임계값 최적화 | 알러젠별 최적 cutoff 도출 | 중간 |
| 개인화 모델 | 환자별 맞춤 해석 | 낮음 |

---

## 7. 기대 효과

### 7.1 임상적 가치

| 항목 | 현재 | 도입 후 |
|------|------|---------|
| 위양성 감소 | 과잉 회피 → 삶의 질 저하 | 불필요한 회피 감소 |
| 위음성 감소 | 미인지 위험 | 조기 경고 및 추가 검사 권장 |
| OFC 권고 근거 | 주관적 판단 | 데이터 기반 의사결정 |
| 환자 신뢰도 | 검사만 의존 | 본인 경험 반영 → 순응도 향상 |

### 7.2 연구 데이터 축적

- 한국인 대상 알러젠별 진단 성능 데이터
- 검사 키트별 정확도 비교 근거
- 알러젠별 최적 진단 임계값 도출

### 7.3 비즈니스 가치

- 진단 키트 제조사에 정확도 피드백 제공
- 차별화된 임상 보고서 (경쟁 우위)
- 의료기관 신뢰도 향상

---

## 8. 참고 문헌

1. Sicherer SH, Sampson HA. Food allergy: A review and update on epidemiology, pathogenesis, diagnosis, prevention, and management. J Allergy Clin Immunol. 2018
2. Santos AF, et al. EAACI guidelines on the diagnosis of IgE-mediated food allergy. Allergy. 2023
3. Sampson HA, et al. Standardizing double-blind, placebo-controlled oral food challenges. J Allergy Clin Immunol. 2012

---

## 변경 이력

| 버전 | 날짜 | 변경 내용 |
|------|------|----------|
| 1.0 | 2025-01-27 | 초기 작성 |
