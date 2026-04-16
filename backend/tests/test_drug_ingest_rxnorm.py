"""RxNorm 어댑터 단위 테스트"""
from __future__ import annotations

import json
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from app.services.drug_ingest.sources.base import DrugProductCandidate, DrugSourceAdapter
from app.services.drug_ingest.sources.rxnorm import RxNormAdapter


SAMPLE_CLASS_MEMBERS_RESPONSE: dict[str, Any] = {
    "drugMemberGroup": {
        "drugMember": [
            {
                "minConcept": {
                    "rxcui": "20610",
                    "name": "cetirizine",
                    "tty": "IN",
                }
            },
            {
                "minConcept": {
                    "rxcui": "25480",
                    "name": "loratadine",
                    "tty": "IN",
                }
            },
        ]
    }
}

SAMPLE_PROPERTIES_RESPONSE: dict[str, Any] = {
    "properties": {
        "rxcui": "20610",
        "name": "cetirizine",
        "synonym": "cetirizine hydrochloride",
        "tty": "IN",
        "language": "ENG",
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
def adapter() -> RxNormAdapter:
    return RxNormAdapter(
        timeout=5.0,
        atc_class_ids=("R06",),
    )


def test_adapter_metadata(adapter: RxNormAdapter) -> None:
    assert isinstance(adapter, DrugSourceAdapter)
    assert adapter.source_name == "rxnorm"
    assert adapter.license_tag == "umls_cat0"


def test_list_updated_since_yields_rxcuis(adapter: RxNormAdapter) -> None:
    fake_client = MagicMock()
    fake_client.get.return_value = _FakeResp(200, SAMPLE_CLASS_MEMBERS_RESPONSE)

    with patch.object(adapter, "_get_client", return_value=fake_client), \
         patch.object(adapter, "_wait", return_value=None):
        ids = list(adapter.list_updated_since(since=None, limit=10))

    assert "20610" in ids
    assert "25480" in ids


def test_list_deduplicates_across_classes() -> None:
    """서로 다른 ATC 클래스에서 같은 rxcui 가 나오면 한 번만 반환."""
    adapter = RxNormAdapter(
        timeout=5.0,
        atc_class_ids=("R06", "R01"),
    )
    fake_client = MagicMock()
    fake_client.get.return_value = _FakeResp(200, SAMPLE_CLASS_MEMBERS_RESPONSE)

    with patch.object(adapter, "_get_client", return_value=fake_client), \
         patch.object(adapter, "_wait", return_value=None):
        ids = list(adapter.list_updated_since(since=None, limit=20))

    assert len(ids) == len(set(ids))


def test_list_respects_limit(adapter: RxNormAdapter) -> None:
    fake_client = MagicMock()
    fake_client.get.return_value = _FakeResp(200, SAMPLE_CLASS_MEMBERS_RESPONSE)

    with patch.object(adapter, "_get_client", return_value=fake_client), \
         patch.object(adapter, "_wait", return_value=None):
        ids = list(adapter.list_updated_since(since=None, limit=1))

    assert len(ids) == 1


def test_fetch_detail(adapter: RxNormAdapter) -> None:
    adapter._atc_cache["20610"] = "R06"
    fake_client = MagicMock()
    fake_client.get.return_value = _FakeResp(200, SAMPLE_PROPERTIES_RESPONSE)

    with patch.object(adapter, "_get_client", return_value=fake_client), \
         patch.object(adapter, "_wait", return_value=None):
        raw = adapter.fetch_detail("20610")

    assert raw["rxcui"] == "20610"
    assert raw["_classified_atc"] == "R06"


def test_fetch_detail_not_found(adapter: RxNormAdapter) -> None:
    fake_client = MagicMock()
    fake_client.get.return_value = _FakeResp(200, {"properties": None})

    with patch.object(adapter, "_get_client", return_value=fake_client), \
         patch.object(adapter, "_wait", return_value=None):
        with pytest.raises(ValueError, match="not found"):
            adapter.fetch_detail("99999")


def test_normalize_basic_fields(adapter: RxNormAdapter) -> None:
    raw = dict(SAMPLE_PROPERTIES_RESPONSE["properties"])
    raw["_classified_atc"] = "R06"

    candidate = adapter.normalize(raw)

    assert isinstance(candidate, DrugProductCandidate)
    assert candidate.source == "rxnorm"
    assert candidate.source_product_id == "20610"
    assert candidate.rxcui == "20610"
    assert candidate.atc_code == "R06"
    assert candidate.name_en == "cetirizine"
    assert candidate.product_type == "drug"
    assert candidate.is_prescription is False
    assert candidate.indications is None  # RxNorm은 성분 개념 — 적응증 없음
