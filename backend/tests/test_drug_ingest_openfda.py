"""openFDA 어댑터 단위 테스트

실제 API는 호출하지 않음 — httpx mock 으로 오프라인 테스트.
실제 API 연동 검증은 별도 integration 테스트에서 수행 (키 필요 시).
"""
from __future__ import annotations

import json
from datetime import datetime
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from app.services.drug_ingest.sources.base import DrugProductCandidate, DrugSourceAdapter
from app.services.drug_ingest.sources.openfda import OpenFdaLabelAdapter


SAMPLE_LABEL_RESPONSE: dict[str, Any] = {
    "meta": {"results": {"total": 2, "limit": 100, "skip": 0}},
    "results": [
        {
            "set_id": "aaaa-0001",
            "id": "aaaa-0001",
            "effective_time": "20240101",
            "openfda": {
                "product_type": ["HUMAN PRESCRIPTION DRUG"],
                "generic_name": ["CETIRIZINE HYDROCHLORIDE"],
                "brand_name": ["SAMPLE BRAND"],
                "rxcui": ["20610"],
                "route": ["ORAL"],
                "pharm_class_epc": ["Histamine H1 Receptor Antagonists [MoA]"],
            },
            "indications_and_usage": [
                "For the relief of symptoms associated with seasonal allergic rhinitis."
            ],
            "dosage_and_administration": ["Adults: 10 mg once daily."],
            "warnings": ["Do not use if you have ever had an allergic reaction."],
        },
        {
            "set_id": "bbbb-0002",
            "id": "bbbb-0002",
            "effective_time": "20240115",
            "openfda": {
                "product_type": ["HUMAN OTC DRUG"],
                "generic_name": ["LORATADINE"],
                "rxcui": ["28889"],
                "route": ["ORAL"],
            },
            "indications_and_usage": ["Temporarily relieves symptoms of hay fever."],
            "dosage_and_administration": ["Adults: 10 mg once daily."],
            "warnings": ["Consult a doctor before use if you have liver or kidney disease."],
        },
    ],
}


class _FakeResponse:
    def __init__(self, status_code: int, payload: dict[str, Any]) -> None:
        self.status_code = status_code
        self._payload = payload
        self.text = json.dumps(payload)

    def json(self) -> dict[str, Any]:
        return self._payload

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            import httpx
            request = httpx.Request("GET", "https://api.fda.gov/drug/label.json")
            response = httpx.Response(self.status_code, request=request)
            raise httpx.HTTPStatusError("fake error", request=request, response=response)


@pytest.fixture
def adapter() -> OpenFdaLabelAdapter:
    return OpenFdaLabelAdapter(api_key=None, timeout=5.0)


def test_adapter_metadata(adapter: OpenFdaLabelAdapter) -> None:
    assert isinstance(adapter, DrugSourceAdapter)
    assert adapter.source_name == "openfda"
    assert adapter.license_tag == "cc0"


def test_list_updated_since_yields_set_ids(adapter: OpenFdaLabelAdapter) -> None:
    fake_client = MagicMock()
    fake_client.get.return_value = _FakeResponse(200, SAMPLE_LABEL_RESPONSE)

    with patch.object(adapter, "_get_client", return_value=fake_client), \
         patch.object(adapter, "_wait", return_value=None):
        ids = list(adapter.list_updated_since(since=None, limit=10))

    assert ids == ["aaaa-0001", "bbbb-0002"]
    # 쿼리에 알러지 pharm_class 필터가 포함되었는지 확인
    call_args = fake_client.get.call_args
    params = call_args.kwargs.get("params") or call_args.args[-1]
    search_expr = params["search"]
    assert "pharm_class_epc:antihistamine" in search_expr
    assert "corticosteroid" in search_expr


def test_list_updated_since_with_since_adds_time_filter(adapter: OpenFdaLabelAdapter) -> None:
    fake_client = MagicMock()
    empty_response = {"meta": {"results": {"total": 0}}, "results": []}
    fake_client.get.return_value = _FakeResponse(404, empty_response)

    since = datetime(2026, 1, 1)
    with patch.object(adapter, "_get_client", return_value=fake_client), \
         patch.object(adapter, "_wait", return_value=None):
        list(adapter.list_updated_since(since=since, limit=1))

    call_args = fake_client.get.call_args
    params = call_args.kwargs.get("params")
    search_expr = params["search"]
    assert "effective_time:[20260101+TO+99991231]" in search_expr


def test_list_updated_since_respects_limit(adapter: OpenFdaLabelAdapter) -> None:
    fake_client = MagicMock()
    fake_client.get.return_value = _FakeResponse(200, SAMPLE_LABEL_RESPONSE)

    with patch.object(adapter, "_get_client", return_value=fake_client), \
         patch.object(adapter, "_wait", return_value=None):
        ids = list(adapter.list_updated_since(since=None, limit=1))

    assert ids == ["aaaa-0001"]


def test_fetch_detail_returns_first_result(adapter: OpenFdaLabelAdapter) -> None:
    single_response = {
        "meta": {"results": {"total": 1}},
        "results": [SAMPLE_LABEL_RESPONSE["results"][0]],
    }
    fake_client = MagicMock()
    fake_client.get.return_value = _FakeResponse(200, single_response)

    with patch.object(adapter, "_get_client", return_value=fake_client), \
         patch.object(adapter, "_wait", return_value=None):
        raw = adapter.fetch_detail("aaaa-0001")

    assert raw["set_id"] == "aaaa-0001"
    assert raw["openfda"]["generic_name"] == ["CETIRIZINE HYDROCHLORIDE"]


def test_fetch_detail_raises_when_not_found(adapter: OpenFdaLabelAdapter) -> None:
    empty_response = {"meta": {"results": {"total": 0}}, "results": []}
    fake_client = MagicMock()
    fake_client.get.return_value = _FakeResponse(200, empty_response)

    with patch.object(adapter, "_get_client", return_value=fake_client), \
         patch.object(adapter, "_wait", return_value=None):
        with pytest.raises(ValueError, match="not found"):
            adapter.fetch_detail("missing")


def test_normalize_prescription_product(adapter: OpenFdaLabelAdapter) -> None:
    raw = SAMPLE_LABEL_RESPONSE["results"][0]
    candidate = adapter.normalize(raw)

    assert isinstance(candidate, DrugProductCandidate)
    assert candidate.source == "openfda"
    assert candidate.source_product_id == "aaaa-0001"
    assert candidate.rxcui == "20610"
    assert candidate.name_en == "CETIRIZINE HYDROCHLORIDE"
    assert candidate.product_type == "drug"
    assert candidate.is_prescription is True
    assert candidate.routes == ["oral"]
    assert candidate.indications and "allergic rhinitis" in candidate.indications
    assert candidate.raw == raw


def test_normalize_otc_product_is_not_prescription(adapter: OpenFdaLabelAdapter) -> None:
    raw = SAMPLE_LABEL_RESPONSE["results"][1]
    candidate = adapter.normalize(raw)

    assert candidate.is_prescription is False
    assert candidate.rxcui == "28889"
    assert candidate.name_en == "LORATADINE"


def test_normalize_missing_optional_fields(adapter: OpenFdaLabelAdapter) -> None:
    raw = {
        "set_id": "cccc-0003",
        "openfda": {},
    }
    candidate = adapter.normalize(raw)

    assert candidate.source_product_id == "cccc-0003"
    assert candidate.rxcui is None
    assert candidate.name_en is None
    assert candidate.is_prescription is False
    assert candidate.routes == []
    assert candidate.indications is None


def test_drug_product_candidate_rejects_invalid_product_type() -> None:
    with pytest.raises(ValueError, match="product_type"):
        DrugProductCandidate(
            source="openfda",
            source_product_id="x",
            product_type="device",
        )
