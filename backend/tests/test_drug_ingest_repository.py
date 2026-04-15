"""drug_ingest.repository 단위 테스트.

test_db fixture (SQLite in-memory) 위에서 upsert 동작과 raw 스냅샷
축적을 검증한다. 실제 외부 API 호출 없음.
"""
from __future__ import annotations

import pytest
from sqlalchemy.orm import Session

from app.database.drug_models import DrugProduct, DrugSourceRaw
from app.services.drug_ingest.repository import (
    persist_candidate,
    save_raw_snapshot,
    upsert_drug_product,
)
from app.services.drug_ingest.sources.base import DrugProductCandidate


def _make_candidate(
    *,
    source: str = "openfda",
    source_product_id: str = "aaaa-0001",
    name_en: str = "CETIRIZINE HYDROCHLORIDE",
    rxcui: str | None = "20610",
    indications: str | None = "allergic rhinitis",
    raw: dict | None = None,
) -> DrugProductCandidate:
    return DrugProductCandidate(
        source=source,
        source_product_id=source_product_id,
        rxcui=rxcui,
        atc_code="R06AE07",
        name_en=name_en,
        product_type="drug",
        is_prescription=False,
        routes=["ORAL"],
        indications=indications,
        dosage="10 mg once daily",
        warnings="Do not use if allergic",
        raw=raw if raw is not None else {"set_id": source_product_id, "v": 1},
    )


def test_upsert_inserts_new_product(test_db: Session) -> None:
    candidate = _make_candidate()

    result = upsert_drug_product(test_db, candidate)
    test_db.commit()

    assert result.created is True
    assert result.product_id > 0

    row = test_db.query(DrugProduct).filter_by(id=result.product_id).one()
    assert row.source == "openfda"
    assert row.source_product_id == "aaaa-0001"
    assert row.rxcui == "20610"
    assert row.name_en == "CETIRIZINE HYDROCHLORIDE"
    assert row.routes == ["ORAL"]
    assert row.raw_jsonb == {"set_id": "aaaa-0001", "v": 1}


def test_upsert_updates_existing_product_on_conflict(test_db: Session) -> None:
    first = _make_candidate(indications="allergic rhinitis", raw={"v": 1})
    first_result = upsert_drug_product(test_db, first)
    test_db.commit()

    updated = _make_candidate(
        indications="allergic rhinitis, chronic urticaria",
        raw={"v": 2, "note": "label revised"},
    )
    updated_result = upsert_drug_product(test_db, updated)
    test_db.commit()

    assert updated_result.created is False
    assert updated_result.product_id == first_result.product_id

    rows = test_db.query(DrugProduct).filter_by(source="openfda").all()
    assert len(rows) == 1
    assert rows[0].indications == "allergic rhinitis, chronic urticaria"
    assert rows[0].raw_jsonb == {"v": 2, "note": "label revised"}


def test_upsert_treats_different_sources_as_distinct_products(
    test_db: Session,
) -> None:
    a = _make_candidate(source="openfda", source_product_id="aaaa-0001")
    b = _make_candidate(source="mfds_eyakeunyo", source_product_id="aaaa-0001")

    upsert_drug_product(test_db, a)
    upsert_drug_product(test_db, b)
    test_db.commit()

    rows = test_db.query(DrugProduct).all()
    assert len(rows) == 2
    sources = sorted(r.source for r in rows)
    assert sources == ["mfds_eyakeunyo", "openfda"]


def test_save_raw_snapshot_accumulates_history(test_db: Session) -> None:
    save_raw_snapshot(
        test_db, "openfda", "aaaa-0001", {"v": 1, "effective_time": "20240101"}
    )
    save_raw_snapshot(
        test_db, "openfda", "aaaa-0001", {"v": 2, "effective_time": "20240615"}
    )
    save_raw_snapshot(
        test_db, "openfda", "aaaa-0001", {"v": 3, "effective_time": "20241201"}
    )
    test_db.commit()

    snapshots = (
        test_db.query(DrugSourceRaw)
        .filter_by(source="openfda", source_product_id="aaaa-0001")
        .order_by(DrugSourceRaw.id)
        .all()
    )
    assert len(snapshots) == 3
    versions = [s.payload["v"] for s in snapshots]
    assert versions == [1, 2, 3]
    assert all(s.fetched_at is not None for s in snapshots)


def test_persist_candidate_upserts_and_snapshots(test_db: Session) -> None:
    candidate = _make_candidate(raw={"v": 1})

    first = persist_candidate(test_db, candidate)
    test_db.commit()
    assert first.created is True

    updated = _make_candidate(
        indications="allergic rhinitis, asthma", raw={"v": 2}
    )
    second = persist_candidate(test_db, updated)
    test_db.commit()
    assert second.created is False
    assert second.product_id == first.product_id

    products = test_db.query(DrugProduct).all()
    assert len(products) == 1
    assert products[0].indications == "allergic rhinitis, asthma"

    snapshots = (
        test_db.query(DrugSourceRaw)
        .filter_by(source="openfda", source_product_id="aaaa-0001")
        .order_by(DrugSourceRaw.id)
        .all()
    )
    assert len(snapshots) == 2
    assert [s.payload["v"] for s in snapshots] == [1, 2]


def test_persist_candidate_skips_snapshot_when_raw_empty(
    test_db: Session,
) -> None:
    candidate = _make_candidate(raw={})

    result = persist_candidate(test_db, candidate)
    test_db.commit()

    assert result.created is True
    snapshots = test_db.query(DrugSourceRaw).all()
    assert snapshots == []
