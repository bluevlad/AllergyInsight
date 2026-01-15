"""배치 프로세서 테스트

실행 방법:
    cd C:\GIT\AllergyInsight\backend
    python tests/test_batch_processor.py
"""
import sys
import os
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.services import (
    BatchProcessor,
    AllergenItem,
    create_allergen_items,
    ProgressiveLoader,
    SmartLoader,
    LoadingStrategy,
)
from app.services.batch_processor import ProcessingStatus


def test_batch_processor_basic():
    """배치 프로세서 기본 테스트"""
    print("\n" + "=" * 60)
    print("테스트 1: 배치 프로세서 기본 동작")
    print("=" * 60)

    processor = BatchProcessor(batch_size=2, delay_between_batches=1.0)

    # 테스트용 알러지 항원
    allergens = [
        AllergenItem(name="peanut", grade=3, priority=100),
        AllergenItem(name="milk", grade=2, priority=80),
        AllergenItem(name="egg", grade=1, priority=75),
        AllergenItem(name="wheat", grade=2, priority=70),
    ]

    # 작업 생성
    job = processor.create_job(allergens, sort_by_priority=True)

    print(f"\n작업 ID: {job.job_id}")
    print(f"총 태스크: {job.total_count}개")

    # 진행 콜백 설정
    def on_progress(job):
        status = job.get_status_summary()
        print(f"  진행: {status['completed']}/{status['total']} "
              f"({status['progress_percent']:.1f}%)")

    processor.set_progress_callback(on_progress)

    # 동기 처리
    print("\n처리 시작...")
    start_time = time.time()
    processor.process_job_sync(job, include_cross_reactivity=False)
    elapsed = time.time() - start_time

    print(f"\n처리 완료! (소요 시간: {elapsed:.1f}초)")
    print(f"상태: {job.get_status_summary()}")

    # 결과 확인
    results = processor.get_completed_results(job)
    print(f"\n결과 ({len(results)}개):")
    for r in results:
        print(f"  - {r['allergen']}: {r['total_found']}개 논문, 캐시: {r['from_cache']}")

    processor.close()
    return job


def test_priority_sorting():
    """우선순위 정렬 테스트"""
    print("\n" + "=" * 60)
    print("테스트 2: 우선순위 기반 정렬")
    print("=" * 60)

    # 등급이 다른 알러지 항원
    allergen_names = ["wheat", "peanut", "milk", "soy", "egg"]
    grades = {
        "wheat": 1,
        "peanut": 4,  # 높은 등급
        "milk": 2,
        "soy": 1,
        "egg": 3,
    }

    allergens = create_allergen_items(allergen_names, grades)

    print("\n정렬 전:")
    for a in allergens:
        print(f"  {a.name}: 등급={a.grade}, 우선순위={a.priority}")

    # 정렬
    sorted_allergens = sorted(allergens, key=lambda x: (-x.priority, -x.grade))

    print("\n정렬 후 (우선순위 + 등급 내림차순):")
    for a in sorted_allergens:
        print(f"  {a.name}: 등급={a.grade}, 우선순위={a.priority}")


def test_caching():
    """캐싱 테스트"""
    print("\n" + "=" * 60)
    print("테스트 3: 캐싱 동작")
    print("=" * 60)

    processor = BatchProcessor(cache_ttl_hours=1)

    # 첫 번째 검색
    allergens = [AllergenItem(name="peanut", grade=3, priority=100)]
    job1 = processor.create_job(allergens)

    print("\n첫 번째 검색...")
    start = time.time()
    processor.process_job_sync(job1, include_cross_reactivity=False)
    elapsed1 = time.time() - start
    print(f"  소요 시간: {elapsed1:.2f}초")
    print(f"  상태: {job1.tasks[0].status.value}")

    # 두 번째 검색 (캐시 히트 예상)
    allergens2 = [AllergenItem(name="peanut", grade=3, priority=100)]
    job2 = processor.create_job(allergens2)

    print("\n두 번째 검색 (캐시)...")
    start = time.time()
    processor.process_job_sync(job2, include_cross_reactivity=False)
    elapsed2 = time.time() - start
    print(f"  소요 시간: {elapsed2:.2f}초")
    print(f"  상태: {job2.tasks[0].status.value}")

    # 캐시 통계
    stats = processor.cache.get_stats()
    print(f"\n캐시 통계: {stats}")

    processor.close()


def test_progressive_loader():
    """점진적 로더 테스트"""
    print("\n" + "=" * 60)
    print("테스트 4: 점진적 로딩")
    print("=" * 60)

    loader = ProgressiveLoader()

    allergens = [
        AllergenItem(name="peanut", grade=4, priority=100),
        AllergenItem(name="milk", grade=3, priority=80),
        AllergenItem(name="egg", grade=2, priority=75),
        AllergenItem(name="wheat", grade=2, priority=70),
        AllergenItem(name="soy", grade=1, priority=65),
        AllergenItem(name="fish", grade=1, priority=85),
    ]

    print(f"\n총 {len(allergens)}개 항원")
    print("우선순위 상위 3개 먼저 로딩, 나머지 백그라운드 처리...")

    # 우선순위 먼저 로딩
    priority_results, bg_job_id = loader.load_priority_first(
        allergens,
        priority_count=3,
        include_cross_reactivity=False,
    )

    print(f"\n즉시 반환된 결과 ({len(priority_results)}개):")
    for r in priority_results:
        print(f"  - {r['allergen']}: {r['total_found']}개 논문")

    if bg_job_id:
        print(f"\n백그라운드 작업 ID: {bg_job_id}")

        # 백그라운드 진행 상태 모니터링
        print("백그라운드 처리 대기...")
        for _ in range(10):
            time.sleep(1)
            results = loader.get_partial_results(bg_job_id)
            progress = loader.loader.processor.get_job_status(bg_job_id)
            if progress:
                print(f"  진행: {progress['completed']}/{progress['total']}")
                if progress['is_completed']:
                    break

        # 최종 결과
        all_results = loader.get_partial_results(bg_job_id)
        print(f"\n최종 결과 ({len(all_results)}개):")
        for r in all_results:
            print(f"  - {r['allergen']}: {r['total_found']}개")

    loader.close()


def test_smart_loader():
    """스마트 로더 테스트"""
    print("\n" + "=" * 60)
    print("테스트 5: 스마트 로더 (자동 전략 선택)")
    print("=" * 60)

    loader = SmartLoader()

    # 소규모 테스트 (IMMEDIATE 전략)
    print("\n[소규모: 3개 항원]")
    result1 = loader.load(
        ["peanut", "milk", "egg"],
        grades={"peanut": 3, "milk": 2, "egg": 1},
        include_cross_reactivity=False,
    )
    print(f"  전략: {result1.strategy_used.value}")
    print(f"  즉시 로딩: {result1.loaded_count}개")

    # 중규모 테스트 (PRIORITY_FIRST 전략)
    print("\n[중규모: 10개 항원]")
    result2 = loader.load(
        ["peanut", "milk", "egg", "wheat", "soy",
         "fish", "shellfish", "tree nut", "sesame", "mustard"],
        include_cross_reactivity=False,
    )
    print(f"  전략: {result2.strategy_used.value}")
    print(f"  즉시 로딩: {result2.loaded_count}개")
    print(f"  백그라운드 작업: {result2.background_job_id or '없음'}")

    # 백그라운드 작업 완료 대기
    if result2.background_job_id:
        print("  백그라운드 처리 대기...")
        for _ in range(15):
            time.sleep(1)
            progress = loader.get_progress(result2.background_job_id)
            if progress and progress['is_completed']:
                print(f"  완료! 총 {progress['completed']}개 처리됨")
                break

    loader.close()


def test_loading_strategy_selection():
    """로딩 전략 선택 테스트"""
    print("\n" + "=" * 60)
    print("테스트 6: 로딩 전략 자동 선택")
    print("=" * 60)

    from app.services.progressive_loader import select_loading_strategy

    test_cases = [
        (1, "1개 항원"),
        (5, "5개 항원"),
        (10, "10개 항원"),
        (20, "20개 항원"),
        (50, "50개 항원"),
        (120, "120개 항원 (최대)"),
    ]

    print("\n항원 수별 권장 전략:")
    print("-" * 40)
    for count, desc in test_cases:
        strategy = select_loading_strategy(count)
        print(f"  {desc:<20} → {strategy.value}")


if __name__ == "__main__":
    print("=" * 60)
    print("AllergyInsight 배치 프로세서 테스트")
    print("=" * 60)

    try:
        # 1. 기본 동작 테스트
        test_batch_processor_basic()

        # 2. 우선순위 정렬 테스트
        test_priority_sorting()

        # 3. 캐싱 테스트
        test_caching()

        # 4. 점진적 로더 테스트
        test_progressive_loader()

        # 5. 스마트 로더 테스트
        test_smart_loader()

        # 6. 전략 선택 테스트
        test_loading_strategy_selection()

        print("\n" + "=" * 60)
        print("모든 테스트 완료!")
        print("=" * 60)

    except Exception as e:
        print(f"\n오류 발생: {e}")
        import traceback
        traceback.print_exc()
