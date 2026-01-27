# Q&A 시스템 고도화 로드맵

> **문서 목적**: 논문 기반 Q&A 시스템 개선 계획
> **버전**: 1.0
> **작성일**: 2025-01-27

---

## 1. 현재 상태 분석

### 1.1 현재 시스템 구조

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│ 사용자 질문 │────▶│ LIKE 검색   │────▶│ 논문 목록   │
│ (전체 문장) │     │ (단순 매칭) │     │ 또는 "없음" │
└─────────────┘     └─────────────┘     └─────────────┘
```

### 1.2 현재 코드 분석

```python
# backend/app/professional/research/routes.py

@router.post("/qa", response_model=QAResponse)
async def ask_question(request: QARequest, ...):
    # 문제점 1: 질문 전체를 검색어로 사용
    search_term = f"%{request.question}%"

    # 문제점 2: 단순 LIKE 매칭
    query = db.query(Paper).filter(
        or_(
            Paper.title.ilike(search_term),
            Paper.title_kr.ilike(search_term),
            Paper.abstract.ilike(search_term)
        )
    )

    # 문제점 3: 고정된 신뢰도
    if papers:
        confidence = 0.7
    else:
        confidence = 0.3  # "논문 없음" = 30%
```

### 1.3 문제점 요약

| 문제 | 현재 상태 | 영향 |
|------|----------|------|
| 키워드 추출 없음 | 전체 문장으로 검색 | 검색 실패율 높음 |
| 동의어 처리 없음 | "알러지" ≠ "알레르기" | 매칭 누락 |
| 형태소 분석 없음 | 한글 처리 미흡 | 부분 매칭 불가 |
| 의미 검색 없음 | 문자열 매칭만 | 의도 파악 불가 |
| 답변 생성 없음 | 논문 목록만 제공 | 사용자 경험 저하 |

---

## 2. 목표 시스템 아키텍처

### 2.1 개선된 구조

```
┌─────────────────────────────────────────────────────────────────┐
│                        Q&A 파이프라인                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐     │
│  │ 질문     │──▶│ 키워드   │──▶│ 동의어   │──▶│ 의도     │     │
│  │ 입력     │   │ 추출     │   │ 확장     │   │ 분류     │     │
│  └──────────┘   └──────────┘   └──────────┘   └──────────┘     │
│                                                    │             │
│                      ┌─────────────────────────────┘             │
│                      ▼                                           │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              하이브리드 검색 엔진                          │   │
│  ├──────────────────────────────────────────────────────────┤   │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐          │   │
│  │  │ 키워드     │  │ 시맨틱     │  │ 임상진술문 │          │   │
│  │  │ 검색       │  │ 검색       │  │ 매칭       │          │   │
│  │  │ (BM25)     │  │ (Vector)   │  │            │          │   │
│  │  └────────────┘  └────────────┘  └────────────┘          │   │
│  └──────────────────────────────────────────────────────────┘   │
│                      │                                           │
│                      ▼                                           │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              LLM 답변 생성기                               │   │
│  ├──────────────────────────────────────────────────────────┤   │
│  │  • 검색된 논문/진술문 기반 답변 생성                       │   │
│  │  • 인용 출처 자동 첨부                                     │   │
│  │  • 의료 면책 조항 추가                                     │   │
│  └──────────────────────────────────────────────────────────┘   │
│                      │                                           │
│                      ▼                                           │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐                    │
│  │ 답변     │   │ 관련     │   │ 신뢰도   │                    │
│  │ 텍스트   │   │ 논문     │   │ 점수     │                    │
│  └──────────┘   └──────────┘   └──────────┘                    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 예시: 개선된 동작

**질문**: "우유 알러지와 유당불내증의 차이점은?"

```
Step 1: 키워드 추출
────────────────────
원문: "우유 알러지와 유당불내증의 차이점은?"
추출: ["우유", "알러지", "유당불내증", "차이점"]

Step 2: 동의어 확장
────────────────────
우유 → milk, cow's milk, 우유, 밀크
알러지 → allergy, 알레르기, CMA (cow's milk allergy)
유당불내증 → lactose intolerance, 유당분해효소결핍
차이점 → difference, comparison, vs, 비교

Step 3: 의도 분류
────────────────────
의도: comparison (비교 요청)
대상: [milk_allergy, lactose_intolerance]

Step 4: 하이브리드 검색
────────────────────
키워드 검색 결과: 3개 논문
시맨틱 검색 결과: 5개 논문 (유사도 > 0.7)
임상진술문 매칭: 2개 진술문

Step 5: LLM 답변 생성
────────────────────
"우유 알러지(CMA)와 유당불내증은 서로 다른 질환입니다.

**우유 알러지 (Cow's Milk Allergy)**
- 원인: 우유 단백질(카제인, 유청)에 대한 면역 반응
- 기전: IgE 매개 또는 non-IgE 매개
- 증상: 두드러기, 구토, 호흡곤란, 아나필락시스 가능
- 발생 시기: 주로 영아기
- 예후: 대부분 5세까지 내성 획득 [1]

**유당불내증 (Lactose Intolerance)**
- 원인: 유당 분해 효소(락타아제) 부족
- 기전: 면역 반응 아님 (소화 효소 문제)
- 증상: 복부 팽만, 설사, 가스, 복통
- 발생 시기: 주로 성인기
- 예후: 지속적 (효소 보충으로 관리)

[1] AAAAI Practice Parameter 2020
[2] J Allergy Clin Immunol. 2018"

신뢰도: 85%
```

---

## 3. 구현 세부 설계

### 3.1 Phase 1: 키워드 추출 및 동의어 확장

#### 3.1.1 한글 형태소 분석

```python
# 의존성: konlpy, mecab-ko

from konlpy.tag import Mecab

class KeywordExtractor:
    def __init__(self):
        self.mecab = Mecab()

    def extract_keywords(self, question: str) -> list[str]:
        """질문에서 핵심 키워드 추출"""
        # 형태소 분석
        pos_tags = self.mecab.pos(question)

        # 명사, 외래어 추출
        keywords = []
        for word, pos in pos_tags:
            if pos in ['NNG', 'NNP', 'SL']:  # 일반명사, 고유명사, 외래어
                keywords.append(word)

        return keywords

    def extract_medical_terms(self, question: str) -> list[str]:
        """의학 용어 추출 (사전 기반)"""
        medical_terms = []
        for term in MEDICAL_TERM_DICTIONARY:
            if term in question or term.lower() in question.lower():
                medical_terms.append(term)
        return medical_terms
```

#### 3.1.2 의학 용어 동의어 사전

```python
# backend/app/data/medical_synonyms.py

ALLERGY_SYNONYMS = {
    # 우유 관련
    "우유 알러지": [
        "milk allergy", "cow's milk allergy", "CMA",
        "우유 알레르기", "우유단백알레르기", "CMPA"
    ],
    "유당불내증": [
        "lactose intolerance", "유당분해효소결핍",
        "lactase deficiency", "유당과민증"
    ],

    # 땅콩 관련
    "땅콩 알러지": [
        "peanut allergy", "땅콩 알레르기",
        "Ara h 2", "legume allergy"
    ],

    # 갑각류 관련
    "새우 알러지": [
        "shrimp allergy", "shellfish allergy",
        "갑각류 알레르기", "tropomyosin"
    ],

    # 일반 용어
    "아나필락시스": [
        "anaphylaxis", "anaphylactic shock",
        "과민성 쇼크", "allergic shock"
    ],
    "두드러기": [
        "urticaria", "hives", "발진", "rash"
    ],
    "에피네프린": [
        "epinephrine", "adrenaline",
        "에피펜", "EpiPen"
    ],
}

def expand_synonyms(keywords: list[str]) -> list[str]:
    """키워드를 동의어로 확장"""
    expanded = set(keywords)
    for keyword in keywords:
        for term, synonyms in ALLERGY_SYNONYMS.items():
            if keyword in term or keyword in synonyms:
                expanded.update(synonyms)
                expanded.add(term)
    return list(expanded)
```

#### 3.1.3 질문 의도 분류

```python
# backend/app/services/intent_classifier.py

from enum import Enum

class QuestionIntent(Enum):
    COMPARISON = "comparison"      # 비교 (A와 B의 차이)
    DEFINITION = "definition"      # 정의 (X란 무엇인가)
    SYMPTOM = "symptom"           # 증상 (어떤 증상이)
    TREATMENT = "treatment"        # 치료 (어떻게 치료)
    DIAGNOSIS = "diagnosis"        # 진단 (어떻게 진단)
    AVOIDANCE = "avoidance"       # 회피 (무엇을 피해야)
    EMERGENCY = "emergency"        # 응급 (응급 상황)
    GENERAL = "general"           # 일반

INTENT_PATTERNS = {
    QuestionIntent.COMPARISON: [
        r"차이점", r"차이가", r"비교", r"vs", r"다른점",
        r"와.*의 차이", r"과.*의 차이"
    ],
    QuestionIntent.DEFINITION: [
        r"무엇인가", r"뭔가요", r"이란", r"란 무엇", r"정의"
    ],
    QuestionIntent.SYMPTOM: [
        r"증상", r"증세", r"어떤 반응", r"나타나"
    ],
    QuestionIntent.TREATMENT: [
        r"치료", r"어떻게 해", r"대처", r"처방"
    ],
    QuestionIntent.DIAGNOSIS: [
        r"진단", r"검사", r"확인", r"알 수 있"
    ],
    QuestionIntent.AVOIDANCE: [
        r"피해야", r"회피", r"먹으면 안", r"조심"
    ],
    QuestionIntent.EMERGENCY: [
        r"응급", r"아나필락시스", r"쇼크", r"119"
    ],
}

def classify_intent(question: str) -> QuestionIntent:
    """질문 의도 분류"""
    import re
    for intent, patterns in INTENT_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, question):
                return intent
    return QuestionIntent.GENERAL
```

### 3.2 Phase 2: 하이브리드 검색 엔진

#### 3.2.1 BM25 키워드 검색

```python
# backend/app/services/keyword_search.py

from rank_bm25 import BM25Okapi

class BM25SearchEngine:
    def __init__(self, papers: list[Paper]):
        # 논문 텍스트 토큰화
        self.papers = papers
        self.tokenized_docs = [
            self._tokenize(p.title + " " + (p.abstract or ""))
            for p in papers
        ]
        self.bm25 = BM25Okapi(self.tokenized_docs)

    def _tokenize(self, text: str) -> list[str]:
        """텍스트 토큰화"""
        # 한글 + 영어 토큰화
        import re
        tokens = re.findall(r'[가-힣]+|[a-zA-Z]+', text.lower())
        return tokens

    def search(self, query: str, top_k: int = 10) -> list[tuple[Paper, float]]:
        """BM25 검색"""
        query_tokens = self._tokenize(query)
        scores = self.bm25.get_scores(query_tokens)

        # 점수 기준 정렬
        ranked = sorted(
            zip(self.papers, scores),
            key=lambda x: x[1],
            reverse=True
        )
        return ranked[:top_k]
```

#### 3.2.2 시맨틱 검색 (Vector Search)

```python
# backend/app/services/semantic_search.py

from sentence_transformers import SentenceTransformer
import numpy as np

class SemanticSearchEngine:
    def __init__(self):
        # 다국어 임베딩 모델
        self.model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
        self.paper_embeddings = None
        self.papers = []

    def index_papers(self, papers: list[Paper]):
        """논문 임베딩 인덱싱"""
        self.papers = papers
        texts = [
            f"{p.title} {p.title_kr or ''} {p.abstract or ''}"
            for p in papers
        ]
        self.paper_embeddings = self.model.encode(texts, convert_to_numpy=True)

    def search(self, query: str, top_k: int = 10, threshold: float = 0.5) -> list[tuple[Paper, float]]:
        """시맨틱 유사도 검색"""
        query_embedding = self.model.encode(query, convert_to_numpy=True)

        # 코사인 유사도 계산
        similarities = np.dot(self.paper_embeddings, query_embedding) / (
            np.linalg.norm(self.paper_embeddings, axis=1) * np.linalg.norm(query_embedding)
        )

        # 임계값 이상만 필터링
        results = []
        for i, score in enumerate(similarities):
            if score >= threshold:
                results.append((self.papers[i], float(score)))

        # 점수 기준 정렬
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:top_k]
```

#### 3.2.3 하이브리드 검색 통합

```python
# backend/app/services/hybrid_search.py

class HybridSearchEngine:
    def __init__(self, papers: list[Paper]):
        self.bm25_engine = BM25SearchEngine(papers)
        self.semantic_engine = SemanticSearchEngine()
        self.semantic_engine.index_papers(papers)

    def search(
        self,
        query: str,
        expanded_keywords: list[str],
        top_k: int = 10,
        bm25_weight: float = 0.4,
        semantic_weight: float = 0.6
    ) -> list[tuple[Paper, float]]:
        """하이브리드 검색 (BM25 + Semantic)"""

        # BM25 검색 (확장된 키워드 사용)
        bm25_query = " ".join(expanded_keywords)
        bm25_results = self.bm25_engine.search(bm25_query, top_k * 2)

        # 시맨틱 검색 (원본 질문 사용)
        semantic_results = self.semantic_engine.search(query, top_k * 2)

        # 점수 통합 (RRF: Reciprocal Rank Fusion)
        paper_scores = {}

        for rank, (paper, _) in enumerate(bm25_results):
            paper_id = paper.id
            paper_scores[paper_id] = paper_scores.get(paper_id, {})
            paper_scores[paper_id]['bm25_rank'] = rank + 1
            paper_scores[paper_id]['paper'] = paper

        for rank, (paper, _) in enumerate(semantic_results):
            paper_id = paper.id
            paper_scores[paper_id] = paper_scores.get(paper_id, {})
            paper_scores[paper_id]['semantic_rank'] = rank + 1
            paper_scores[paper_id]['paper'] = paper

        # RRF 점수 계산
        k = 60  # RRF 상수
        final_scores = []
        for paper_id, data in paper_scores.items():
            bm25_rank = data.get('bm25_rank', 1000)
            semantic_rank = data.get('semantic_rank', 1000)

            rrf_score = (
                bm25_weight * (1 / (k + bm25_rank)) +
                semantic_weight * (1 / (k + semantic_rank))
            )
            final_scores.append((data['paper'], rrf_score))

        # 최종 정렬
        final_scores.sort(key=lambda x: x[1], reverse=True)
        return final_scores[:top_k]
```

### 3.3 Phase 3: LLM 답변 생성

#### 3.3.1 프롬프트 템플릿

```python
# backend/app/services/llm_qa.py

SYSTEM_PROMPT = """당신은 알레르기 전문 의료 정보 AI 어시스턴트입니다.

규칙:
1. 제공된 논문과 임상 진술문만을 근거로 답변하세요.
2. 답변에 출처를 반드시 인용하세요 (예: [1], [2]).
3. 확실하지 않은 정보는 "추가 확인이 필요합니다"라고 명시하세요.
4. 의학적 조언이 아닌 정보 제공임을 명확히 하세요.
5. 응급 상황 관련 질문에는 항상 "즉시 의료진 상담" 권고를 포함하세요.

답변 형식:
- 핵심 내용을 먼저 간결하게 요약
- 세부 내용은 구조화하여 제시
- 마지막에 출처 목록 첨부
"""

COMPARISON_TEMPLATE = """
다음 질문에 답변하세요:
{question}

참고 논문:
{papers}

참고 임상 진술문:
{clinical_statements}

비교 형식으로 답변하세요:
1. 첫 번째 항목 (정의, 원인, 증상, 예후)
2. 두 번째 항목 (정의, 원인, 증상, 예후)
3. 핵심 차이점 요약

출처를 반드시 인용하세요.
"""

DEFINITION_TEMPLATE = """
다음 질문에 답변하세요:
{question}

참고 논문:
{papers}

다음 구조로 답변하세요:
1. 정의
2. 원인/기전
3. 주요 증상
4. 진단 방법
5. 관리/치료

출처를 반드시 인용하세요.
"""
```

#### 3.3.2 LLM 서비스

```python
# backend/app/services/llm_service.py

from anthropic import Anthropic
from openai import OpenAI

class LLMService:
    def __init__(self, provider: str = "anthropic"):
        if provider == "anthropic":
            self.client = Anthropic()
            self.model = "claude-3-5-sonnet-20241022"
        else:
            self.client = OpenAI()
            self.model = "gpt-4o"
        self.provider = provider

    def generate_answer(
        self,
        question: str,
        intent: QuestionIntent,
        papers: list[Paper],
        clinical_statements: list[ClinicalStatement]
    ) -> dict:
        """LLM 기반 답변 생성"""

        # 논문 컨텍스트 생성
        papers_context = self._format_papers(papers)
        statements_context = self._format_statements(clinical_statements)

        # 의도에 맞는 템플릿 선택
        template = self._get_template(intent)

        # 프롬프트 구성
        prompt = template.format(
            question=question,
            papers=papers_context,
            clinical_statements=statements_context
        )

        # LLM 호출
        if self.provider == "anthropic":
            response = self.client.messages.create(
                model=self.model,
                max_tokens=2000,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}]
            )
            answer = response.content[0].text
        else:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt}
                ]
            )
            answer = response.choices[0].message.content

        return {
            "answer": answer,
            "papers_used": len(papers),
            "statements_used": len(clinical_statements)
        }

    def _format_papers(self, papers: list[Paper]) -> str:
        """논문 포맷팅"""
        formatted = []
        for i, paper in enumerate(papers, 1):
            formatted.append(
                f"[{i}] {paper.title}\n"
                f"    저자: {paper.authors}\n"
                f"    저널: {paper.journal} ({paper.year})\n"
                f"    요약: {paper.abstract[:500] if paper.abstract else 'N/A'}..."
            )
        return "\n\n".join(formatted)

    def _format_statements(self, statements: list[ClinicalStatement]) -> str:
        """임상 진술문 포맷팅"""
        formatted = []
        for stmt in statements:
            formatted.append(
                f"- [{stmt.evidence_level}] {stmt.statement_kr}\n"
                f"  출처: {stmt.paper.title if stmt.paper else 'N/A'}"
            )
        return "\n".join(formatted)
```

### 3.4 Phase 4: 신뢰도 계산 고도화

```python
# backend/app/services/confidence_calculator.py

class ConfidenceCalculator:
    def calculate(
        self,
        papers: list[Paper],
        clinical_statements: list[ClinicalStatement],
        search_scores: list[float],
        intent: QuestionIntent
    ) -> float:
        """다요소 신뢰도 계산"""

        score = 0.0

        # 1. 검색 결과 품질 (30%)
        if papers:
            avg_search_score = sum(search_scores) / len(search_scores)
            score += avg_search_score * 0.3

        # 2. 논문 수 및 품질 (30%)
        paper_score = 0.0
        if papers:
            # 논문 수 (최대 5개 기준)
            paper_score += min(len(papers) / 5, 1.0) * 0.15

            # 최근 논문 비율 (2020년 이후)
            recent_ratio = sum(1 for p in papers if p.year and p.year >= 2020) / len(papers)
            paper_score += recent_ratio * 0.10

            # DOI/PMID 있는 비율
            verified_ratio = sum(1 for p in papers if p.doi or p.pmid) / len(papers)
            paper_score += verified_ratio * 0.05

        score += paper_score

        # 3. 임상 진술문 매칭 (25%)
        if clinical_statements:
            # 진술문 수
            stmt_score = min(len(clinical_statements) / 3, 1.0) * 0.15

            # GRADE 수준
            grade_scores = {'A': 1.0, 'B': 0.8, 'C': 0.6, 'D': 0.4}
            avg_grade = sum(
                grade_scores.get(s.evidence_level, 0.5)
                for s in clinical_statements
            ) / len(clinical_statements)
            stmt_score += avg_grade * 0.10

            score += stmt_score

        # 4. 의도 매칭 보너스 (15%)
        # 비교, 정의 등 명확한 의도는 답변 품질이 높음
        intent_bonus = {
            QuestionIntent.COMPARISON: 0.15,
            QuestionIntent.DEFINITION: 0.15,
            QuestionIntent.SYMPTOM: 0.12,
            QuestionIntent.TREATMENT: 0.12,
            QuestionIntent.DIAGNOSIS: 0.12,
            QuestionIntent.AVOIDANCE: 0.10,
            QuestionIntent.EMERGENCY: 0.10,
            QuestionIntent.GENERAL: 0.05,
        }
        score += intent_bonus.get(intent, 0.05)

        return min(score, 1.0)
```

---

## 4. 데이터베이스 확장

### 4.1 새로운 테이블

```sql
-- 질문-답변 로그 (학습 및 분석용)
CREATE TABLE qa_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    question TEXT NOT NULL,
    extracted_keywords TEXT[],
    expanded_keywords TEXT[],
    detected_intent VARCHAR(50),

    -- 검색 결과
    papers_found INTEGER,
    statements_found INTEGER,
    search_scores JSONB,

    -- 답변
    answer TEXT,
    confidence DECIMAL(3,2),

    -- 피드백
    user_rating INTEGER,  -- 1-5
    user_feedback TEXT,

    created_at TIMESTAMP DEFAULT NOW()
);

-- 의학 용어 동의어 사전 (관리자 편집 가능)
CREATE TABLE medical_synonyms (
    id SERIAL PRIMARY KEY,
    term VARCHAR(100) NOT NULL,
    synonyms TEXT[] NOT NULL,
    category VARCHAR(50),  -- allergen, symptom, treatment, etc.
    language VARCHAR(10) DEFAULT 'ko',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP
);

-- 논문 임베딩 캐시
CREATE TABLE paper_embeddings (
    id SERIAL PRIMARY KEY,
    paper_id INTEGER REFERENCES papers(id) UNIQUE,
    embedding VECTOR(384),  -- pgvector 사용
    model_version VARCHAR(100),
    created_at TIMESTAMP DEFAULT NOW()
);
```

### 4.2 pgvector 확장 설치

```sql
-- PostgreSQL에서 벡터 검색 지원
CREATE EXTENSION IF NOT EXISTS vector;

-- 임베딩 인덱스 생성
CREATE INDEX ON paper_embeddings
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);
```

---

## 5. API 설계

### 5.1 개선된 Q&A 엔드포인트

```python
# backend/app/professional/research/routes.py

class QARequestV2(BaseModel):
    question: str
    context_allergens: Optional[list[str]] = None
    include_clinical_statements: bool = True
    max_papers: int = Field(default=5, le=10)
    language: str = Field(default="ko", pattern="^(ko|en)$")

class QAResponseV2(BaseModel):
    answer: str
    confidence: float
    intent: str
    keywords: list[str]
    related_papers: list[PaperResponse]
    clinical_statements: list[ClinicalStatementResponse]
    warnings: list[str]
    processing_time_ms: int

@router.post("/qa/v2", response_model=QAResponseV2)
async def ask_question_v2(
    request: QARequestV2,
    user: User = Depends(require_professional),
    db: Session = Depends(get_db)
):
    """고도화된 Q&A API

    - 키워드 추출 및 동의어 확장
    - 하이브리드 검색 (BM25 + Semantic)
    - LLM 기반 답변 생성
    - 다요소 신뢰도 계산
    """
    start_time = time.time()

    # 1. 키워드 추출
    keywords = keyword_extractor.extract_keywords(request.question)
    medical_terms = keyword_extractor.extract_medical_terms(request.question)

    # 2. 동의어 확장
    expanded = expand_synonyms(keywords + medical_terms)

    # 3. 의도 분류
    intent = classify_intent(request.question)

    # 4. 하이브리드 검색
    search_results = hybrid_engine.search(
        request.question,
        expanded,
        top_k=request.max_papers
    )
    papers = [r[0] for r in search_results]
    scores = [r[1] for r in search_results]

    # 5. 임상 진술문 매칭
    statements = []
    if request.include_clinical_statements:
        statements = match_clinical_statements(keywords, papers)

    # 6. LLM 답변 생성
    llm_result = llm_service.generate_answer(
        request.question, intent, papers, statements
    )

    # 7. 신뢰도 계산
    confidence = confidence_calculator.calculate(
        papers, statements, scores, intent
    )

    # 8. 경고 생성
    warnings = generate_warnings(intent, papers)

    processing_time = int((time.time() - start_time) * 1000)

    # 9. 로그 저장
    save_qa_log(user.id, request, keywords, intent, papers,
                llm_result['answer'], confidence)

    return QAResponseV2(
        answer=llm_result['answer'],
        confidence=confidence,
        intent=intent.value,
        keywords=keywords,
        related_papers=papers,
        clinical_statements=statements,
        warnings=warnings,
        processing_time_ms=processing_time
    )
```

---

## 6. 구현 로드맵

### Phase 1: 키워드 및 동의어 (2주)

| 작업 | 설명 | 의존성 |
|------|------|--------|
| 형태소 분석기 설치 | konlpy + mecab-ko | 없음 |
| KeywordExtractor 구현 | 키워드 추출 클래스 | 형태소 분석기 |
| 의학 동의어 사전 구축 | medical_synonyms 테이블 + 초기 데이터 | 없음 |
| 동의어 확장 로직 | expand_synonyms 함수 | 동의어 사전 |
| 의도 분류기 | IntentClassifier 구현 | 없음 |

### Phase 2: 하이브리드 검색 (3주)

| 작업 | 설명 | 의존성 |
|------|------|--------|
| BM25 검색 엔진 | rank_bm25 기반 구현 | 없음 |
| 시맨틱 검색 엔진 | sentence-transformers 기반 | 없음 |
| pgvector 설치 | PostgreSQL 벡터 확장 | 없음 |
| 논문 임베딩 인덱싱 | 기존 논문 벡터화 | 시맨틱 엔진 |
| 하이브리드 통합 | RRF 기반 점수 통합 | BM25 + 시맨틱 |

### Phase 3: LLM 통합 (2주)

| 작업 | 설명 | 의존성 |
|------|------|--------|
| LLM 서비스 구현 | Anthropic/OpenAI 클라이언트 | API 키 |
| 프롬프트 템플릿 | 의도별 템플릿 설계 | 의도 분류기 |
| 답변 생성 로직 | generate_answer 구현 | LLM 서비스 |
| 출처 인용 포맷터 | 논문 인용 자동 생성 | 없음 |

### Phase 4: 통합 및 최적화 (2주)

| 작업 | 설명 | 의존성 |
|------|------|--------|
| 신뢰도 계산기 | 다요소 신뢰도 | 모든 컴포넌트 |
| QA API v2 | 통합 엔드포인트 | 모든 컴포넌트 |
| 프론트엔드 업데이트 | QAPage 개선 | API v2 |
| 로깅 및 분석 | qa_logs 테이블 | 없음 |
| 성능 최적화 | 캐싱, 배치 처리 | 없음 |

---

## 7. 기술 스택

| 컴포넌트 | 기술 | 용도 |
|----------|------|------|
| 형태소 분석 | konlpy + mecab-ko | 한글 키워드 추출 |
| 키워드 검색 | rank_bm25 | BM25 알고리즘 |
| 시맨틱 검색 | sentence-transformers | 임베딩 생성 |
| 벡터 DB | pgvector | 벡터 유사도 검색 |
| LLM | Claude API / GPT-4 | 답변 생성 |

### 의존성 추가

```txt
# requirements.txt 추가
konlpy==0.6.0
mecab-python3==1.0.8
rank-bm25==0.2.2
sentence-transformers==2.2.2
pgvector==0.2.4
anthropic==0.18.0
openai==1.12.0
```

---

## 8. 예상 결과

### 8.1 개선 전/후 비교

| 지표 | 개선 전 | 개선 후 |
|------|---------|---------|
| 검색 성공률 | ~30% | ~85% |
| 평균 신뢰도 | 0.35 | 0.75 |
| 응답 품질 | 논문 목록만 | 구조화된 답변 |
| 출처 인용 | 없음 | 자동 인용 |
| 응답 시간 | <500ms | <2000ms |

### 8.2 예시 결과

**질문**: "우유 알러지와 유당불내증의 차이점은?"

**개선 전**:
```
'우유 알러지와 유당불내증의 차이점은?'에 대한 관련 논문을 찾지 못했습니다.
다른 키워드로 검색해 보시기 바랍니다.

신뢰도: 30%
```

**개선 후**:
```
우유 알러지(Cow's Milk Allergy, CMA)와 유당불내증(Lactose Intolerance)은
서로 다른 질환입니다.

## 우유 알러지 (CMA)
- **원인**: 우유 단백질(카제인, β-락토글로불린)에 대한 면역 반응
- **기전**: IgE 매개 또는 non-IgE 매개 면역 반응
- **증상**: 두드러기, 구토, 호흡곤란, 아나필락시스 가능
- **발생 시기**: 주로 영아기 (생후 1년 내)
- **예후**: 약 80%가 5세까지 자연 관해 [1]

## 유당불내증
- **원인**: 유당 분해 효소(락타아제) 활성 저하
- **기전**: 효소 결핍으로 인한 소화 장애 (면역 반응 아님)
- **증상**: 복부 팽만, 설사, 가스, 복통
- **발생 시기**: 주로 성인기 (원발성) 또는 장 손상 후 (이차성)
- **예후**: 지속적이나 효소 보충 또는 유당 제한으로 관리 가능

## 핵심 차이점
| 구분 | 우유 알러지 | 유당불내증 |
|------|-----------|-----------|
| 기전 | 면역 반응 | 효소 결핍 |
| 원인 물질 | 우유 단백질 | 유당(탄수화물) |
| 심각성 | 아나필락시스 가능 | 생명 위협 없음 |
| 진단 | sIgE, 피부단자검사, OFC | 유당부하검사, 수소호기검사 |

---
**참고 문헌**
[1] AAAAI Practice Parameter: Food Allergy. J Allergy Clin Immunol. 2020
[2] Lactose Intolerance in Adults. Am Fam Physician. 2022

⚠️ 본 정보는 의학 논문을 기반으로 작성되었습니다.
   정확한 진단과 치료는 전문 의료진과 상담하세요.

신뢰도: 87%
```

---

## 변경 이력

| 버전 | 날짜 | 변경 내용 |
|------|------|----------|
| 1.0 | 2025-01-27 | 초기 작성 |
