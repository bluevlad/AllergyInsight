"""통합 논문 검색 서비스 (Registry 기반).

PubMed, Semantic Scholar, Europe PMC, OpenAlex, bioRxiv/medRxiv, CORE를
``app.core.sources`` registry 를 통해 통합 검색하고, 중복을 제거하며
PDF 다운로드 링크를 보강합니다.

Step 1.D 리팩토링:
- 6 hardcoded source instantiation → ``registry.all_of_kind(SourceKind.PAPER)``
- PDF 보강 → ``SemanticScholarConnector.get_pdf_url_by_pmid/doi`` cross-lookup
- 부분 실패 가시화 → ``UnifiedSearchResult.errors`` dict

알러지 특화 query 빌더 (``search_allergy``) 는 도메인 로직이므로 Phase 1.G
DomainPack 으로 이관 예정. 그 전까지는 legacy ``*Service.search_allergy*``
메서드를 그대로 호출한다.
"""
from __future__ import annotations

import logging
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from typing import Optional

from sqlalchemy.orm import Session

# Layer 1 (registry-based)
from ..core.sources import registry
from ..core.sources.base import SourceKind
from ..core.sources.paper.base import (
    PaperSourceConnector,
    normalized_to_paper,
)
# Auto-register all paper connectors on import
from ..core.sources.paper import (  # noqa: F401
    pubmed as _pubmed_module,
    semantic_scholar as _s2_module,
    europe_pmc as _epmc_module,
    openalex as _oa_module,
    biorxiv as _biorxiv_module,
    core as _core_module,
)
from ..core.sources.paper.semantic_scholar import SemanticScholarConnector

# Legacy services — search_allergy 의 도메인 특화 query 메서드 호출용
# (Phase 1.G DomainPack 으로 이관 시 제거)
from .pubmed_service import PubMedService
from .semantic_scholar_service import SemanticScholarService
from .europe_pmc_service import EuropePMCService
from .openalex_service import OpenAlexService
from .biorxiv_service import BiorxivService
from .core_service import CoreService
from ..models.paper import Paper, PaperSource

logger = logging.getLogger(__name__)


# Registry name ↔ legacy UnifiedSearchResult per-source count field
_COUNT_FIELDS: dict[str, str] = {
    "pubmed": "pubmed_count",
    "semantic_scholar": "semantic_scholar_count",
    "europe_pmc": "europe_pmc_count",
    "openalex": "openalex_count",
    "biorxiv": "biorxiv_count",
    "core": "core_count",
}


@dataclass
class UnifiedSearchResult:
    """통합 검색 결과.

    Step 1.D 에서 ``errors`` 필드가 추가됨 (default 빈 dict 으로 backward-compat).
    """
    papers: list[Paper]
    pubmed_count: int
    semantic_scholar_count: int
    total_unique: int
    query: str
    search_time_ms: float

    # PDF 다운로드 가능한 논문 수
    downloadable_count: int = 0
    europe_pmc_count: int = 0
    openalex_count: int = 0
    biorxiv_count: int = 0
    core_count: int = 0

    # Step 1.D-003: 부분 실패 가시화 (source 이름 → 에러 메시지)
    errors: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "papers": [p.to_dict() for p in self.papers],
            "pubmed_count": self.pubmed_count,
            "semantic_scholar_count": self.semantic_scholar_count,
            "europe_pmc_count": self.europe_pmc_count,
            "openalex_count": self.openalex_count,
            "biorxiv_count": self.biorxiv_count,
            "core_count": self.core_count,
            "total_unique": self.total_unique,
            "downloadable_count": self.downloadable_count,
            "query": self.query,
            "search_time_ms": self.search_time_ms,
            "errors": dict(self.errors),
        }


class PaperSearchService:
    """통합 논문 검색 서비스 (registry 기반).

    Step 1.D 리팩토링: 6 hardcoded service → registry.all_of_kind(PAPER).
    ``__init__`` 의 api_key/email 인자는 search_allergy 전용 legacy 서비스에만
    전달되며, registry connector 들은 자체 환경변수 (NCBI_API_KEY,
    SEMANTIC_SCHOLAR_API_KEY, CORE_API_KEY, OPENALEX_EMAIL 등) 를 읽는다.
    """

    def __init__(
        self,
        pubmed_api_key: Optional[str] = None,
        pubmed_email: Optional[str] = None,
        semantic_scholar_api_key: Optional[str] = None,
    ):
        # Registry-based connectors (Step 1.D-001)
        self._connectors: dict[str, PaperSourceConnector] = {
            c.name: c for c in registry.all_of_kind(SourceKind.PAPER)
        }
        # S2 connector 별도 보관 — PDF 보강 cross-lookup 에 사용 (Step 1.D-002)
        self._s2_connector: Optional[SemanticScholarConnector] = self._connectors.get(
            "semantic_scholar"
        )  # type: ignore[assignment]

        # Legacy services — search_allergy 도메인 query 빌더 호출 전용
        # (Phase 1.G 에서 DomainPack 으로 이관 후 제거 예정)
        self.pubmed = PubMedService(api_key=pubmed_api_key, email=pubmed_email)
        self.semantic_scholar = SemanticScholarService(
            api_key=semantic_scholar_api_key
        )
        self.europe_pmc = EuropePMCService()
        self.openalex = OpenAlexService(email=pubmed_email)
        self.biorxiv = BiorxivService()
        self.core = CoreService()

        self._executor = ThreadPoolExecutor(max_workers=7)

    # ───────── 일반 검색 (registry path) ─────────

    def search(
        self,
        query: str,
        max_results_per_source: int = 20,
        sources: Optional[list[str]] = None,
        merge_duplicates: bool = True,
        enrich_pdf_links: bool = True,
        db: Optional[Session] = None,
    ) -> UnifiedSearchResult:
        """Registry 기반 통합 검색.

        Args:
            query: 검색 쿼리
            max_results_per_source: 소스당 최대 결과 수
            sources: 검색할 source 이름 목록 (registry 키). None 이면 ``is_available()``
                가 True 인 모든 paper connector 사용.
            merge_duplicates: DOI/제목 기반 중복 제거
            enrich_pdf_links: S2 connector 로 PDF 링크 cross-lookup
            db: DB 세션 전달 시 결과 자동 저장
        """
        start_time = time.time()

        selected = self._select_connectors(sources)
        all_papers, counts, errors = self._run_parallel(
            selected, query, max_results_per_source
        )

        if merge_duplicates:
            all_papers = self._merge_duplicates(all_papers)

        if enrich_pdf_links:
            all_papers = self._enrich_pdf_links(all_papers)

        downloadable = sum(1 for p in all_papers if p.pdf_url)

        result = UnifiedSearchResult(
            papers=all_papers,
            pubmed_count=counts.get("pubmed", 0),
            semantic_scholar_count=counts.get("semantic_scholar", 0),
            europe_pmc_count=counts.get("europe_pmc", 0),
            openalex_count=counts.get("openalex", 0),
            biorxiv_count=counts.get("biorxiv", 0),
            core_count=counts.get("core", 0),
            total_unique=len(all_papers),
            downloadable_count=downloadable,
            query=query,
            search_time_ms=(time.time() - start_time) * 1000,
            errors=errors,
        )

        if db is not None:
            self._maybe_persist(result, db)

        return result

    def _select_connectors(
        self,
        sources: Optional[list[str]],
    ) -> list[PaperSourceConnector]:
        """sources 필터 + is_available 검증 후 호출 대상 connector 리스트."""
        if sources is None:
            wanted = set(self._connectors.keys())
        else:
            wanted = set(sources)

        result: list[PaperSourceConnector] = []
        for name, conn in self._connectors.items():
            if name not in wanted:
                continue
            try:
                if not conn.is_available():
                    logger.debug("%s connector unavailable — skipped", name)
                    continue
            except Exception as e:
                logger.warning("%s.is_available() 예외 (skip): %s", name, e)
                continue
            result.append(conn)
        return result

    def _run_parallel(
        self,
        connectors: list[PaperSourceConnector],
        query: str,
        max_results: int,
    ) -> tuple[list[Paper], dict[str, int], dict[str, str]]:
        """Connector 병렬 호출, NormalizedDoc → Paper 변환, count/error 수집."""
        futures = {
            self._executor.submit(c.search, query, max_results): c.name
            for c in connectors
        }
        all_papers: list[Paper] = []
        counts: dict[str, int] = {}
        errors: dict[str, str] = {}

        for fut, name in list(futures.items()):
            try:
                res = fut.result(timeout=60)
            except Exception as e:
                logger.warning("%s search future 예외: %s", name, e)
                errors[name] = f"{type(e).__name__}: {e}"
                continue

            # Connector 내부에서 잡힌 부분 실패도 가시화
            if res.has_error:
                errors[name] = res.meta.get("error", "unknown")

            # NormalizedDoc → Paper 역변환
            for doc in res.docs:
                try:
                    all_papers.append(normalized_to_paper(doc))
                except Exception as e:
                    logger.debug("normalized_to_paper 실패 (skip): %s", e)

            # total_count 우선, 없으면 docs 개수
            counts[name] = res.meta.get("total_count", res.count)

        return all_papers, counts, errors

    # ───────── 알러지 특화 검색 (legacy path, Phase 1.G 이관 예정) ─────────

    def search_allergy(
        self,
        allergen: str,
        include_cross_reactivity: bool = True,
        max_results_per_source: int = 20,
        db: Optional[Session] = None,
    ) -> UnifiedSearchResult:
        """알러지 특화 통합 검색.

        Legacy 서비스의 ``search_allergy*`` 메서드를 호출하여 각 source 별
        특화 query (MeSH, Title/Abstract 등) 를 활용한다. Phase 1.G 에서
        DomainPack YAML 의 query_template 으로 이관 예정.
        """
        start_time = time.time()

        futures = {
            "pubmed": self._executor.submit(
                self.pubmed.search_allergy_papers,
                allergen, include_cross_reactivity, max_results_per_source,
            ),
            "semantic_scholar": self._executor.submit(
                self.semantic_scholar.search_allergy_papers,
                allergen, include_cross_reactivity, max_results_per_source,
            ),
            "europe_pmc": self._executor.submit(
                self.europe_pmc.search_allergy, allergen, max_results_per_source,
            ),
            "openalex": self._executor.submit(
                self.openalex.search_allergy, allergen, max_results_per_source,
            ),
            "biorxiv": self._executor.submit(
                self.biorxiv.search_allergy, allergen, max_results_per_source,
            ),
        }
        if self.core.is_available:
            futures["core"] = self._executor.submit(
                self.core.search_allergy, allergen, max_results_per_source,
            )

        all_papers: list[Paper] = []
        counts: dict[str, int] = {}
        errors: dict[str, str] = {}

        for name, fut in futures.items():
            try:
                r = fut.result(timeout=60)
                all_papers.extend(r.papers)
                counts[name] = r.total_count
            except Exception as e:
                logger.warning("%s.search_allergy 예외: %s", name, e)
                errors[name] = f"{type(e).__name__}: {e}"

        all_papers = self._merge_duplicates(all_papers)
        all_papers = self._enrich_pdf_links(all_papers)
        downloadable = sum(1 for p in all_papers if p.pdf_url)

        result = UnifiedSearchResult(
            papers=all_papers,
            pubmed_count=counts.get("pubmed", 0),
            semantic_scholar_count=counts.get("semantic_scholar", 0),
            europe_pmc_count=counts.get("europe_pmc", 0),
            openalex_count=counts.get("openalex", 0),
            biorxiv_count=counts.get("biorxiv", 0),
            core_count=counts.get("core", 0),
            total_unique=len(all_papers),
            downloadable_count=downloadable,
            query=(
                f"{allergen} allergy"
                + (" cross-reactivity" if include_cross_reactivity else "")
            ),
            search_time_ms=(time.time() - start_time) * 1000,
            errors=errors,
        )

        if db is not None:
            self._maybe_persist(result, db, allergen_code=allergen)

        return result

    # ───────── 중복 제거 / PDF 보강 ─────────

    def _merge_duplicates(self, papers: list[Paper]) -> list[Paper]:
        """DOI 기반 중복 제거 및 정보 병합 (변경 없음)."""
        doi_map: dict[str, Paper] = {}
        title_map: dict[str, Paper] = {}
        unique_papers = []

        for paper in papers:
            if paper.doi:
                doi_lower = paper.doi.lower()
                if doi_lower in doi_map:
                    self._merge_paper_info(doi_map[doi_lower], paper)
                    continue
                doi_map[doi_lower] = paper
                unique_papers.append(paper)
            else:
                title_key = paper.title.lower().strip()[:100]
                if title_key in title_map:
                    self._merge_paper_info(title_map[title_key], paper)
                    continue
                title_map[title_key] = paper
                unique_papers.append(paper)
        return unique_papers

    def _merge_paper_info(self, target: Paper, source: Paper) -> None:
        if not target.pdf_url and source.pdf_url:
            target.pdf_url = source.pdf_url
        if source.citation_count and (
            not target.citation_count
            or source.citation_count > target.citation_count
        ):
            target.citation_count = source.citation_count
        existing_keywords = set(target.keywords)
        for kw in source.keywords:
            if kw not in existing_keywords:
                target.keywords.append(kw)
                existing_keywords.add(kw)

    def _enrich_pdf_links(self, papers: list[Paper]) -> list[Paper]:
        """PDF URL 미보유 논문에 대해 S2 connector 로 cross-lookup.

        Step 1.D-002: 기존 ``self.semantic_scholar.get_paper_by_pmid/doi`` 직접
        호출 → ``self._s2_connector.get_pdf_url_by_pmid/doi`` ABC 메서드로 위임.
        S2 connector 가 없거나 미가용이면 보강 skip.
        """
        if self._s2_connector is None:
            return papers

        for paper in papers:
            if paper.pdf_url:
                continue
            pdf_url: Optional[str] = None
            if paper.source == PaperSource.PUBMED and paper.source_id:
                pdf_url = self._s2_connector.get_pdf_url_by_pmid(paper.source_id)
            elif paper.doi:
                pdf_url = self._s2_connector.get_pdf_url_by_doi(paper.doi)
            if pdf_url:
                paper.pdf_url = pdf_url
        return papers

    # ───────── 기타 ─────────

    def get_paper_with_pdf(self, doi: str) -> Optional[Paper]:
        """DOI 로 논문 + PDF 단건 조회 (S2 직행)."""
        return self.semantic_scholar.get_paper_by_doi(doi)

    def _maybe_persist(
        self,
        result: UnifiedSearchResult,
        db: Session,
        allergen_code: Optional[str] = None,
    ) -> None:
        try:
            from .paper_persistence_service import PaperPersistenceService

            persistence = PaperPersistenceService()
            if allergen_code is not None:
                persistence.save_search_results(result, db, allergen_code=allergen_code)
            else:
                persistence.save_search_results(result, db)
        except Exception as e:
            logger.warning("검색 결과 DB 저장 실패: %s", e)

    def close(self):
        """리소스 정리 — connector + legacy service 모두."""
        for conn in self._connectors.values():
            try:
                conn.close()
            except Exception:
                pass
        # Legacy services
        for svc in (self.europe_pmc, self.openalex, self.biorxiv, self.core):
            try:
                svc.close()
            except Exception:
                pass
        self._executor.shutdown(wait=False)
