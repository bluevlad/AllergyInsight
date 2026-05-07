"""임상 함의(clinical_implication) 추출 서비스 — B2a

논문 abstract → 의료진 대상 한국어 1~2문장 임상 함의를 LLM 으로 추출하여
`Paper.clinical_implication` 컬럼에 저장한다.

- 단일 추출: extract_for_paper(db, paper_id)
- 배치 백필: extract_from_papers(db, limit, skip_extracted=True)
- LLM: OllamaService 사용 (Gemini 우선, 로컬 LLM fallback). 추출 정책은
  OllamaService.extract_clinical_implication 가 담당 — 본 서비스는 영속화·
  스케줄링 책임만.

주의: 의료 조언 아님. 외부 노출 시 면책 동반 권장.
"""
from __future__ import annotations

import logging
from typing import Optional

from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from ..database.models import Paper
from .ollama_service import get_ollama_service

logger = logging.getLogger(__name__)


class ClinicalImplicationService:
    """clinical_implication 추출 + 영속화."""

    def extract_for_paper(self, db: Session, paper_id: int) -> Optional[str]:
        """단일 논문 추출 + 저장.

        Returns:
            저장된 implication 문자열, 또는 None (abstract 부재/너무 짧음/LLM 실패).
        """
        paper = db.query(Paper).filter(Paper.id == paper_id).first()
        if not paper:
            return None
        if not paper.abstract:
            return None

        ollama = get_ollama_service()
        result = ollama.extract_clinical_implication(
            title=paper.title or "", abstract=paper.abstract
        )
        if not result:
            return None

        paper.clinical_implication = result
        db.commit()
        logger.info(
            "clinical_implication: paper_id=%d 저장 (len=%d)",
            paper.id, len(result),
        )
        return result

    def extract_from_papers(
        self,
        db: Session,
        limit: int = 50,
        skip_extracted: bool = True,
    ) -> dict:
        """배치 추출.

        Args:
            db: DB 세션.
            limit: 최대 처리 논문 수 (운영 비용 가드).
            skip_extracted: True 면 이미 clinical_implication 이 있는 논문 제외.

        Returns:
            {processed, extracted, skipped, errors}
        """
        query = (
            db.query(Paper)
            .filter(
                Paper.abstract.isnot(None),
                Paper.abstract != "",
            )
        )
        if skip_extracted:
            query = query.filter(
                or_(
                    Paper.clinical_implication.is_(None),
                    Paper.clinical_implication == "",
                )
            )
        # 최신 논문 우선
        papers = (
            query.order_by(Paper.year.desc().nullslast(), Paper.id.desc())
            .limit(limit)
            .all()
        )

        if not papers:
            logger.info("clinical_implication: 처리할 논문 없음")
            return {"processed": 0, "extracted": 0, "skipped": 0, "errors": 0}

        ollama = get_ollama_service()
        processed = 0
        extracted = 0
        skipped = 0
        errors = 0

        for paper in papers:
            processed += 1
            try:
                result = ollama.extract_clinical_implication(
                    title=paper.title or "", abstract=paper.abstract or ""
                )
                if result:
                    paper.clinical_implication = result
                    extracted += 1
                else:
                    skipped += 1
            except Exception as e:
                logger.warning(
                    "clinical_implication: paper_id=%d 추출 예외: %s",
                    paper.id, e,
                )
                errors += 1

        db.commit()
        logger.info(
            "clinical_implication 배치: processed=%d, extracted=%d, "
            "skipped=%d, errors=%d",
            processed, extracted, skipped, errors,
        )
        return {
            "processed": processed,
            "extracted": extracted,
            "skipped": skipped,
            "errors": errors,
        }


_singleton: Optional[ClinicalImplicationService] = None


def get_clinical_implication_service() -> ClinicalImplicationService:
    """프로세스 싱글턴 인스턴스 반환."""
    global _singleton
    if _singleton is None:
        _singleton = ClinicalImplicationService()
    return _singleton
