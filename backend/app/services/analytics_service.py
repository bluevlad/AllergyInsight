"""분석 집계 서비스

Module A: 임상 트렌드 분석
- 월별 알러젠 양성률 집계
- 동반 양성 패턴 분석
"""
import logging
from datetime import date, datetime
from collections import Counter
from typing import Optional

from sqlalchemy.orm import Session
from sqlalchemy import func, extract

from ..database.models import UserDiagnosis
from ..database.analytics_models import AnalyticsSnapshot

logger = logging.getLogger(__name__)


class AnalyticsService:
    """임상 트렌드 분석 서비스"""

    def aggregate_monthly(self, db: Session, year: int, month: int) -> dict:
        """월별 알러젠 양성률 집계

        Args:
            db: DB 세션
            year: 집계 연도
            month: 집계 월

        Returns:
            집계 결과 요약
        """
        snapshot_date = date(year, month, 1)

        # 해당 월의 진단 데이터 조회
        diagnoses = db.query(UserDiagnosis).filter(
            extract('year', UserDiagnosis.diagnosis_date) == year,
            extract('month', UserDiagnosis.diagnosis_date) == month,
        ).all()

        if not diagnoses:
            logger.info(f"No diagnoses found for {year}-{month:02d}")
            return {"period": f"{year}-{month:02d}", "total_diagnoses": 0, "allergens_processed": 0}

        # 알러젠별 집계
        allergen_stats = {}  # {allergen_code: {grades: [], cooccurrences: Counter}}

        for diag in diagnoses:
            results = diag.results or {}
            positive_allergens = [k for k, v in results.items() if isinstance(v, (int, float)) and v >= 1]

            for allergen_code, grade in results.items():
                if not isinstance(grade, (int, float)):
                    continue

                if allergen_code not in allergen_stats:
                    allergen_stats[allergen_code] = {
                        "grades": [],
                        "cooccurrences": Counter(),
                    }

                allergen_stats[allergen_code]["grades"].append(int(grade))

                # 동반 양성 패턴 (현재 알러젠이 양성일 때)
                if grade >= 1:
                    for other in positive_allergens:
                        if other != allergen_code:
                            allergen_stats[allergen_code]["cooccurrences"][other] += 1

        # 기존 스냅샷 삭제 (upsert)
        db.query(AnalyticsSnapshot).filter(
            AnalyticsSnapshot.snapshot_date == snapshot_date,
            AnalyticsSnapshot.period_type == "monthly",
        ).delete()

        # 알러젠별 스냅샷 생성
        created_count = 0
        for allergen_code, stats in allergen_stats.items():
            grades = stats["grades"]
            total_tests = len(grades)
            positive_count = sum(1 for g in grades if g >= 1)
            positive_rate = positive_count / total_tests if total_tests > 0 else 0.0
            avg_grade = sum(grades) / total_tests if total_tests > 0 else 0.0

            # 등급 분포
            grade_dist = {}
            for g in range(7):  # 0-6
                grade_dist[str(g)] = sum(1 for x in grades if x == g)

            # 동반 양성 Top 5
            cooccurrence_total = sum(1 for g in grades if g >= 1)
            cooccurrence_top5 = []
            if cooccurrence_total > 0:
                for other_allergen, count in stats["cooccurrences"].most_common(5):
                    cooccurrence_top5.append({
                        "allergen": other_allergen,
                        "count": count,
                        "rate": round(count / cooccurrence_total, 4),
                    })

            snapshot = AnalyticsSnapshot(
                snapshot_date=snapshot_date,
                period_type="monthly",
                allergen_code=allergen_code,
                total_tests=total_tests,
                positive_count=positive_count,
                positive_rate=round(positive_rate, 4),
                avg_grade=round(avg_grade, 2),
                grade_distribution=grade_dist,
                cooccurrence_top5=cooccurrence_top5,
            )
            db.add(snapshot)
            created_count += 1

        db.commit()
        logger.info(f"Monthly aggregation completed: {year}-{month:02d}, {created_count} allergens processed")

        return {
            "period": f"{year}-{month:02d}",
            "total_diagnoses": len(diagnoses),
            "allergens_processed": created_count,
        }

    def aggregate_all_months(self, db: Session) -> list[dict]:
        """모든 미집계 월에 대해 집계 실행"""
        # 가장 오래된 진단 날짜 조회
        oldest = db.query(func.min(UserDiagnosis.diagnosis_date)).scalar()
        if not oldest:
            return []

        results = []
        current = date(oldest.year, oldest.month, 1)
        today = date.today()

        while current < today:
            result = self.aggregate_monthly(db, current.year, current.month)
            if result["total_diagnoses"] > 0:
                results.append(result)

            # 다음 달로 이동
            if current.month == 12:
                current = date(current.year + 1, 1, 1)
            else:
                current = date(current.year, current.month + 1, 1)

        return results

    def get_allergen_trend(
        self,
        db: Session,
        allergen_code: str,
        period_type: str = "monthly",
        limit: int = 12,
    ) -> list[dict]:
        """특정 알러젠의 트렌드 조회"""
        snapshots = db.query(AnalyticsSnapshot).filter(
            AnalyticsSnapshot.allergen_code == allergen_code,
            AnalyticsSnapshot.period_type == period_type,
        ).order_by(
            AnalyticsSnapshot.snapshot_date.desc()
        ).limit(limit).all()

        return [
            {
                "period": s.snapshot_date.isoformat(),
                "total_tests": s.total_tests,
                "positive_count": s.positive_count,
                "positive_rate": s.positive_rate,
                "avg_grade": s.avg_grade,
                "grade_distribution": s.grade_distribution,
                "cooccurrence_top5": s.cooccurrence_top5,
            }
            for s in reversed(snapshots)
        ]

    def get_overview(self, db: Session) -> dict:
        """최근 월별 집계 개요"""
        # 가장 최근 스냅샷 날짜
        latest_date = db.query(func.max(AnalyticsSnapshot.snapshot_date)).filter(
            AnalyticsSnapshot.period_type == "monthly"
        ).scalar()

        if not latest_date:
            return {"latest_period": None, "allergens": []}

        snapshots = db.query(AnalyticsSnapshot).filter(
            AnalyticsSnapshot.snapshot_date == latest_date,
            AnalyticsSnapshot.period_type == "monthly",
        ).order_by(
            AnalyticsSnapshot.positive_rate.desc()
        ).all()

        return {
            "latest_period": latest_date.isoformat(),
            "total_allergens": len(snapshots),
            "total_tests": sum(s.total_tests for s in snapshots),
            "allergens": [
                {
                    "allergen_code": s.allergen_code,
                    "total_tests": s.total_tests,
                    "positive_rate": s.positive_rate,
                    "avg_grade": s.avg_grade,
                    "cooccurrence_top5": s.cooccurrence_top5,
                }
                for s in snapshots
            ],
        }
