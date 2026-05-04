"""MFDS 제품허가정보 어댑터 단위 테스트"""
from __future__ import annotations

import json
from datetime import datetime
from typing import Any
from unittest.mock import MagicMock, patch

import httpx
import pytest

from app.services.drug_ingest.sources.base import DrugProductCandidate, DrugSourceAdapter
from app.services.drug_ingest.sources.mfds_license import MfdsLicenseAdapter


SAMPLE_PAGE_RESPONSE: dict[str, Any] = {
    "header": {"resultCode": "00", "resultMsg": "NORMAL SERVICE."},
    "body": {
        "pageNo": 1,
        "totalCount": 3,
        "numOfRows": 100,
        "items": [
            {
                "ITEM_SEQ": "200400001",
                "ITEM_NAME": "세티리진정10mg",
                "ENTP_NAME": "한국제약(주)",
                "MAIN_ITEM_INGR": "세티리진염산염",
                "ATC_CODE": "R06AE07",
                "ETC_OTC_NAME": "일반의약품",
                "CHNG_DATE": "20250601",
                "EE_DOC_DATA": "알레르기 비염, 만성 두드러기에 효능.",
                "UD_DOC_DATA": "1일 1회 10mg 복용.",
                "NB_DOC_DATA": "졸림 주의.",
            },
            {
                "ITEM_SEQ": "200400002",
                "ITEM_NAME": "몬테루카스트나트륨정10mg",
                "ENTP_NAME": "다른제약(주)",
                "MAIN_ITEM_INGR": "몬테루카스트나트륨",
                "ATC_CODE": "R03DC03",
                "ETC_OTC_NAME": "전문의약품",
                "CHNG_DATE": "20260101",
            },
            {
                "ITEM_SEQ": "200400003",
                "ITEM_NAME": "비관련약물",
                "ENTP_NAME": "어딘가제약",
                "ATC_CODE": "C09AA01",
                "CHNG_DATE": "20260201",
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
            req = httpx.Request("GET", MfdsLicenseAdapter.BASE_URL)
            raise httpx.HTTPStatusError(
                "err", request=req, response=httpx.Response(self.status_code, request=req)
            )


@pytest.fixture
def adapter() -> MfdsLicenseAdapter:
    return MfdsLicenseAdapter(api_key="TEST_KEY", timeout=5.0)


def test_missing_key_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("MFDS_API_KEY", raising=False)
    with pytest.raises(RuntimeError, match="MFDS_API_KEY"):
        MfdsLicenseAdapter(api_key=None)


def test_adapter_metadata(adapter: MfdsLicenseAdapter) -> None:
    assert isinstance(adapter, DrugSourceAdapter)
    assert adapter.source_name == "mfds_license"
    assert adapter.license_tag == "kogl_type1"


def test_list_filters_by_atc_whitelist(adapter: MfdsLicenseAdapter) -> None:
    fake_client = MagicMock()
    fake_client.get.return_value = _FakeResp(200, SAMPLE_PAGE_RESPONSE)

    with patch.object(adapter, "_get_client", return_value=fake_client), \
         patch.object(adapter, "_wait", return_value=None):
        ids = list(adapter.list_updated_since(since=None, limit=10))

    # C09AA01 은 ATC 화이트리스트에 포함되지 않으므로 제외
    assert "200400003" not in ids
    assert "200400001" in ids
    assert "200400002" in ids


def test_list_filters_by_chng_date(adapter: MfdsLicenseAdapter) -> None:
    fake_client = MagicMock()
    fake_client.get.return_value = _FakeResp(200, SAMPLE_PAGE_RESPONSE)

    with patch.object(adapter, "_get_client", return_value=fake_client), \
         patch.object(adapter, "_wait", return_value=None):
        ids = list(
            adapter.list_updated_since(since=datetime(2026, 1, 1), limit=10)
        )

    assert "200400001" not in ids  # 20250601 < 20260101
    assert "200400002" in ids


def test_list_respects_limit(adapter: MfdsLicenseAdapter) -> None:
    fake_client = MagicMock()
    fake_client.get.return_value = _FakeResp(200, SAMPLE_PAGE_RESPONSE)

    with patch.object(adapter, "_get_client", return_value=fake_client), \
         patch.object(adapter, "_wait", return_value=None):
        ids = list(adapter.list_updated_since(since=None, limit=1))

    assert len(ids) == 1


def test_normalize_etc_otc_prescription(adapter: MfdsLicenseAdapter) -> None:
    """전문의약품 구분 검사."""
    raw_otc = SAMPLE_PAGE_RESPONSE["body"]["items"][0]
    candidate_otc = adapter.normalize(raw_otc)
    assert candidate_otc.is_prescription is False

    raw_rx = SAMPLE_PAGE_RESPONSE["body"]["items"][1]
    candidate_rx = adapter.normalize(raw_rx)
    assert candidate_rx.is_prescription is True


def test_normalize_atc_code(adapter: MfdsLicenseAdapter) -> None:
    raw = SAMPLE_PAGE_RESPONSE["body"]["items"][0]
    candidate = adapter.normalize(raw)
    assert candidate.atc_code == "R06AE07"


def test_normalize_entp_not_in_name_fields(adapter: MfdsLicenseAdapter) -> None:
    """ADR-007: 업체명은 raw 보관만, name_* 미노출."""
    raw = SAMPLE_PAGE_RESPONSE["body"]["items"][0]
    candidate = adapter.normalize(raw)
    assert candidate.raw["ENTP_NAME"] == "한국제약(주)"
    assert not hasattr(candidate, "entp_name")
    assert not hasattr(candidate, "manufacturer")


def test_normalize_indications_and_warnings(adapter: MfdsLicenseAdapter) -> None:
    raw = SAMPLE_PAGE_RESPONSE["body"]["items"][0]
    candidate = adapter.normalize(raw)
    assert isinstance(candidate, DrugProductCandidate)
    assert candidate.source == "mfds_license"
    assert "알레르기 비염" in candidate.indications
    assert candidate.warnings == "졸림 주의."
