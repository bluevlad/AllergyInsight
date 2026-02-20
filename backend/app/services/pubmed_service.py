"""PubMed E-utilities API 연동 서비스

PubMed는 미국 국립의학도서관(NLM)에서 제공하는 의학/생명과학 논문 데이터베이스입니다.
E-utilities API를 통해 무료로 논문 검색 및 메타데이터를 가져올 수 있습니다.

API 문서: https://www.ncbi.nlm.nih.gov/books/NBK25497/
"""
import time
import logging
import xml.etree.ElementTree as ET
from typing import Optional
from datetime import datetime

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)

from ..models.paper import Paper, PaperSearchResult, PaperSource


class PubMedService:
    """PubMed E-utilities API 클라이언트"""

    BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"

    def __init__(self, api_key: Optional[str] = None, email: Optional[str] = None):
        """
        Args:
            api_key: NCBI API 키 (선택, 있으면 요청 제한 완화)
            email: 연락용 이메일 (NCBI 권장사항)
        """
        self.api_key = api_key
        self.email = email
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "AllergyInsight/1.0 (Research Tool)"
        })
        # 재시도 전략: 429/500/502/503/504 시 지수 백오프
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)

    def _build_params(self, **kwargs) -> dict:
        """기본 파라미터 구성"""
        params = dict(kwargs)
        if self.api_key:
            params["api_key"] = self.api_key
        if self.email:
            params["email"] = self.email
        return params

    def search(
        self,
        query: str,
        max_results: int = 20,
        sort: str = "relevance",
        min_date: Optional[str] = None,
        max_date: Optional[str] = None,
    ) -> PaperSearchResult:
        """
        PubMed에서 논문 검색

        Args:
            query: 검색 쿼리 (예: "peanut allergy cross-reactivity")
            max_results: 최대 결과 수 (기본 20, 최대 10000)
            sort: 정렬 방식 ("relevance", "pub_date")
            min_date: 최소 발행일 (YYYY/MM/DD)
            max_date: 최대 발행일 (YYYY/MM/DD)

        Returns:
            PaperSearchResult: 검색 결과
        """
        start_time = time.time()

        # 1단계: esearch로 논문 ID 목록 검색
        search_params = self._build_params(
            db="pubmed",
            term=query,
            retmax=max_results,
            retmode="json",
            sort=sort,
            usehistory="y",  # 대용량 결과 처리용
        )

        if min_date:
            search_params["mindate"] = min_date
        if max_date:
            search_params["maxdate"] = max_date
            search_params["datetype"] = "pdat"  # publication date

        try:
            search_response = self.session.get(
                f"{self.BASE_URL}/esearch.fcgi",
                params=search_params,
                timeout=30,
            )
            search_response.raise_for_status()
            search_data = search_response.json()
        except requests.RequestException as e:
            logger.warning(f"PubMed search failed: {query} - {e}")
            return PaperSearchResult(
                papers=[],
                total_count=0,
                query=query,
                source=PaperSource.PUBMED,
                search_time_ms=(time.time() - start_time) * 1000,
            )

        result = search_data.get("esearchresult", {})
        id_list = result.get("idlist", [])
        total_count = int(result.get("count", 0))

        if not id_list:
            return PaperSearchResult(
                papers=[],
                total_count=0,
                query=query,
                source=PaperSource.PUBMED,
                search_time_ms=(time.time() - start_time) * 1000,
            )

        # 2단계: efetch로 논문 상세 정보 가져오기
        papers = self._fetch_paper_details(id_list)

        return PaperSearchResult(
            papers=papers,
            total_count=total_count,
            query=query,
            source=PaperSource.PUBMED,
            search_time_ms=(time.time() - start_time) * 1000,
        )

    def _fetch_paper_details(self, pmids: list[str]) -> list[Paper]:
        """
        논문 ID 목록으로 상세 정보 가져오기

        Args:
            pmids: PubMed ID 목록

        Returns:
            list[Paper]: 논문 목록
        """
        fetch_params = self._build_params(
            db="pubmed",
            id=",".join(pmids),
            retmode="xml",
            rettype="abstract",
        )

        try:
            fetch_response = self.session.get(
                f"{self.BASE_URL}/efetch.fcgi",
                params=fetch_params,
                timeout=60,
            )
            fetch_response.raise_for_status()
            return self._parse_pubmed_xml(fetch_response.text)
        except requests.RequestException as e:
            logger.warning(f"PubMed fetch failed for {len(pmids)} papers: {e}")
            return []

    def _parse_pubmed_xml(self, xml_content: str) -> list[Paper]:
        """
        PubMed XML 응답 파싱

        Args:
            xml_content: XML 문자열

        Returns:
            list[Paper]: 파싱된 논문 목록
        """
        papers = []

        try:
            root = ET.fromstring(xml_content)
        except ET.ParseError:
            return papers

        for article in root.findall(".//PubmedArticle"):
            try:
                paper = self._parse_article(article)
                if paper:
                    papers.append(paper)
            except Exception:
                continue

        return papers

    def _parse_article(self, article: ET.Element) -> Optional[Paper]:
        """단일 논문 XML 파싱"""
        medline = article.find(".//MedlineCitation")
        if medline is None:
            return None

        # PMID
        pmid_elem = medline.find(".//PMID")
        pmid = pmid_elem.text if pmid_elem is not None else None
        if not pmid:
            return None

        article_elem = medline.find(".//Article")
        if article_elem is None:
            return None

        # 제목
        title_elem = article_elem.find(".//ArticleTitle")
        title = self._get_text_content(title_elem) if title_elem is not None else "제목 없음"

        # 초록
        abstract_elem = article_elem.find(".//Abstract")
        abstract = ""
        if abstract_elem is not None:
            abstract_texts = []
            for text_elem in abstract_elem.findall(".//AbstractText"):
                label = text_elem.get("Label", "")
                text = self._get_text_content(text_elem)
                if label:
                    abstract_texts.append(f"{label}: {text}")
                else:
                    abstract_texts.append(text)
            abstract = " ".join(abstract_texts)

        # 저자
        authors = []
        author_list = article_elem.find(".//AuthorList")
        if author_list is not None:
            for author in author_list.findall(".//Author"):
                last_name = author.find("LastName")
                fore_name = author.find("ForeName")
                if last_name is not None:
                    name_parts = []
                    if fore_name is not None:
                        name_parts.append(fore_name.text)
                    name_parts.append(last_name.text)
                    authors.append(" ".join(name_parts))

        # 저널
        journal_elem = article_elem.find(".//Journal/Title")
        journal = journal_elem.text if journal_elem is not None else None

        # 발행년도
        year = None
        pub_date = article_elem.find(".//Journal/JournalIssue/PubDate")
        if pub_date is not None:
            year_elem = pub_date.find("Year")
            if year_elem is not None and year_elem.text:
                try:
                    year = int(year_elem.text)
                except ValueError:
                    pass

        # DOI
        doi = None
        article_id_list = article.find(".//PubmedData/ArticleIdList")
        if article_id_list is not None:
            for article_id in article_id_list.findall("ArticleId"):
                if article_id.get("IdType") == "doi":
                    doi = article_id.text
                    break

        # 키워드
        keywords = []
        keyword_list = medline.find(".//KeywordList")
        if keyword_list is not None:
            for kw in keyword_list.findall("Keyword"):
                if kw.text:
                    keywords.append(kw.text)

        # MeSH Terms
        mesh_list = medline.find(".//MeshHeadingList")
        if mesh_list is not None:
            for mesh in mesh_list.findall(".//DescriptorName"):
                if mesh.text and mesh.text not in keywords:
                    keywords.append(mesh.text)

        return Paper(
            title=title,
            abstract=abstract,
            authors=authors,
            source=PaperSource.PUBMED,
            source_id=pmid,
            doi=doi,
            year=year,
            journal=journal,
            keywords=keywords[:20],  # 상위 20개만
        )

    def _get_text_content(self, element: ET.Element) -> str:
        """XML 요소의 전체 텍스트 내용 추출 (하위 태그 포함)"""
        return "".join(element.itertext()).strip()

    def get_paper_by_pmid(self, pmid: str) -> Optional[Paper]:
        """
        PMID로 논문 정보 가져오기

        Args:
            pmid: PubMed ID

        Returns:
            Paper 또는 None
        """
        papers = self._fetch_paper_details([pmid])
        return papers[0] if papers else None

    def search_allergy_papers(
        self,
        allergen: str,
        include_cross_reactivity: bool = True,
        max_results: int = 20,
    ) -> PaperSearchResult:
        """
        알러지 관련 논문 특화 검색

        Args:
            allergen: 알러지 항원 (예: "peanut", "milk", "egg")
            include_cross_reactivity: 교차 반응 관련 논문 포함 여부
            max_results: 최대 결과 수

        Returns:
            PaperSearchResult: 검색 결과
        """
        # 알러지 특화 검색 쿼리 구성
        query_parts = [
            f'"{allergen}"[Title/Abstract]',
            'allergy[Title/Abstract] OR allergic[Title/Abstract] OR hypersensitivity[Title/Abstract]',
        ]

        if include_cross_reactivity:
            query_parts.append(
                'cross-reactivity[Title/Abstract] OR cross-reactive[Title/Abstract]'
            )

        query = f"({query_parts[0]}) AND ({query_parts[1]})"
        if include_cross_reactivity:
            query = f"{query} AND ({query_parts[2]})"

        return self.search(query, max_results=max_results)
