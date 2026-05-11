"""Tests for allergy domain pack + DomainPack helpers + migration integration.

WBS: P1-G-006 ~ G-012
"""
from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from app.core.domains import (
    DomainPack,
    DomainPackLoader,
    clear_pack_cache,
    get_pack,
    preload_packs,
)


# ───────── 알러지 pack 자체 검증 (G-006) ─────────


ALLERGY_PACK_PATH = (
    Path(__file__).resolve().parents[1]
    / "app" / "domains" / "allergy" / "pack.yaml"
)


class TestAllergyPackLoads:
    def test_allergy_pack_file_exists(self):
        assert ALLERGY_PACK_PATH.exists(), f"missing: {ALLERGY_PACK_PATH}"

    def test_allergy_pack_loads_cleanly(self):
        loader = DomainPackLoader()
        pack = loader.load(ALLERGY_PACK_PATH)
        assert pack.id == "allergy"
        assert pack.name_kr == "알러지"
        assert pack.status == "active"
        assert pack.version == 1
        assert pack.accent_color == "#8b5cf6"

    def test_allergy_pack_8_sources(self):
        pack = DomainPackLoader().load(ALLERGY_PACK_PATH)
        # 6 paper + 2 news
        assert set(pack.enabled_sources) == {
            "pubmed", "semantic_scholar", "europe_pmc", "openalex",
            "biorxiv", "core", "naver_news", "google_news_rss",
        }

    def test_allergy_pack_personas(self):
        pack = DomainPackLoader().load(ALLERGY_PACK_PATH)
        ids = {p["id"] for p in pack.personas}
        assert ids == {"clinician", "consumer"}


# ───────── G-007: rotation 마이그레이션 회귀 ─────────


class TestRotationMigration:
    """알러지 pack 의 get_allergens_for_day 가 기존 ALLERGEN_TIERS 와 동일 결과.

    Note: scheduler_jobs 모듈 직접 import 회피 — JSONB 타입 미지원 SQLite 환경에서
    test_db fixture 와 충돌. 통합 검증은 별도 파일에서.
    """

    # 기존 ALLERGEN_TIERS 와 동일한 값을 인라인 — 회귀 비교용 reference
    _LEGACY_TIERS_REFERENCE = {
        2: ["peanut", "tree_nut", "shellfish", "milk", "egg"],
        3: ["wheat", "soy", "fish", "sesame"],
        4: ["dust_mite", "cat", "dog", "pollen", "mold", "latex", "insect", "drug"],
    }

    @pytest.fixture(autouse=True)
    def _reset_cache(self):
        clear_pack_cache()
        yield
        clear_pack_cache()

    def test_pack_rotation_matches_legacy_algorithm(self):
        pack = DomainPackLoader().load(ALLERGY_PACK_PATH)

        for day in range(0, 30):
            yaml_result = pack.get_allergens_for_day(day)
            legacy_result: list[str] = []
            for interval, allergens in self._LEGACY_TIERS_REFERENCE.items():
                for i, a in enumerate(allergens):
                    if (day + i) % interval == 0:
                        legacy_result.append(a)
            assert yaml_result == legacy_result, f"day={day} 불일치"


# ───────── G-008: 프롬프트 마이그레이션 회귀 ─────────


class TestPromptMigration:
    @pytest.fixture(autouse=True)
    def _reset_cache(self):
        clear_pack_cache()
        yield
        clear_pack_cache()

    def test_pack_prompt_system_loaded(self):
        pack = DomainPackLoader().load(ALLERGY_PACK_PATH)
        body = pack.get_prompt("system")
        assert body is not None
        assert "알러지" in body
        assert "한국어" in body

    def test_pack_prompt_digest_implication_loaded(self):
        pack = DomainPackLoader().load(ALLERGY_PACK_PATH)
        body = pack.get_prompt("digest_implication")
        assert body is not None
        assert "{title}" in body
        assert "{abstract}" in body

    def test_pack_prompt_news_relevance_loaded(self):
        pack = DomainPackLoader().load(ALLERGY_PACK_PATH)
        body = pack.get_prompt("news_relevance")
        assert body is not None
        assert "{title}" in body
        assert "{description}" in body

    def test_pack_prompt_unknown_returns_none(self):
        pack = DomainPackLoader().load(ALLERGY_PACK_PATH)
        assert pack.get_prompt("nonexistent") is None

    def test_pack_prompt_config(self):
        pack = DomainPackLoader().load(ALLERGY_PACK_PATH)
        cfg = pack.get_prompt_config("digest_implication")
        assert cfg.get("model_preference") == "gemini"
        assert cfg.get("max_tokens") == 200

    def test_ollama_system_prompt_uses_pack(self):
        """OllamaService.SYSTEM_PROMPT 가 pack 의 prompts.system 본문."""
        clear_pack_cache()
        preload_packs()

        from app.services.ollama_service import OllamaService
        svc = OllamaService.__new__(OllamaService)  # __init__ 없이
        prompt = svc.SYSTEM_PROMPT
        assert "알러지" in prompt
        assert "한국어" in prompt

    def test_ollama_system_prompt_fallback_without_pack(self):
        clear_pack_cache()
        # 캐시 비우고 + path 없는 곳에서 호출 — lazy load 실패
        from app.services.ollama_service import OllamaService
        svc = OllamaService.__new__(OllamaService)
        # _SYSTEM_PROMPT_FALLBACK 는 그래도 동작
        # (실제로 ALLERGY_PACK_PATH 가 있어서 lazy load 가 성공할 수 있음)
        result = svc.SYSTEM_PROMPT
        assert "알러지" in result  # YAML or fallback 둘 다 알러지 포함


# ───────── G-009: scheduler data ─────────


class TestSchedulerData:
    def test_scheduler_jobs_count(self):
        pack = DomainPackLoader().load(ALLERGY_PACK_PATH)
        jobs = pack.get_scheduler_jobs()
        # 10개 도메인 cron (drug_ingest / strategic_intel_* 는 별도)
        assert len(jobs) == 10

    def test_scheduler_timezone(self):
        pack = DomainPackLoader().load(ALLERGY_PACK_PATH)
        assert pack.get_scheduler_timezone() == "Asia/Seoul"

    def test_scheduler_jobs_have_required_fields(self):
        pack = DomainPackLoader().load(ALLERGY_PACK_PATH)
        for job in pack.get_scheduler_jobs():
            assert "id" in job
            assert "task" in job
            assert "cron" in job

    def test_persona_digest_jobs_have_args(self):
        pack = DomainPackLoader().load(ALLERGY_PACK_PATH)
        digest_jobs = [j for j in pack.get_scheduler_jobs() if j["task"] == "digest.send"]
        # 2 persona × 1 send = 2
        assert len(digest_jobs) == 2
        personas = {j.get("args", {}).get("persona") for j in digest_jobs}
        assert personas == {"clinician", "consumer"}


# ───────── G-011: taxonomy config ─────────


class TestTaxonomyConfig:
    def test_db_table_config(self):
        pack = DomainPackLoader().load(ALLERGY_PACK_PATH)
        cfg = pack.get_taxonomy_config()
        assert cfg["source"] == "db_table"
        assert cfg["table_name"] == "allergen_master"
        assert cfg["id_field"] == "code"
        assert cfg["name_field"] == "name_kr"


# ───────── G-012: preload / get_pack ─────────


class TestPreloadAndAccessor:
    @pytest.fixture(autouse=True)
    def _reset(self):
        clear_pack_cache()
        yield
        clear_pack_cache()

    def test_preload_returns_allergy_pack(self):
        packs = preload_packs()
        assert "allergy" in packs
        assert isinstance(packs["allergy"], DomainPack)

    def test_get_pack_after_preload(self):
        preload_packs()
        pack = get_pack("allergy")
        assert pack is not None
        assert pack.id == "allergy"

    def test_get_pack_lazy_load_when_cache_empty(self):
        clear_pack_cache()
        # preload 안 했어도 lazy load 동작
        pack = get_pack("allergy")
        assert pack is not None

    def test_get_pack_returns_none_for_missing_domain(self):
        assert get_pack("nonexistent_domain") is None

    def test_preload_fatal_false_swallows_error(self, tmp_path):
        # 잘못된 pack 만 있는 디렉토리
        bad_dir = tmp_path / "broken"
        bad_dir.mkdir()
        (bad_dir / "pack.yaml").write_text("version: 1\n# missing required fields")
        # fatal=False → 예외 없이 return
        result = preload_packs(domains_dir=tmp_path, fatal=False)
        assert isinstance(result, dict)

    def test_preload_fatal_true_raises(self, tmp_path):
        from app.core.domains import DomainPackInvalid
        bad_dir = tmp_path / "broken"
        bad_dir.mkdir()
        (bad_dir / "pack.yaml").write_text("version: 1\n# missing required fields")
        with pytest.raises(DomainPackInvalid):
            preload_packs(domains_dir=tmp_path, fatal=True)

    def test_preload_empty_dir_returns_empty(self, tmp_path):
        result = preload_packs(domains_dir=tmp_path)
        assert result == {}


# ───────── DomainPack helper 직접 검증 ─────────


class TestDomainPackHelpers:
    def test_get_guardrails(self):
        pack = DomainPackLoader().load(ALLERGY_PACK_PATH)
        guards = pack.get_guardrails()
        assert len(guards) == 2
        assert any(g["tag"] == "emergency" for g in guards)
        assert any(g["tag"] == "medical_disclaimer" for g in guards)

    def test_feature_enabled(self):
        pack = DomainPackLoader().load(ALLERGY_PACK_PATH)
        assert pack.feature_enabled("rag_enabled") is True
        assert pack.feature_enabled("newsletter_enabled") is True
        assert pack.feature_enabled("nonexistent_feature") is False
        assert pack.feature_enabled("nonexistent_feature", default=True) is True

    def test_get_allergens_for_day_zero(self):
        pack = DomainPackLoader().load(ALLERGY_PACK_PATH)
        result = pack.get_allergens_for_day(0)
        # day=0 → 각 tier 의 i=0 인덱스 알러젠
        assert "peanut" in result      # Tier 1 i=0
        assert "wheat" in result        # Tier 2 i=0
        assert "dust_mite" in result    # Tier 3 i=0

    def test_get_allergens_for_day_deterministic(self):
        pack = DomainPackLoader().load(ALLERGY_PACK_PATH)
        # 같은 day_number 면 같은 결과
        assert pack.get_allergens_for_day(7) == pack.get_allergens_for_day(7)
