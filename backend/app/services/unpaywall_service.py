"""Unpaywall PDF URL 보강 서비스

DOI를 사용하여 무료 PDF URL을 조회합니다.
기존 논문의 pdf_url이 없는 경우 Unpaywall API로 보강합니다.

API: https://api.unpaywall.org/v2/{doi}?email={email}
Rate limit: 초당 10회
비용: 무료 (이메일 주소만 필요)
"""
import logging
import time
from typing import Optional

import httpx

from ..config import settings

logger = logging.getLogger(__name__)

_API_BASE = "https://api.unpaywall.org/v2"


class UnpaywallService:
    """Unpaywall PDF URL 조회 서비스"""

    def __init__(self, email: Optional[str] = None):
        self.email = email or settings.PUBMED_EMAIL or "allergyinsight@example.com"
        self._client: Optional[httpx.Client] = None

    def _get_client(self) -> httpx.Client:
        if self._client is None:
            self._client = httpx.Client(timeout=10.0)
        return self._client

    def get_pdf_url(self, doi: str) -> Optional[str]:
        """DOI로 무료 PDF URL 조회

        Args:
            doi: 논문 DOI (예: "10.1016/j.jaci.2020.01.012")

        Returns:
            PDF URL 또는 None
        """
        if not doi:
            return None

        client = self._get_client()
        try:
            resp = client.get(
                f"{_API_BASE}/{doi}",
                params={"email": self.email},
            )
            if resp.status_code != 200:
                return None

            data = resp.json()
            best_oa = data.get("best_oa_location")
            if best_oa:
                return best_oa.get("url_for_pdf") or best_oa.get("url")

            # best_oa가 없으면 다른 OA location 확인
            for loc in data.get("oa_locations", []):
                pdf = loc.get("url_for_pdf")
                if pdf:
                    return pdf

        except Exception as e:
            logger.warning(f"Unpaywall 조회 실패 (DOI: {doi}): {e}")

        return None

    def enrich_papers(self, db, batch_size: int = 50) -> dict:
        """pdf_url이 없는 논문에 대해 Unpaywall로 PDF URL 보강

        Args:
            db: SQLAlchemy 세션
            batch_size: 한 번에 처리할 논문 수

        Returns:
            {"checked": int, "enriched": int, "failed": int}
        """
        from ..database.models import Paper as PaperORM

        # pdf_url이 없고 DOI가 있는 논문 조회
        papers = (
            db.query(PaperORM)
            .filter(PaperORM.doi.isnot(None))
            .filter(PaperORM.doi != "")
            .filter(
                (PaperORM.pdf_url.is_(None)) | (PaperORM.pdf_url == "")
            )
            .order_by(PaperORM.created_at.desc())
            .limit(batch_size)
            .all()
        )

        if not papers:
            return {"checked": 0, "enriched": 0, "failed": 0}

        logger.info(f"[Unpaywall] {len(papers)}건 PDF URL 보강 시작")

        enriched = 0
        failed = 0

        for paper in papers:
            pdf_url = self.get_pdf_url(paper.doi)
            if pdf_url:
                paper.pdf_url = pdf_url
                enriched += 1
            else:
                failed += 1

            # Rate limit: 초당 10회 → 0.12초 간격
            time.sleep(0.12)

        db.commit()
        logger.info(f"[Unpaywall] 완료: {enriched}/{len(papers)}건 PDF URL 확보")

        return {"checked": len(papers), "enriched": enriched, "failed": failed}

    def close(self):
        """리소스 정리"""
        if self._client:
            self._client.close()
            self._client = None
