"""drug_ingest.cursor 단위 테스트.

SQLite in-memory 환경(test_db fixture)에서 커서 로드/전진/실패-격리
동작을 검증한다.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy.orm import Session

# drug_ingest_cursors.last_updated_at 은 naive TIMESTAMP 로 저장된다
# (DateTime 컬럼에 timezone=True 미지정 — Postgres/SQLite 모두 동일).
# 따라서 어댑터/파이프라인은 항상 naive UTC 로 넘긴다는 규약을 따른다.

from app.database.drug_models import DrugIngestCursor
from app.services.drug_ingest.cursor import (
    STATUS_ERROR,
    STATUS_SUCCESS,
    get_since,
    load_cursor,
    mark_failure,
    mark_success,
)


def test_load_cursor_returns_none_when_empty(test_db: Session) -> None:
    assert load_cursor(test_db, "openfda") is None
    assert get_since(test_db, "openfda") is None


def test_mark_success_creates_new_cursor(test_db: Session) -> None:
    ts = datetime(2026, 4, 1, 10, 0)

    state = mark_success(
        test_db,
        "openfda",
        last_updated_at=ts,
        next_page_token="page-2",
    )
    test_db.commit()

    assert state.source == "openfda"
    assert state.last_updated_at == ts
    assert state.next_page_token == "page-2"
    assert state.last_status == STATUS_SUCCESS
    assert state.last_error is None

    loaded = load_cursor(test_db, "openfda")
    assert loaded is not None
    assert loaded.last_updated_at == ts
    assert get_since(test_db, "openfda") == ts


def test_mark_success_advances_existing_cursor(test_db: Session) -> None:
    t1 = datetime(2026, 4, 1, 10, 0)
    t2 = datetime(2026, 4, 2, 10, 0)

    mark_success(test_db, "openfda", last_updated_at=t1)
    test_db.commit()

    mark_success(
        test_db, "openfda", last_updated_at=t2, next_page_token="tok"
    )
    test_db.commit()

    rows = test_db.query(DrugIngestCursor).all()
    assert len(rows) == 1
    assert rows[0].last_updated_at == t2
    assert rows[0].next_page_token == "tok"


def test_mark_failure_preserves_last_updated_at(test_db: Session) -> None:
    t1 = datetime(2026, 4, 1, 10, 0)

    mark_success(test_db, "openfda", last_updated_at=t1, next_page_token="tok")
    test_db.commit()

    state = mark_failure(test_db, "openfda", error="HTTP 503 upstream down")
    test_db.commit()

    assert state.last_updated_at == t1
    assert state.next_page_token == "tok"
    assert state.last_status == STATUS_ERROR
    assert "503" in state.last_error

    assert get_since(test_db, "openfda") == t1


def test_mark_failure_on_first_run_creates_empty_cursor(
    test_db: Session,
) -> None:
    state = mark_failure(test_db, "mfds_eyakeunyo", error="timeout")
    test_db.commit()

    assert state.source == "mfds_eyakeunyo"
    assert state.last_updated_at is None
    assert state.last_status == STATUS_ERROR
    assert state.last_error == "timeout"

    assert get_since(test_db, "mfds_eyakeunyo") is None


def test_cursors_are_isolated_per_source(test_db: Session) -> None:
    t_openfda = datetime(2026, 4, 1)
    t_mfds = datetime(2026, 3, 20)

    mark_success(test_db, "openfda", last_updated_at=t_openfda)
    mark_success(test_db, "mfds_eyakeunyo", last_updated_at=t_mfds)
    test_db.commit()

    assert get_since(test_db, "openfda") == t_openfda
    assert get_since(test_db, "mfds_eyakeunyo") == t_mfds

    mark_failure(test_db, "openfda", error="boom")
    test_db.commit()

    assert get_since(test_db, "openfda") == t_openfda
    assert get_since(test_db, "mfds_eyakeunyo") == t_mfds


def test_mark_failure_truncates_large_error_message(test_db: Session) -> None:
    huge = "x" * 50_000
    state = mark_failure(test_db, "openfda", error=huge)
    test_db.commit()

    assert state.last_error is not None
    assert len(state.last_error) == 10_000
