"""치료법 엔티티 추출 및 트렌드 분석 서비스

Phase 2: 논문 abstract에서 치료법을 LLM으로 추출하고 연도별 트렌드를 집계.
- OllamaService.extract_treatments() 활용
- 로컬 LLM 우선, Gemini fallback
- TreatmentEntity → TreatmentTrend 집계
"""
import logging
from collections import Counter
from typing import Optional

from sqlalchemy.orm import Session
from sqlalchemy import func

from ..database.models import Paper, PaperAllergenLink
from ..database.analytics_models import TreatmentEntity, TreatmentTrend

logger = logging.getLogger(__name__)


class TreatmentExtractionService:
    """치료법 추출 및 트렌드 서비스"""

    # LLM이 한국어로 반환하는 알러젠 코드를 영문 코드로 매핑
    ALLERGEN_KR_MAP = {
        "땅콩": "peanut", "우유": "milk", "계란": "egg", "달걀": "egg",
        "밀": "wheat", "대두": "soy", "콩": "soy", "생선": "fish",
        "새우": "shrimp", "게": "crab", "복숭아": "peach", "호두": "walnut",
        "참깨": "sesame", "메밀": "buckwheat", "토마토": "tomato",
        "돼지고기": "pork", "닭고기": "chicken", "소고기": "beef",
        "집먼지진드기": "dust_mite", "개": "dog", "고양이": "cat",
        "곰팡이": "mold", "꽃가루": "pollen", "잔디": "grass",
        "미지정": "general", "일반": "general", "전반": "general",
    }

    def _normalize_allergen_code(self, code: str, fallback: str = "general") -> str:
        """알러젠 코드 정규화 (한국어 → 영문 코드)"""
        if not code:
            return fallback
        # 이미 영문 코드면 그대로
        from .ollama_service import OllamaService
        if code in OllamaService.KNOWN_ALLERGENS:
            return code
        # 한국어 매핑
        return self.ALLERGEN_KR_MAP.get(code, fallback)

    def extract_from_papers(
        self,
        db: Session,
        limit: int = 100,
        skip_extracted: bool = True,
    ) -> dict:
        """미처리 논문에서 치료법 엔티티를 배치 추출

        Args:
            db: DB 세션
            limit: 처리할 논문 수
            skip_extracted: 이미 추출된 논문 건너뛰기
        """
        from .ollama_service import get_ollama_service
        ollama = get_ollama_service()

        # 추출 대상 논문 조회 (abstract가 있고, management/treatment 관련 링크가 있는 논문 우선)
        query = (
            db.query(Paper)
            .filter(Paper.abstract.isnot(None), Paper.abstract != "")
        )

        if skip_extracted:
            already_extracted = db.query(TreatmentEntity.paper_id).distinct()
            query = query.filter(~Paper.id.in_(already_extracted))

        # management 링크가 있는 논문 우선 정렬
        papers = query.order_by(Paper.year.desc().nullslast()).limit(limit).all()

        if not papers:
            logger.info("No papers to process for treatment extraction")
            return {"processed": 0, "extracted": 0, "skipped": 0}

        # 논문별 알러젠 코드 매핑 (빈번한 알러젠 힌트 제공용)
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
        skipped = 0

        for paper in papers:
            try:
                allergen_hint = ""
                if paper.id in paper_allergens:
                    allergen_hint = paper_allergens[paper.id][0]

                treatments = ollama.extract_treatments(
                    title=paper.title or "",
                    abstract=paper.abstract or "",
                    allergen_code=allergen_hint,
                )

                if not treatments:
                    skipped += 1
                    processed += 1
                    continue

                for t in treatments:
                    # 알러젠 코드 결정: LLM 추출값 > 힌트값 (한국어 보정)
                    raw_code = t.get("allergen", "") or allergen_hint or "general"
                    allergen_code = self._normalize_allergen_code(raw_code, allergen_hint or "general")

                    # 중복 확인
                    existing = db.query(TreatmentEntity).filter(
                        TreatmentEntity.treatment_name == t["name"],
                        TreatmentEntity.allergen_code == allergen_code,
                        TreatmentEntity.paper_id == paper.id,
                    ).first()

                    if existing:
                        continue

                    entity = TreatmentEntity(
                        treatment_name=t["name"],
                        treatment_name_kr=t.get("name_kr", ""),
                        treatment_type=t["type"],
                        allergen_code=allergen_code,
                        paper_id=paper.id,
                        year=paper.year,
                        evidence_level=t.get("evidence_level"),
                        source_text=t.get("source_text", ""),
                        confidence=t.get("confidence", 0.5),
                    )
                    db.add(entity)
                    extracted += 1

                processed += 1

                # 50건마다 중간 커밋
                if processed % 50 == 0:
                    db.commit()
                    logger.info(f"Treatment extraction progress: {processed}/{len(papers)}, extracted={extracted}")

            except Exception as e:
                logger.warning(f"Treatment extraction failed for paper {paper.id}: {e}")
                skipped += 1
                processed += 1

        db.commit()
        logger.info(
            f"Treatment extraction completed: processed={processed}, "
            f"extracted={extracted}, skipped={skipped}"
        )

        return {
            "processed": processed,
            "extracted": extracted,
            "skipped": skipped,
        }

    def aggregate_trends(self, db: Session) -> dict:
        """TreatmentEntity에서 연도별 TreatmentTrend 집계"""
        # 치료법별 연도별 논문 수
        rows = (
            db.query(
                TreatmentEntity.treatment_name,
                TreatmentEntity.treatment_type,
                TreatmentEntity.year,
                func.count(func.distinct(TreatmentEntity.paper_id)).label("paper_count"),
                func.avg(TreatmentEntity.confidence).label("avg_confidence"),
            )
            .filter(TreatmentEntity.year.isnot(None))
            .group_by(
                TreatmentEntity.treatment_name,
                TreatmentEntity.treatment_type,
                TreatmentEntity.year,
            )
            .all()
        )

        if not rows:
            return {"trends_created": 0}

        # 치료법별 관련 알러젠
        allergen_rows = (
            db.query(
                TreatmentEntity.treatment_name,
                TreatmentEntity.allergen_code,
                func.count(TreatmentEntity.id),
            )
            .group_by(TreatmentEntity.treatment_name, TreatmentEntity.allergen_code)
            .all()
        )
        allergen_map = {}
        for name, code, cnt in allergen_rows:
            allergen_map.setdefault(name, Counter())[code] = cnt

        # 치료법별 최초 언급 연도
        first_year_rows = (
            db.query(
                TreatmentEntity.treatment_name,
                func.min(TreatmentEntity.year),
            )
            .group_by(TreatmentEntity.treatment_name)
            .all()
        )
        first_year_map = {name: yr for name, yr in first_year_rows}

        # 기존 트렌드 전체 삭제 (재집계)
        db.query(TreatmentTrend).delete()

        # 전년도 데이터 구축 (트렌드 방향 계산용)
        year_data = {}  # {(name, year): paper_count}
        for row in rows:
            year_data[(row.treatment_name, row.year)] = row.paper_count

        created = 0
        for row in rows:
            name = row.treatment_name
            year = row.year
            paper_count = row.paper_count

            # 트렌드 방향 계산
            prev_count = year_data.get((name, year - 1))
            if prev_count is not None and prev_count > 0:
                change_rate = round(((paper_count - prev_count) / prev_count) * 100, 1)
                if change_rate > 20:
                    direction = "rising"
                elif change_rate < -20:
                    direction = "declining"
                else:
                    direction = "stable"
            else:
                change_rate = None
                direction = "new" if paper_count > 0 else None

            # 관련 알러젠 상위 5개
            counter = allergen_map.get(name, Counter())
            related = [
                {"code": code, "count": cnt}
                for code, cnt in counter.most_common(5)
            ]

            trend = TreatmentTrend(
                treatment_name=name,
                treatment_type=row.treatment_type,
                year=year,
                paper_count=paper_count,
                first_mentioned_year=first_year_map.get(name),
                related_allergens=related,
                avg_confidence=round(float(row.avg_confidence or 0), 2),
                trend_direction=direction,
                change_rate=change_rate,
            )
            db.add(trend)
            created += 1

        db.commit()
        logger.info(f"Treatment trend aggregation completed: {created} trends created")

        return {"trends_created": created}

    def get_treatments_by_allergen(
        self,
        db: Session,
        allergen_code: str,
        period: str = "yearly",
        limit: int = 20,
    ) -> dict:
        """특정 알러젠의 치료법 트렌드"""
        # 해당 알러젠 관련 치료법 목록
        treatment_names = (
            db.query(TreatmentEntity.treatment_name)
            .filter(TreatmentEntity.allergen_code == allergen_code)
            .distinct()
            .all()
        )
        names = [n[0] for n in treatment_names]

        if not names:
            return {"allergen_code": allergen_code, "treatments": []}

        # 치료법별 트렌드
        trends = (
            db.query(TreatmentTrend)
            .filter(TreatmentTrend.treatment_name.in_(names))
            .order_by(TreatmentTrend.year.desc(), TreatmentTrend.paper_count.desc())
            .limit(limit * len(names))
            .all()
        )

        # 치료법별 그룹핑
        grouped = {}
        for t in trends:
            if t.treatment_name not in grouped:
                grouped[t.treatment_name] = {
                    "treatment_name": t.treatment_name,
                    "treatment_type": t.treatment_type,
                    "first_mentioned_year": t.first_mentioned_year,
                    "yearly": [],
                }
            grouped[t.treatment_name]["yearly"].append({
                "year": t.year,
                "paper_count": t.paper_count,
                "trend_direction": t.trend_direction,
                "change_rate": t.change_rate,
                "avg_confidence": t.avg_confidence,
            })

        # yearly 정렬
        for data in grouped.values():
            data["yearly"].sort(key=lambda x: x["year"])

        return {
            "allergen_code": allergen_code,
            "total_treatments": len(grouped),
            "treatments": list(grouped.values()),
        }

    def get_emerging_treatments(self, db: Session, limit: int = 10) -> dict:
        """최근 등장한 치료법 (최근 3년 내 first_mentioned)"""
        latest_year = db.query(func.max(TreatmentTrend.year)).scalar()
        if not latest_year:
            return {"treatments": []}

        cutoff_year = latest_year - 2

        trends = (
            db.query(TreatmentTrend)
            .filter(
                TreatmentTrend.first_mentioned_year >= cutoff_year,
                TreatmentTrend.year == latest_year,
            )
            .order_by(TreatmentTrend.paper_count.desc())
            .limit(limit)
            .all()
        )

        return {
            "latest_year": latest_year,
            "cutoff_year": cutoff_year,
            "treatments": [
                {
                    "treatment_name": t.treatment_name,
                    "treatment_type": t.treatment_type,
                    "first_mentioned_year": t.first_mentioned_year,
                    "paper_count": t.paper_count,
                    "related_allergens": t.related_allergens,
                    "trend_direction": t.trend_direction,
                    "avg_confidence": t.avg_confidence,
                }
                for t in trends
            ],
        }

    def get_overview(self, db: Session) -> dict:
        """치료법 트렌드 개요"""
        latest_year = db.query(func.max(TreatmentTrend.year)).scalar()
        if not latest_year:
            return {"latest_year": None, "summary": {}}

        trends = db.query(TreatmentTrend).filter(
            TreatmentTrend.year == latest_year,
        ).order_by(TreatmentTrend.paper_count.desc()).all()

        # 유형별 집계
        by_type = Counter()
        for t in trends:
            by_type[t.treatment_type] += 1

        rising = [t for t in trends if t.trend_direction == "rising"]

        total_entities = db.query(func.count(TreatmentEntity.id)).scalar() or 0
        total_papers = db.query(func.count(func.distinct(TreatmentEntity.paper_id))).scalar() or 0

        return {
            "latest_year": latest_year,
            "total_treatments": len(trends),
            "total_entities": total_entities,
            "total_papers_with_treatments": total_papers,
            "by_type": dict(by_type),
            "rising_treatments": [
                {
                    "treatment_name": t.treatment_name,
                    "treatment_type": t.treatment_type,
                    "paper_count": t.paper_count,
                    "change_rate": t.change_rate,
                    "related_allergens": t.related_allergens,
                }
                for t in rising[:10]
            ],
            "top_treatments": [
                {
                    "treatment_name": t.treatment_name,
                    "treatment_type": t.treatment_type,
                    "paper_count": t.paper_count,
                    "trend_direction": t.trend_direction,
                }
                for t in trends[:15]
            ],
        }
