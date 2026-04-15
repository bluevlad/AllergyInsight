"""분석 집계 수동 실행 스크립트

알러젠 양성률 집계 + 키워드 트렌드 추출을 즉시 실행합니다.

사용법:
    cd backend
    python -m scripts.run_analytics_aggregation
"""
import sys
import os

# backend 디렉토리를 path에 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database.connection import SessionLocal
from app.services.analytics_service import AnalyticsService
from app.services.keyword_trend_service import KeywordTrendService


def main():
    db = SessionLocal()
    try:
        analytics_svc = AnalyticsService()
        keyword_svc = KeywordTrendService()

        # 1) 알러젠 양성률 집계
        print("=" * 60)
        print("[1/2] 알러젠 양성률 월별 집계 시작...")
        agg_results = analytics_svc.aggregate_all_months(db)
        if agg_results:
            for r in agg_results:
                print(f"  {r['period']}: 진단 {r['total_diagnoses']}건, 알러젠 {r['allergens_processed']}종")
            print(f"  → 총 {len(agg_results)}개월 집계 완료")
        else:
            print("  → 집계할 진단 데이터가 없습니다.")

        # 2) 키워드 트렌드 추출
        print()
        print("[2/2] 키워드 트렌드 추출 시작...")
        kw_results = keyword_svc.extract_all_months(db)
        if kw_results:
            for r in kw_results:
                print(f"  {r['period']}: 뉴스 {r['total_news']}건, 키워드 {r['keywords_extracted']}개")
            print(f"  → 총 {len(kw_results)}개월 추출 완료")
        else:
            print("  → 추출할 뉴스 데이터가 없습니다.")

        print()
        print("=" * 60)
        print("집계 완료!")

    except Exception as e:
        print(f"오류 발생: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
