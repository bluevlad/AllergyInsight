"""drug_ingest.factory 단위 테스트.

환경변수 조합에 따라 어댑터가 제대로 조립되는지 검증한다.
실제 HTTP 호출은 발생하지 않음 (어댑터 생성자만 실행).
"""
from __future__ import annotations

import pytest

from app.services.drug_ingest.factory import build_default_pipeline


def test_factory_builds_openfda_only_when_mfds_key_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("MFDS_API_KEY", raising=False)

    pipeline = build_default_pipeline()

    assert pipeline.source_names == ["openfda"]


def test_factory_builds_both_adapters_when_mfds_key_set(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("MFDS_API_KEY", "test-key")

    pipeline = build_default_pipeline()

    assert "openfda" in pipeline.source_names
    assert "mfds_eyakeunyo" in pipeline.source_names
    assert len(pipeline.source_names) == 2
