"""DailyMed SPL 어댑터 단위 테스트"""
from __future__ import annotations

import json
from datetime import datetime
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from app.services.drug_ingest.sources.base import DrugProductCandidate, DrugSourceAdapter
from app.services.drug_ingest.sources.dailymed import DailyMedAdapter


SAMPLE_LIST_RESPONSE: dict[str, Any] = {
    "metadata": {"total_pages": 1, "current_page": 1, "total_elements": 2},
    "data": [
        {"setid": "abc-123", "title": "CETIRIZINE HCL tablet"},
        {"setid": "def-456", "title": "LORATADINE tablet"},
    ],
}

SAMPLE_DETAIL_RESPONSE: dict[str, Any] = {
    "data": {
        "setid": "abc-123",
        "title": "CETIRIZINE HYDROCHLORIDE tablet [OTC]",
        "published_date": "2025-12-01",
        "products": [
            {
                "product_name": "Cetirizine HCl Tablets 10mg",
                "generic_name": "cetirizine hydrochloride",
                "route": ["ORAL"],
                "marketing_category": "ANDA",
                "active_ingredients": [
                    {"name": "CETIRIZINE HYDROCHLORIDE", "rxcui": "20610"}
                ],
            }
        ],
        "indications_and_usage": ["Temporarily relieves allergy symptoms..."],
        "dosage_and_administration": ["Adults: 10mg once daily."],
        "warnings": ["Ask a doctor before use if you have kidney disease."],
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
def adapter() -> DailyMedAdapter:
    return DailyMedAdapter(
        timeout=5.0,
        ingredient_whitelist=("cetirizine", "loratadine"),
    )


def test_adapter_metadata(adapter: DailyMedAdapter) -> None:
    assert isinstance(adapter, DrugSourceAdapter)
    assert adapter.source_name == "dailymed"
    assert adapter.license_tag == "public_domain"


def test_list_updated_since_deduplicates(adapter: DailyMedAdapter) -> None:
    """동일 setid가 다른 검색어에서 중복 반환되면 deduplicate."""
    fake_client = MagicMock()
    fake_client.get.return_value = _FakeResp(200, SAMPLE_LIST_RESPONSE)

    with patch.object(adapter, "_get_client", return_value=fake_client), \
         patch.object(adapter, "_wait", return_value=None):
        ids = list(adapter.list_updated_since(since=None, limit=20))

    assert ids == ["abc-123", "def-456"]


def test_list_updated_since_respects_limit(adapter: DailyMedAdapter) -> None:
    fake_client = MagicMock()
    fake_client.get.return_value = _FakeResp(200, SAMPLE_LIST_RESPONSE)

    with patch.object(adapter, "_get_client", return_value=fake_client), \
         patch.object(adapter, "_wait", return_value=None):
        ids = list(adapter.list_updated_since(since=None, limit=1))

    assert len(ids) == 1


def test_fetch_detail(adapter: DailyMedAdapter) -> None:
    fake_client = MagicMock()
    fake_client.get.return_value = _FakeResp(200, SAMPLE_DETAIL_RESPONSE)

    with patch.object(adapter, "_get_client", return_value=fake_client), \
         patch.object(adapter, "_wait", return_value=None):
        raw = adapter.fetch_detail("abc-123")

    assert raw["setid"] == "abc-123"


def test_fetch_detail_not_found(adapter: DailyMedAdapter) -> None:
    fake_client = MagicMock()
    fake_client.get.return_value = _FakeResp(404, {})

    with patch.object(adapter, "_get_client", return_value=fake_client), \
         patch.object(adapter, "_wait", return_value=None):
        with pytest.raises(ValueError, match="not found"):
            adapter.fetch_detail("nonexistent")


def test_normalize_basic_fields(adapter: DailyMedAdapter) -> None:
    raw = SAMPLE_DETAIL_RESPONSE["data"]
    candidate = adapter.normalize(raw)

    assert isinstance(candidate, DrugProductCandidate)
    assert candidate.source == "dailymed"
    assert candidate.source_product_id == "abc-123"
    assert candidate.name_en == "cetirizine hydrochloride"
    assert candidate.rxcui == "20610"
    assert candidate.routes == ["oral"]
    assert candidate.product_type == "drug"


def test_normalize_otc_detection(adapter: DailyMedAdapter) -> None:
    raw = SAMPLE_DETAIL_RESPONSE["data"]
    candidate = adapter.normalize(raw)
    # ANDA + OTC in title → is_prescription False
    assert candidate.is_prescription is False


def test_normalize_prescription_detection(adapter: DailyMedAdapter) -> None:
    raw = dict(SAMPLE_DETAIL_RESPONSE["data"])
    raw["title"] = "FLUTICASONE PROPIONATE nasal spray [NDA]"
    raw["products"] = [
        {
            "product_name": "Fluticasone",
            "generic_name": "fluticasone propionate",
            "marketing_category": "NDA",
            "active_ingredients": [],
            "route": ["NASAL"],
        }
    ]
    candidate = adapter.normalize(raw)
    assert candidate.is_prescription is True


def test_normalize_indications_and_warnings(adapter: DailyMedAdapter) -> None:
    raw = SAMPLE_DETAIL_RESPONSE["data"]
    candidate = adapter.normalize(raw)
    assert "allergy symptoms" in (candidate.indications or "")
    assert "kidney disease" in (candidate.warnings or "")
