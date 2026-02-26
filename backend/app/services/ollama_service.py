"""Ollama AI 서비스

로컬 LLM (Ollama)을 사용한 뉴스 요약/분류/중요도 평가.
Ollama 미가용 시 키워드 기반 fallback을 제공합니다.
"""
import os
import logging
from typing import Optional

from ..models.news_category import NewsCategoryType, classify_by_keywords

logger = logging.getLogger(__name__)


class OllamaService:
    """Ollama 기반 AI 분석 서비스"""

    def __init__(
        self,
        host: Optional[str] = None,
        model: Optional[str] = None,
    ):
        self.host = host or os.getenv("OLLAMA_HOST", "http://172.30.1.72:11434")
        self.model = model or os.getenv("OLLAMA_MODEL", "qwen2.5:7b")
        self._client = None
        self._available = None

    def _get_client(self):
        """Ollama 클라이언트 (lazy 초기화)"""
        if self._client is None:
            try:
                import ollama
                self._client = ollama.Client(host=self.host)
                self._available = True
            except ImportError:
                logger.warning("ollama 패키지가 설치되지 않았습니다. Fallback 모드로 동작합니다.")
                self._available = False
            except Exception as e:
                logger.warning(f"Ollama 연결 실패: {e}. Fallback 모드로 동작합니다.")
                self._available = False
        return self._client

    @property
    def is_available(self) -> bool:
        """Ollama 사용 가능 여부"""
        if self._available is None:
            self._get_client()
        return self._available

    def _chat(self, prompt: str, max_retries: int = 2) -> Optional[str]:
        """Ollama 채팅 호출"""
        client = self._get_client()
        if not client or not self._available:
            return None

        for attempt in range(max_retries):
            try:
                response = client.chat(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    options={"temperature": 0.3, "num_predict": 500},
                )
                return response["message"]["content"].strip()
            except Exception as e:
                logger.warning(f"Ollama 호출 실패 (시도 {attempt + 1}): {e}")
                if attempt == 0:
                    self._available = False

        return None

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


# 싱글톤
_ollama_service: Optional[OllamaService] = None


def get_ollama_service() -> OllamaService:
    """OllamaService 싱글톤"""
    global _ollama_service
    if _ollama_service is None:
        _ollama_service = OllamaService()
    return _ollama_service
