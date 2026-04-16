"""MFDS 건강기능식품 어댑터 단위 테스트"""
from __future__ import annotations

import json
from datetime import datetime
from typing import Any
from unittest.mock import MagicMock, patch

import httpx
import pytest

from app.services.drug_ingest.sources.base import DrugProductCandidate, DrugSourceAdapter
from app.services.drug_ingest.sources.mfds_hfood import MfdsHfoodAdapter


SAMPLE_PAGE_RESPONSE: dict[str, Any] = {
    "header": {"resultCode": "00", "resultMsg": "NORMAL SERVICE."},
    "body": {
        "pageNo": 1,
        "totalCount": 3,
        "numOfRows": 100,
        "items": [
            {
                "PRDLST_REPORT_NO": "20240001001",
                "PRDLST_NM": "프로바이오틱스 면역포뮬러",
                "BSSH_NM": "건강식품(주)",
                "PRIMARY_FNCLTY": "유산균 증식 및 유해균 억제, 면역 기능 개선에 도움",
                "INDIV_RAW_MATRL_NM": "락토바실러스 플란타룸 200억 CFU",
                "DAILY_INTK_HINT_MPB": "1일 1회, 1캡슐(500mg)",
                "CSMNT": "알레르기 체질인 경우 주의.",
                "ALLERGIC_MTRL": "대두, 우유",
                "PRMS_DT": "20240301",
            },
            {
                "PRDLST_REPORT_NO": "20240002002",
                "PRDLST_NM": "비타민D 1000IU",
                "BSSH_NM": "비타민회사(주)",
                "PRIMARY_FNCLTY": "비타민D 보충, 칼슘 흡수 촉진",
                "INDIV_RAW_MATRL_NM": "비타민D3 콜레칼시페롤 25mcg",
                "DAILY_INTK_HINT_MPB": "1일 1회 1정",
                "PRMS_DT": "20260101",
            },
            {
                "PRDLST_REPORT_NO": "20240003003",
                "PRDLST_NM": "다이어트 가르시니아",
                "BSSH_NM": "관련없는회사",
                "PRIMARY_FNCLTY": "체지방 감소에 도움",
                "INDIV_RAW_MATRL_NM": "가르시니아캄보지아 HCA 250mg",
                "PRMS_DT": "20250101",
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
            req = httpx.Request("GET", MfdsHfoodAdapter.BASE_URL)
            raise httpx.HTTPStatusError(
                "err", request=req, response=httpx.Response(self.status_code, request=req)
            )


@pytest.fixture
def adapter() -> MfdsHfoodAdapter:
    return MfdsHfoodAdapter(api_key="TEST_KEY", timeout=5.0)


def test_missing_key_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("MFDS_API_KEY", raising=False)
    with pytest.raises(RuntimeError, match="MFDS_API_KEY"):
        MfdsHfoodAdapter(api_key=None)


def test_adapter_metadata(adapter: MfdsHfoodAdapter) -> None:
    assert isinstance(adapter, DrugSourceAdapter)
    assert adapter.source_name == "mfds_hfood"
    assert adapter.license_tag == "kogl_type1"


def test_list_filters_by_keyword(adapter: MfdsHfoodAdapter) -> None:
    fake_client = MagicMock()
    fake_client.get.return_value = _FakeResp(200, SAMPLE_PAGE_RESPONSE)

    with patch.object(adapter, "_get_client", return_value=fake_client), \
         patch.object(adapter, "_wait", return_value=None):
        ids = list(adapter.list_updated_since(since=None, limit=10))

    # "면역", "유산균", "비타민D" 키워드 → 1, 2 통과 / "가르시니아" → 제외
    assert "20240001001" in ids
    assert "20240002002" in ids
    assert "20240003003" not in ids


def test_list_filters_by_date(adapter: MfdsHfoodAdapter) -> None:
    fake_client = MagicMock()
    fake_client.get.return_value = _FakeResp(200, SAMPLE_PAGE_RESPONSE)

    with patch.object(adapter, "_get_client", return_value=fake_client), \
         patch.object(adapter, "_wait", return_value=None):
        ids = list(
            adapter.list_updated_since(since=datetime(2026, 1, 1), limit=10)
        )

    assert "20240001001" not in ids  # 20240301 < 20260101
    assert "20240002002" in ids


def test_normalize_supplement_type(adapter: MfdsHfoodAdapter) -> None:
    raw = SAMPLE_PAGE_RESPONSE["body"]["items"][0]
    candidate = adapter.normalize(raw)
    assert isinstance(candidate, DrugProductCandidate)
    assert candidate.product_type == "supplement"
    assert candidate.is_prescription is False


def test_normalize_preserves_bssh_in_raw(adapter: MfdsHfoodAdapter) -> None:
    """ADR-007: 업소명은 raw 보관만."""
    raw = SAMPLE_PAGE_RESPONSE["body"]["items"][0]
    candidate = adapter.normalize(raw)
    assert candidate.raw["BSSH_NM"] == "건강식품(주)"


def test_normalize_functional_claims(adapter: MfdsHfoodAdapter) -> None:
    raw = SAMPLE_PAGE_RESPONSE["body"]["items"][0]
    candidate = adapter.normalize(raw)
    assert "면역 기능 개선" in (candidate.indications or "")


def test_normalize_warnings(adapter: MfdsHfoodAdapter) -> None:
    raw = SAMPLE_PAGE_RESPONSE["body"]["items"][0]
    candidate = adapter.normalize(raw)
    assert candidate.warnings is not None
    assert "[섭취 시 주의]" in candidate.warnings
    assert "[알레르기 유발원료]" in candidate.warnings


def test_normalize_no_warnings(adapter: MfdsHfoodAdapter) -> None:
    raw = SAMPLE_PAGE_RESPONSE["body"]["items"][1]
    candidate = adapter.normalize(raw)
    assert candidate.warnings is None
