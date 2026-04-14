"""Drug ingest 파이프라인 오케스트레이터.

어댑터(Phase 0) · 저장소(Phase 1) · 커서(Phase 2) 를 엮어
소스별 증분 수집을 한 트랜잭션으로 실행한다.

핵심 설계:
- **per-item 격리**: 각 제품마다 SAVEPOINT(begin_nested) 로 감싸 한
  건의 실패가 배치 전체를 오염시키지 않는다. 실패한 item 은 로깅·
  IngestResult 에 기록하고 루프는 계속 전진.
- **커서 전진**: 배치 시작 시각(run_started_at, naive UTC) 을 새로운
  last_updated_at 으로 기록한다. list_updated_since 경계는 inclusive
  로 다뤄 재수집이 생기더라도 upsert 로 멱등 보장.
- **list_updated_since 실패**: 수집 목록 조회 자체가 실패하면 단일
  item 이 아니라 run 전체 실패로 간주 → mark_failure 호출, 커서
  전진 없음. 다음 run 이 이전 지점부터 재시도.
- **트랜잭션**: 본 모듈은 session.commit() 을 수행한다. CLI/API
  진입점(Phase 4) 이 호출 단위로 세션을 생성·주입하는 것을 가정.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Iterable

from sqlalchemy.orm import Session

from .cursor import get_since, mark_failure, mark_success
from .repository import persist_candidate
from .sources.base import DrugSourceAdapter

logger = logging.getLogger(__name__)


def _utc_now_naive() -> datetime:
    """커서 컬럼(naive TIMESTAMP) 과 호환되는 현재 시각."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


@dataclass
class IngestResult:
    """단일 소스의 한 run 결과."""

    source: str
    run_started_at: datetime
    success_count: int = 0
    failed_items: list[tuple[str, str]] = field(default_factory=list)
    fatal_error: str | None = None  # list_updated_since 자체 실패 시에만

    @property
    def attempted_count(self) -> int:
        return self.success_count + len(self.failed_items)

    @property
    def ok(self) -> bool:
        return self.fatal_error is None


class DrugIngestPipeline:
    """소스 어댑터 묶음을 받아 증분 수집을 수행한다.

    사용 예::

        pipeline = DrugIngestPipeline([
            OpenFdaLabelAdapter(),
            MfdsEyakeunyoAdapter(service_key=...),
        ])
        result = pipeline.run_source(session, "openfda", limit=500)
    """

    def __init__(self, adapters: Iterable[DrugSourceAdapter]) -> None:
        self._adapters: dict[str, DrugSourceAdapter] = {}
        for adapter in adapters:
            name = adapter.source_name
            if not name:
                raise ValueError(
                    f"adapter {type(adapter).__name__} has no source_name"
                )
            if name in self._adapters:
                raise ValueError(f"duplicate adapter source_name: {name}")
            self._adapters[name] = adapter

    @property
    def source_names(self) -> list[str]:
        return list(self._adapters.keys())

    def run_source(
        self,
        session: Session,
        source_name: str,
        *,
        limit: int | None = None,
    ) -> IngestResult:
        """단일 소스 증분 수집.

        limit=None 이면 어댑터 기본값(보통 소스 페이지 한도) 따름.
        """
        if source_name not in self._adapters:
            raise KeyError(f"unknown source: {source_name}")

        adapter = self._adapters[source_name]
        run_started_at = _utc_now_naive()
        result = IngestResult(source=source_name, run_started_at=run_started_at)

        since = get_since(session, source_name)
        logger.info(
            "drug_ingest.run_source start source=%s since=%s limit=%s",
            source_name,
            since.isoformat() if since else "None",
            limit,
        )

        try:
            ids = list(adapter.list_updated_since(since, limit=limit))
        except Exception as exc:
            logger.exception(
                "drug_ingest.list_updated_since failed source=%s", source_name
            )
            session.rollback()
            result.fatal_error = f"list_updated_since: {exc}"
            mark_failure(session, source_name, error=result.fatal_error)
            session.commit()
            return result

        for source_product_id in ids:
            try:
                with session.begin_nested():
                    candidate = adapter.fetch_and_normalize(source_product_id)
                    persist_candidate(session, candidate)
                result.success_count += 1
            except Exception as exc:
                logger.warning(
                    "drug_ingest.item_failed source=%s id=%s err=%s",
                    source_name,
                    source_product_id,
                    exc,
                )
                result.failed_items.append((source_product_id, str(exc)))

        mark_success(
            session,
            source_name,
            last_updated_at=run_started_at,
        )
        session.commit()

        logger.info(
            "drug_ingest.run_source done source=%s success=%d failed=%d",
            source_name,
            result.success_count,
            len(result.failed_items),
        )
        return result

    def run_all(
        self,
        session: Session,
        *,
        limit: int | None = None,
    ) -> list[IngestResult]:
        """등록된 모든 소스를 순차 실행.

        한 소스의 실패는 다음 소스 실행을 막지 않는다.
        (병렬화는 Phase 4 스케줄러 단에서 검토.)
        """
        results: list[IngestResult] = []
        for source_name in self._adapters:
            try:
                results.append(
                    self.run_source(session, source_name, limit=limit)
                )
            except Exception as exc:
                logger.exception(
                    "drug_ingest.run_source crashed source=%s", source_name
                )
                results.append(
                    IngestResult(
                        source=source_name,
                        run_started_at=_utc_now_naive(),
                        fatal_error=f"pipeline_crash: {exc}",
                    )
                )
        return results
