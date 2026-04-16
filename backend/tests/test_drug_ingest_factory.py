"""drug_ingest.factory 단위 테스트.

환경변수 조합에 따라 어댑터가 제대로 조립되는지 검증한다.
실제 HTTP 호출은 발생하지 않음 (어댑터 생성자만 실행).
"""
from __future__ import annotations

import pytest

from app.services.drug_ingest.factory import build_default_pipeline


@pytest.fixture(autouse=True)
def _disable_networked_adapters(monkeypatch: pytest.MonkeyPatch) -> None:
    """기본 활성화되는 네트워크 어댑터(DailyMed/DSLD/RxNorm)는
    factory 구성 검증에서 제외한다.

    테스트 목적은 팩토리가 환경변수를 해석하는 방식을 확인하는 것이지
    네트워크 상태가 아니며, 각 어댑터 단위 테스트에서 별도 검증한다.
    """
    monkeypatch.setenv("DAILYMED_ENABLED", "0")
    monkeypatch.setenv("DSLD_ENABLED", "0")
    monkeypatch.setenv("RXNORM_ENABLED", "0")


def test_factory_builds_openfda_only_when_mfds_key_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("MFDS_API_KEY", raising=False)

    pipeline = build_default_pipeline()

    assert pipeline.source_names == ["openfda"]


def test_factory_builds_all_mfds_adapters_when_mfds_key_set(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("MFDS_API_KEY", "test-key")

    pipeline = build_default_pipeline()

    assert "openfda" in pipeline.source_names
    assert "mfds_eyakeunyo" in pipeline.source_names
    assert "mfds_license" in pipeline.source_names
    assert "mfds_hfood" in pipeline.source_names
    assert len(pipeline.source_names) == 4


def test_factory_enables_dailymed_dsld_rxnorm_by_default(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """기본 플래그로 DailyMed/DSLD/RxNorm 3개가 자동 활성화돼야 한다."""
    monkeypatch.delenv("MFDS_API_KEY", raising=False)
    monkeypatch.delenv("DAILYMED_ENABLED", raising=False)
    monkeypatch.delenv("DSLD_ENABLED", raising=False)
    monkeypatch.delenv("RXNORM_ENABLED", raising=False)

    pipeline = build_default_pipeline()

    assert pipeline.source_names == ["openfda", "dailymed", "dsld", "rxnorm"]


def test_factory_flag_disables_individual_public_adapters(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("MFDS_API_KEY", raising=False)
    monkeypatch.setenv("DAILYMED_ENABLED", "1")
    monkeypatch.setenv("DSLD_ENABLED", "0")
    monkeypatch.setenv("RXNORM_ENABLED", "false")

    pipeline = build_default_pipeline()

    assert "dailymed" in pipeline.source_names
    assert "dsld" not in pipeline.source_names
    assert "rxnorm" not in pipeline.source_names
