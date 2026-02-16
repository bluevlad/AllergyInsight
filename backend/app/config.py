"""AllergyInsight 설정

환경 변수 또는 .env 파일에서 설정을 로드합니다.
"""
import os
from typing import Optional
from dataclasses import dataclass

# .env 파일 지원 (선택사항)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


@dataclass
class Settings:
    """애플리케이션 설정"""

    # PubMed API
    # API 키가 있으면 요청 제한이 완화됩니다 (초당 10회 -> 초당 10회 이상)
    # https://www.ncbi.nlm.nih.gov/account/settings/ 에서 발급
    PUBMED_API_KEY: Optional[str] = None
    PUBMED_EMAIL: Optional[str] = None  # NCBI 권장사항

    # Semantic Scholar API
    # https://www.semanticscholar.org/product/api 에서 발급
    SEMANTIC_SCHOLAR_API_KEY: Optional[str] = None

    # OpenAI (향후 요약 기능용)
    OPENAI_API_KEY: Optional[str] = None

    # 다운로드 설정
    DOWNLOAD_DIR: str = "./downloads/papers"

    # 검색 설정
    DEFAULT_MAX_RESULTS: int = 20
    SEARCH_TIMEOUT: int = 30  # 초

    # 검색 결과 자동 저장
    AUTO_SAVE_SEARCH: bool = True

    @classmethod
    def from_env(cls) -> "Settings":
        """환경 변수에서 설정 로드"""
        return cls(
            PUBMED_API_KEY=os.getenv("PUBMED_API_KEY"),
            PUBMED_EMAIL=os.getenv("PUBMED_EMAIL"),
            SEMANTIC_SCHOLAR_API_KEY=os.getenv("SEMANTIC_SCHOLAR_API_KEY"),
            OPENAI_API_KEY=os.getenv("OPENAI_API_KEY"),
            DOWNLOAD_DIR=os.getenv("DOWNLOAD_DIR", "./downloads/papers"),
            DEFAULT_MAX_RESULTS=int(os.getenv("DEFAULT_MAX_RESULTS", "20")),
            SEARCH_TIMEOUT=int(os.getenv("SEARCH_TIMEOUT", "30")),
            AUTO_SAVE_SEARCH=os.getenv("AUTO_SAVE_SEARCH", "true").lower() == "true",
        )


# 전역 설정 인스턴스
settings = Settings.from_env()
