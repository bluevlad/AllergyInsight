"""bioRxiv/medRxiv 프리프린트 검색 서비스

bioRxiv/medRxiv API로 최근 프리프린트 수집,
키워드 검색은 Europe PMC의 프리프린트 필터(SRC:PPR)를 활용.

API 문서:
- bioRxiv: https://api.biorxiv.org/
- Europe PMC: https://europepmc.org/RestfulWebService
"""
import logging
import time
from typing import Optional

import httpx

from ..models.paper import Paper, PaperSearchResult, PaperSource

logger = logging.getLogger(__name__)


class BiorxivService:
    """bioRxiv/medRxiv 프리프린트 검색 클라이언트

    키워드 검색: Europe PMC API (SRC:PPR 필터)
    날짜 범위 수집: bioRxiv content detail API
    """

    BIORXIV_API_URL = "https://api.biorxiv.org/details"
    EPMC_BASE_URL = "https://www.ebi.ac.uk/europepmc/webservices/rest"

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
        sort: str = "DATE",
    ) -> PaperSearchResult:
        """프리프린트 키워드 검색 (Europe PMC 경유)

        bioRxiv API는 키워드 검색을 지원하지 않으므로
        Europe PMC의 프리프린트 필터(SRC:PPR)를 사용.

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
            # Europe PMC에서 프리프린트만 필터링
            epmc_query = f"({query}) AND (SRC:PPR)"

            resp = client.get(
                f"{self.EPMC_BASE_URL}/search",
                params={
                    "query": epmc_query,
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
                paper = self._parse_epmc_result(item)
                if paper:
                    papers.append(paper)

        except Exception as e:
            logger.error(f"bioRxiv/medRxiv 검색 실패: {e}")

        elapsed = (time.time() - start_time) * 1000

        return PaperSearchResult(
            papers=papers,
            total_count=len(papers),
            query=query,
            source=PaperSource.BIORXIV_MEDRXIV,
            search_time_ms=round(elapsed, 1),
        )

    def search_allergy(
        self,
        allergen: str,
        max_results: int = 20,
    ) -> PaperSearchResult:
        """알러지 관련 프리프린트 검색

        Args:
            allergen: 알러젠 이름 (예: "peanut")
            max_results: 최대 결과 수
        """
        query = f'"{allergen} allergy" OR "{allergen} hypersensitivity"'
        return self.search(query, max_results=max_results, sort="DATE")

    def collect_recent(
        self,
        date_from: str,
        date_to: str,
        server: str = "medrxiv",
        max_results: int = 50,
    ) -> PaperSearchResult:
        """날짜 범위로 최근 프리프린트 수집 (bioRxiv API 직접 호출)

        Args:
            date_from: 시작 날짜 (YYYY-MM-DD)
            date_to: 종료 날짜 (YYYY-MM-DD)
            server: 서버 (biorxiv, medrxiv)
            max_results: 최대 결과 수

        Returns:
            PaperSearchResult
        """
        start_time = time.time()
        client = self._get_client()

        papers = []
        cursor = 0
        try:
            while len(papers) < max_results:
                resp = client.get(
                    f"{self.BIORXIV_API_URL}/{server}/{date_from}/{date_to}/{cursor}",
                )
                resp.raise_for_status()
                data = resp.json()

                collection = data.get("collection", [])
                if not collection:
                    break

                for item in collection:
                    if len(papers) >= max_results:
                        break
                    paper = self._parse_biorxiv_result(item, server)
                    if paper:
                        papers.append(paper)

                # bioRxiv API는 30개씩 반환
                total = data.get("messages", [{}])[0].get("total", 0)
                cursor += 30
                if cursor >= total:
                    break

        except Exception as e:
            logger.error(
                f"bioRxiv/medRxiv 수집 실패 ({server}, {date_from}~{date_to}): {e}"
            )

        elapsed = (time.time() - start_time) * 1000

        return PaperSearchResult(
            papers=papers,
            total_count=len(papers),
            query=f"{server}:{date_from}~{date_to}",
            source=PaperSource.BIORXIV_MEDRXIV,
            search_time_ms=round(elapsed, 1),
        )

    def _parse_epmc_result(self, item: dict) -> Optional[Paper]:
        """Europe PMC 프리프린트 결과를 Paper 모델로 변환"""
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

        # PDF URL
        pdf_url = None
        full_text_url_list = item.get("fullTextUrlList", {}).get("fullTextUrl", [])
        for url_info in full_text_url_list:
            if url_info.get("documentStyle") == "pdf":
                pdf_url = url_info.get("url")
                break

        # 소스 ID
        source_id = item.get("doi") or item.get("id", "")

        # 키워드
        keywords = []
        keyword_list = item.get("keywordList", {}).get("keyword", [])
        if isinstance(keyword_list, list):
            keywords = keyword_list[:10]

        # 프리프린트 서버 판별
        source_name = item.get("bookOrReportDetails", {}).get("publisher", "")
        if not source_name:
            source_name = item.get("source", "Preprint")

        return Paper(
            title=title,
            abstract=item.get("abstractText", "") or "",
            authors=authors,
            source=PaperSource.BIORXIV_MEDRXIV,
            source_id=str(source_id),
            doi=doi,
            year=year,
            journal=source_name if source_name else "Preprint",
            citation_count=item.get("citedByCount"),
            pdf_url=pdf_url,
            keywords=keywords,
        )

    def _parse_biorxiv_result(
        self, item: dict, server: str
    ) -> Optional[Paper]:
        """bioRxiv API 결과를 Paper 모델로 변환"""
        title = item.get("title", "").strip()
        if not title:
            return None

        # 저자 파싱 (세미콜론 구분 문자열)
        authors = []
        author_str = item.get("authors", "")
        if author_str:
            authors = [
                a.strip()
                for a in author_str.split(";")
                if a.strip()
            ][:10]

        # DOI
        doi = item.get("doi")

        # 연도 파싱
        year = None
        date_str = item.get("date", "")
        if date_str:
            try:
                year = int(date_str.split("-")[0])
            except (ValueError, IndexError):
                pass

        # 카테고리
        category = item.get("category", "")
        keywords = [category] if category else []

        # 서버 표시명
        server_display = "bioRxiv" if server == "biorxiv" else "medRxiv"

        return Paper(
            title=title,
            abstract=item.get("abstract", "") or "",
            authors=authors,
            source=PaperSource.BIORXIV_MEDRXIV,
            source_id=doi or item.get("doi", ""),
            doi=doi,
            year=year,
            journal=f"{server_display} (preprint)",
            citation_count=None,
            pdf_url=f"https://doi.org/{doi}" if doi else None,
            keywords=keywords,
        )

    def close(self):
        """리소스 정리"""
        if self._client:
            self._client.close()
            self._client = None
