"""점진적 로더 - 사용자 인터랙션 기반 단계적 로딩

사용자가 먼저 필요한 정보부터 보여주고,
나머지는 백그라운드에서 점진적으로 로딩합니다.

## 전략

1. **즉시 응답 (Instant Response)**
   - 캐시된 결과 즉시 반환
   - 가장 중요한 항원 3-5개 우선 처리

2. **점진적 로딩 (Progressive Loading)**
   - 나머지 항원은 백그라운드에서 처리
   - SSE/WebSocket으로 실시간 업데이트

3. **온디맨드 로딩 (On-Demand Loading)**
   - 사용자가 특정 항원 클릭 시 상세 정보 로딩
   - Lazy Loading 패턴
"""
import asyncio
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Callable, AsyncGenerator, Generator
from enum import Enum
from queue import Queue
import json

from .batch_processor import (
    BatchProcessor,
    BatchJob,
    AllergenItem,
    SearchTask,
    ProcessingStatus,
    create_allergen_items,
)
from .paper_search_service import UnifiedSearchResult


class LoadingStrategy(str, Enum):
    """로딩 전략"""
    IMMEDIATE = "immediate"      # 즉시 전체 로딩 (소규모용)
    PRIORITY_FIRST = "priority_first"  # 우선순위 높은 것 먼저
    ON_DEMAND = "on_demand"      # 요청 시 로딩
    BACKGROUND = "background"    # 백그라운드 전체 로딩


@dataclass
class LoadingProgress:
    """로딩 진행 상태"""
    job_id: str
    total: int
    loaded: int
    cached: int
    failed: int
    current_allergen: Optional[str] = None
    estimated_remaining_seconds: float = 0

    @property
    def percent(self) -> float:
        if self.total == 0:
            return 100.0
        return ((self.loaded + self.cached) / self.total) * 100

    @property
    def is_complete(self) -> bool:
        return (self.loaded + self.cached + self.failed) >= self.total

    def to_dict(self) -> dict:
        return {
            "job_id": self.job_id,
            "total": self.total,
            "loaded": self.loaded,
            "cached": self.cached,
            "failed": self.failed,
            "percent": round(self.percent, 1),
            "is_complete": self.is_complete,
            "current_allergen": self.current_allergen,
            "estimated_remaining_seconds": round(self.estimated_remaining_seconds, 1),
        }


class ProgressiveLoader:
    """점진적 로더"""

    # 기본 설정
    PRIORITY_BATCH_SIZE = 5     # 우선순위 배치 크기
    BACKGROUND_BATCH_SIZE = 3   # 백그라운드 배치 크기
    AVG_SEARCH_TIME_SEC = 2.0   # 평균 검색 시간 (추정용)

    def __init__(
        self,
        batch_processor: Optional[BatchProcessor] = None,
    ):
        self.processor = batch_processor or BatchProcessor()

        # 이벤트 큐 (SSE용)
        self._event_queues: dict[str, Queue] = {}
        self._background_jobs: dict[str, threading.Thread] = {}

    def load_immediate(
        self,
        allergens: list[AllergenItem],
        include_cross_reactivity: bool = True,
    ) -> tuple[BatchJob, list[dict]]:
        """
        즉시 로딩 (동기, 소규모용)

        10개 이하의 항원에 적합합니다.

        Args:
            allergens: 알러지 항원 목록
            include_cross_reactivity: 교차 반응 포함

        Returns:
            (BatchJob, 결과 목록)
        """
        job = self.processor.create_job(allergens, sort_by_priority=True)
        self.processor.process_job_sync(
            job,
            include_cross_reactivity=include_cross_reactivity,
        )

        results = self.processor.get_completed_results(job)
        return job, results

    def load_priority_first(
        self,
        allergens: list[AllergenItem],
        priority_count: int = 5,
        include_cross_reactivity: bool = True,
    ) -> tuple[list[dict], str]:
        """
        우선순위 높은 항원 먼저 로딩

        상위 N개는 즉시 반환하고, 나머지는 백그라운드에서 처리합니다.

        Args:
            allergens: 알러지 항원 목록
            priority_count: 우선 처리할 항원 수
            include_cross_reactivity: 교차 반응 포함

        Returns:
            (우선 결과 목록, 백그라운드 작업 ID)
        """
        # 우선순위 정렬
        sorted_allergens = sorted(allergens, key=lambda x: (-x.priority, -x.grade))

        # 우선순위 항원 즉시 처리
        priority_allergens = sorted_allergens[:priority_count]
        remaining_allergens = sorted_allergens[priority_count:]

        # 우선순위 항원 처리
        priority_job = self.processor.create_job(priority_allergens, sort_by_priority=False)
        self.processor.process_job_sync(
            priority_job,
            include_cross_reactivity=include_cross_reactivity,
        )
        priority_results = self.processor.get_completed_results(priority_job)

        # 나머지 백그라운드 처리
        background_job_id = ""
        if remaining_allergens:
            background_job_id = self._start_background_job(
                remaining_allergens,
                include_cross_reactivity,
            )

        return priority_results, background_job_id

    def _start_background_job(
        self,
        allergens: list[AllergenItem],
        include_cross_reactivity: bool,
    ) -> str:
        """백그라운드 작업 시작"""
        job = self.processor.create_job(allergens, sort_by_priority=True)

        # 이벤트 큐 생성
        self._event_queues[job.job_id] = Queue()

        # 진행 콜백 설정
        def on_progress(job: BatchJob):
            progress = self._calculate_progress(job)
            self._event_queues[job.job_id].put(progress)

        self.processor.set_progress_callback(on_progress)

        # 백그라운드 스레드 시작
        thread = threading.Thread(
            target=self._background_process,
            args=(job, include_cross_reactivity),
            daemon=True,
        )
        self._background_jobs[job.job_id] = thread
        thread.start()

        return job.job_id

    def _background_process(
        self,
        job: BatchJob,
        include_cross_reactivity: bool,
    ):
        """백그라운드 처리 실행"""
        try:
            self.processor.process_job_sync(
                job,
                include_cross_reactivity=include_cross_reactivity,
            )
        finally:
            # 완료 이벤트 전송
            if job.job_id in self._event_queues:
                progress = self._calculate_progress(job)
                self._event_queues[job.job_id].put(progress)
                self._event_queues[job.job_id].put(None)  # 종료 신호

    def _calculate_progress(self, job: BatchJob) -> LoadingProgress:
        """진행 상태 계산"""
        in_progress_task = None
        for task in job.tasks:
            if task.status == ProcessingStatus.IN_PROGRESS:
                in_progress_task = task
                break

        remaining = sum(1 for t in job.tasks
                       if t.status in [ProcessingStatus.PENDING, ProcessingStatus.IN_PROGRESS])
        estimated_remaining = remaining * self.AVG_SEARCH_TIME_SEC

        return LoadingProgress(
            job_id=job.job_id,
            total=len(job.tasks),
            loaded=sum(1 for t in job.tasks if t.status == ProcessingStatus.COMPLETED),
            cached=sum(1 for t in job.tasks if t.status == ProcessingStatus.CACHED),
            failed=sum(1 for t in job.tasks if t.status == ProcessingStatus.FAILED),
            current_allergen=in_progress_task.allergen.name if in_progress_task else None,
            estimated_remaining_seconds=estimated_remaining,
        )

    def get_progress_stream(self, job_id: str) -> Generator[LoadingProgress, None, None]:
        """
        진행 상태 스트림 (Generator)

        SSE(Server-Sent Events) 구현에 사용합니다.

        Args:
            job_id: 작업 ID

        Yields:
            LoadingProgress: 진행 상태
        """
        if job_id not in self._event_queues:
            return

        queue = self._event_queues[job_id]

        while True:
            progress = queue.get()
            if progress is None:  # 종료 신호
                break
            yield progress

    def get_background_results(self, job_id: str) -> Optional[list[dict]]:
        """
        백그라운드 작업 결과 조회

        Args:
            job_id: 작업 ID

        Returns:
            결과 목록 또는 None (아직 진행 중)
        """
        job = self.processor.get_job(job_id)
        if not job:
            return None

        if not job.is_completed:
            return None

        return self.processor.get_completed_results(job)

    def get_partial_results(self, job_id: str) -> list[dict]:
        """
        부분 결과 조회 (진행 중에도 조회 가능)

        Args:
            job_id: 작업 ID

        Returns:
            현재까지 완료된 결과 목록
        """
        job = self.processor.get_job(job_id)
        if not job:
            return []

        return self.processor.get_completed_results(job)

    def load_on_demand(
        self,
        allergen: AllergenItem,
        include_cross_reactivity: bool = True,
    ) -> Optional[dict]:
        """
        온디맨드 로딩 (단일 항원)

        사용자가 특정 항원을 클릭했을 때 사용합니다.

        Args:
            allergen: 알러지 항원
            include_cross_reactivity: 교차 반응 포함

        Returns:
            검색 결과 또는 None
        """
        job = self.processor.create_job([allergen], sort_by_priority=False)
        self.processor.process_job_sync(
            job,
            include_cross_reactivity=include_cross_reactivity,
        )

        results = self.processor.get_completed_results(job)
        return results[0] if results else None

    def get_cache_stats(self) -> dict:
        """캐시 통계 조회"""
        return self.processor.cache.get_stats()

    def clear_cache(self):
        """캐시 초기화"""
        self.processor.cache.clear()

    def close(self):
        """리소스 정리"""
        self.processor.close()


def select_loading_strategy(allergen_count: int) -> LoadingStrategy:
    """
    항원 수에 따른 최적 로딩 전략 선택

    Args:
        allergen_count: 항원 수

    Returns:
        LoadingStrategy: 권장 로딩 전략
    """
    if allergen_count <= 5:
        return LoadingStrategy.IMMEDIATE
    elif allergen_count <= 20:
        return LoadingStrategy.PRIORITY_FIRST
    else:
        return LoadingStrategy.BACKGROUND


@dataclass
class SmartLoaderResult:
    """스마트 로더 결과"""
    strategy_used: LoadingStrategy
    immediate_results: list[dict]
    background_job_id: Optional[str]
    total_allergens: int
    loaded_count: int


class SmartLoader:
    """스마트 로더 - 자동 전략 선택"""

    def __init__(self):
        self.loader = ProgressiveLoader()

    def load(
        self,
        allergen_names: list[str],
        grades: Optional[dict[str, int]] = None,
        include_cross_reactivity: bool = True,
        force_strategy: Optional[LoadingStrategy] = None,
    ) -> SmartLoaderResult:
        """
        스마트 로딩 - 항원 수에 따라 최적 전략 자동 선택

        Args:
            allergen_names: 항원 이름 목록
            grades: 항원별 양성 등급
            include_cross_reactivity: 교차 반응 포함
            force_strategy: 강제 지정할 전략 (선택)

        Returns:
            SmartLoaderResult: 로딩 결과
        """
        # AllergenItem 생성
        allergens = create_allergen_items(allergen_names, grades)

        # 전략 선택
        strategy = force_strategy or select_loading_strategy(len(allergens))

        if strategy == LoadingStrategy.IMMEDIATE:
            job, results = self.loader.load_immediate(
                allergens,
                include_cross_reactivity,
            )
            return SmartLoaderResult(
                strategy_used=strategy,
                immediate_results=results,
                background_job_id=None,
                total_allergens=len(allergens),
                loaded_count=len(results),
            )

        elif strategy == LoadingStrategy.PRIORITY_FIRST:
            priority_count = min(5, len(allergens))
            results, bg_job_id = self.loader.load_priority_first(
                allergens,
                priority_count=priority_count,
                include_cross_reactivity=include_cross_reactivity,
            )
            return SmartLoaderResult(
                strategy_used=strategy,
                immediate_results=results,
                background_job_id=bg_job_id,
                total_allergens=len(allergens),
                loaded_count=len(results),
            )

        else:  # BACKGROUND
            # 최상위 3개만 즉시 반환
            results, bg_job_id = self.loader.load_priority_first(
                allergens,
                priority_count=3,
                include_cross_reactivity=include_cross_reactivity,
            )
            return SmartLoaderResult(
                strategy_used=strategy,
                immediate_results=results,
                background_job_id=bg_job_id,
                total_allergens=len(allergens),
                loaded_count=len(results),
            )

    def get_progress(self, job_id: str) -> Optional[dict]:
        """백그라운드 작업 진행 상태"""
        job = self.loader.processor.get_job(job_id)
        if job:
            return job.get_status_summary()
        return None

    def get_results(self, job_id: str) -> list[dict]:
        """백그라운드 작업 결과 (부분 또는 전체)"""
        return self.loader.get_partial_results(job_id)

    def close(self):
        """리소스 정리"""
        self.loader.close()
