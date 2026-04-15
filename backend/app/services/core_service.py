"""CORE API v3 연동 서비스

Open University(영국) 운영, 오픈액세스 논문 전문(Full-text) 제공.
2억+ 논문, API 키 필요 (무료 발급: https://core.ac.uk/services/api).
API 키 미설정 시 서비스 자동 비활성화.

API 문서: https://api.core.ac.uk/docs/v3
"""
import logging
import os
import time
from typing import Optional

import httpx

from ..models.paper import Paper, PaperSearchResult, PaperSource

logger = logging.getLogger(__name__)


class CoreService:
    """CORE API v3 클라이언트"""

    BASE_URL = "https://api.core.ac.uk/v3"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("CORE_API_KEY")
        self._client: Optional[httpx.Client] = None
        self._last_request_time = 0.0

    @property
    def is_available(self) -> bool:
        """API 키가 설정되어 있으면 사용 가능"""
        return bool(self.api_key)

    def _get_client(self) -> Optional[httpx.Client]:
        if not self.is_available:
            return None
        if self._client is None:
            self._client = httpx.Client(
                timeout=30.0,
                headers={"Authorization": f"Bearer {self.api_key}"},
            )
        return self._client

    def _wait_for_rate_limit(self):
        """Rate limit 준수 (초당 10회 → 0.12초 간격)"""
        elapsed = time.time() - self._last_request_time
        if elapsed < 0.12:
            time.sleep(0.12 - elapsed)
        self._last_request_time = time.time()

    def search(
        self,
        query: str,
        max_results: int = 20,
    ) -> PaperSearchResult:
        """논문 검색

        Args:
            query: 검색 쿼리
            max_results: 최대 결과 수

        Returns:
            PaperSearchResult
        """
        start_time = time.time()
        client = self._get_client()

        papers = []
        if not client:
            return PaperSearchResult(
                papers=[], total_count=0, query=query,
                source=PaperSource.MANUAL_UPLOAD, search_time_ms=0,
            )

        try:
            self._wait_for_rate_limit()
            resp = client.post(
                f"{self.BASE_URL}/search/works",
                json={
                    "q": query,
                    "limit": min(max_results, 100),
                    "scroll": False,
                },
            )
            resp.raise_for_status()
            data = resp.json()

            for item in data.get("results", []):
                paper = self._parse_result(item)
                if paper:
                    papers.append(paper)

        except Exception as e:
            logger.error(f"CORE 검색 실패: {e}")

        elapsed = (time.time() - start_time) * 1000

        return PaperSearchResult(
            papers=papers,
            total_count=data.get("totalHits", len(papers)) if papers else 0,
            query=query,
            source=PaperSource.MANUAL_UPLOAD,  # CORE 전용 enum 없음, 임시
            search_time_ms=round(elapsed, 1),
        )

    def search_allergy(
        self,
        allergen: str,
        max_results: int = 20,
    ) -> PaperSearchResult:
        """알러지 관련 논문 검색"""
        query = f'("{allergen} allergy" OR "{allergen} hypersensitivity")'
        return self.search(query, max_results=max_results)

    def get_fulltext(self, core_id: str) -> Optional[str]:
        """전문(Full-text) 조회

        Args:
            core_id: CORE 문서 ID

        Returns:
            전문 텍스트 또는 None
        """
        client = self._get_client()
        if not client:
            return None

        try:
            self._wait_for_rate_limit()
            resp = client.get(f"{self.BASE_URL}/works/{core_id}")
            resp.raise_for_status()
            data = resp.json()
            return data.get("fullText")
        except Exception as e:
            logger.warning(f"CORE 전문 조회 실패 ({core_id}): {e}")
            return None

    def _parse_result(self, item: dict) -> Optional[Paper]:
        """API 결과를 Paper 모델로 변환"""
        title = item.get("title", "")
        if not title:
            return None

        # 저자 파싱
        authors = []
        for author in (item.get("authors") or [])[:10]:
            name = author.get("name", "")
            if name:
                authors.append(name)

        # DOI (최상위 필드 우선)
        doi = item.get("doi")

        # 연도
        year = item.get("yearPublished")

        # PDF URL
        pdf_url = None
        download_url = item.get("downloadUrl")
        if download_url:
            pdf_url = download_url

        # 소스 ID
        core_id = str(item.get("id", ""))

        return Paper(
            title=title,
            abstract=item.get("abstract", "") or "",
            authors=authors,
            source=PaperSource.MANUAL_UPLOAD,  # 임시
            source_id=f"core:{core_id}",
            doi=doi,
            year=year,
            journal=item.get("publisher"),
            citation_count=item.get("citationCount"),
            pdf_url=pdf_url,
            keywords=[],
        )

    def close(self):
        """리소스 정리"""
        if self._client:
            self._client.close()
            self._client = None
