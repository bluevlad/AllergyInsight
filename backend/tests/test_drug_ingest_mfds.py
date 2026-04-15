"""식약처 e약은요 어댑터 단위 테스트

외부 API 호출은 MagicMock으로 격리. 실제 API 검증은
별도 integration 테스트로 분리.
"""
from __future__ import annotations

import json
from datetime import datetime
from typing import Any
from unittest.mock import MagicMock, patch

import httpx
import pytest

from app.services.drug_ingest.sources.base import (
    DrugProductCandidate,
    DrugSourceAdapter,
)
from app.services.drug_ingest.sources.mfds_eyakeunyo import MfdsEyakeunyoAdapter


SAMPLE_PAGE_RESPONSE: dict[str, Any] = {
    "header": {"resultCode": "00", "resultMsg": "NORMAL SERVICE."},
    "body": {
        "pageNo": 1,
        "totalCount": 3,
        "numOfRows": 100,
        "items": [
            {
                "itemSeq": "195700020",
                "itemName": "활명수",
                "entpName": "동화약품(주)",
                "efcyQesitm": "이 약은 식욕감퇴, 소화불량에 사용합니다.",
                "useMethodQesitm": "1회 1병(75mL), 1일 3회 식후 복용.",
                "atpnWarnQesitm": "3개월 미만 젖먹이 복용 금지.",
                "atpnQesitm": "1세 미만 젖먹이, 임부 복용 전 전문가 상담.",
                "intrcQesitm": None,
                "seQesitm": None,
                "updateDe": "2024-05-09",
            },
            {
                "itemSeq": "200100123",
                "itemName": "세티리진정",
                "entpName": "한국XX제약",
                "efcyQesitm": "알러지성 비염, 두드러기에 사용합니다.",
                "useMethodQesitm": "성인 1일 1회 10mg.",
                "atpnWarnQesitm": None,
                "atpnQesitm": "운전 시 주의.",
                "intrcQesitm": "중추신경 억제제와 병용 주의.",
                "seQesitm": "졸림, 피로감.",
                "updateDe": "2025-12-15",
            },
            {
                "itemSeq": "200100999",
                "itemName": "레거시제품",
                "entpName": "구판사",
                "efcyQesitm": "레거시.",
                "updateDe": "2020-01-01",
            },
        ],
    },
}


class _FakeResp:
    def __init__(self, status: int, payload: dict[str, Any]) -> None:
        self.status_code = status
        self._payload = payload
        self.text = json.dumps(payload)
        self.headers = {"content-type": "application/json;charset=utf-8"}

    def json(self) -> dict[str, Any]:
        return self._payload

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            req = httpx.Request("GET", MfdsEyakeunyoAdapter.BASE_URL)
            raise httpx.HTTPStatusError(
                "err", request=req, response=httpx.Response(self.status_code, request=req)
            )


@pytest.fixture
def adapter() -> MfdsEyakeunyoAdapter:
    return MfdsEyakeunyoAdapter(api_key="TEST_KEY", timeout=5.0)


def test_missing_key_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("MFDS_API_KEY", raising=False)
    with pytest.raises(RuntimeError, match="MFDS_API_KEY"):
        MfdsEyakeunyoAdapter(api_key=None)


def test_adapter_metadata(adapter: MfdsEyakeunyoAdapter) -> None:
    assert isinstance(adapter, DrugSourceAdapter)
    assert adapter.source_name == "mfds_eyakeunyo"
    assert adapter.license_tag == "kogl_type1"


def test_list_updated_since_none_yields_all(adapter: MfdsEyakeunyoAdapter) -> None:
    fake_client = MagicMock()
    fake_client.get.return_value = _FakeResp(200, SAMPLE_PAGE_RESPONSE)

    with patch.object(adapter, "_get_client", return_value=fake_client), \
         patch.object(adapter, "_wait", return_value=None):
        ids = list(adapter.list_updated_since(since=None, limit=10))

    assert ids == ["195700020", "200100123", "200100999"]
    call = fake_client.get.call_args
    params = call.kwargs.get("params", {})
    assert params["serviceKey"] == "TEST_KEY"
    assert params["type"] == "json"
    assert params["pageNo"] == 1


def test_list_updated_since_filters_by_date(adapter: MfdsEyakeunyoAdapter) -> None:
    fake_client = MagicMock()
    fake_client.get.return_value = _FakeResp(200, SAMPLE_PAGE_RESPONSE)

    with patch.object(adapter, "_get_client", return_value=fake_client), \
         patch.object(adapter, "_wait", return_value=None):
        ids = list(
            adapter.list_updated_since(since=datetime(2024, 1, 1), limit=10)
        )

    # 2020-01-01 은 제외됨
    assert "200100999" not in ids
    assert "195700020" in ids
    assert "200100123" in ids


def test_list_updated_since_respects_limit(adapter: MfdsEyakeunyoAdapter) -> None:
    fake_client = MagicMock()
    fake_client.get.return_value = _FakeResp(200, SAMPLE_PAGE_RESPONSE)

    with patch.object(adapter, "_get_client", return_value=fake_client), \
         patch.object(adapter, "_wait", return_value=None):
        ids = list(adapter.list_updated_since(since=None, limit=1))

    assert ids == ["195700020"]


def test_fetch_detail_returns_first_item(adapter: MfdsEyakeunyoAdapter) -> None:
    single = {
        "header": {"resultCode": "00", "resultMsg": "NORMAL SERVICE."},
        "body": {
            "pageNo": 1,
            "totalCount": 1,
            "numOfRows": 1,
            "items": [SAMPLE_PAGE_RESPONSE["body"]["items"][1]],
        },
    }
    fake_client = MagicMock()
    fake_client.get.return_value = _FakeResp(200, single)

    with patch.object(adapter, "_get_client", return_value=fake_client), \
         patch.object(adapter, "_wait", return_value=None):
        raw = adapter.fetch_detail("200100123")

    assert raw["itemSeq"] == "200100123"
    assert raw["itemName"] == "세티리진정"


def test_fetch_detail_raises_when_missing(adapter: MfdsEyakeunyoAdapter) -> None:
    empty = {
        "header": {"resultCode": "00", "resultMsg": "NORMAL SERVICE."},
        "body": {"pageNo": 1, "totalCount": 0, "items": []},
    }
    fake_client = MagicMock()
    fake_client.get.return_value = _FakeResp(200, empty)

    with patch.object(adapter, "_get_client", return_value=fake_client), \
         patch.object(adapter, "_wait", return_value=None):
        with pytest.raises(ValueError, match="not found"):
            adapter.fetch_detail("99999")


def test_api_error_result_code_raises(adapter: MfdsEyakeunyoAdapter) -> None:
    error_resp = {
        "header": {"resultCode": "22", "resultMsg": "LIMITED NUMBER OF SERVICE REQUESTS EXCEEDS ERROR"},
        "body": {"items": []},
    }
    fake_client = MagicMock()
    fake_client.get.return_value = _FakeResp(200, error_resp)

    with patch.object(adapter, "_get_client", return_value=fake_client), \
         patch.object(adapter, "_wait", return_value=None):
        with pytest.raises(RuntimeError, match="resultCode=22"):
            list(adapter.list_updated_since(since=None, limit=1))


def test_normalize_preserves_entp_name_in_raw_only(
    adapter: MfdsEyakeunyoAdapter,
) -> None:
    """상업정보(entpName)는 raw에만 보관, name_* 필드에는 복사되지 않아야 함 (ADR-007)."""
    raw = SAMPLE_PAGE_RESPONSE["body"]["items"][1]
    candidate = adapter.normalize(raw)

    assert isinstance(candidate, DrugProductCandidate)
    assert candidate.source == "mfds_eyakeunyo"
    assert candidate.source_product_id == "200100123"
    assert candidate.kfda_item_seq == "200100123"
    assert candidate.name_kr == "세티리진정"
    # entpName은 raw에만 보존
    assert candidate.raw["entpName"] == "한국XX제약"
    # DrugProductCandidate에 entp_name 같은 필드가 없음을 보장
    assert not hasattr(candidate, "entp_name")
    assert not hasattr(candidate, "manufacturer")


def test_normalize_indications_and_dosage(adapter: MfdsEyakeunyoAdapter) -> None:
    raw = SAMPLE_PAGE_RESPONSE["body"]["items"][1]
    candidate = adapter.normalize(raw)

    assert "알러지성 비염" in candidate.indications
    assert "1회 10mg" in candidate.dosage


def test_normalize_combines_warnings(adapter: MfdsEyakeunyoAdapter) -> None:
    raw = SAMPLE_PAGE_RESPONSE["body"]["items"][1]
    candidate = adapter.normalize(raw)

    # atpnQesitm + intrcQesitm + seQesitm 모두 합쳐져야 함
    assert candidate.warnings is not None
    assert "[주의사항]" in candidate.warnings
    assert "[상호작용]" in candidate.warnings
    assert "[부작용]" in candidate.warnings


def test_normalize_empty_warnings_returns_none(adapter: MfdsEyakeunyoAdapter) -> None:
    raw = {"itemSeq": "x", "itemName": "y"}
    candidate = adapter.normalize(raw)
    assert candidate.warnings is None


def test_normalize_prescription_defaults_to_false(
    adapter: MfdsEyakeunyoAdapter,
) -> None:
    """e약은요는 전문/일반 구분 필드가 없음 — 기본 False, 후속 단계에서 보강."""
    raw = SAMPLE_PAGE_RESPONSE["body"]["items"][1]
    candidate = adapter.normalize(raw)
    assert candidate.is_prescription is False
