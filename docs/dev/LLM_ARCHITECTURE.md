# LLM 아키텍처

## 개요

AllergyInsight는 뉴스 분석, RAG Q&A, 번역 등 다양한 AI 기능에 LLM을 활용합니다.
용도별로 최적의 LLM을 선택하는 **이중화 프로바이더 구조**를 사용합니다.

## 프로바이더 구조

```
OllamaService (통합 인터페이스)
├── Gemini API (클라우드) — 고품질이 필요한 작업
├── 로컬 LLM (MLX/Ollama) — 대량 처리 작업
└── 키워드 Fallback — LLM 전체 불가 시
```

### 용도별 배분

| 용도 | 기본 프로바이더 | Fallback | 환경변수 |
|------|----------------|----------|----------|
| 뉴스 분석 (요약/중요도/분류) | Gemini | 로컬 → 키워드 | `NEWS_LLM_PROVIDER` |
| RAG Q&A 답변 | Gemini | 로컬 | `RAG_LLM_PROVIDER` |
| 한국어 번역 | 로컬 | — | — |
| 알러젠 추출 | 로컬 | 키워드 | — |

### Fallback 체인

```
1차: Gemini API → 성공 시 결과 반환
  ↓ (실패)
2차: 로컬 LLM (MLX/Ollama) → 성공 시 결과 반환
  ↓ (실패)
3차: 키워드 기반 분석 (규칙 기반)
```

## 환경변수

| 변수 | 설명 | 기본값 |
|------|------|--------|
| `GEMINI_API_KEY` | Google Gemini API 키 | (필수) |
| `NEWS_LLM_PROVIDER` | 뉴스 분석 LLM 선택 (`gemini` \| `local`) | `gemini` |
| `RAG_LLM_PROVIDER` | RAG 답변 LLM 선택 (`gemini` \| `local`) | `gemini` |
| `LLM_API_URL` | 로컬 LLM OpenAI 호환 API URL | `http://localhost:11435/v1` |
| `LLM_MODEL` | 로컬 LLM 모델명 | (설정 참조) |
| `NEWS_RELEVANCE_THRESHOLD` | 뉴스 관련성 최소 임계값 | `0.3` |
| `NEWS_IMPORTANCE_THRESHOLD` | 뉴스 중요도 최소 임계값 | `0.2` |

## 뉴스 분석 파이프라인

```
수집 (Naver API + Google RSS)
  ↓
중복 제거 (URL + content_hash)
  ↓
AI 통합 분석 (1회 호출로 4항목 동시 분석)
  ├── 관련성 점수 (relevance_score)
  ├── 한국어 요약 (summary)
  ├── 중요도 점수 (importance_score)
  └── 카테고리 분류 (category)
  ↓
품질 게이트
  ├── 관련성 < 0.3 → 제외
  ├── 중요도 < 0.2 → 제외
  └── 요약 실패 패턴 → 제외
  ↓
뉴스레터 발송
```

## 통합 프롬프트

기사당 API 호출을 최소화하기 위해 단일 프롬프트로 4가지를 동시 분석합니다.

**응답 형식:**
```
RELEVANCE: 0.8
SUMMARY: 한국어 2-3문장 요약
IMPORTANCE: 0.6
CATEGORY: market
```
