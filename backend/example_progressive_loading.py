"""점진적 로딩 예제

이 스크립트는 대량의 알러지 항원(최대 120개)에 대해
논문을 단계적으로 검색하는 방법을 보여줍니다.

## 시나리오

환자의 알러지 검사 결과:
- 120개 항원 중 30개 양성
- 각 항원별 등급 (Class 0-6)

## 처리 전략

1. 등급이 높은 항원 (Class 4-6) → 즉시 검색 후 반환
2. 중간 등급 (Class 2-3) → 백그라운드에서 처리
3. 낮은 등급 (Class 0-1) → 사용자 요청 시 검색

실행 방법:
    cd C:\GIT\AllergyInsight\backend
    pip install -r requirements.txt
    python example_progressive_loading.py
"""
import time
import json
from app.services import (
    SmartLoader,
    ProgressiveLoader,
    AllergenItem,
    create_allergen_items,
    LoadingStrategy,
)


def example_1_smart_loading():
    """예제 1: 스마트 로딩 (자동 전략 선택)"""
    print("\n" + "=" * 60)
    print("예제 1: 스마트 로딩")
    print("=" * 60)

    loader = SmartLoader()

    # 환자의 양성 알러지 항목 (예시)
    positive_allergens = [
        "peanut", "milk", "egg", "wheat", "soy",
        "shrimp", "crab", "salmon", "cod",
        "almond", "walnut", "cashew",
    ]

    # 등급 정보 (높을수록 심함)
    grades = {
        "peanut": 5,   # 심각
        "shrimp": 4,   # 심각
        "milk": 3,
        "egg": 3,
        "crab": 3,
        "wheat": 2,
        "soy": 2,
        "salmon": 2,
        "cod": 1,
        "almond": 1,
        "walnut": 1,
        "cashew": 1,
    }

    print(f"\n환자 양성 항원: {len(positive_allergens)}개")
    print(f"고등급 (4-5): {sum(1 for g in grades.values() if g >= 4)}개")
    print(f"중등급 (2-3): {sum(1 for g in grades.values() if 2 <= g <= 3)}개")
    print(f"저등급 (0-1): {sum(1 for g in grades.values() if g <= 1)}개")

    # 스마트 로딩 실행
    print("\n스마트 로딩 시작...")
    start_time = time.time()

    result = loader.load(
        positive_allergens,
        grades=grades,
        include_cross_reactivity=False,  # 빠른 테스트용
    )

    elapsed = time.time() - start_time

    print(f"\n선택된 전략: {result.strategy_used.value}")
    print(f"즉시 반환: {result.loaded_count}개 항원")
    print(f"소요 시간: {elapsed:.1f}초")

    print("\n즉시 반환된 결과 (고우선순위):")
    for r in result.immediate_results:
        grade = grades.get(r['allergen'], 0)
        print(f"  - {r['allergen']} (등급 {grade}): {r['total_found']}개 논문")

    # 백그라운드 작업이 있으면 완료 대기
    if result.background_job_id:
        print(f"\n백그라운드 작업 진행 중... (ID: {result.background_job_id})")

        for _ in range(30):  # 최대 30초 대기
            time.sleep(1)
            progress = loader.get_progress(result.background_job_id)
            if progress:
                pct = progress['progress_percent']
                print(f"  진행: {progress['completed']}/{progress['total']} ({pct:.0f}%)")
                if progress['is_completed']:
                    break

        # 전체 결과 조회
        all_results = loader.get_results(result.background_job_id)
        print(f"\n전체 결과: {len(all_results)}개 항원")

    loader.close()


def example_2_priority_first_loading():
    """예제 2: 우선순위 먼저 로딩"""
    print("\n" + "=" * 60)
    print("예제 2: 우선순위 기반 점진적 로딩")
    print("=" * 60)

    loader = ProgressiveLoader()

    # 알러지 항원 생성 (우선순위 직접 지정)
    allergens = [
        # 고위험 식품 알러지 (아나필락시스 위험)
        AllergenItem(name="peanut", name_kr="땅콩", grade=5, priority=100),
        AllergenItem(name="tree nut", name_kr="견과류", grade=4, priority=95),
        AllergenItem(name="shellfish", name_kr="갑각류", grade=4, priority=90),

        # 일반 식품 알러지
        AllergenItem(name="milk", name_kr="우유", grade=3, priority=80),
        AllergenItem(name="egg", name_kr="계란", grade=3, priority=75),
        AllergenItem(name="wheat", name_kr="밀", grade=2, priority=70),
        AllergenItem(name="soy", name_kr="대두", grade=2, priority=65),
        AllergenItem(name="fish", name_kr="생선", grade=2, priority=60),

        # 흡입성 알러지
        AllergenItem(name="dust mite", name_kr="집먼지진드기", grade=3, priority=50),
        AllergenItem(name="cat", name_kr="고양이", grade=2, priority=45),
    ]

    print(f"\n총 {len(allergens)}개 항원")

    # 상위 3개 즉시 로딩
    print("\n[1단계] 고위험 항원 즉시 검색...")
    priority_results, bg_job_id = loader.load_priority_first(
        allergens,
        priority_count=3,
        include_cross_reactivity=False,
    )

    print("\n즉시 반환된 결과:")
    for r in priority_results:
        print(f"  ★ {r['allergen']}: {r['total_found']}개 논문 발견")

    # 백그라운드 진행 모니터링
    if bg_job_id:
        print(f"\n[2단계] 나머지 항원 백그라운드 처리...")

        completed_count = len(priority_results)
        while True:
            time.sleep(2)
            partial = loader.get_partial_results(bg_job_id)

            new_results = [r for r in partial if r['allergen'] not in
                          [p['allergen'] for p in priority_results]]

            if len(partial) > completed_count:
                for r in new_results[completed_count - len(priority_results):]:
                    print(f"  + {r['allergen']}: {r['total_found']}개 논문 (백그라운드)")
                completed_count = len(partial)

            # 진행 상태 확인
            job = loader.loader.processor.get_job(bg_job_id)
            if job and job.is_completed:
                break

        print("\n[완료] 모든 항원 처리 완료!")

    loader.close()


def example_3_on_demand_loading():
    """예제 3: 온디맨드 로딩 (사용자 요청 시)"""
    print("\n" + "=" * 60)
    print("예제 3: 온디맨드 로딩")
    print("=" * 60)

    loader = ProgressiveLoader()

    print("\n시나리오: 사용자가 특정 항원 클릭 시 상세 정보 로딩")

    # 사용자가 선택한 항원
    selected_allergens = ["peanut", "milk", "dust mite"]

    for allergen_name in selected_allergens:
        print(f"\n사용자가 '{allergen_name}' 클릭...")

        allergen = AllergenItem(name=allergen_name, grade=3, priority=50)
        result = loader.load_on_demand(allergen, include_cross_reactivity=False)

        if result:
            print(f"  → {result['total_found']}개 논문 발견")
            if result['papers']:
                paper = result['papers'][0]
                print(f"     첫 번째 논문: {paper['title'][:50]}...")
        else:
            print("  → 검색 실패")

    # 캐시 상태 확인
    stats = loader.get_cache_stats()
    print(f"\n캐시 상태: {stats}")

    loader.close()


def example_4_large_scale_loading():
    """예제 4: 대규모 로딩 (120개 항원)"""
    print("\n" + "=" * 60)
    print("예제 4: 대규모 로딩 시뮬레이션")
    print("=" * 60)

    # 120개 알러지 항원 생성 (실제 검사 패널)
    allergen_panel = [
        # 식품 (60개)
        "peanut", "tree nut", "walnut", "almond", "cashew", "pistachio",
        "milk", "casein", "whey", "egg white", "egg yolk",
        "wheat", "gluten", "rye", "barley", "oat",
        "soy", "soybean",
        "shrimp", "crab", "lobster", "clam", "oyster", "mussel",
        "salmon", "tuna", "cod", "mackerel", "sardine",
        "beef", "pork", "chicken", "lamb",
        "tomato", "potato", "carrot", "celery", "onion",
        "apple", "peach", "cherry", "strawberry", "banana", "kiwi",
        "orange", "lemon", "grape",
        "sesame", "mustard", "corn",

        # 흡입성 (40개)
        "dust mite", "house dust", "storage mite",
        "cat", "dog", "horse", "rabbit", "hamster",
        "cockroach", "moth",
        "grass pollen", "tree pollen", "weed pollen",
        "ragweed", "birch", "oak", "cedar", "pine",
        "mold", "aspergillus", "alternaria", "cladosporium", "penicillium",
        "latex",

        # 기타
        "bee venom", "wasp venom", "fire ant",
        "nickel", "cobalt", "chromium",
    ]

    # 랜덤 등급 생성 (실제로는 검사 결과에서 가져옴)
    import random
    random.seed(42)
    grades = {a: random.randint(0, 6) for a in allergen_panel}

    # 양성만 필터 (등급 1 이상)
    positive_allergens = [a for a in allergen_panel if grades[a] >= 1]

    print(f"\n총 검사 항원: {len(allergen_panel)}개")
    print(f"양성 항원: {len(positive_allergens)}개")

    # 등급별 분포
    grade_dist = {}
    for g in range(7):
        count = sum(1 for a in positive_allergens if grades[a] == g)
        if count > 0:
            grade_dist[g] = count

    print(f"등급 분포: {grade_dist}")

    # 스마트 로딩 (실제 API 호출은 하지 않음 - 시뮬레이션)
    print("\n[시뮬레이션] 스마트 로딩 전략 선택...")

    from app.services.progressive_loader import select_loading_strategy
    strategy = select_loading_strategy(len(positive_allergens))
    print(f"선택된 전략: {strategy.value}")

    # 예상 시간 계산
    avg_time_per_allergen = 2.0  # 초
    total_time = len(positive_allergens) * avg_time_per_allergen

    print(f"\n예상 처리 시간:")
    print(f"  - 전체 순차 처리: {total_time:.0f}초 ({total_time/60:.1f}분)")
    print(f"  - 배치 처리 (5개씩): {total_time/2:.0f}초 (병렬화)")
    print(f"  - 우선순위 먼저 (상위 5개): ~10초 후 첫 결과")

    # 고등급 항원 식별
    high_grade = [a for a in positive_allergens if grades[a] >= 4]
    print(f"\n고등급 항원 (즉시 처리 대상): {high_grade}")


def example_5_real_workflow():
    """예제 5: 실제 워크플로우 시뮬레이션"""
    print("\n" + "=" * 60)
    print("예제 5: 실제 워크플로우")
    print("=" * 60)

    print("""
    실제 서비스 워크플로우:

    1. 사용자가 알러지 검사 결과 업로드
       └─ 120개 항원 중 양성 항목 추출

    2. 시스템이 로딩 전략 자동 선택
       ├─ 5개 이하: 즉시 전체 로딩
       ├─ 6-20개: 우선순위 먼저 + 백그라운드
       └─ 21개 이상: 최상위 3개만 + 백그라운드

    3. 프론트엔드 동작
       ├─ 즉시: 고위험 항원 결과 표시
       ├─ 프로그레스 바로 진행 상태 표시
       └─ 백그라운드 완료 시 알림

    4. 사용자 인터랙션
       ├─ 특정 항원 클릭 → 온디맨드 상세 로딩
       ├─ 교차 반응 정보 요청 → 추가 검색
       └─ PDF 다운로드 요청 → 논문 전문 다운로드

    5. 캐싱 활용
       ├─ 같은 항원 재검색 시 캐시 히트
       └─ 24시간 TTL로 신선도 유지
    """)

    # 간단한 데모
    print("\n[데모] 실제 워크플로우 실행...")

    loader = SmartLoader()

    # 테스트 데이터
    test_allergens = ["peanut", "milk", "egg", "wheat", "soy"]
    test_grades = {"peanut": 5, "milk": 3, "egg": 2, "wheat": 1, "soy": 1}

    print(f"\n입력: {test_allergens}")
    print(f"등급: {test_grades}")

    result = loader.load(
        test_allergens,
        grades=test_grades,
        include_cross_reactivity=False,
    )

    print(f"\n출력:")
    print(f"  - 전략: {result.strategy_used.value}")
    print(f"  - 즉시 로딩: {result.loaded_count}개")
    print(f"  - 백그라운드: {'있음' if result.background_job_id else '없음'}")

    # 결과 샘플
    if result.immediate_results:
        print(f"\n첫 번째 결과 (고우선순위):")
        first = result.immediate_results[0]
        print(f"  항원: {first['allergen']}")
        print(f"  논문 수: {first['total_found']}")
        if first['papers']:
            print(f"  첫 논문: {first['papers'][0]['title'][:60]}...")

    loader.close()


if __name__ == "__main__":
    print("=" * 60)
    print("AllergyInsight 점진적 로딩 예제")
    print("=" * 60)

    try:
        # 예제 선택
        print("\n실행할 예제를 선택하세요:")
        print("1. 스마트 로딩 (자동 전략)")
        print("2. 우선순위 기반 로딩")
        print("3. 온디맨드 로딩")
        print("4. 대규모 로딩 시뮬레이션")
        print("5. 실제 워크플로우")
        print("0. 전체 실행")

        choice = input("\n선택 (0-5): ").strip() or "0"

        if choice == "0":
            example_1_smart_loading()
            example_2_priority_first_loading()
            example_3_on_demand_loading()
            example_4_large_scale_loading()
            example_5_real_workflow()
        elif choice == "1":
            example_1_smart_loading()
        elif choice == "2":
            example_2_priority_first_loading()
        elif choice == "3":
            example_3_on_demand_loading()
        elif choice == "4":
            example_4_large_scale_loading()
        elif choice == "5":
            example_5_real_workflow()

        print("\n" + "=" * 60)
        print("예제 완료!")
        print("=" * 60)

    except KeyboardInterrupt:
        print("\n\n사용자에 의해 중단됨")
    except Exception as e:
        print(f"\n오류 발생: {e}")
        import traceback
        traceback.print_exc()
