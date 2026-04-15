"""DrugIngestPipeline end-to-end 테스트.

실제 HTTP 호출 없이 FakeAdapter 로 어댑터 계약만 구현해
파이프라인의 조율·트랜잭션·per-item 격리·커서 전진 동작을 검증한다.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Iterable

import pytest
from sqlalchemy.orm import Session

from app.database.drug_models import DrugIngestCursor, DrugProduct, DrugSourceRaw
from app.services.drug_ingest.cursor import (
    STATUS_ERROR,
    STATUS_SUCCESS,
    mark_success,
)
from app.services.drug_ingest.pipeline import DrugIngestPipeline, IngestResult
from app.services.drug_ingest.sources.base import (
    DrugProductCandidate,
    DrugSourceAdapter,
)


# ---------- Fake adapter ----------

class FakeAdapter(DrugSourceAdapter):
    """테스트용 인메모리 어댑터.

    `products` 는 source_product_id → candidate 매핑.
    `list_ids` 로 list_updated_since 응답을 스텁한다.
    `fail_on_list`, `fail_on_fetch_ids` 로 실패 경로 주입.
    """

    def __init__(
        self,
        source_name: str,
        *,
        products: dict[str, DrugProductCandidate] | None = None,
        list_ids: list[str] | None = None,
        fail_on_list: Exception | None = None,
        fail_on_fetch_ids: set[str] | None = None,
    ) -> None:
        self.source_name = source_name
        self.license_tag = "test"
        self._products = products or {}
        self._list_ids = list_ids or list(self._products.keys())
        self._fail_on_list = fail_on_list
        self._fail_on_fetch_ids = fail_on_fetch_ids or set()
        self.list_since_calls: list[tuple[datetime | None, int | None]] = []
        self.fetch_calls: list[str] = []

    def list_updated_since(
        self, since: datetime | None, limit: int | None = None
    ) -> Iterable[str]:
        self.list_since_calls.append((since, limit))
        if self._fail_on_list is not None:
            raise self._fail_on_list
        ids = list(self._list_ids)
        if limit is not None:
            ids = ids[:limit]
        return ids

    def fetch_detail(self, source_product_id: str) -> dict[str, Any]:
        self.fetch_calls.append(source_product_id)
        if source_product_id in self._fail_on_fetch_ids:
            raise RuntimeError(f"stub fetch error for {source_product_id}")
        return {"id": source_product_id}

    def normalize(self, raw: dict[str, Any]) -> DrugProductCandidate:
        source_product_id = raw["id"]
        if source_product_id not in self._products:
            raise KeyError(f"unknown product {source_product_id}")
        return self._products[source_product_id]


def _cand(
    source: str,
    source_product_id: str,
    *,
    name_en: str = "TEST",
    raw_version: int = 1,
) -> DrugProductCandidate:
    return DrugProductCandidate(
        source=source,
        source_product_id=source_product_id,
        rxcui="99999",
        atc_code="R06AE07",
        name_en=name_en,
        product_type="drug",
        is_prescription=False,
        routes=["ORAL"],
        indications="test indication",
        raw={"id": source_product_id, "v": raw_version},
    )


# ---------- Tests ----------

def test_run_source_happy_path_persists_and_advances_cursor(
    test_db: Session,
) -> None:
    adapter = FakeAdapter(
        "openfda",
        products={
            "aaaa-0001": _cand("openfda", "aaaa-0001", name_en="CETIRIZINE"),
            "bbbb-0002": _cand("openfda", "bbbb-0002", name_en="LORATADINE"),
            "cccc-0003": _cand("openfda", "cccc-0003", name_en="FEXOFENADINE"),
        },
    )
    pipeline = DrugIngestPipeline([adapter])

    result = pipeline.run_source(test_db, "openfda")

    assert result.ok
    assert result.success_count == 3
    assert result.failed_items == []
    assert result.source == "openfda"

    products = test_db.query(DrugProduct).all()
    assert len(products) == 3
    names = sorted(p.name_en for p in products)
    assert names == ["CETIRIZINE", "FEXOFENADINE", "LORATADINE"]

    cursor = test_db.query(DrugIngestCursor).filter_by(source="openfda").one()
    assert cursor.last_status == STATUS_SUCCESS
    assert cursor.last_updated_at == result.run_started_at


def test_run_source_isolates_per_item_failures(test_db: Session) -> None:
    adapter = FakeAdapter(
        "openfda",
        products={
            "aaaa": _cand("openfda", "aaaa"),
            "bbbb": _cand("openfda", "bbbb"),
            "cccc": _cand("openfda", "cccc"),
        },
        list_ids=["aaaa", "bbbb", "cccc"],
        fail_on_fetch_ids={"bbbb"},
    )
    pipeline = DrugIngestPipeline([adapter])

    result = pipeline.run_source(test_db, "openfda")

    assert result.ok  # run as a whole succeeds
    assert result.success_count == 2
    assert len(result.failed_items) == 1
    assert result.failed_items[0][0] == "bbbb"
    assert "stub fetch error" in result.failed_items[0][1]

    products = test_db.query(DrugProduct).order_by(DrugProduct.source_product_id).all()
    assert [p.source_product_id for p in products] == ["aaaa", "cccc"]

    cursor = test_db.query(DrugIngestCursor).filter_by(source="openfda").one()
    assert cursor.last_status == STATUS_SUCCESS


def test_run_source_marks_failure_when_list_updated_since_raises(
    test_db: Session,
) -> None:
    prev_ts = datetime(2026, 4, 1, 10, 0)
    mark_success(test_db, "openfda", last_updated_at=prev_ts)
    test_db.commit()

    adapter = FakeAdapter(
        "openfda",
        fail_on_list=RuntimeError("HTTP 503 upstream down"),
    )
    pipeline = DrugIngestPipeline([adapter])

    result = pipeline.run_source(test_db, "openfda")

    assert result.ok is False
    assert result.fatal_error is not None
    assert "503" in result.fatal_error
    assert result.success_count == 0

    assert test_db.query(DrugProduct).count() == 0
    cursor = test_db.query(DrugIngestCursor).filter_by(source="openfda").one()
    assert cursor.last_status == STATUS_ERROR
    assert cursor.last_updated_at == prev_ts  # preserved, not advanced


def test_run_source_passes_cursor_since_to_adapter(test_db: Session) -> None:
    prev_ts = datetime(2026, 4, 1, 10, 0)
    mark_success(test_db, "openfda", last_updated_at=prev_ts)
    test_db.commit()

    adapter = FakeAdapter(
        "openfda",
        products={"xxxx": _cand("openfda", "xxxx")},
    )
    pipeline = DrugIngestPipeline([adapter])

    pipeline.run_source(test_db, "openfda", limit=50)

    assert len(adapter.list_since_calls) == 1
    since_arg, limit_arg = adapter.list_since_calls[0]
    assert since_arg == prev_ts
    assert limit_arg == 50


def test_run_source_full_load_when_cursor_missing(test_db: Session) -> None:
    adapter = FakeAdapter(
        "openfda",
        products={"xxxx": _cand("openfda", "xxxx")},
    )
    pipeline = DrugIngestPipeline([adapter])

    pipeline.run_source(test_db, "openfda")

    since_arg, _ = adapter.list_since_calls[0]
    assert since_arg is None


def test_run_source_writes_raw_snapshot(test_db: Session) -> None:
    adapter = FakeAdapter(
        "openfda",
        products={
            "xxxx": _cand("openfda", "xxxx", raw_version=7),
        },
    )
    pipeline = DrugIngestPipeline([adapter])

    pipeline.run_source(test_db, "openfda")

    snapshots = (
        test_db.query(DrugSourceRaw)
        .filter_by(source="openfda", source_product_id="xxxx")
        .all()
    )
    assert len(snapshots) == 1
    assert snapshots[0].payload["v"] == 7


def test_run_source_is_idempotent_on_rerun(test_db: Session) -> None:
    adapter = FakeAdapter(
        "openfda",
        products={
            "aaaa": _cand("openfda", "aaaa", name_en="CETIRIZINE", raw_version=1),
        },
    )
    pipeline = DrugIngestPipeline([adapter])
    pipeline.run_source(test_db, "openfda")

    adapter_v2 = FakeAdapter(
        "openfda",
        products={
            "aaaa": _cand("openfda", "aaaa", name_en="CETIRIZINE_HCL", raw_version=2),
        },
    )
    pipeline_v2 = DrugIngestPipeline([adapter_v2])
    pipeline_v2.run_source(test_db, "openfda")

    products = test_db.query(DrugProduct).all()
    assert len(products) == 1
    assert products[0].name_en == "CETIRIZINE_HCL"

    snapshots = test_db.query(DrugSourceRaw).all()
    assert len(snapshots) == 2
    assert sorted(s.payload["v"] for s in snapshots) == [1, 2]


def test_run_all_iterates_all_sources(test_db: Session) -> None:
    openfda = FakeAdapter(
        "openfda",
        products={"o1": _cand("openfda", "o1")},
    )
    mfds = FakeAdapter(
        "mfds_eyakeunyo",
        products={"m1": _cand("mfds_eyakeunyo", "m1")},
    )
    pipeline = DrugIngestPipeline([openfda, mfds])

    results = pipeline.run_all(test_db)

    assert len(results) == 2
    assert {r.source for r in results} == {"openfda", "mfds_eyakeunyo"}
    assert all(r.ok for r in results)
    assert test_db.query(DrugProduct).count() == 2


def test_run_all_continues_after_source_failure(test_db: Session) -> None:
    bad = FakeAdapter(
        "openfda",
        fail_on_list=RuntimeError("network down"),
    )
    good = FakeAdapter(
        "mfds_eyakeunyo",
        products={"m1": _cand("mfds_eyakeunyo", "m1")},
    )
    pipeline = DrugIngestPipeline([bad, good])

    results = pipeline.run_all(test_db)

    assert len(results) == 2
    by_source = {r.source: r for r in results}
    assert by_source["openfda"].ok is False
    assert by_source["mfds_eyakeunyo"].ok is True
    assert by_source["mfds_eyakeunyo"].success_count == 1


def test_pipeline_rejects_unknown_source(test_db: Session) -> None:
    pipeline = DrugIngestPipeline(
        [FakeAdapter("openfda", products={})]
    )
    with pytest.raises(KeyError):
        pipeline.run_source(test_db, "nonexistent")


def test_pipeline_rejects_duplicate_adapter_names() -> None:
    a = FakeAdapter("openfda", products={})
    b = FakeAdapter("openfda", products={})
    with pytest.raises(ValueError, match="duplicate"):
        DrugIngestPipeline([a, b])
