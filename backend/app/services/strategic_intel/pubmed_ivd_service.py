"""PubMed IVD 도메인 키워드 강화 어댑터 (Phase D-잔여)

기존 PubMed 검색은 알러젠 로테이션(peanut/milk/...) 기반 — 일반 임상 논문 비중 큼.
Strategic Intel 가설 엔진은 IVD 진단 키트/시약 도메인 신호가 필요하므로,
별도 큐를 운용해 알러지 IVD 키워드 논문을 추가 적재한다.

저장:
  - papers 테이블 (기존 영속화 흐름 그대로) — source='pubmed'
  - 후속 stage_classify 가 published_at 기준으로 자동 픽업

원칙:
  - PubMed E-utilities rate limit 준수 (호출 간 0.3s, with API key 면 더 빠름)
  - 쿼리당 최대 max_per_query 건만 적재 (대량 적재 회피)
  - 기존 논문은 dedupe (DOI/PMID/제목)

Strategic Intel 모듈 전용. 외부 사용자 노출 금지.
"""
from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from datetime import date

from sqlalchemy.orm import Session

from ..pubmed_service import PubMedService
from ..paper_persistence_service import PaperPersistenceService

logger = logging.getLogger(__name__)


# 알러지 IVD 진단 키트/시약 도메인 한정 검색 쿼리 — Tech Taxonomy v1.1 카테고리와 정합
PUBMED_IVD_QUERIES: list[str] = [
    # multiplex / microarray
    '("multiplex" AND "allergen") OR "ALEX2" OR "ImmunoCAP ISAC"',
    # CRD
    '"component-resolved diagnosis" OR "molecular allergology"',
    # singleplex
    '"specific IgE" AND ("ImmunoCAP" OR "FEIA" OR "fluorescent enzyme immunoassay")',
    # POC / lateral flow
    '"point-of-care" AND ("IgE" OR "allergy")',
    # MAST / immunoblot
    '"MAST" AND "allergy" OR "immunoblot" AND "IgE"',
    # BAT / functional
    '"basophil activation test" AND "allergy"',
    # microfluidics
    '"microfluidic" AND ("IgE" OR "allergy")',
    # biosensor / nano
    '"biosensor" AND "IgE"',
    # NGS / omics
    '"NGS" AND "allergen panel"',
]


@dataclass
class PubmedIvdCollectResult:
    query: str
    fetched: int
    inserted: int
    error: str | None = None


class PubmedIvdService:
    """알러지 IVD 도메인 한정 PubMed 큐"""

    def __init__(
        self,
        *,
        pubmed: PubMedService | None = None,
        persistence: PaperPersistenceService | None = None,
        max_per_query: int = 10,
        between_call_seconds: float = 0.4,
    ):
        self.pubmed = pubmed or PubMedService()
        self.persistence = persistence or PaperPersistenceService()
        self.max_per_query = max_per_query
        self.between_call_seconds = between_call_seconds

    def collect(
        self,
        db: Session,
        *,
        since: date,
        until: date,
        queries: list[str] | None = None,
    ) -> list[PubmedIvdCollectResult]:
        """IVD 쿼리들을 PubMed 에 발행 → papers 테이블 적재.

        Returns: 쿼리별 결과 리스트.
        """
        targets = queries or PUBMED_IVD_QUERIES
        out: list[PubmedIvdCollectResult] = []
        min_date = since.strftime("%Y/%m/%d")
        max_date = until.strftime("%Y/%m/%d")

        for q in targets:
            try:
                result = self.pubmed.search(
                    query=q,
                    max_results=self.max_per_query,
                    sort="pub_date",
                    min_date=min_date,
                    max_date=max_date,
                )
            except Exception as e:
                logger.warning("PubMed IVD search 실패 q=%s: %s", q[:60], e)
                out.append(PubmedIvdCollectResult(query=q, fetched=0, inserted=0, error=str(e)))
                time.sleep(self.between_call_seconds)
                continue

            inserted = 0
            for paper_dc in result.papers:
                try:
                    if self.persistence.save_paper(paper_dc, db):
                        inserted += 1
                except Exception as e:
                    logger.warning("PubMed IVD save_paper 실패 (title=%s): %s",
                                   (paper_dc.title or "")[:60], e)
            try:
                db.commit()
            except Exception as e:
                logger.warning("PubMed IVD commit 실패: %s", e)
                db.rollback()

            out.append(PubmedIvdCollectResult(
                query=q, fetched=len(result.papers), inserted=inserted,
            ))
            # E-utilities rate limit
            time.sleep(self.between_call_seconds)

        return out
