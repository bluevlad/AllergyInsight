"""로컬 LLM AI 서비스

OpenAI 호환 API를 사용하여 로컬 LLM 서버(MLX, Ollama 등)와 통신합니다.
LLM 서버 미가용 시 키워드 기반 fallback을 제공합니다.

환경 변수:
    LLM_API_URL: OpenAI 호환 API base URL (기본: http://localhost:11435/v1)
    LLM_MODEL: 사용할 모델명 (기본: mlx-community/Qwen2.5-7B-Instruct-4bit)
    OLLAMA_HOST: (하위 호환) Ollama 호스트 URL
    OLLAMA_MODEL: (하위 호환) Ollama 모델명
"""
import os
import logging
from typing import Optional

import httpx

from ..models.news_category import NewsCategoryType, classify_by_keywords

logger = logging.getLogger(__name__)

# 기본값: MLX 서버 (Ollama 환경 변수 하위 호환)
_DEFAULT_MLX_URL = "http://localhost:11435/v1"
_DEFAULT_MLX_MODEL = "mlx-community/Qwen2.5-7B-Instruct-4bit"


def _resolve_api_config() -> tuple[str, str]:
    """LLM API URL과 모델을 환경 변수에서 결정

    우선순위:
    1. LLM_API_URL / LLM_MODEL (명시적 설정)
    2. OLLAMA_HOST / OLLAMA_MODEL (하위 호환 → Ollama /v1 경로 자동 추가)
    3. 기본값 (MLX 서버)
    """
    llm_url = os.getenv("LLM_API_URL")
    llm_model = os.getenv("LLM_MODEL")

    if llm_url:
        return llm_url, llm_model or _DEFAULT_MLX_MODEL

    ollama_host = os.getenv("OLLAMA_HOST")
    ollama_model = os.getenv("OLLAMA_MODEL")

    if ollama_host:
        # Ollama도 OpenAI 호환 /v1 엔드포인트를 지원
        base = ollama_host.rstrip("/")
        return f"{base}/v1", ollama_model or "qwen2.5:latest"

    return _DEFAULT_MLX_URL, llm_model or _DEFAULT_MLX_MODEL


class OllamaService:
    """로컬 LLM 기반 AI 분석 서비스 (OpenAI 호환 API)"""

    def __init__(
        self,
        api_url: Optional[str] = None,
        model: Optional[str] = None,
    ):
        resolved_url, resolved_model = _resolve_api_config()
        self.api_url = api_url or resolved_url
        self.model = model or resolved_model
        self._available: Optional[bool] = None
        self._client: Optional[httpx.Client] = None

    def _get_client(self) -> httpx.Client:
        """httpx 클라이언트 (lazy 초기화)"""
        if self._client is None:
            self._client = httpx.Client(timeout=120.0)
        return self._client

    @property
    def is_available(self) -> bool:
        """LLM 서버 사용 가능 여부"""
        if self._available is None:
            try:
                client = self._get_client()
                # /models 엔드포인트로 서버 상태 확인
                resp = client.get(f"{self.api_url}/models", timeout=5.0)
                self._available = resp.status_code == 200
            except Exception as e:
                logger.warning(f"LLM 서버 연결 실패 ({self.api_url}): {e}. Fallback 모드로 동작합니다.")
                self._available = False
        return self._available

    def _chat(self, prompt: str, max_tokens: int = 500, max_retries: int = 2) -> Optional[str]:
        """OpenAI 호환 chat/completions 호출"""
        if not self.is_available:
            return None

        client = self._get_client()
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.3,
            "max_tokens": max_tokens,
        }

        for attempt in range(max_retries):
            try:
                resp = client.post(
                    f"{self.api_url}/chat/completions",
                    json=payload,
                    timeout=120.0,
                )
                resp.raise_for_status()
                data = resp.json()
                return data["choices"][0]["message"]["content"].strip()
            except Exception as e:
                logger.warning(f"LLM 호출 실패 (시도 {attempt + 1}): {e}")
                if attempt == max_retries - 1:
                    self._available = False

        return None

    def _chat_long(self, prompt: str) -> Optional[str]:
        """긴 응답용 호출 (max_tokens 확장)"""
        return self._chat(prompt, max_tokens=2000)

    def summarize(self, title: str, description: str) -> str:
        """기사 요약 생성"""
        prompt = (
            "다음 뉴스 기사를 한국어로 2-3문장으로 요약하세요. "
            "핵심 내용만 간결하게 작성하세요.\n\n"
            f"제목: {title}\n"
            f"내용: {description or '(내용 없음)'}\n\n"
            "요약:"
        )

        result = self._chat(prompt)
        if result:
            return result

        # Fallback: 제목 + 설명 앞부분
        if description:
            return description[:200].strip()
        return title

    def score_importance(self, title: str, description: str) -> float:
        """중요도 점수 (0.0~1.0)"""
        prompt = (
            "다음 뉴스 기사의 체외진단/알러지 산업 관련 중요도를 0.0~1.0 사이 숫자로만 답하세요.\n"
            "기준: 규제 변화, 신제품 출시, M&A, 큰 투자는 높은 점수, "
            "일반 홍보/이벤트는 낮은 점수.\n\n"
            f"제목: {title}\n"
            f"내용: {description or '(내용 없음)'}\n\n"
            "점수(숫자만):"
        )

        result = self._chat(prompt)
        if result:
            try:
                score = float(result.split()[0].strip(".,"))
                return max(0.0, min(1.0, score))
            except (ValueError, IndexError):
                pass

        # Fallback: 키워드 기반 점수
        return self._keyword_importance(title, description)

    def classify(self, title: str, description: str) -> str:
        """카테고리 분류"""
        categories = ", ".join([c.value for c in NewsCategoryType])
        prompt = (
            f"다음 뉴스 기사를 이 카테고리 중 하나로 분류하세요: {categories}\n"
            "카테고리 이름만 답하세요.\n\n"
            f"제목: {title}\n"
            f"내용: {description or '(내용 없음)'}\n\n"
            "카테고리:"
        )

        result = self._chat(prompt)
        if result:
            result_lower = result.lower().strip()
            for cat in NewsCategoryType:
                if cat.value in result_lower:
                    return cat.value

        # Fallback: 키워드 분류
        text = f"{title} {description or ''}"
        return classify_by_keywords(text).value

    def analyze_article(self, title: str, description: str) -> dict:
        """기사 종합 분석 (요약 + 중요도 + 카테고리)"""
        return {
            "summary": self.summarize(title, description),
            "importance_score": self.score_importance(title, description),
            "category": self.classify(title, description),
        }

    # --- 알러젠 인사이트 분석 기능 ---

    KNOWN_ALLERGENS = [
        "peanut", "milk", "egg", "wheat", "soy", "fish", "shrimp", "crab",
        "peach", "walnut", "pine_nut", "sesame", "buckwheat", "tomato",
        "pork", "chicken", "beef", "squid", "mussel", "abalone",
        "dust_mite", "dog", "cat", "cockroach", "mold",
        "cedar", "birch", "ragweed", "grass", "mugwort",
    ]

    def extract_allergens(self, title: str, description: str) -> list[dict]:
        """뉴스/논문에서 알러젠 코드 + 카테고리 추출"""
        allergen_list = ", ".join(self.KNOWN_ALLERGENS)
        prompt = (
            "다음 기사에서 관련된 알러젠과 내용 카테고리를 JSON 배열로 추출하세요.\n"
            f"알러젠 목록: {allergen_list}\n"
            "카테고리: treatment, epidemiology, diagnosis_method, regulation, research\n"
            "관련 알러젠이 없으면 빈 배열 []을 반환하세요.\n\n"
            f"제목: {title}\n"
            f"내용: {description or '(내용 없음)'}\n\n"
            '응답 형식(JSON만): [{"allergen": "peanut", "category": "treatment", "relevance": 0.8}]'
        )

        result = self._chat(prompt)
        if result:
            try:
                import json
                # JSON 배열 부분 추출
                start = result.find("[")
                end = result.rfind("]") + 1
                if start >= 0 and end > start:
                    items = json.loads(result[start:end])
                    valid = []
                    for item in items:
                        code = item.get("allergen", "")
                        if code in self.KNOWN_ALLERGENS:
                            valid.append({
                                "allergen": code,
                                "category": item.get("category", "research"),
                                "relevance": max(0.0, min(1.0, float(item.get("relevance", 0.5)))),
                            })
                    return valid
            except (ValueError, KeyError):
                pass

        # Fallback: 키워드 매칭
        return self._keyword_allergen_extract(title, description)

    def _keyword_allergen_extract(self, title: str, description: str) -> list[dict]:
        """키워드 기반 알러젠 추출 (fallback)"""
        text = f"{title} {description or ''}".lower()
        allergen_kr = {
            "peanut": ["땅콩", "peanut"], "milk": ["우유", "유제품", "milk", "dairy"],
            "egg": ["계란", "달걀", "egg"], "wheat": ["밀", "글루텐", "wheat", "gluten"],
            "soy": ["대두", "콩", "soy"], "shrimp": ["새우", "shrimp"],
            "crab": ["게", "crab"], "fish": ["생선", "어류", "fish"],
            "peach": ["복숭아", "peach"], "walnut": ["호두", "walnut"],
            "dust_mite": ["집먼지진드기", "dust mite"], "dog": ["개", "반려견", "dog"],
            "cat": ["고양이", "cat"], "mold": ["곰팡이", "mold"],
            "cedar": ["삼나무", "cedar"], "birch": ["자작나무", "birch"],
            "ragweed": ["돼지풀", "ragweed"],
        }
        found = []
        for code, keywords in allergen_kr.items():
            for kw in keywords:
                if kw in text:
                    found.append({"allergen": code, "category": "research", "relevance": 0.5})
                    break
        return found

    def generate_insight_report(self, allergen_code: str, sources: list[dict]) -> dict | None:
        """알러젠별 인사이트 리포트 생성

        Args:
            allergen_code: 알러젠 코드
            sources: [{"type": "paper"|"news", "title": str, "abstract": str}]

        Returns:
            {"title": str, "content": str, "key_findings": list, "treatment_score": int}
        """
        if not sources:
            return None

        # 소스 텍스트 구성 (최대 15개)
        source_texts = []
        for i, s in enumerate(sources[:15], 1):
            src_type = "논문" if s["type"] == "paper" else "뉴스"
            abstract = (s.get("abstract") or "")[:300]
            source_texts.append(f"{i}. [{src_type}] {s['title']}\n   {abstract}")

        sources_block = "\n".join(source_texts)

        prompt = (
            f"당신은 알러지 전문 분석가입니다. 아래는 '{allergen_code}' 알러젠 관련 최근 논문/뉴스입니다.\n"
            f"이 자료들을 종합 분석하여 다음 형식으로 보고서를 작성하세요.\n\n"
            f"=== 자료 ===\n{sources_block}\n\n"
            "=== 보고서 형식 ===\n"
            "1. 제목: 한 줄로 작성\n"
            "2. 본문: 마크다운 형식으로 아래 3개 섹션을 포함\n"
            "   ## 최근 연구 동향\n"
            "   ## 치료법 발전 현황\n"
            "   ## 주목할 발견\n"
            "3. 핵심 발견: 3-5개 항목을 | 로 구분\n"
            "4. 치료 발전도: 0-100 사이 숫자 (최근 자료 기준 치료 관련 진전 정도)\n\n"
            "응답 형식:\n"
            "TITLE: (제목)\n"
            "CONTENT:\n(마크다운 본문)\n"
            "FINDINGS: (발견1|발견2|발견3)\n"
            "SCORE: (숫자)"
        )

        result = self._chat_long(prompt)
        if not result:
            return None

        return self._parse_insight_response(result, allergen_code)

    def _parse_insight_response(self, response: str, allergen_code: str) -> dict:
        """인사이트 리포트 응답 파싱"""
        title = f"{allergen_code} 알러젠 월간 분석 리포트"
        content = response
        key_findings = []
        treatment_score = 50

        lines = response.split("\n")
        content_start = -1
        findings_line = ""

        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith("TITLE:"):
                title = stripped.replace("TITLE:", "").strip()
            elif stripped == "CONTENT:":
                content_start = i + 1
            elif stripped.startswith("FINDINGS:"):
                findings_line = stripped.replace("FINDINGS:", "").strip()
                if content_start >= 0:
                    content = "\n".join(lines[content_start:i]).strip()
            elif stripped.startswith("SCORE:"):
                try:
                    score_text = stripped.replace("SCORE:", "").strip()
                    treatment_score = int(float(score_text.split()[0]))
                    treatment_score = max(0, min(100, treatment_score))
                except (ValueError, IndexError):
                    pass

        if findings_line:
            key_findings = [f.strip() for f in findings_line.split("|") if f.strip()]

        if content_start >= 0 and not key_findings:
            # FINDINGS 라인을 찾지 못한 경우 content는 CONTENT: 이후 전체
            content = "\n".join(lines[content_start:]).strip()

        return {
            "title": title,
            "content": content,
            "key_findings": key_findings[:5],
            "treatment_score": treatment_score,
        }

    def _keyword_importance(self, title: str, description: str) -> float:
        """키워드 기반 중요도 (fallback)"""
        text = f"{title} {description or ''}".lower()
        high_keywords = ["허가", "승인", "fda", "인수", "합병", "투자", "신제품", "출시", "규제"]
        mid_keywords = ["시장", "매출", "기술", "개발", "연구", "특허", "계약"]

        score = 0.3
        for kw in high_keywords:
            if kw in text:
                score += 0.1
        for kw in mid_keywords:
            if kw in text:
                score += 0.05

        return min(1.0, score)

    def close(self):
        """리소스 정리"""
        if self._client:
            self._client.close()
            self._client = None


# 싱글톤
_ollama_service: Optional[OllamaService] = None


def get_ollama_service() -> OllamaService:
    """OllamaService 싱글톤"""
    global _ollama_service
    if _ollama_service is None:
        _ollama_service = OllamaService()
    return _ollama_service


def check_ollama_available() -> bool:
    """LLM 서버 접속 가능 여부 확인 (스케줄러에서 사용)"""
    return get_ollama_service().is_available


def ollama_translate(text: str) -> Optional[str]:
    """영문 텍스트를 한국어로 번역 (스케줄러 korean_translation Job에서 사용)

    Args:
        text: 번역할 영문 텍스트

    Returns:
        한국어 번역문 또는 None (실패 시)
    """
    service = get_ollama_service()
    if not service.is_available:
        return None

    prompt = (
        "Translate the following English text into natural Korean. "
        "Output ONLY the translation, nothing else.\n\n"
        f"{text}\n\n"
        "한국어 번역:"
    )
    return service._chat(prompt)
