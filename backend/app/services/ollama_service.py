"""LLM AI 서비스

Gemini(클라우드) 또는 로컬 LLM(MLX/Ollama)을 용도별로 분리 운영합니다.
- 뉴스 분석, RAG 답변: Gemini 2.5 Flash (고품질, 무료)
- 한국어 번역, 알러젠 추출: 로컬 LLM (대량 처리)

환경 변수:
    GEMINI_API_KEY: Google Gemini API 키
    NEWS_LLM_PROVIDER: 뉴스 분석용 LLM (gemini|local, 기본: gemini)
    RAG_LLM_PROVIDER: RAG 답변용 LLM (gemini|local, 기본: gemini)
    LLM_API_URL: 로컬 LLM OpenAI 호환 API base URL
    LLM_MODEL: 로컬 LLM 모델명
    OLLAMA_HOST: (하위 호환) Ollama 호스트 URL
    OLLAMA_MODEL: (하위 호환) Ollama 모델명
"""
import os
import logging
import time
from typing import Optional

import httpx

from ..models.news_category import NewsCategoryType, classify_by_keywords

logger = logging.getLogger(__name__)

# Gemini 설정
_GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/openai"
_GEMINI_MODEL = "gemini-2.5-flash"

# 로컬 LLM 기본값
_DEFAULT_LOCAL_URL = "http://localhost:11435/v1"
_DEFAULT_LOCAL_MODEL = "mlx-community/EXAONE-3.5-7.8B-Instruct-4bit"


def _resolve_local_config() -> tuple[str, str]:
    """로컬 LLM API URL과 모델을 환경 변수에서 결정

    우선순위:
    1. LLM_API_URL / LLM_MODEL (명시적 설정)
    2. OLLAMA_HOST / OLLAMA_MODEL (하위 호환)
    3. 기본값 (MLX 서버)
    """
    llm_url = os.getenv("LLM_API_URL")
    llm_model = os.getenv("LLM_MODEL")

    if llm_url:
        return llm_url, llm_model or _DEFAULT_LOCAL_MODEL

    ollama_host = os.getenv("OLLAMA_HOST")
    ollama_model = os.getenv("OLLAMA_MODEL")

    if ollama_host:
        base = ollama_host.rstrip("/")
        return f"{base}/v1", ollama_model or "qwen2.5:latest"

    return _DEFAULT_LOCAL_URL, llm_model or _DEFAULT_LOCAL_MODEL


def _resolve_gemini_config() -> tuple[Optional[str], str, str]:
    """Gemini API 설정 반환: (api_key, url, model).

    Model 우선순위: GEMINI_MODEL env var → _GEMINI_MODEL 상수.
    무료 티어 운영 시 `GEMINI_MODEL=gemini-2.5-flash-lite` 권장
    (RPD 1,000 / RPM 15) — 한국어 1~2문장 요약에는 품질 차이 미미.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    model = os.getenv("GEMINI_MODEL") or _GEMINI_MODEL
    return api_key, _GEMINI_API_URL, model


class OllamaService:
    """LLM AI 분석 서비스 (Gemini + 로컬 LLM 이중화)"""

    def __init__(
        self,
        api_url: Optional[str] = None,
        model: Optional[str] = None,
    ):
        # 로컬 LLM 설정
        resolved_url, resolved_model = _resolve_local_config()
        self.api_url = api_url or resolved_url
        self.model = model or resolved_model
        self._available: Optional[bool] = None
        self._client: Optional[httpx.Client] = None

        # Gemini 설정
        gemini_key, gemini_url, gemini_model = _resolve_gemini_config()
        self._gemini_api_key = gemini_key
        self._gemini_url = gemini_url
        self._gemini_model = gemini_model
        self._gemini_available: Optional[bool] = None
        self._gemini_client: Optional[httpx.Client] = None

        # 용도별 프로바이더 설정
        self._news_provider = os.getenv("NEWS_LLM_PROVIDER", "gemini")
        self._rag_provider = os.getenv("RAG_LLM_PROVIDER", "gemini")

    def _get_client(self) -> httpx.Client:
        """로컬 LLM httpx 클라이언트 (lazy 초기화)"""
        if self._client is None:
            self._client = httpx.Client(timeout=120.0)
        return self._client

    def _get_gemini_client(self) -> httpx.Client:
        """Gemini httpx 클라이언트 (lazy 초기화)"""
        if self._gemini_client is None:
            self._gemini_client = httpx.Client(
                timeout=60.0,
                headers={"Authorization": f"Bearer {self._gemini_api_key}"},
            )
        return self._gemini_client

    @property
    def is_available(self) -> bool:
        """로컬 LLM 서버 사용 가능 여부"""
        if self._available is None:
            try:
                client = self._get_client()
                resp = client.get(f"{self.api_url}/models", timeout=5.0)
                self._available = resp.status_code == 200
            except Exception as e:
                logger.warning(f"로컬 LLM 연결 실패 ({self.api_url}): {e}. Fallback 모드로 동작합니다.")
                self._available = False
        return self._available

    @property
    def is_gemini_available(self) -> bool:
        """Gemini API 사용 가능 여부"""
        if self._gemini_available is None:
            if not self._gemini_api_key:
                logger.info("GEMINI_API_KEY 미설정. Gemini 비활성화.")
                self._gemini_available = False
            else:
                try:
                    client = self._get_gemini_client()
                    resp = client.get(f"{self._gemini_url}/models", timeout=10.0)
                    self._gemini_available = resp.status_code == 200
                except Exception as e:
                    logger.warning(f"Gemini API 연결 실패: {e}")
                    self._gemini_available = False
        return self._gemini_available

    # 알러지/면역학 도메인 시스템 프롬프트 (Phase 1.G-008 폴백)
    # 1차: DomainPack 의 prompts.system 슬롯 (domains/allergy/prompts/system.md).
    # 2차: 아래 _SYSTEM_PROMPT_FALLBACK 상수 (pack 미로딩 시).
    # Phase 1.F 에서 폴백 제거 예정.
    _SYSTEM_PROMPT_FALLBACK = (
        "당신은 알러지 및 면역학 전문 의학 AI 어시스턴트입니다. "
        "반드시 한국어로만 답변하세요. 영어 논문을 참고하더라도 답변은 한국어로 작성하세요. "
        "의학 용어는 한국어 표기를 우선하되, 필요시 영문 약어를 괄호에 병기하세요. "
        "예: 경구 면역치료(OIT), 아나필락시스(Anaphylaxis). "
        "근거 없는 추측은 하지 마세요."
    )

    @classmethod
    def _resolve_prompt(cls, slot: str, fallback: str) -> str:
        """DomainPack 의 prompts.{slot} → 본문 반환. 미로딩 시 fallback."""
        try:
            from ..core.domains import get_pack
            pack = get_pack("allergy")
            if pack is not None:
                body = pack.get_prompt(slot)
                if body:
                    return body.strip()
        except Exception:
            pass
        return fallback

    @property
    def SYSTEM_PROMPT(self) -> str:  # type: ignore[override]
        """SYSTEM_PROMPT 를 동적으로 해석 — DomainPack 우선, fallback 보존."""
        return self._resolve_prompt("system", self._SYSTEM_PROMPT_FALLBACK)

    def _chat_gemini(self, prompt: str, max_tokens: int = 500) -> Optional[str]:
        """Gemini API 호출 (OpenAI 호환)"""
        if not self.is_gemini_available:
            return None

        client = self._get_gemini_client()
        payload = {
            "model": self._gemini_model,
            "messages": [
                {"role": "system", "content": self.SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.3,
            "max_tokens": max_tokens,
        }

        try:
            resp = client.post(
                f"{self._gemini_url}/chat/completions",
                json=payload,
                timeout=60.0,
            )
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"].strip()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                logger.warning("Gemini Rate Limit 초과. 5초 대기 후 재시도합니다.")
                time.sleep(5)
                try:
                    resp = client.post(
                        f"{self._gemini_url}/chat/completions",
                        json=payload,
                        timeout=60.0,
                    )
                    resp.raise_for_status()
                    data = resp.json()
                    return data["choices"][0]["message"]["content"].strip()
                except Exception as retry_err:
                    logger.warning(f"Gemini 재시도 실패: {retry_err}")
            else:
                logger.warning(f"Gemini API 오류: {e}")
        except Exception as e:
            logger.warning(f"Gemini 호출 실패: {e}")
            self._gemini_available = False

        return None

    def _chat_local(self, prompt: str, max_tokens: int = 500, max_retries: int = 2) -> Optional[str]:
        """로컬 LLM chat/completions 호출"""
        if not self.is_available:
            return None

        client = self._get_client()
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": self.SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
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
                logger.warning(f"로컬 LLM 호출 실패 (시도 {attempt + 1}): {e}")
                if attempt == max_retries - 1:
                    self._available = False

        return None

    def _chat(self, prompt: str, max_tokens: int = 500, max_retries: int = 2, provider: str = "news") -> Optional[str]:
        """용도별 LLM 호출 (Gemini 우선 → 로컬 Fallback)

        Args:
            prompt: 프롬프트
            max_tokens: 최대 토큰 수
            max_retries: 로컬 LLM 재시도 횟수
            provider: 용도 ("news" | "rag" | "local")
        """
        # 프로바이더 결정
        use_gemini = False
        if provider == "news":
            use_gemini = self._news_provider == "gemini"
        elif provider == "rag":
            use_gemini = self._rag_provider == "gemini"
        # provider == "local"이면 항상 로컬 사용

        if use_gemini:
            result = self._chat_gemini(prompt, max_tokens)
            if result:
                return result
            logger.info("Gemini 응답 실패. 로컬 LLM으로 Fallback합니다.")

        return self._chat_local(prompt, max_tokens, max_retries)

    def _chat_long(self, prompt: str, provider: str = "news") -> Optional[str]:
        """긴 응답용 호출 (max_tokens 확장)"""
        return self._chat(prompt, max_tokens=2000, provider=provider)

    _NEWS_RELEVANCE_PROMPT_FALLBACK = (
        "다음 뉴스 기사가 알러지, 체외진단(IVD), 면역학, 진단키트, "
        "알러젠, 또는 관련 의료기기 산업과 관련이 있는지 판단하세요.\n"
        "0.0~1.0 사이 숫자로만 답하세요.\n"
        "- 1.0: 직접적으로 관련됨 (알러지 진단, IVD 제품, 면역치료 등)\n"
        "- 0.5: 간접적으로 관련됨 (의료기기 일반, 체외진단 기업의 사업 뉴스)\n"
        "- 0.0: 전혀 관련 없음 (주식 투자분석, 일반 경제뉴스 등)\n\n"
        "제목: {title}\n"
        "내용: {description}\n\n"
        "관련성 점수(숫자만):"
    )

    def check_relevance(self, title: str, description: str) -> float:
        """알러지/체외진단/IVD 산업 관련성 점수 (0.0~1.0)

        Returns:
            관련성 점수. 0.3 미만이면 무관 기사로 판정.
        """
        template = self._resolve_prompt(
            "news_relevance", self._NEWS_RELEVANCE_PROMPT_FALLBACK
        )
        prompt = template.format(
            title=title,
            description=description or "(내용 없음)",
        )

        result = self._chat(prompt, max_tokens=50, provider="news")
        if result:
            try:
                score = float(result.split()[0].strip(".,"))
                return max(0.0, min(1.0, score))
            except (ValueError, IndexError):
                pass

        # Fallback: 키워드 기반 관련성 판정
        return self._keyword_relevance(title, description)

    def _keyword_relevance(self, title: str, description: str) -> float:
        """키워드 기반 관련성 판정 (fallback)"""
        text = f"{title} {description or ''}".lower()
        relevant_keywords = [
            "알러지", "알러젠", "allergy", "allergen", "체외진단", "ivd",
            "면역", "immuno", "진단키트", "아나필락시스", "anaphylaxis",
            "항체", "ige", "항원", "피부반응", "두드러기", "천식",
            "비염", "아토피", "식품알레르기", "약물알레르기",
        ]
        matches = sum(1 for kw in relevant_keywords if kw in text)
        if matches >= 3:
            return 0.9
        elif matches >= 2:
            return 0.7
        elif matches >= 1:
            return 0.5
        return 0.1

    def summarize(self, title: str, description: str) -> str:
        """기사 요약 생성"""
        prompt = (
            "다음 뉴스 기사를 한국어로 2-3문장으로 요약하세요. "
            "핵심 내용만 간결하게 작성하세요.\n\n"
            f"제목: {title}\n"
            f"내용: {description or '(내용 없음)'}\n\n"
            "요약:"
        )

        result = self._chat(prompt, provider="news")
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

        result = self._chat(prompt, provider="news")
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

        result = self._chat(prompt, provider="news")
        if result:
            result_lower = result.lower().strip()
            for cat in NewsCategoryType:
                if cat.value in result_lower:
                    return cat.value

        # Fallback: 키워드 분류
        text = f"{title} {description or ''}"
        return classify_by_keywords(text).value

    def analyze_article(self, title: str, description: str) -> dict:
        """기사 종합 분석 — 1회 통합 호출 (API 사용량 절약)

        Gemini 무료 티어 RPD 한도(250/일)를 고려하여,
        관련성/요약/중요도/카테고리를 단일 프롬프트로 한 번에 분석합니다.
        통합 호출 실패 시 개별 메서드 Fallback으로 전환합니다.
        """
        categories = ", ".join([c.value for c in NewsCategoryType])
        prompt = (
            "다음 뉴스 기사를 분석하여 아래 4개 항목을 정확히 답하세요.\n"
            "각 항목을 한 줄씩, 라벨과 값만 출력하세요. 다른 설명은 불필요합니다.\n\n"
            f"제목: {title}\n"
            f"내용: {description or '(내용 없음)'}\n\n"
            "=== 분석 항목 ===\n"
            "1. RELEVANCE: 알러지/체외진단(IVD)/면역학/진단키트 산업과의 관련성 (0.0~1.0 숫자)\n"
            "   - 1.0: 직접 관련 (알러지 진단, IVD 제품, 면역치료)\n"
            "   - 0.5: 간접 관련 (체외진단 기업의 일반 사업 뉴스)\n"
            "   - 0.0: 무관 (주식 투자분석, 일반 경제뉴스)\n"
            "2. SUMMARY: 한국어 2-3문장 요약 (핵심 내용만 간결하게)\n"
            "3. IMPORTANCE: 체외진단/알러지 산업 중요도 (0.0~1.0 숫자)\n"
            "   - 규제 변화, 신제품, M&A, 큰 투자 → 높은 점수\n"
            "   - 일반 홍보/이벤트 → 낮은 점수\n"
            f"4. CATEGORY: 다음 중 하나 → {categories}\n\n"
            "=== 응답 형식 (이 형식 그대로 출력) ===\n"
            "RELEVANCE: (숫자)\n"
            "SUMMARY: (요약문)\n"
            "IMPORTANCE: (숫자)\n"
            "CATEGORY: (카테고리명)"
        )

        result = self._chat(prompt, max_tokens=500, provider="news")
        if result:
            parsed = self._parse_analysis_response(result)
            if parsed:
                return parsed

        # 통합 호출 실패 시: 개별 Fallback (로컬 LLM + 키워드)
        logger.info("통합 분석 실패. 개별 Fallback으로 전환합니다.")
        return {
            "relevance_score": self._keyword_relevance(title, description),
            "summary": (description[:200].strip() if description else title),
            "importance_score": self._keyword_importance(title, description),
            "category": classify_by_keywords(f"{title} {description or ''}").value,
        }

    def _parse_analysis_response(self, response: str) -> Optional[dict]:
        """통합 분석 응답 파싱

        예상 형식:
            RELEVANCE: 0.8
            SUMMARY: 요약 내용...
            IMPORTANCE: 0.6
            CATEGORY: market
        """
        import re

        result = {}
        lines = response.strip().split("\n")

        for line in lines:
            stripped = line.strip()

            # RELEVANCE
            if stripped.upper().startswith("RELEVANCE:"):
                val = stripped.split(":", 1)[1].strip()
                try:
                    result["relevance_score"] = max(0.0, min(1.0, float(val.split()[0].strip(".,)"))))
                except (ValueError, IndexError):
                    pass

            # SUMMARY
            elif stripped.upper().startswith("SUMMARY:"):
                result["summary"] = stripped.split(":", 1)[1].strip()

            # IMPORTANCE
            elif stripped.upper().startswith("IMPORTANCE:"):
                val = stripped.split(":", 1)[1].strip()
                try:
                    result["importance_score"] = max(0.0, min(1.0, float(val.split()[0].strip(".,)"))))
                except (ValueError, IndexError):
                    pass

            # CATEGORY
            elif stripped.upper().startswith("CATEGORY:"):
                cat_val = stripped.split(":", 1)[1].strip().lower()
                for cat in NewsCategoryType:
                    if cat.value in cat_val:
                        result["category"] = cat.value
                        break

        # 필수 필드 검증
        if "relevance_score" in result and "summary" in result:
            result.setdefault("importance_score", 0.3)
            result.setdefault("category", "general")
            return result

        return None

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

        result = self._chat(prompt, provider="local")
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

    # --- 치료법 엔티티 추출 ---

    TREATMENT_TYPES = ["drug", "immunotherapy", "avoidance", "biologic", "dietary"]

    def extract_treatments(self, title: str, abstract: str, allergen_code: str = "") -> list[dict]:
        """논문 abstract에서 치료법 엔티티를 추출

        Args:
            title: 논문 제목
            abstract: 논문 초록
            allergen_code: 관련 알러젠 코드 (힌트)

        Returns:
            [{"name": "omalizumab", "name_kr": "오말리주맙", "type": "biologic",
              "allergen": "peanut", "evidence_level": "B", "confidence": 0.85,
              "source_text": "...근거 문장..."}]
        """
        if not abstract:
            return []

        type_list = ", ".join(self.TREATMENT_TYPES)
        prompt = (
            "다음 논문 초록에서 알러지 치료법/치료제를 JSON 배열로 추출하세요.\n"
            "치료법 유형: " + type_list + "\n"
            "- drug: 약물 (항히스타민제, 에피네프린, 코르티코스테로이드 등)\n"
            "- immunotherapy: 면역요법 (경구, 피하, 설하 면역요법)\n"
            "- avoidance: 회피요법 (알러젠 회피, 식이 제한)\n"
            "- biologic: 생물학적 제제 (오말리주맙, 두필루맙 등)\n"
            "- dietary: 식이 요법 (대체 식품, 영양 관리)\n\n"
            f"알러젠 힌트: {allergen_code or '(미지정)'}\n"
            f"제목: {title}\n"
            f"초록: {abstract[:1500]}\n\n"
            "치료법이 없으면 빈 배열 []을 반환하세요.\n"
            '응답 형식(JSON만): [{"name": "영문 치료법명", "name_kr": "한국어명", '
            '"type": "drug|immunotherapy|avoidance|biologic|dietary", '
            '"allergen": "관련 알러젠 코드", "evidence_level": "A|B|C|D|null", '
            '"confidence": 0.0~1.0, "source_text": "근거가 된 초록 문장"}]'
        )

        result = self._chat(prompt, provider="local")
        if result:
            try:
                import json
                start = result.find("[")
                end = result.rfind("]") + 1
                if start >= 0 and end > start:
                    items = json.loads(result[start:end])
                    valid = []
                    for item in items:
                        name = item.get("name", "").strip()
                        if not name:
                            continue
                        t_type = item.get("type", "drug")
                        if t_type not in self.TREATMENT_TYPES:
                            t_type = "drug"
                        valid.append({
                            "name": name,
                            "name_kr": item.get("name_kr", ""),
                            "type": t_type,
                            "allergen": item.get("allergen", allergen_code or ""),
                            "evidence_level": item.get("evidence_level"),
                            "confidence": max(0.0, min(1.0, float(item.get("confidence", 0.5)))),
                            "source_text": (item.get("source_text", "") or "")[:500],
                        })
                    return valid
            except (ValueError, KeyError, TypeError):
                pass

        # Fallback: 키워드 매칭
        return self._keyword_treatment_extract(title, abstract, allergen_code)

    def _keyword_treatment_extract(self, title: str, abstract: str, allergen_code: str) -> list[dict]:
        """키워드 기반 치료법 추출 (LLM fallback)"""
        text = f"{title} {abstract or ''}".lower()
        treatments = {
            "epinephrine": ("drug", "에피네프린"),
            "antihistamine": ("drug", "항히스타민제"),
            "corticosteroid": ("drug", "코르티코스테로이드"),
            "omalizumab": ("biologic", "오말리주맙"),
            "dupilumab": ("biologic", "두필루맙"),
            "oral immunotherapy": ("immunotherapy", "경구 면역요법"),
            "sublingual immunotherapy": ("immunotherapy", "설하 면역요법"),
            "subcutaneous immunotherapy": ("immunotherapy", "피하 면역요법"),
            "allergen avoidance": ("avoidance", "알러젠 회피"),
            "elimination diet": ("dietary", "제거식이"),
        }
        found = []
        for name, (t_type, name_kr) in treatments.items():
            if name in text:
                found.append({
                    "name": name,
                    "name_kr": name_kr,
                    "type": t_type,
                    "allergen": allergen_code,
                    "evidence_level": None,
                    "confidence": 0.4,
                    "source_text": "",
                })
        return found

    # --- 임상 함의 (clinical_implication) 추출 — B2a ---

    # 너무 짧은 abstract 는 추출 가치 없음 (제목만 있는 인덱스 항목 등)
    _CLINICAL_IMPLICATION_MIN_ABSTRACT_LEN = 200
    # 의료진에게 노출되는 한 줄 카드용 — 너무 길면 잘림
    _CLINICAL_IMPLICATION_MAX_OUTPUT_CHARS = 240

    # Phase 1.G-008 폴백 — DomainPack 미로딩 시 사용 (Phase 1.F 에서 제거)
    _CLINICAL_IMPLICATION_PROMPT_FALLBACK = (
        "당신은 알레르기·면역학 임상 전문가입니다. "
        "다음 논문 초록을 읽고, 의료진(알러지내과·소아과·이비인후과)에게 "
        "전달할 \"한 줄 임상 함의\"를 한국어로 1~2문장(최대 200자)으로 작성하세요.\n\n"
        "지침:\n"
        "- 초록에 명시된 사실만 사용. 추정/일반화 금지.\n"
        "- 환자에게 직접 전하는 조언 형식 금지 (의료 조언 아님).\n"
        "- 통계 수치가 있으면 1개까지 인용 가능 (% 포함).\n"
        "- 마크다운/번호/머리말 금지. 평문 한국어.\n\n"
        "제목: {title}\n"
        "초록: {abstract}\n\n"
        "임상 함의 (1~2문장):"
    )

    def extract_clinical_implication(
        self, title: str, abstract: str
    ) -> Optional[str]:
        """논문 abstract → 의료진 대상 한국어 1~2문장 임상 함의 요약.

        뉴스레터 논문 카드 등 외부 소비자에게 "한 줄 요약" 을 제공하기 위함.
        - abstract 가 너무 짧으면 (< 200자) None — 노이즈 차단.
        - LLM 호출 실패 / 빈 응답 → None.
        - 응답에서 따옴표·markdown 제거 후 240자 안에서 잘라 반환.

        주의: 의료 조언 아님. 호출자는 면책을 함께 노출해야 한다.
        """
        if not abstract or len(abstract.strip()) < self._CLINICAL_IMPLICATION_MIN_ABSTRACT_LEN:
            return None

        template = self._resolve_prompt(
            "digest_implication",
            self._CLINICAL_IMPLICATION_PROMPT_FALLBACK,
        )
        prompt = template.format(title=title, abstract=abstract[:3000])

        try:
            raw = self._chat(prompt, max_tokens=200, provider="news")
        except Exception as e:
            logger.warning(f"clinical_implication LLM 호출 실패: {e}")
            return None

        if not raw:
            return None

        # 흔한 잡음 제거: 머리말, 따옴표, markdown, 줄바꿈
        text = raw.strip()
        for noise in ("임상 함의:", "임상함의:", "임상 함의 (1~2문장):", "**", "__"):
            text = text.replace(noise, "")
        text = text.strip().strip('"').strip("'").strip()
        text = " ".join(text.split())  # 다중 공백/개행 → 단일 공백

        if not text:
            return None
        if len(text) > self._CLINICAL_IMPLICATION_MAX_OUTPUT_CHARS:
            text = text[: self._CLINICAL_IMPLICATION_MAX_OUTPUT_CHARS].rstrip() + "…"
        return text

    # --- 역학 데이터 추출 ---

    EPIDEMIOLOGY_TYPES = ["prevalence", "incidence", "patient_count", "sensitization_rate"]

    def extract_epidemiology(self, title: str, abstract: str, allergen_code: str = "") -> list[dict]:
        """논문 abstract에서 역학 수치(유병률, 발병률, 환자 수 등)를 추출

        Returns:
            [{"data_type": "prevalence", "value": 8.5, "unit": "%",
              "region": "USA", "sample_size": 5000, "age_group": "children",
              "confidence": 0.85, "source_text": "...근거..."}]
        """
        if not abstract:
            return []

        type_list = ", ".join(self.EPIDEMIOLOGY_TYPES)
        prompt = (
            "다음 논문 초록에서 알러지 관련 역학 수치를 JSON 배열로 추출하세요.\n"
            f"데이터 유형: {type_list}\n"
            "- prevalence: 유병률 (%)\n"
            "- incidence: 발병률 (% 또는 per 100,000)\n"
            "- patient_count: 환자 수 (명)\n"
            "- sensitization_rate: 감작률 (%)\n\n"
            f"알러젠 힌트: {allergen_code or '(미지정)'}\n"
            f"제목: {title}\n"
            f"초록: {abstract[:1500]}\n\n"
            "역학 수치가 없으면 빈 배열 []을 반환하세요.\n"
            "수치가 명확하지 않거나 추정치인 경우 confidence를 낮게 설정하세요.\n"
            '응답 형식(JSON만): [{"data_type": "prevalence|incidence|patient_count|sensitization_rate", '
            '"value": 숫자, "unit": "%|per_100k|count", '
            '"region": "지역명(영문)", "sample_size": 숫자|null, '
            '"age_group": "children|adults|all|연령범위", '
            '"confidence": 0.0~1.0, "source_text": "근거 문장"}]'
        )

        result = self._chat(prompt, provider="local")
        if result:
            try:
                import json
                start = result.find("[")
                end = result.rfind("]") + 1
                if start >= 0 and end > start:
                    items = json.loads(result[start:end])
                    valid = []
                    for item in items:
                        d_type = item.get("data_type", "")
                        if d_type not in self.EPIDEMIOLOGY_TYPES:
                            continue
                        try:
                            value = float(item.get("value", 0))
                        except (ValueError, TypeError):
                            continue
                        if value <= 0:
                            continue
                        valid.append({
                            "data_type": d_type,
                            "value": value,
                            "unit": item.get("unit", "%"),
                            "region": item.get("region", ""),
                            "sample_size": item.get("sample_size"),
                            "age_group": item.get("age_group", ""),
                            "confidence": max(0.0, min(1.0, float(item.get("confidence", 0.5)))),
                            "source_text": (item.get("source_text", "") or "")[:500],
                        })
                    return valid
            except (ValueError, KeyError, TypeError):
                pass

        return []

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

        result = self._chat_long(prompt, provider="news")
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
        if self._gemini_client:
            self._gemini_client.close()
            self._gemini_client = None


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

    로컬 LLM 우선 사용, 실패 시 Gemini Fallback.

    Args:
        text: 번역할 영문 텍스트

    Returns:
        한국어 번역문 또는 None (실패 시)
    """
    service = get_ollama_service()

    prompt = (
        "Translate the following English text into natural Korean. "
        "Output ONLY the translation, nothing else.\n\n"
        f"{text}\n\n"
        "한국어 번역:"
    )
    return service._chat(prompt, provider="local")
