"""배치 프로세서 - 단계적 논문 검색 시스템

알러지 검사 결과(최대 120개 항원)에 대해 논문을 단계적으로 검색합니다.

## 처리 전략

1. **우선순위 기반 처리**
   - 양성 등급이 높은 항원부터 처리
   - 임상적 중요도에 따른 우선순위

2. **배치 단위 처리**
   - 한 번에 5-10개 항원씩 처리
   - API Rate Limit 준수

3. **캐싱 활용**
   - 이미 검색한 항원은 캐시에서 반환
   - TTL 기반 캐시 만료

4. **비동기 처리**
   - 백그라운드에서 점진적 처리
   - 실시간 진행 상태 제공
"""
import asyncio
import time
import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional, Callable
from pathlib import Path
from collections import defaultdict
import threading
from queue import PriorityQueue

from ..models.paper import Paper, PaperSource
from .paper_search_service import PaperSearchService, UnifiedSearchResult


class ProcessingStatus(str, Enum):
    """처리 상태"""
    PENDING = "pending"          # 대기 중
    IN_PROGRESS = "in_progress"  # 처리 중
    COMPLETED = "completed"      # 완료
    FAILED = "failed"            # 실패
    CACHED = "cached"            # 캐시에서 반환


@dataclass
class AllergenItem:
    """알러지 항원 항목"""
    name: str                    # 항원 이름 (예: "peanut", "milk")
    name_kr: str = ""            # 한글 이름 (예: "땅콩", "우유")
    grade: int = 0               # 양성 등급 (0-6, 높을수록 심함)
    priority: int = 0            # 처리 우선순위 (높을수록 먼저)
    category: str = ""           # 카테고리 (food, inhalant, etc.)

    def __lt__(self, other):
        """우선순위 비교 (PriorityQueue용)"""
        return self.priority > other.priority  # 높은 우선순위 먼저


@dataclass
class SearchTask:
    """검색 작업"""
    task_id: str
    allergen: AllergenItem
    status: ProcessingStatus = ProcessingStatus.PENDING
    result: Optional[UnifiedSearchResult] = None
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    retry_count: int = 0

    @property
    def duration_ms(self) -> float:
        """처리 소요 시간 (ms)"""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds() * 1000
        return 0


@dataclass
class BatchJob:
    """배치 작업"""
    job_id: str
    tasks: list[SearchTask]
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    @property
    def total_count(self) -> int:
        return len(self.tasks)

    @property
    def completed_count(self) -> int:
        return sum(1 for t in self.tasks
                   if t.status in [ProcessingStatus.COMPLETED, ProcessingStatus.CACHED])

    @property
    def failed_count(self) -> int:
        return sum(1 for t in self.tasks if t.status == ProcessingStatus.FAILED)

    @property
    def progress_percent(self) -> float:
        if self.total_count == 0:
            return 100.0
        return (self.completed_count / self.total_count) * 100

    @property
    def is_completed(self) -> bool:
        return all(t.status in [ProcessingStatus.COMPLETED,
                                ProcessingStatus.CACHED,
                                ProcessingStatus.FAILED]
                   for t in self.tasks)

    def get_status_summary(self) -> dict:
        """상태 요약"""
        return {
            "job_id": self.job_id,
            "total": self.total_count,
            "completed": self.completed_count,
            "failed": self.failed_count,
            "in_progress": sum(1 for t in self.tasks
                              if t.status == ProcessingStatus.IN_PROGRESS),
            "pending": sum(1 for t in self.tasks
                          if t.status == ProcessingStatus.PENDING),
            "cached": sum(1 for t in self.tasks
                         if t.status == ProcessingStatus.CACHED),
            "progress_percent": round(self.progress_percent, 1),
            "is_completed": self.is_completed,
        }

    def to_dict(self) -> dict:
        """딕셔너리로 변환"""
        return {
            "job_id": self.job_id,
            "status": self.get_status_summary(),
            "tasks": [
                {
                    "task_id": t.task_id,
                    "allergen": t.allergen.name,
                    "allergen_kr": t.allergen.name_kr,
                    "grade": t.allergen.grade,
                    "status": t.status.value,
                    "paper_count": len(t.result.papers) if t.result else 0,
                    "error": t.error,
                    "duration_ms": t.duration_ms,
                }
                for t in self.tasks
            ],
            "created_at": self.created_at.isoformat(),
        }


class SimpleCache:
    """간단한 메모리 캐시 (TTL 지원)"""

    def __init__(self, ttl_hours: int = 24):
        self._cache: dict[str, tuple[datetime, any]] = {}
        self._ttl = timedelta(hours=ttl_hours)
        self._lock = threading.Lock()

    def _make_key(self, allergen: str, include_cross: bool) -> str:
        """캐시 키 생성"""
        return f"{allergen.lower()}:{include_cross}"

    def get(self, allergen: str, include_cross: bool = True) -> Optional[UnifiedSearchResult]:
        """캐시에서 조회"""
        key = self._make_key(allergen, include_cross)
        with self._lock:
            if key in self._cache:
                cached_at, result = self._cache[key]
                if datetime.now() - cached_at < self._ttl:
                    return result
                else:
                    # 만료된 캐시 삭제
                    del self._cache[key]
        return None

    def set(self, allergen: str, include_cross: bool, result: UnifiedSearchResult):
        """캐시에 저장"""
        key = self._make_key(allergen, include_cross)
        with self._lock:
            self._cache[key] = (datetime.now(), result)

    def clear(self):
        """캐시 전체 삭제"""
        with self._lock:
            self._cache.clear()

    def get_stats(self) -> dict:
        """캐시 통계"""
        with self._lock:
            valid_count = sum(1 for cached_at, _ in self._cache.values()
                             if datetime.now() - cached_at < self._ttl)
            return {
                "total_entries": len(self._cache),
                "valid_entries": valid_count,
                "ttl_hours": self._ttl.total_seconds() / 3600,
            }


class BatchProcessor:
    """배치 프로세서 - 단계적 논문 검색"""

    # 기본 설정
    DEFAULT_BATCH_SIZE = 5           # 한 번에 처리할 항원 수
    DEFAULT_DELAY_BETWEEN_BATCHES = 2.0  # 배치 간 대기 시간 (초)
    DEFAULT_MAX_RETRIES = 2          # 최대 재시도 횟수
    DEFAULT_RESULTS_PER_ALLERGEN = 10  # 항원당 검색 결과 수

    def __init__(
        self,
        search_service: Optional[PaperSearchService] = None,
        cache_ttl_hours: int = 24,
        batch_size: int = DEFAULT_BATCH_SIZE,
        delay_between_batches: float = DEFAULT_DELAY_BETWEEN_BATCHES,
    ):
        self.search_service = search_service or PaperSearchService()
        self.cache = SimpleCache(ttl_hours=cache_ttl_hours)
        self.batch_size = batch_size
        self.delay_between_batches = delay_between_batches

        # 작업 저장소
        self._jobs: dict[str, BatchJob] = {}
        self._lock = threading.Lock()

        # 콜백
        self._progress_callback: Optional[Callable[[BatchJob], None]] = None

    def set_progress_callback(self, callback: Callable[[BatchJob], None]):
        """진행 상황 콜백 설정"""
        self._progress_callback = callback

    def _generate_job_id(self) -> str:
        """작업 ID 생성"""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        random_part = hashlib.md5(str(time.time()).encode()).hexdigest()[:6]
        return f"job_{timestamp}_{random_part}"

    def _generate_task_id(self, allergen: str) -> str:
        """태스크 ID 생성"""
        return f"task_{allergen.lower()}_{int(time.time() * 1000)}"

    def create_job(
        self,
        allergens: list[AllergenItem],
        sort_by_priority: bool = True,
    ) -> BatchJob:
        """
        배치 작업 생성

        Args:
            allergens: 알러지 항원 목록
            sort_by_priority: 우선순위로 정렬 여부

        Returns:
            BatchJob: 생성된 배치 작업
        """
        # 우선순위 정렬
        if sort_by_priority:
            allergens = sorted(allergens, key=lambda x: (-x.priority, -x.grade))

        # 태스크 생성
        tasks = [
            SearchTask(
                task_id=self._generate_task_id(a.name),
                allergen=a,
            )
            for a in allergens
        ]

        # 작업 생성
        job = BatchJob(
            job_id=self._generate_job_id(),
            tasks=tasks,
        )

        with self._lock:
            self._jobs[job.job_id] = job

        return job

    def process_job_sync(
        self,
        job: BatchJob,
        include_cross_reactivity: bool = True,
        max_results_per_allergen: int = DEFAULT_RESULTS_PER_ALLERGEN,
    ) -> BatchJob:
        """
        배치 작업 동기 처리 (블로킹)

        Args:
            job: 배치 작업
            include_cross_reactivity: 교차 반응 포함 여부
            max_results_per_allergen: 항원당 최대 결과 수

        Returns:
            BatchJob: 완료된 배치 작업
        """
        job.started_at = datetime.now()

        # 배치 단위로 처리
        for i in range(0, len(job.tasks), self.batch_size):
            batch = job.tasks[i:i + self.batch_size]

            for task in batch:
                self._process_single_task(
                    task,
                    include_cross_reactivity,
                    max_results_per_allergen,
                )

            # 콜백 호출
            if self._progress_callback:
                self._progress_callback(job)

            # 배치 간 대기 (Rate Limit 방지)
            if i + self.batch_size < len(job.tasks):
                time.sleep(self.delay_between_batches)

        job.completed_at = datetime.now()
        return job

    def _process_single_task(
        self,
        task: SearchTask,
        include_cross_reactivity: bool,
        max_results: int,
    ):
        """단일 태스크 처리"""
        task.started_at = datetime.now()
        task.status = ProcessingStatus.IN_PROGRESS

        allergen_name = task.allergen.name

        # 1. 캐시 확인
        cached = self.cache.get(allergen_name, include_cross_reactivity)
        if cached:
            task.result = cached
            task.status = ProcessingStatus.CACHED
            task.completed_at = datetime.now()
            return

        # 2. API 검색
        try:
            result = self.search_service.search_allergy(
                allergen=allergen_name,
                include_cross_reactivity=include_cross_reactivity,
                max_results_per_source=max_results,
            )

            task.result = result
            task.status = ProcessingStatus.COMPLETED
            task.completed_at = datetime.now()

            # 캐시에 저장
            self.cache.set(allergen_name, include_cross_reactivity, result)

        except Exception as e:
            task.error = str(e)
            task.retry_count += 1

            # 재시도
            if task.retry_count < self.DEFAULT_MAX_RETRIES:
                time.sleep(1)  # 잠시 대기 후 재시도
                self._process_single_task(task, include_cross_reactivity, max_results)
            else:
                task.status = ProcessingStatus.FAILED
                task.completed_at = datetime.now()

    async def process_job_async(
        self,
        job: BatchJob,
        include_cross_reactivity: bool = True,
        max_results_per_allergen: int = DEFAULT_RESULTS_PER_ALLERGEN,
    ) -> BatchJob:
        """
        배치 작업 비동기 처리

        Args:
            job: 배치 작업
            include_cross_reactivity: 교차 반응 포함 여부
            max_results_per_allergen: 항원당 최대 결과 수

        Returns:
            BatchJob: 완료된 배치 작업
        """
        job.started_at = datetime.now()

        # 배치 단위로 비동기 처리
        for i in range(0, len(job.tasks), self.batch_size):
            batch = job.tasks[i:i + self.batch_size]

            # 배치 내 태스크 동시 처리
            await asyncio.gather(*[
                self._process_single_task_async(
                    task,
                    include_cross_reactivity,
                    max_results_per_allergen,
                )
                for task in batch
            ])

            # 콜백 호출
            if self._progress_callback:
                self._progress_callback(job)

            # 배치 간 대기
            if i + self.batch_size < len(job.tasks):
                await asyncio.sleep(self.delay_between_batches)

        job.completed_at = datetime.now()
        return job

    async def _process_single_task_async(
        self,
        task: SearchTask,
        include_cross_reactivity: bool,
        max_results: int,
    ):
        """단일 태스크 비동기 처리"""
        # 동기 처리를 스레드풀에서 실행
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            self._process_single_task,
            task,
            include_cross_reactivity,
            max_results,
        )

    def get_job(self, job_id: str) -> Optional[BatchJob]:
        """작업 조회"""
        with self._lock:
            return self._jobs.get(job_id)

    def get_job_status(self, job_id: str) -> Optional[dict]:
        """작업 상태 조회"""
        job = self.get_job(job_id)
        if job:
            return job.get_status_summary()
        return None

    def get_completed_results(self, job: BatchJob) -> list[dict]:
        """완료된 결과만 반환"""
        results = []
        for task in job.tasks:
            if task.status in [ProcessingStatus.COMPLETED, ProcessingStatus.CACHED]:
                results.append({
                    "allergen": task.allergen.name,
                    "allergen_kr": task.allergen.name_kr,
                    "grade": task.allergen.grade,
                    "papers": [p.to_dict() for p in task.result.papers] if task.result else [],
                    "total_found": task.result.total_unique if task.result else 0,
                    "from_cache": task.status == ProcessingStatus.CACHED,
                })
        return results

    def close(self):
        """리소스 정리"""
        self.search_service.close()


# 알러지 항원 우선순위 매핑 (임상적 중요도 기반)
ALLERGEN_PRIORITIES = {
    # 식품 알러지 - 높은 우선순위 (아나필락시스 위험)
    "peanut": 100,
    "tree nut": 95,
    "shellfish": 90,
    "fish": 85,
    "milk": 80,
    "egg": 75,
    "wheat": 70,
    "soy": 65,
    "sesame": 60,

    # 흡입성 알러지 - 중간 우선순위
    "dust mite": 50,
    "cat": 45,
    "dog": 45,
    "mold": 40,
    "pollen": 35,
    "grass": 35,

    # 기타 - 낮은 우선순위
    "latex": 30,
    "insect": 25,
}


def create_allergen_items(
    allergen_names: list[str],
    grades: Optional[dict[str, int]] = None,
) -> list[AllergenItem]:
    """
    알러지 항원 목록에서 AllergenItem 생성

    Args:
        allergen_names: 항원 이름 목록
        grades: 항원별 양성 등급 딕셔너리

    Returns:
        list[AllergenItem]: 항원 아이템 목록
    """
    grades = grades or {}

    items = []
    for name in allergen_names:
        grade = grades.get(name, 0)
        priority = ALLERGEN_PRIORITIES.get(name.lower(), 10)

        # 등급에 따른 우선순위 보정 (높은 등급 = 높은 우선순위)
        adjusted_priority = priority + (grade * 5)

        items.append(AllergenItem(
            name=name,
            grade=grade,
            priority=adjusted_priority,
        ))

    return items
