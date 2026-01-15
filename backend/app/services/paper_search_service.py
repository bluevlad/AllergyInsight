"""통합 논문 검색 서비스

PubMed와 Semantic Scholar를 통합하여 검색하고,
중복을 제거하며 PDF 다운로드 링크를 보강합니다.
"""
import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import Optional
from dataclasses import dataclass, field

from .pubmed_service import PubMedService
from .semantic_scholar_service import SemanticScholarService
from ..models.paper import Paper, PaperSearchResult, PaperSource


@dataclass
class UnifiedSearchResult:
    """통합 검색 결과"""
    papers: list[Paper]
    pubmed_count: int
    semantic_scholar_count: int
    total_unique: int
    query: str
    search_time_ms: float

    # PDF 다운로드 가능한 논문 수
    downloadable_count: int = 0

    def to_dict(self) -> dict:
        return {
            "papers": [p.to_dict() for p in self.papers],
            "pubmed_count": self.pubmed_count,
            "semantic_scholar_count": self.semantic_scholar_count,
            "total_unique": self.total_unique,
            "downloadable_count": self.downloadable_count,
            "query": self.query,
            "search_time_ms": self.search_time_ms,
        }


class PaperSearchService:
    """통합 논문 검색 서비스"""

    def __init__(
        self,
        pubmed_api_key: Optional[str] = None,
        pubmed_email: Optional[str] = None,
        semantic_scholar_api_key: Optional[str] = None,
    ):
        self.pubmed = PubMedService(api_key=pubmed_api_key, email=pubmed_email)
        self.semantic_scholar = SemanticScholarService(api_key=semantic_scholar_api_key)
        self._executor = ThreadPoolExecutor(max_workers=4)

    def search(
        self,
        query: str,
        max_results_per_source: int = 20,
        sources: Optional[list[str]] = None,
        merge_duplicates: bool = True,
        enrich_pdf_links: bool = True,
    ) -> UnifiedSearchResult:
        """
        PubMed와 Semantic Scholar에서 동시에 검색

        Args:
            query: 검색 쿼리
            max_results_per_source: 소스당 최대 결과 수
            sources: 검색할 소스 목록 ["pubmed", "semantic_scholar"]
            merge_duplicates: DOI 기반 중복 제거
            enrich_pdf_links: Semantic Scholar에서 PDF 링크 보강

        Returns:
            UnifiedSearchResult: 통합 검색 결과
        """
        import time
        start_time = time.time()

        if sources is None:
            sources = ["pubmed", "semantic_scholar"]

        all_papers = []
        pubmed_count = 0
        ss_count = 0

        # 병렬 검색 실행
        futures = []

        if "pubmed" in sources:
            futures.append(
                self._executor.submit(
                    self.pubmed.search, query, max_results_per_source
                )
            )
        else:
            futures.append(None)

        if "semantic_scholar" in sources:
            futures.append(
                self._executor.submit(
                    self.semantic_scholar.search, query, max_results_per_source
                )
            )
        else:
            futures.append(None)

        # 결과 수집
        if futures[0]:
            try:
                pubmed_result = futures[0].result(timeout=60)
                all_papers.extend(pubmed_result.papers)
                pubmed_count = pubmed_result.total_count
            except Exception:
                pass

        if len(futures) > 1 and futures[1]:
            try:
                ss_result = futures[1].result(timeout=60)
                all_papers.extend(ss_result.papers)
                ss_count = ss_result.total_count
            except Exception:
                pass

        # 중복 제거
        if merge_duplicates:
            all_papers = self._merge_duplicates(all_papers)

        # PDF 링크 보강
        if enrich_pdf_links:
            all_papers = self._enrich_pdf_links(all_papers)

        # PDF 다운로드 가능 수 계산
        downloadable = sum(1 for p in all_papers if p.pdf_url)

        return UnifiedSearchResult(
            papers=all_papers,
            pubmed_count=pubmed_count,
            semantic_scholar_count=ss_count,
            total_unique=len(all_papers),
            downloadable_count=downloadable,
            query=query,
            search_time_ms=(time.time() - start_time) * 1000,
        )

    def search_allergy(
        self,
        allergen: str,
        include_cross_reactivity: bool = True,
        max_results_per_source: int = 20,
    ) -> UnifiedSearchResult:
        """
        알러지 특화 통합 검색

        Args:
            allergen: 알러지 항원
            include_cross_reactivity: 교차 반응 포함 여부
            max_results_per_source: 소스당 최대 결과 수

        Returns:
            UnifiedSearchResult: 검색 결과
        """
        import time
        start_time = time.time()

        # 병렬 검색
        pubmed_future = self._executor.submit(
            self.pubmed.search_allergy_papers,
            allergen,
            include_cross_reactivity,
            max_results_per_source,
        )

        ss_future = self._executor.submit(
            self.semantic_scholar.search_allergy_papers,
            allergen,
            include_cross_reactivity,
            max_results_per_source,
        )

        all_papers = []
        pubmed_count = 0
        ss_count = 0

        try:
            pubmed_result = pubmed_future.result(timeout=60)
            all_papers.extend(pubmed_result.papers)
            pubmed_count = pubmed_result.total_count
        except Exception:
            pass

        try:
            ss_result = ss_future.result(timeout=60)
            all_papers.extend(ss_result.papers)
            ss_count = ss_result.total_count
        except Exception:
            pass

        # 중복 제거 및 PDF 링크 보강
        all_papers = self._merge_duplicates(all_papers)
        all_papers = self._enrich_pdf_links(all_papers)

        downloadable = sum(1 for p in all_papers if p.pdf_url)

        return UnifiedSearchResult(
            papers=all_papers,
            pubmed_count=pubmed_count,
            semantic_scholar_count=ss_count,
            total_unique=len(all_papers),
            downloadable_count=downloadable,
            query=f"{allergen} allergy" + (" cross-reactivity" if include_cross_reactivity else ""),
            search_time_ms=(time.time() - start_time) * 1000,
        )

    def _merge_duplicates(self, papers: list[Paper]) -> list[Paper]:
        """
        DOI 기반 중복 제거 및 정보 병합

        동일 논문이 PubMed와 Semantic Scholar 모두에서 발견되면
        정보를 병합합니다 (PDF URL 등).
        """
        doi_map: dict[str, Paper] = {}
        title_map: dict[str, Paper] = {}
        unique_papers = []

        for paper in papers:
            # DOI로 중복 체크
            if paper.doi:
                doi_lower = paper.doi.lower()
                if doi_lower in doi_map:
                    # 기존 논문에 정보 보강
                    existing = doi_map[doi_lower]
                    self._merge_paper_info(existing, paper)
                    continue
                doi_map[doi_lower] = paper
                unique_papers.append(paper)
            else:
                # DOI 없으면 제목으로 체크 (간단한 정규화)
                title_key = paper.title.lower().strip()[:100]
                if title_key in title_map:
                    existing = title_map[title_key]
                    self._merge_paper_info(existing, paper)
                    continue
                title_map[title_key] = paper
                unique_papers.append(paper)

        return unique_papers

    def _merge_paper_info(self, target: Paper, source: Paper) -> None:
        """논문 정보 병합 (target에 source 정보 추가)"""
        # PDF URL 보강
        if not target.pdf_url and source.pdf_url:
            target.pdf_url = source.pdf_url

        # 인용 수 보강
        if source.citation_count and (
            not target.citation_count or source.citation_count > target.citation_count
        ):
            target.citation_count = source.citation_count

        # 키워드 병합
        existing_keywords = set(target.keywords)
        for kw in source.keywords:
            if kw not in existing_keywords:
                target.keywords.append(kw)
                existing_keywords.add(kw)

    def _enrich_pdf_links(self, papers: list[Paper]) -> list[Paper]:
        """
        PDF 링크가 없는 PubMed 논문에 대해
        Semantic Scholar에서 PDF 링크 조회
        """
        for paper in papers:
            if paper.pdf_url:
                continue

            # PubMed 논문이면 Semantic Scholar에서 PDF 링크 찾기
            if paper.source == PaperSource.PUBMED:
                try:
                    ss_paper = self.semantic_scholar.get_paper_by_pmid(paper.source_id)
                    if ss_paper and ss_paper.pdf_url:
                        paper.pdf_url = ss_paper.pdf_url
                except Exception:
                    pass
            # DOI가 있으면 Semantic Scholar에서 조회
            elif paper.doi:
                try:
                    ss_paper = self.semantic_scholar.get_paper_by_doi(paper.doi)
                    if ss_paper and ss_paper.pdf_url:
                        paper.pdf_url = ss_paper.pdf_url
                except Exception:
                    pass

        return papers

    def get_paper_with_pdf(self, doi: str) -> Optional[Paper]:
        """
        DOI로 논문 정보와 PDF 링크 가져오기

        Args:
            doi: DOI

        Returns:
            Paper 또는 None
        """
        paper = self.semantic_scholar.get_paper_by_doi(doi)
        return paper

    def close(self):
        """리소스 정리"""
        self._executor.shutdown(wait=False)
