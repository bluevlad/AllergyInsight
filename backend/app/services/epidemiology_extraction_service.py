"""역학 데이터 추출 서비스

Phase 4: 논문 abstract에서 유병률/발병률/환자 수를 추출.
- 1차: 정규식으로 역학 수치 포함 논문 선별
- 2차: LLM으로 구조화된 데이터 추출
- 품질 검증: 비현실적 수치 필터링 + confidence_score
"""
import re
import logging
from typing import Optional

from sqlalchemy.orm import Session
from sqlalchemy import func

from ..database.models import Paper, PaperAllergenLink
from ..database.analytics_models import EpidemiologyData

logger = logging.getLogger(__name__)

# 역학 수치 포함 여부를 판단하는 정규식 패턴
EPIDEMIOLOGY_PATTERNS = [
    re.compile(r'\bprevalence\b', re.IGNORECASE),
    re.compile(r'\bincidence\b', re.IGNORECASE),
    re.compile(r'\bsensitiz(?:ation|ed)\b', re.IGNORECASE),
    re.compile(r'\b\d+\.?\d*\s*%', re.IGNORECASE),  # 숫자+%
    re.compile(r'\bper\s+\d+[,.]?\d*\b', re.IGNORECASE),  # per 100,000
    re.compile(r'\bepidemiolog', re.IGNORECASE),
    re.compile(r'\b유병률\b'),
    re.compile(r'\b발병률\b'),
    re.compile(r'\b감작률\b'),
]

# 비현실적 수치 검증 임계값
VALIDATION_RULES = {
    "prevalence": {"max": 50.0, "unit": "%"},       # 유병률 50% 초과 비현실적
    "incidence": {"max": 30.0, "unit": "%"},         # 발병률 30% 초과 비현실적
    "sensitization_rate": {"max": 80.0, "unit": "%"},  # 감작률 80% 초과 비현실적
    "patient_count": {"max": 1_000_000_000, "unit": "count"},  # 10억 명 초과 비현실적
}


class EpidemiologyExtractionService:
    """역학 데이터 추출 및 조회 서비스"""

    def _has_epidemiology_content(self, text: str) -> bool:
        """정규식으로 역학 수치 포함 여부 판단 (1차 필터)"""
        match_count = sum(1 for p in EPIDEMIOLOGY_PATTERNS if p.search(text))
        return match_count >= 2  # 2개 이상 패턴 매칭 시 역학 관련으로 판단

    def _validate_value(self, data_type: str, value: float, unit: str) -> bool:
        """비현실적 수치 필터링"""
        rule = VALIDATION_RULES.get(data_type)
        if not rule:
            return True
        if value > rule["max"]:
            return False
        if value < 0:
            return False
        return True

    def extract_from_papers(
        self,
        db: Session,
        limit: int = 50,
        skip_extracted: bool = True,
    ) -> dict:
        """미처리 논문에서 역학 데이터를 배치 추출

        1차: 정규식으로 역학 관련 abstract 선별
        2차: LLM으로 구조화된 데이터 추출
        """
        from .ollama_service import get_ollama_service
        ollama = get_ollama_service()

        # 대상 논문 조회
        query = db.query(Paper).filter(
            Paper.abstract.isnot(None),
            Paper.abstract != "",
        )

        if skip_extracted:
            already_extracted = db.query(EpidemiologyData.paper_id).distinct()
            query = query.filter(~Paper.id.in_(already_extracted))

        papers = query.order_by(Paper.year.desc().nullslast()).limit(limit * 3).all()

        if not papers:
            return {"processed": 0, "extracted": 0, "filtered": 0, "skipped": 0}

        # 논문별 알러젠 코드 매핑
        paper_ids = [p.id for p in papers]
        allergen_links = (
            db.query(PaperAllergenLink.paper_id, PaperAllergenLink.allergen_code)
            .filter(PaperAllergenLink.paper_id.in_(paper_ids))
            .all()
        )
        paper_allergens = {}
        for pid, code in allergen_links:
            paper_allergens.setdefault(pid, []).append(code)

        processed = 0
        extracted = 0
        filtered = 0  # 정규식 필터로 제외된 수
        skipped = 0

        for paper in papers:
            if processed >= limit:
                break

            # 1차: 정규식 필터
            text = f"{paper.title or ''} {paper.abstract or ''}"
            if not self._has_epidemiology_content(text):
                filtered += 1
                continue

            try:
                allergen_hint = ""
                if paper.id in paper_allergens:
                    allergen_hint = paper_allergens[paper.id][0]

                items = ollama.extract_epidemiology(
                    title=paper.title or "",
                    abstract=paper.abstract or "",
                    allergen_code=allergen_hint,
                )

                if not items:
                    skipped += 1
                    processed += 1
                    continue

                for item in items:
                    # 알러젠 코드 정규화
                    from .treatment_extraction_service import TreatmentExtractionService
                    normalizer = TreatmentExtractionService()
                    allergen_code = normalizer._normalize_allergen_code(
                        item.get("allergen", "") or allergen_hint,
                        allergen_hint or "general",
                    )

                    # 수치 검증
                    if not self._validate_value(
                        item["data_type"], item["value"], item.get("unit", "%")
                    ):
                        logger.debug(
                            f"Unrealistic value filtered: {item['data_type']}={item['value']} "
                            f"(paper {paper.id})"
                        )
                        continue

                    # 중복 확인
                    existing = db.query(EpidemiologyData).filter(
                        EpidemiologyData.allergen_code == allergen_code,
                        EpidemiologyData.paper_id == paper.id,
                        EpidemiologyData.data_type == item["data_type"],
                        EpidemiologyData.value == item["value"],
                    ).first()

                    if existing:
                        continue

                    # sample_size 정수 변환
                    sample_size = item.get("sample_size")
                    if sample_size is not None:
                        try:
                            sample_size = int(sample_size)
                        except (ValueError, TypeError):
                            sample_size = None

                    entity = EpidemiologyData(
                        allergen_code=allergen_code,
                        paper_id=paper.id,
                        year=paper.year,
                        region=item.get("region", "") or "",
                        data_type=item["data_type"],
                        value=item["value"],
                        unit=item.get("unit", "%"),
                        sample_size=sample_size,
                        age_group=item.get("age_group", "") or "",
                        source_text=item.get("source_text", ""),
                        confidence_score=item.get("confidence", 0.5),
                    )
                    db.add(entity)
                    extracted += 1

                processed += 1

                if processed % 30 == 0:
                    db.commit()
                    logger.info(
                        f"Epidemiology extraction progress: {processed}/{limit}, "
                        f"extracted={extracted}"
                    )

            except Exception as e:
                logger.warning(f"Epidemiology extraction failed for paper {paper.id}: {e}")
                skipped += 1
                processed += 1

        db.commit()
        logger.info(
            f"Epidemiology extraction completed: processed={processed}, "
            f"extracted={extracted}, filtered={filtered}, skipped={skipped}"
        )

        return {
            "processed": processed,
            "extracted": extracted,
            "filtered_by_regex": filtered,
            "skipped": skipped,
        }

    def get_by_allergen(
        self,
        db: Session,
        allergen_code: str,
        data_type: Optional[str] = None,
    ) -> dict:
        """특정 알러젠의 역학 데이터 조회 (연도별 추이)"""
        query = db.query(EpidemiologyData).filter(
            EpidemiologyData.allergen_code == allergen_code,
        )
        if data_type:
            query = query.filter(EpidemiologyData.data_type == data_type)

        rows = query.order_by(
            EpidemiologyData.year.asc().nullslast(),
        ).all()

        # data_type별 그룹핑
        by_type = {}
        for r in rows:
            if r.data_type not in by_type:
                by_type[r.data_type] = []
            by_type[r.data_type].append({
                "year": r.year,
                "value": r.value,
                "unit": r.unit,
                "region": r.region,
                "sample_size": r.sample_size,
                "age_group": r.age_group,
                "confidence_score": r.confidence_score,
                "is_verified": r.is_verified,
            })

        return {
            "allergen_code": allergen_code,
            "total_records": len(rows),
            "disclaimer": "본 데이터는 논문 abstract에서 자동 추출된 것으로 의료 조언이 아닙니다.",
            "by_type": by_type,
        }

    def get_overview(self, db: Session) -> dict:
        """역학 데이터 전체 개요"""
        total = db.query(func.count(EpidemiologyData.id)).scalar() or 0
        total_papers = db.query(
            func.count(func.distinct(EpidemiologyData.paper_id))
        ).scalar() or 0

        # 유형별 분포
        type_rows = (
            db.query(EpidemiologyData.data_type, func.count(EpidemiologyData.id))
            .group_by(EpidemiologyData.data_type)
            .all()
        )

        # 알러젠별 상위
        allergen_rows = (
            db.query(
                EpidemiologyData.allergen_code,
                func.count(EpidemiologyData.id).label("count"),
            )
            .group_by(EpidemiologyData.allergen_code)
            .order_by(func.count(EpidemiologyData.id).desc())
            .limit(15)
            .all()
        )

        # 검증 현황
        verified = db.query(func.count(EpidemiologyData.id)).filter(
            EpidemiologyData.is_verified == True,
        ).scalar() or 0

        return {
            "total_records": total,
            "total_papers": total_papers,
            "verified_count": verified,
            "unverified_count": total - verified,
            "disclaimer": "본 데이터는 논문 abstract에서 자동 추출된 것으로 의료 조언이 아닙니다.",
            "by_type": {dt: cnt for dt, cnt in type_rows},
            "top_allergens": [
                {"allergen_code": code, "record_count": cnt}
                for code, cnt in allergen_rows
            ],
        }
