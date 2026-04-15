"""Drug ingest 증분 수집 커서 관리.

drug_ingest_cursors 테이블에 소스별 "마지막으로 성공한 수집 지점" 을
보관한다. 파이프라인이 이 값을 어댑터의 `list_updated_since(since)` 에
넘겨 증분 수집을 수행한다.

실패-격리 원칙:
- mark_success 는 last_updated_at 을 전진시킨다.
- mark_failure 는 last_updated_at 을 건드리지 않는다 — 실패한 run 이
  커서를 망가뜨려 다음 run 에서 데이터가 유실되는 일을 막기 위함.
  (ADR 없음, Phase 2 설계 결정. 필요 시 커서 재시드는 관리자 수동.)

타임존 규약:
- drug_ingest_cursors.last_updated_at 은 naive TIMESTAMP 로 저장된다
  (DateTime 컬럼에 timezone=True 미지정). 파이프라인·어댑터는 항상
  naive UTC datetime 으로 값을 주고받는다 — tz-aware 를 넘기면
  Postgres/SQLite 모두 round-trip 후 tzinfo 가 사라져 비교가 깨진다.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from sqlalchemy.orm import Session

from app.database.drug_models import DrugIngestCursor
from app.utils.timezone import utc_now


STATUS_SUCCESS = "success"
STATUS_ERROR = "error"
STATUS_RUNNING = "running"


@dataclass(frozen=True)
class CursorState:
    source: str
    last_updated_at: datetime | None
    next_page_token: str | None
    last_run_at: datetime
    last_status: str | None
    last_error: str | None


def _to_state(row: DrugIngestCursor) -> CursorState:
    return CursorState(
        source=row.source,
        last_updated_at=row.last_updated_at,
        next_page_token=row.next_page_token,
        last_run_at=row.last_run_at,
        last_status=row.last_status,
        last_error=row.last_error,
    )


def load_cursor(session: Session, source: str) -> CursorState | None:
    """주어진 source 의 커서를 읽어온다. 없으면 None."""
    row = (
        session.query(DrugIngestCursor)
        .filter(DrugIngestCursor.source == source)
        .one_or_none()
    )
    return _to_state(row) if row is not None else None


def get_since(session: Session, source: str) -> datetime | None:
    """파이프라인이 어댑터에 넘길 since 값을 반환.

    커서가 없거나 이전 run 이 last_updated_at 을 남기지 못했으면 None
    (= 전체 수집). 초기 적재를 자연스럽게 지원한다.
    """
    state = load_cursor(session, source)
    return state.last_updated_at if state is not None else None


def mark_success(
    session: Session,
    source: str,
    *,
    last_updated_at: datetime,
    next_page_token: str | None = None,
) -> CursorState:
    """성공적으로 완료된 run 을 기록 — last_updated_at 을 전진시킨다.

    commit 은 호출자 책임. 파이프라인이 배치 트랜잭션 안에서
    drug_products upsert 와 한 번에 묶어 커밋한다.
    """
    row = (
        session.query(DrugIngestCursor)
        .filter(DrugIngestCursor.source == source)
        .one_or_none()
    )
    if row is None:
        row = DrugIngestCursor(source=source)
        session.add(row)

    row.last_updated_at = last_updated_at
    row.next_page_token = next_page_token
    row.last_run_at = utc_now()
    row.last_status = STATUS_SUCCESS
    row.last_error = None
    session.flush()
    return _to_state(row)


def mark_failure(
    session: Session,
    source: str,
    *,
    error: str,
) -> CursorState:
    """실패한 run 을 기록 — last_updated_at 은 보존한다.

    다음 run 은 이전 성공 지점부터 다시 수집을 시도하게 된다.
    커서 row 가 없던 상태에서 첫 run 이 실패했다면 새 row 를
    last_updated_at=None 으로 생성해 상태만 기록한다.
    """
    row = (
        session.query(DrugIngestCursor)
        .filter(DrugIngestCursor.source == source)
        .one_or_none()
    )
    if row is None:
        row = DrugIngestCursor(source=source, last_updated_at=None)
        session.add(row)

    row.last_run_at = utc_now()
    row.last_status = STATUS_ERROR
    row.last_error = error[:10_000] if error else None
    session.flush()
    return _to_state(row)
