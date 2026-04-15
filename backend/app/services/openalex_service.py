"""OpenAlex API 연동 서비스

OurResearch(비영리)에서 운영하는 학술 논문 검색 엔진.
2.5억+ 논문, 완전 무료, API 키 불필요.
Concept 기반 분류 체계와 인용 네트워크 분석 지원.

API 문서: https://docs.openalex.org/
"""
import logging
import time
from typing import Optional
from datetime import datetime

import httpx

from ..models.paper import Paper, PaperSearchResult, PaperSource

logger = logging.getLogger(__name__)


class OpenAlexService:
    """OpenAlex REST API 클라이언트"""

    BASE_URL = "https://api.openalex.org"

    # 알러지 관련 OpenAlex Concept ID
    ALLERGY_CONCEPTS = {
        "allergy": "C71924100",
        "food_allergy": "C2777710206",
        "anaphylaxis": "C2779770265",
        "immunology": "C203014093",
        "hypersensitivity": "C2779134260",
    }

    def __init__(self, email: Optional[str] = None):
        self._client: Optional[httpx.Client] = None
        # polite pool: 이메일 제공 시 rate limit 완화
        self.email = email

    def _get_client(self) -> httpx.Client:
        if self._client is None:
            self._client = httpx.Client(timeout=30.0)
        return self._client

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
        try:
            params = {
                "search": query,
                "per_page": min(max_results, 50),
                "sort": "relevance_score:desc",
                "select": "id,doi,title,authorships,publication_year,"
                          "primary_location,cited_by_count,abstract_inverted_index,"
                          "keywords,open_access,concepts",
            }
            if self.email:
                params["mailto"] = self.email

            resp = client.get(f"{self.BASE_URL}/works", params=params)
            resp.raise_for_status()
            data = resp.json()

            for item in data.get("results", []):
                paper = self._parse_result(item)
                if paper:
                    papers.append(paper)

        except Exception as e:
            logger.error(f"OpenAlex 검색 실패: {e}")

        elapsed = (time.time() - start_time) * 1000

        return PaperSearchResult(
            papers=papers,
            total_count=len(papers),
            query=query,
            source=PaperSource.OPENALEX,
            search_time_ms=round(elapsed, 1),
        )

    def search_allergy(
        self,
        allergen: str,
        max_results: int = 20,
    ) -> PaperSearchResult:
        """알러지 관련 논문 검색

        Args:
            allergen: 알러젠 이름 (예: "peanut")
            max_results: 최대 결과 수
        """
        query = f"{allergen} allergy"
        return self.search(query, max_results=max_results)

    def search_by_concept(
        self,
        concept_id: str,
        max_results: int = 20,
    ) -> PaperSearchResult:
        """OpenAlex Concept ID로 검색

        Args:
            concept_id: OpenAlex Concept ID (예: "C71924100")
            max_results: 최대 결과 수
        """
        start_time = time.time()
        client = self._get_client()

        papers = []
        try:
            params = {
                "filter": f"concepts.id:https://openalex.org/{concept_id}",
                "per_page": min(max_results, 50),
                "sort": "cited_by_count:desc",
                "select": "id,doi,title,authorships,publication_year,"
                          "primary_location,cited_by_count,abstract_inverted_index,"
                          "keywords,open_access,concepts",
            }
            if self.email:
                params["mailto"] = self.email

            resp = client.get(f"{self.BASE_URL}/works", params=params)
            resp.raise_for_status()
            data = resp.json()

            for item in data.get("results", []):
                paper = self._parse_result(item)
                if paper:
                    papers.append(paper)

        except Exception as e:
            logger.error(f"OpenAlex Concept 검색 실패: {e}")

        elapsed = (time.time() - start_time) * 1000

        return PaperSearchResult(
            papers=papers,
            total_count=len(papers),
            query=f"concept:{concept_id}",
            source=PaperSource.OPENALEX,
            search_time_ms=round(elapsed, 1),
        )

    def _parse_result(self, item: dict) -> Optional[Paper]:
        """API 결과를 Paper 모델로 변환"""
        title = item.get("title", "")
        if not title:
            return None

        # 저자 파싱
        authors = []
        for authorship in (item.get("authorships") or [])[:10]:
            author = authorship.get("author", {})
            name = author.get("display_name", "")
            if name:
                authors.append(name)

        # DOI 파싱 (https://doi.org/ 접두사 제거)
        doi = item.get("doi")
        if doi and doi.startswith("https://doi.org/"):
            doi = doi[16:]

        # 초록 복원 (inverted index → plain text)
        abstract = self._reconstruct_abstract(
            item.get("abstract_inverted_index")
        )

        # PDF URL (open access)
        pdf_url = None
        oa = item.get("open_access", {})
        if oa.get("is_oa"):
            pdf_url = oa.get("oa_url")

        # 저널
        journal = None
        primary = item.get("primary_location", {})
        if primary:
            source = primary.get("source", {})
            if source:
                journal = source.get("display_name")

        # 키워드 (concepts에서 추출)
        keywords = []
        for concept in (item.get("concepts") or [])[:8]:
            if concept.get("score", 0) > 0.3:
                keywords.append(concept.get("display_name", ""))

        # OpenAlex ID (W로 시작하는 부분)
        openalex_id = item.get("id", "")
        if "/" in openalex_id:
            openalex_id = openalex_id.split("/")[-1]

        return Paper(
            title=title,
            abstract=abstract or "",
            authors=authors,
            source=PaperSource.OPENALEX,
            source_id=openalex_id,
            doi=doi,
            year=item.get("publication_year"),
            journal=journal,
            citation_count=item.get("cited_by_count"),
            pdf_url=pdf_url,
            keywords=keywords,
        )

    @staticmethod
    def _reconstruct_abstract(inverted_index: Optional[dict]) -> Optional[str]:
        """OpenAlex의 inverted index 형태 초록을 일반 텍스트로 복원

        inverted_index: {"word": [pos1, pos2], ...}
        """
        if not inverted_index:
            return None

        # 위치 → 단어 매핑
        positions = {}
        for word, indices in inverted_index.items():
            for idx in indices:
                positions[idx] = word

        if not positions:
            return None

        # 위치 순서대로 조합
        max_pos = max(positions.keys())
        words = [positions.get(i, "") for i in range(max_pos + 1)]
        return " ".join(w for w in words if w)

    def close(self):
        """리소스 정리"""
        if self._client:
            self._client.close()
            self._client = None
