"""Europe PMC API 연동 서비스

PubMed + PubMed Central + 유럽 논문 통합 검색.
전문(Full-text) 무료 제공, API 키 불필요.

API 문서: https://europepmc.org/RestfulWebService
"""
import logging
import time
from typing import Optional
from datetime import datetime

import httpx

from ..models.paper import Paper, PaperSearchResult, PaperSource

logger = logging.getLogger(__name__)


class EuropePMCService:
    """Europe PMC REST API 클라이언트"""

    BASE_URL = "https://www.ebi.ac.uk/europepmc/webservices/rest"

    def __init__(self):
        self._client: Optional[httpx.Client] = None

    def _get_client(self) -> httpx.Client:
        if self._client is None:
            self._client = httpx.Client(timeout=30.0)
        return self._client

    def search(
        self,
        query: str,
        max_results: int = 20,
        sort: str = "RELEVANCE",
    ) -> PaperSearchResult:
        """논문 검색

        Args:
            query: 검색 쿼리
            max_results: 최대 결과 수
            sort: 정렬 기준 (RELEVANCE, DATE)

        Returns:
            PaperSearchResult
        """
        start_time = time.time()
        client = self._get_client()

        papers = []
        try:
            resp = client.get(
                f"{self.BASE_URL}/search",
                params={
                    "query": query,
                    "format": "json",
                    "pageSize": min(max_results, 100),
                    "sort": sort,
                    "resultType": "core",
                },
            )
            resp.raise_for_status()
            data = resp.json()

            results = data.get("resultList", {}).get("result", [])
            for item in results:
                paper = self._parse_result(item)
                if paper:
                    papers.append(paper)

        except Exception as e:
            logger.error(f"Europe PMC 검색 실패: {e}")

        elapsed = (time.time() - start_time) * 1000

        return PaperSearchResult(
            papers=papers,
            total_count=len(papers),
            query=query,
            source=PaperSource.EUROPE_PMC,
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
        query = f'("{allergen} allergy" OR "{allergen} hypersensitivity") AND (SRC:MED OR SRC:PMC)'
        return self.search(query, max_results=max_results, sort="DATE")

    def get_fulltext(self, source: str, ext_id: str) -> Optional[str]:
        """전문(Full-text) XML 조회

        Args:
            source: 소스 (예: "MED", "PMC")
            ext_id: 외부 ID (PMID 또는 PMCID)

        Returns:
            전문 텍스트 또는 None
        """
        client = self._get_client()
        try:
            resp = client.get(
                f"{self.BASE_URL}/{source}/{ext_id}/fullTextXML",
            )
            if resp.status_code == 200:
                return resp.text
        except Exception as e:
            logger.warning(f"Europe PMC 전문 조회 실패 ({source}/{ext_id}): {e}")

        return None

    def _parse_result(self, item: dict) -> Optional[Paper]:
        """API 결과를 Paper 모델로 변환"""
        title = item.get("title", "").strip()
        if not title:
            return None

        # 저자 파싱
        authors = []
        author_list = item.get("authorList", {}).get("author", [])
        for author in author_list[:10]:
            name = author.get("fullName") or author.get("lastName", "")
            if name:
                authors.append(name)

        # 연도 파싱
        year = None
        pub_year = item.get("pubYear")
        if pub_year:
            try:
                year = int(pub_year)
            except (ValueError, TypeError):
                pass

        # DOI
        doi = item.get("doi")

        # PDF URL (Europe PMC full-text 링크)
        pdf_url = None
        full_text_url_list = item.get("fullTextUrlList", {}).get("fullTextUrl", [])
        for url_info in full_text_url_list:
            if url_info.get("documentStyle") == "pdf":
                pdf_url = url_info.get("url")
                break

        # 소스 ID (PMID 우선, 없으면 PMC ID)
        source_id = item.get("pmid") or item.get("pmcid") or item.get("id", "")

        # 키워드
        keywords = []
        keyword_list = item.get("keywordList", {}).get("keyword", [])
        if isinstance(keyword_list, list):
            keywords = keyword_list[:10]

        return Paper(
            title=title,
            abstract=item.get("abstractText", "") or "",
            authors=authors,
            source=PaperSource.EUROPE_PMC,
            source_id=str(source_id),
            doi=doi,
            year=year,
            journal=item.get("journalTitle"),
            citation_count=item.get("citedByCount"),
            pdf_url=pdf_url,
            keywords=keywords,
        )

    def close(self):
        """리소스 정리"""
        if self._client:
            self._client.close()
            self._client = None
