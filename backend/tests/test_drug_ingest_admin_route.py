"""POST /api/admin/drug-ingest/run 엔드포인트 테스트.

실제 어댑터·HTTP 호출 없이 drug_ingest_routes.build_default_pipeline 을
스텁으로 교체해 라우터 층(인증·dispatch·응답 포맷)만 검증한다.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.services.drug_ingest.pipeline import IngestResult


class _StubPipeline:
    def __init__(
        self,
        *,
        source_names: list[str] | None = None,
        run_source_result: IngestResult | None = None,
        run_all_results: list[IngestResult] | None = None,
    ) -> None:
        self.source_names = source_names or ["openfda", "mfds_eyakeunyo"]
        self._run_source_result = run_source_result
        self._run_all_results = run_all_results or []
        self.calls: list[tuple[str, Any]] = []

    def run_source(self, db, source_name, *, limit=None):
        self.calls.append(("run_source", (source_name, limit)))
        return self._run_source_result or IngestResult(
            source=source_name,
            run_started_at=datetime(2026, 4, 14, 0, 0),
            success_count=3,
        )

    def run_all(self, db, *, limit=None):
        self.calls.append(("run_all", limit))
        return self._run_all_results or [
            IngestResult(
                source="openfda",
                run_started_at=datetime(2026, 4, 14, 0, 0),
                success_count=5,
            ),
            IngestResult(
                source="mfds_eyakeunyo",
                run_started_at=datetime(2026, 4, 14, 0, 0),
                success_count=2,
                failed_items=[("broken", "parse error")],
            ),
        ]


@pytest.fixture
def stub_pipeline(monkeypatch: pytest.MonkeyPatch) -> _StubPipeline:
    stub = _StubPipeline()
    from app.admin import drug_ingest_routes

    monkeypatch.setattr(
        drug_ingest_routes, "build_default_pipeline", lambda: stub
    )
    return stub


def test_run_drug_ingest_requires_auth(client: TestClient) -> None:
    resp = client.post("/api/admin/drug-ingest/run", json={})
    assert resp.status_code in (401, 403)


def test_run_drug_ingest_rejects_non_admin(
    client: TestClient, auth_headers: dict
) -> None:
    resp = client.post(
        "/api/admin/drug-ingest/run", headers=auth_headers, json={}
    )
    assert resp.status_code == 403


def test_run_drug_ingest_all_sources(
    client: TestClient, admin_headers: dict, stub_pipeline: _StubPipeline
) -> None:
    resp = client.post(
        "/api/admin/drug-ingest/run",
        headers=admin_headers,
        json={"limit": 100},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()

    assert len(body["results"]) == 2
    sources = {r["source"] for r in body["results"]}
    assert sources == {"openfda", "mfds_eyakeunyo"}

    mfds = next(r for r in body["results"] if r["source"] == "mfds_eyakeunyo")
    assert mfds["success_count"] == 2
    assert mfds["failed_count"] == 1
    assert mfds["failed_items"][0]["source_product_id"] == "broken"
    assert mfds["ok"] is True

    assert stub_pipeline.calls == [("run_all", 100)]


def test_run_drug_ingest_single_source(
    client: TestClient, admin_headers: dict, stub_pipeline: _StubPipeline
) -> None:
    resp = client.post(
        "/api/admin/drug-ingest/run",
        headers=admin_headers,
        json={"source": "openfda", "limit": 10},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert len(body["results"]) == 1
    assert body["results"][0]["source"] == "openfda"
    assert stub_pipeline.calls == [("run_source", ("openfda", 10))]


def test_run_drug_ingest_rejects_unknown_source(
    client: TestClient, admin_headers: dict, stub_pipeline: _StubPipeline
) -> None:
    resp = client.post(
        "/api/admin/drug-ingest/run",
        headers=admin_headers,
        json={"source": "nonexistent"},
    )
    assert resp.status_code == 400
    assert "unknown source" in resp.json()["detail"]


def test_run_drug_ingest_returns_fatal_error(
    client: TestClient, admin_headers: dict, monkeypatch: pytest.MonkeyPatch
) -> None:
    stub = _StubPipeline(
        run_source_result=IngestResult(
            source="openfda",
            run_started_at=datetime(2026, 4, 14, 0, 0),
            fatal_error="HTTP 503 upstream down",
        )
    )
    from app.admin import drug_ingest_routes

    monkeypatch.setattr(
        drug_ingest_routes, "build_default_pipeline", lambda: stub
    )

    resp = client.post(
        "/api/admin/drug-ingest/run",
        headers=admin_headers,
        json={"source": "openfda"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["results"][0]["ok"] is False
    assert "503" in body["results"][0]["fatal_error"]
