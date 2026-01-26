# 논문 링크 자동 추출 고도화 방안

## 현재 구현 (Phase 1: 키워드 사전 매칭)

### 구현 완료 항목

1. **키워드 사전** (`backend/app/data/paper_keywords.py`)
   - 증상 키워드 (영어 → 한국어 매핑)
   - 회피 식품 키워드 (알러젠별 분류)
   - 대체 식품 키워드
   - 환경 관리 키워드 (흡입성 알러젠)
   - 논문 타입 감지 키워드

2. **추출 서비스** (`backend/app/services/paper_link_extractor.py`)
   - Abstract에서 키워드 자동 추출
   - 알러젠 자동 감지
   - 논문 타입 자동 분류
   - 관련도 점수 계산

3. **API 엔드포인트** (`backend/app/auth/paper_routes.py`)
   - `POST /papers` - 저장 시 자동 링크 추출
   - `POST /papers/{id}/extract-links` - 기존 논문 링크 추출
   - `POST /papers/extract-links/batch` - 일괄 추출
   - `GET /papers/citations/by-specific-item` - 특정 항목별 출처 조회

4. **프론트엔드 UI** (`frontend/src/pages/MyDiagnosisPage.jsx`)
   - CitationBadge 컴포넌트 (출처 표시)
   - 증상 항목별 출처 아이콘
   - 식이 관리 항목별 출처 표시
   - 호버 시 논문 정보 툴팁

---

## Phase 2: MeSH Terms 활용 (고도화)

### 개요
PubMed에서 제공하는 MeSH(Medical Subject Headings)를 활용하여 더 정확한 의학 용어 매핑

### 구현 계획

#### 1. MeSH Terms 수집
```python
# pubmed_service.py 수정
def get_paper_with_mesh(pmid: str) -> Paper:
    """PubMed에서 MeSH terms 포함하여 논문 정보 조회"""
    # E-utilities API 호출
    # MeSH terms 파싱
    # Paper 객체에 mesh_terms 필드 추가
```

#### 2. MeSH → specific_item 매핑 테이블
```python
# mesh_mapping.py
MESH_TO_SPECIFIC_ITEM = {
    # 증상
    "Anaphylaxis": {
        "link_type": "symptom",
        "specific_item_kr": "아나필락시스",
        "allergens": ["peanut", "milk", "shellfish", "tree_nuts"]
    },
    "Urticaria": {
        "link_type": "symptom",
        "specific_item_kr": "두드러기",
        "allergens": ["*"]  # 모든 알러젠
    },

    # 식이 관리
    "Diet, Gluten-Free": {
        "link_type": "dietary",
        "specific_item_kr": "글루텐프리 식단",
        "allergens": ["wheat"]
    },
    "Milk Substitutes": {
        "link_type": "substitute",
        "specific_item_kr": "우유 대체제",
        "allergens": ["milk"]
    },

    # 치료/관리
    "Epinephrine": {
        "link_type": "emergency",
        "specific_item_kr": "에피네프린",
        "allergens": ["*"]
    },
}
```

#### 3. 자동 추출 로직 개선
```python
class PaperLinkExtractor:
    def extract_links_with_mesh(self, paper: Paper) -> List[ExtractedLink]:
        links = []

        # 1. 기존 키워드 매칭
        keyword_links = self.extract_links(paper.title, paper.abstract)
        links.extend(keyword_links)

        # 2. MeSH terms 매핑 (더 높은 신뢰도)
        if paper.mesh_terms:
            for mesh_term in paper.mesh_terms:
                if mesh_term in MESH_TO_SPECIFIC_ITEM:
                    mapping = MESH_TO_SPECIFIC_ITEM[mesh_term]
                    links.append(ExtractedLink(
                        link_type=mapping["link_type"],
                        specific_item=mapping["specific_item_kr"],
                        relevance_score=95,  # MeSH는 높은 점수
                        source="mesh"
                    ))

        return self._deduplicate_links(links)
```

### 기대 효과
- 의학적으로 검증된 표준 용어 사용
- 키워드 사전 관리 부담 감소
- 더 정확한 논문-항목 매칭

### 필요 작업
1. PubMed E-utilities API 연동 강화
2. MeSH 매핑 테이블 구축 (약 200개 주요 용어)
3. DB 스키마에 mesh_terms 필드 추가
4. 추출 로직 통합

---

## Phase 3: LLM 기반 추출 (고급 고도화)

### 개요
OpenAI/Claude API를 활용하여 논문 초록에서 구조화된 정보를 정밀하게 추출

### 구현 계획

#### 1. LLM 추출 서비스
```python
# llm_extractor.py
import openai
from typing import List, Dict

class LLMPaperExtractor:
    def __init__(self, api_key: str, model: str = "gpt-4o-mini"):
        self.client = openai.OpenAI(api_key=api_key)
        self.model = model

    async def extract_links(self, paper: Paper) -> List[ExtractedLink]:
        prompt = self._build_prompt(paper)

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.1  # 일관성을 위해 낮은 temperature
        )

        return self._parse_response(response)

    def _build_prompt(self, paper: Paper) -> str:
        return f"""
논문 정보를 분석하여 알러지 관련 항목을 추출하세요.

제목: {paper.title}
초록: {paper.abstract}

다음 카테고리별로 구체적 항목을 추출하세요:

1. 증상 (symptoms): 논문에서 언급된 알러지 증상
2. 회피식품 (avoid_foods): 회피해야 할 구체적 식품
3. 대체식품 (substitutes): 권장되는 대체 식품
4. 교차반응 (cross_reactivity): 교차반응 관계
5. 관리방법 (management): 환경 관리 또는 치료 방법

JSON 형식으로 응답하세요:
{{
  "allergens": ["peanut", "milk"],
  "items": [
    {{
      "category": "symptom",
      "item_kr": "아나필락시스",
      "item_en": "anaphylaxis",
      "allergen": "peanut",
      "confidence": 0.95,
      "evidence": "논문에서 직접 언급된 문장"
    }}
  ]
}}
"""
```

#### 2. 프롬프트 최적화
```python
SYSTEM_PROMPT = """
당신은 의학 논문 분석 전문가입니다.
알러지 관련 논문에서 환자 교육에 필요한 정보를 정확하게 추출합니다.

규칙:
1. 논문에 명시적으로 언급된 항목만 추출
2. 추론하거나 일반화하지 않음
3. 각 항목에 대한 근거 문장 제시
4. 신뢰도(confidence)는 0.7 이상인 항목만 포함
5. 한국어 의학 용어 사용
"""
```

#### 3. 비용 최적화 전략
```python
class SmartLLMExtractor:
    def should_use_llm(self, paper: Paper) -> bool:
        """LLM 사용 여부 판단"""
        # 1. 키워드 매칭으로 충분한지 확인
        keyword_links = self.keyword_extractor.extract_links(paper)
        if len(keyword_links) >= 5:
            return False  # 키워드로 충분

        # 2. 중요 논문인지 확인
        if paper.paper_type in ["guideline", "meta_analysis"]:
            return True  # 가이드라인은 LLM 사용

        # 3. 초록 길이 확인
        if len(paper.abstract or "") > 1500:
            return True  # 긴 초록은 LLM 사용

        return False

    async def extract_with_fallback(self, paper: Paper) -> List[ExtractedLink]:
        """하이브리드 추출"""
        # 1단계: 키워드 매칭
        links = self.keyword_extractor.extract_links(paper)

        # 2단계: MeSH 매칭
        if paper.mesh_terms:
            mesh_links = self.mesh_extractor.extract_links(paper)
            links = self._merge_links(links, mesh_links)

        # 3단계: 필요시 LLM 보강
        if self.should_use_llm(paper):
            llm_links = await self.llm_extractor.extract_links(paper)
            links = self._merge_links(links, llm_links)

        return links
```

#### 4. 배치 처리 (비용 절감)
```python
async def batch_extract_with_llm(papers: List[Paper], batch_size: int = 10):
    """배치로 LLM 호출하여 비용 절감"""
    results = {}

    for i in range(0, len(papers), batch_size):
        batch = papers[i:i+batch_size]

        # 여러 논문을 하나의 프롬프트로
        combined_prompt = "\n---\n".join([
            f"[Paper {p.id}]\nTitle: {p.title}\nAbstract: {p.abstract}"
            for p in batch
        ])

        response = await llm_client.extract_batch(combined_prompt)

        # 결과 파싱 및 저장
        for paper_id, links in response.items():
            results[paper_id] = links

    return results
```

### 기대 효과
- 키워드 사전에 없는 새로운 용어 처리
- 문맥 기반 정확한 분류
- 복잡한 관계(교차반응 등) 추출
- 논문 품질에 따른 관련도 점수 세분화

### 비용 예측 (gpt-4o-mini 기준)
- 논문당 평균 토큰: ~2,000 (입력) + ~500 (출력)
- 비용: 약 $0.001/논문
- 1,000개 논문 처리: 약 $1

### 필요 작업
1. OpenAI API 키 설정 (환경변수)
2. 프롬프트 테스트 및 최적화
3. 결과 검증 로직 구현
4. 관리자 UI에서 LLM 추출 옵션 추가

---

## 구현 로드맵

| Phase | 내용 | 예상 소요 | 난이도 |
|-------|------|----------|--------|
| 1 (완료) | 키워드 사전 매칭 | - | ★★☆ |
| 2 | MeSH Terms 활용 | 3-5일 | ★★★ |
| 3 | LLM 기반 추출 | 5-7일 | ★★★★ |

---

## 모니터링 및 품질 관리

### 추출 품질 대시보드
```python
@router.get("/papers/extraction-stats")
async def get_extraction_stats(db: Session = Depends(get_db)):
    """추출 통계 조회"""
    return {
        "total_papers": db.query(Paper).count(),
        "papers_with_links": db.query(Paper).filter(
            Paper.allergen_links.any()
        ).count(),
        "links_by_source": {
            "keyword": db.query(PaperAllergenLink).filter(
                PaperAllergenLink.note.like("Auto-extracted:%")
            ).count(),
            "mesh": db.query(PaperAllergenLink).filter(
                PaperAllergenLink.note.like("MeSH:%")
            ).count(),
            "llm": db.query(PaperAllergenLink).filter(
                PaperAllergenLink.note.like("LLM:%")
            ).count(),
            "manual": db.query(PaperAllergenLink).filter(
                PaperAllergenLink.note.is_(None)
            ).count(),
        },
        "avg_links_per_paper": ...,
        "coverage_by_allergen": {...}
    }
```

### 수동 검증 워크플로우
1. 자동 추출된 링크에 `is_verified=False` 설정
2. 관리자 UI에서 검증 대기 목록 표시
3. 관리자가 승인/수정/삭제
4. 승인된 링크만 사용자에게 표시

---

## 참고 자료

- [PubMed E-utilities API](https://www.ncbi.nlm.nih.gov/books/NBK25499/)
- [MeSH Browser](https://meshb.nlm.nih.gov/)
- [OpenAI API Documentation](https://platform.openai.com/docs)
- [Semantic Scholar API](https://api.semanticscholar.org/)
