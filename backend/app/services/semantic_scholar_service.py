"""Semantic Scholar API 연동 서비스

Semantic Scholar는 AI2(Allen Institute for AI)에서 운영하는 학술 논문 검색 엔진입니다.
2억 개 이상의 논문을 보유하고 있으며, 오픈 액세스 PDF 링크를 제공합니다.

API 문서: https://api.semanticscholar.org/api-docs/
"""
import time
import logging
from typing import Optional
from datetime import datetime

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)

from ..models.paper import Paper, PaperSearchResult, PaperSource


class SemanticScholarService:
    """Semantic Scholar API 클라이언트"""

    BASE_URL = "https://api.semanticscholar.org/graph/v1"

    # API 필드 정의
    PAPER_FIELDS = [
        "paperId",
        "title",
        "abstract",
        "authors",
        "year",
        "citationCount",
        "journal",
        "externalIds",
        "openAccessPdf",
        "fieldsOfStudy",
        "s2FieldsOfStudy",
    ]

    def __init__(self, api_key: Optional[str] = None):
        """
        Args:
            api_key: Semantic Scholar API 키 (선택, 있으면 요청 제한 완화)
        """
        self.api_key = api_key
        self.session = requests.Session()
        headers = {
            "User-Agent": "AllergyInsight/1.0 (Research Tool)",
        }
        if api_key:
            headers["x-api-key"] = api_key
        self.session.headers.update(headers)
        # 재시도 전략: 429/500/502/503/504 시 지수 백오프
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)

    def search(
        self,
        query: str,
        max_results: int = 20,
        year_range: Optional[tuple[int, int]] = None,
        open_access_only: bool = False,
        fields_of_study: Optional[list[str]] = None,
    ) -> PaperSearchResult:
        """
        Semantic Scholar에서 논문 검색

        Args:
            query: 검색 쿼리
            max_results: 최대 결과 수 (기본 20, 최대 100)
            year_range: (시작년도, 끝년도) 튜플
            open_access_only: 오픈 액세스 논문만 검색
            fields_of_study: 분야 필터 (예: ["Medicine", "Biology"])

        Returns:
            PaperSearchResult: 검색 결과
        """
        start_time = time.time()

        params = {
            "query": query,
            "limit": min(max_results, 100),
            "fields": ",".join(self.PAPER_FIELDS),
        }

        if year_range:
            params["year"] = f"{year_range[0]}-{year_range[1]}"

        if open_access_only:
            params["openAccessPdf"] = ""  # 필터 활성화

        if fields_of_study:
            params["fieldsOfStudy"] = ",".join(fields_of_study)

        try:
            response = self.session.get(
                f"{self.BASE_URL}/paper/search",
                params=params,
                timeout=30,
            )
            response.raise_for_status()
            data = response.json()
        except requests.RequestException as e:
            logger.warning(f"Semantic Scholar search failed: {query} - {e}")
            return PaperSearchResult(
                papers=[],
                total_count=0,
                query=query,
                source=PaperSource.SEMANTIC_SCHOLAR,
                search_time_ms=(time.time() - start_time) * 1000,
            )

        papers = []
        for item in data.get("data", []):
            paper = self._parse_paper(item)
            if paper:
                papers.append(paper)

        return PaperSearchResult(
            papers=papers,
            total_count=data.get("total", len(papers)),
            query=query,
            source=PaperSource.SEMANTIC_SCHOLAR,
            search_time_ms=(time.time() - start_time) * 1000,
        )

    def _parse_paper(self, data: dict) -> Optional[Paper]:
        """
        API 응답에서 Paper 객체 생성

        Args:
            data: API 응답 데이터

        Returns:
            Paper 또는 None
        """
        paper_id = data.get("paperId")
        title = data.get("title")

        if not paper_id or not title:
            return None

        # 저자 파싱
        authors = []
        for author in data.get("authors", []):
            name = author.get("name")
            if name:
                authors.append(name)

        # DOI 추출
        external_ids = data.get("externalIds", {}) or {}
        doi = external_ids.get("DOI")

        # PDF URL 추출
        pdf_info = data.get("openAccessPdf", {}) or {}
        pdf_url = pdf_info.get("url")

        # 저널 정보
        journal_info = data.get("journal", {}) or {}
        journal = journal_info.get("name")

        # 분야 키워드
        keywords = []
        for field in data.get("s2FieldsOfStudy", []) or []:
            category = field.get("category")
            if category:
                keywords.append(category)

        return Paper(
            title=title,
            abstract=data.get("abstract") or "",
            authors=authors,
            source=PaperSource.SEMANTIC_SCHOLAR,
            source_id=paper_id,
            doi=doi,
            year=data.get("year"),
            journal=journal,
            citation_count=data.get("citationCount"),
            pdf_url=pdf_url,
            keywords=keywords,
        )

    def get_paper_by_id(self, paper_id: str) -> Optional[Paper]:
        """
        논문 ID로 상세 정보 가져오기

        Args:
            paper_id: Semantic Scholar Paper ID

        Returns:
            Paper 또는 None
        """
        try:
            response = self.session.get(
                f"{self.BASE_URL}/paper/{paper_id}",
                params={"fields": ",".join(self.PAPER_FIELDS)},
                timeout=30,
            )
            response.raise_for_status()
            data = response.json()
            return self._parse_paper(data)
        except requests.RequestException:
            return None

    def get_paper_by_doi(self, doi: str) -> Optional[Paper]:
        """
        DOI로 논문 정보 가져오기

        Args:
            doi: DOI (예: "10.1016/j.jaci.2020.01.001")

        Returns:
            Paper 또는 None
        """
        return self.get_paper_by_id(f"DOI:{doi}")

    def get_paper_by_pmid(self, pmid: str) -> Optional[Paper]:
        """
        PubMed ID로 논문 정보 가져오기 (PDF URL 확인용)

        Args:
            pmid: PubMed ID

        Returns:
            Paper 또는 None
        """
        return self.get_paper_by_id(f"PMID:{pmid}")

    def search_allergy_papers(
        self,
        allergen: str,
        include_cross_reactivity: bool = True,
        max_results: int = 20,
        open_access_only: bool = False,
    ) -> PaperSearchResult:
        """
        알러지 관련 논문 특화 검색

        Args:
            allergen: 알러지 항원 (예: "peanut", "milk", "egg")
            include_cross_reactivity: 교차 반응 관련 논문 포함 여부
            max_results: 최대 결과 수
            open_access_only: 오픈 액세스만 검색

        Returns:
            PaperSearchResult: 검색 결과
        """
        # 알러지 특화 검색 쿼리 구성
        query = f"{allergen} allergy"

        if include_cross_reactivity:
            query = f"{allergen} allergy cross-reactivity"

        return self.search(
            query=query,
            max_results=max_results,
            open_access_only=open_access_only,
            fields_of_study=["Medicine", "Biology"],
        )

    def get_recommendations(self, paper_id: str, limit: int = 10) -> list[Paper]:
        """
        관련 논문 추천

        Args:
            paper_id: 기준 논문 ID
            limit: 추천 논문 수

        Returns:
            list[Paper]: 추천 논문 목록
        """
        try:
            response = self.session.get(
                f"{self.BASE_URL}/recommendations/v1/papers/forpaper/{paper_id}",
                params={
                    "limit": limit,
                    "fields": ",".join(self.PAPER_FIELDS),
                },
                timeout=30,
            )
            response.raise_for_status()
            data = response.json()

            papers = []
            for item in data.get("recommendedPapers", []):
                paper = self._parse_paper(item)
                if paper:
                    papers.append(paper)
            return papers
        except requests.RequestException:
            return []

    def get_citations(self, paper_id: str, limit: int = 50) -> list[Paper]:
        """
        논문을 인용한 논문 목록

        Args:
            paper_id: 논문 ID
            limit: 최대 수

        Returns:
            list[Paper]: 인용 논문 목록
        """
        try:
            response = self.session.get(
                f"{self.BASE_URL}/paper/{paper_id}/citations",
                params={
                    "limit": limit,
                    "fields": ",".join(self.PAPER_FIELDS),
                },
                timeout=30,
            )
            response.raise_for_status()
            data = response.json()

            papers = []
            for item in data.get("data", []):
                citing_paper = item.get("citingPaper", {})
                paper = self._parse_paper(citing_paper)
                if paper:
                    papers.append(paper)
            return papers
        except requests.RequestException:
            return []
