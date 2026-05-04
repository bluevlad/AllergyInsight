"""DSLD 보충제 어댑터 단위 테스트"""
from __future__ import annotations

import json
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from app.services.drug_ingest.sources.base import DrugProductCandidate, DrugSourceAdapter
from app.services.drug_ingest.sources.dsld import DsldAdapter


SAMPLE_SEARCH_RESPONSE: dict[str, Any] = {
    "total": 2,
    "hits": [
        {"_source": {"DSLD_ID": "1001", "productName": "Vitamin D3 1000IU"}},
        {"_source": {"DSLD_ID": "1002", "productName": "Quercetin Complex"}},
    ],
}

SAMPLE_LABEL_RESPONSE: dict[str, Any] = {
    "data": {
        "DSLD_ID": "1001",
        "productName": "Vitamin D3 1000IU",
        "brandName": "NatureMade",
        "servingSizeDescription": "1 Softgel",
        "statements": [
            {"statement": "Helps support bone, teeth, and immune health."}
        ],
        "cautions": ["If pregnant, consult a physician before use."],
        "suggestedUse": "Take 1 softgel daily with a meal.",
    }
}


class _FakeResp:
    def __init__(self, status: int, payload: dict[str, Any]) -> None:
        self.status_code = status
        self._payload = payload
        self.text = json.dumps(payload)
        self.headers = {"content-type": "application/json"}

    def json(self) -> dict[str, Any]:
        return self._payload

    def raise_for_status(self) -> None:
        pass


@pytest.fixture
def adapter() -> DsldAdapter:
    return DsldAdapter(
        timeout=5.0,
        search_queries=("vitamin D", "quercetin"),
    )


def test_adapter_metadata(adapter: DsldAdapter) -> None:
    assert isinstance(adapter, DrugSourceAdapter)
    assert adapter.source_name == "dsld"
    assert adapter.license_tag == "public_domain"


def test_list_updated_since_yields_dsld_ids(adapter: DsldAdapter) -> None:
    fake_client = MagicMock()
    fake_client.get.return_value = _FakeResp(200, SAMPLE_SEARCH_RESPONSE)

    with patch.object(adapter, "_get_client", return_value=fake_client), \
         patch.object(adapter, "_wait", return_value=None):
        ids = list(adapter.list_updated_since(since=None, limit=10))

    assert "1001" in ids
    assert "1002" in ids


def test_list_updated_since_deduplicates(adapter: DsldAdapter) -> None:
    fake_client = MagicMock()
    fake_client.get.return_value = _FakeResp(200, SAMPLE_SEARCH_RESPONSE)

    with patch.object(adapter, "_get_client", return_value=fake_client), \
         patch.object(adapter, "_wait", return_value=None):
        ids = list(adapter.list_updated_since(since=None, limit=20))

    assert len(ids) == len(set(ids))


def test_list_respects_limit(adapter: DsldAdapter) -> None:
    fake_client = MagicMock()
    fake_client.get.return_value = _FakeResp(200, SAMPLE_SEARCH_RESPONSE)

    with patch.object(adapter, "_get_client", return_value=fake_client), \
         patch.object(adapter, "_wait", return_value=None):
        ids = list(adapter.list_updated_since(since=None, limit=1))

    assert len(ids) == 1


def test_fetch_detail(adapter: DsldAdapter) -> None:
    fake_client = MagicMock()
    fake_client.get.return_value = _FakeResp(200, SAMPLE_LABEL_RESPONSE)

    with patch.object(adapter, "_get_client", return_value=fake_client), \
         patch.object(adapter, "_wait", return_value=None):
        raw = adapter.fetch_detail("1001")

    assert raw["DSLD_ID"] == "1001"


def test_fetch_detail_not_found(adapter: DsldAdapter) -> None:
    fake_client = MagicMock()
    fake_client.get.return_value = _FakeResp(404, {})

    with patch.object(adapter, "_get_client", return_value=fake_client), \
         patch.object(adapter, "_wait", return_value=None):
        with pytest.raises(ValueError, match="not found"):
            adapter.fetch_detail("99999")


def test_normalize_supplement_type(adapter: DsldAdapter) -> None:
    raw = SAMPLE_LABEL_RESPONSE["data"]
    candidate = adapter.normalize(raw)
    assert isinstance(candidate, DrugProductCandidate)
    assert candidate.product_type == "supplement"
    assert candidate.is_prescription is False
    assert candidate.source == "dsld"
    assert candidate.source_product_id == "1001"


def test_normalize_product_name(adapter: DsldAdapter) -> None:
    raw = SAMPLE_LABEL_RESPONSE["data"]
    candidate = adapter.normalize(raw)
    assert candidate.name_en == "Vitamin D3 1000IU"


def test_normalize_brand_not_in_name(adapter: DsldAdapter) -> None:
    """ADR-007: brandName 은 raw 보관만."""
    raw = SAMPLE_LABEL_RESPONSE["data"]
    candidate = adapter.normalize(raw)
    assert candidate.raw["brandName"] == "NatureMade"


def test_normalize_statements_as_indications(adapter: DsldAdapter) -> None:
    raw = SAMPLE_LABEL_RESPONSE["data"]
    candidate = adapter.normalize(raw)
    assert "immune health" in (candidate.indications or "")


def test_normalize_warnings(adapter: DsldAdapter) -> None:
    raw = SAMPLE_LABEL_RESPONSE["data"]
    candidate = adapter.normalize(raw)
    assert "pregnant" in (candidate.warnings or "")
