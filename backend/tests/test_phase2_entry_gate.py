"""Phase 2 Entry Gate — ADR-011 Trigger #1 검증.

> "두 번째 DomainPack 이 ``core/`` 코드 수정 없이 동작"

본 테스트는 두 가지를 검증한다:
1. dermatology pack 이 lint 통과 + loader 가 실패 없이 로드
2. 두 도메인 (allergy, dermatology) 이 동일한 ``core/`` API 로 작동하되,
   각자의 YAML 만으로 서로 다른 동작 (prompt, rotation, taxonomy, persona) 을 보임

이 테스트가 통과하면 Phase 2 entry 가 가능해진다 (ADR-011 §"분리 Trigger 조건" #1).

WBS: P1-I-001, P1-I-002
"""
from __future__ import annotations

from pathlib import Path

import pytest

from app.core.domains import (
    DomainPack,
    DomainPackLoader,
    clear_pack_cache,
    get_pack,
    preload_packs,
    validate,
)
from app.core.sources import registry
from app.core.sources.base import SourceKind


DOMAINS_DIR = (
    Path(__file__).resolve().parents[1] / "app" / "domains"
)
ALLERGY_PACK = DOMAINS_DIR / "allergy" / "pack.yaml"
DERMATOLOGY_PACK = DOMAINS_DIR / "dermatology" / "pack.yaml"


@pytest.fixture(autouse=True)
def _reset_cache():
    clear_pack_cache()
    yield
    clear_pack_cache()


# ═══════════════════ I-001: Dermatology pack 자체 검증 ═══════════════════


class TestDermatologyPackBasics:
    def test_pack_file_exists(self):
        assert DERMATOLOGY_PACK.exists(), f"missing: {DERMATOLOGY_PACK}"

    def test_lints_clean_no_errors(self):
        import yaml

        raw = yaml.safe_load(DERMATOLOGY_PACK.read_text())
        result = validate(raw, base_dir=DERMATOLOGY_PACK.parent)
        assert result.ok, f"errors: {result.errors}"

    def test_lints_with_no_warnings(self):
        """Phase 2 fixture 는 errors + warnings 모두 0."""
        import yaml

        raw = yaml.safe_load(DERMATOLOGY_PACK.read_text())
        result = validate(raw, base_dir=DERMATOLOGY_PACK.parent)
        assert len(result.warnings) == 0, (
            f"warnings should be 0: {[str(w) for w in result.warnings]}"
        )

    def test_pack_loads_via_loader(self):
        pack = DomainPackLoader().load(DERMATOLOGY_PACK)
        assert isinstance(pack, DomainPack)
        assert pack.id == "dermatology"
        assert pack.name_kr == "피부질환"
        assert pack.status == "active"

    def test_pack_has_10_plus_taxonomy_items(self):
        """v1 fixture: 10개 이상의 inline taxonomy items."""
        pack = DomainPackLoader().load(DERMATOLOGY_PACK)
        items = pack.get_taxonomy_config()["items"]
        assert len(items) >= 10

    def test_pack_has_prompt(self):
        pack = DomainPackLoader().load(DERMATOLOGY_PACK)
        body = pack.get_prompt("digest_implication")
        assert body is not None
        assert "피부" in body


# ═══════════════════ I-002a: 두 pack 공존 ═══════════════════


class TestBothPacksCoexist:
    def test_load_all_finds_both(self):
        packs = DomainPackLoader().load_all(DOMAINS_DIR)
        assert set(packs.keys()) == {"allergy", "dermatology"}

    def test_preload_caches_both(self):
        preload_packs()
        assert get_pack("allergy") is not None
        assert get_pack("dermatology") is not None

    def test_explicit_get_pack(self):
        a = get_pack("allergy")
        d = get_pack("dermatology")
        assert a.id == "allergy"
        assert d.id == "dermatology"


# ═══════════════════ I-002b: 도메인 격리 검증 ═══════════════════


class TestDomainIsolation:
    """각 pack 의 YAML 만 다른데, 행동이 도메인별로 분리되는지."""

    def test_different_accent_colors(self):
        a = get_pack("allergy")
        d = get_pack("dermatology")
        assert a.accent_color == "#8b5cf6"           # violet
        assert d.accent_color == "#ec4899"           # pink
        assert a.accent_color != d.accent_color

    def test_different_taxonomy_source_types(self):
        """allergy=db_table vs dermatology=inline — taxonomy plug-in 검증."""
        a = get_pack("allergy").get_taxonomy_config()
        d = get_pack("dermatology").get_taxonomy_config()
        assert a["source"] == "db_table"
        assert d["source"] == "inline"

    def test_different_rotation_topics(self):
        a_topics = set()
        for tier in get_pack("allergy").raw["sources"]["rotation"]["tiers"]:
            a_topics.update(tier["topics"])
        d_topics = set()
        for tier in get_pack("dermatology").raw["sources"]["rotation"]["tiers"]:
            d_topics.update(tier["topics"])
        # 완전히 분리됨 — overlap 0
        assert a_topics.isdisjoint(d_topics), (
            f"overlap detected: {a_topics & d_topics}"
        )

    def test_different_prompts_per_domain(self):
        a = get_pack("allergy").get_prompt("digest_implication")
        d = get_pack("dermatology").get_prompt("digest_implication")
        assert a is not None and d is not None
        # 두 도메인 모두 한국어 임상 함의지만 본문은 다름
        assert a != d
        # 알러지 prompt 는 알러지 어휘, derm prompt 는 피부 어휘
        assert "알레르기" in a or "알러지" in a
        assert "피부" in d
        # SJS/TEN 은 dermatology 만 명시
        assert "SJS" in d
        assert "SJS" not in a

    def test_different_rag_collections(self):
        a = get_pack("allergy").raw["rag"]["vector_store"]["collection"]
        d = get_pack("dermatology").raw["rag"]["vector_store"]["collection"]
        assert a == "papers_allergy"
        assert d == "papers_dermatology"
        assert a != d

    def test_different_personas(self):
        a_ids = {p["id"] for p in get_pack("allergy").personas}
        d_ids = {p["id"] for p in get_pack("dermatology").personas}
        assert a_ids == {"clinician", "consumer"}
        assert d_ids == {"dermatologist"}
        assert a_ids.isdisjoint(d_ids)

    def test_different_guardrail_tags(self):
        a_tags = {g["tag"] for g in get_pack("allergy").get_guardrails()}
        d_tags = {g["tag"] for g in get_pack("dermatology").get_guardrails()}
        # 공통: medical_disclaimer, emergency. derm 만: drug_safety
        assert "drug_safety" in d_tags
        assert "drug_safety" not in a_tags

    def test_rotation_algorithms_independent(self):
        """같은 day 입력으로 두 도메인이 서로 다른 결과 반환."""
        a = get_pack("allergy")
        d = get_pack("dermatology")
        for day in range(0, 10):
            ar = a.get_allergens_for_day(day)
            dr = d.get_allergens_for_day(day)
            # 결과가 비어있지 않은 day 에 대해 set 자체가 disjoint 여야 함
            if ar and dr:
                assert set(ar).isdisjoint(set(dr)), f"day={day}: {ar} ∩ {dr}"


# ═══════════════════ I-002c: Connector 재사용 검증 ═══════════════════


class TestConnectorReuse:
    """ADR-011 Trigger #1 핵심: dermatology 가 기존 connector 를 그대로 사용."""

    def test_same_registry_serves_both(self):
        """registry 는 도메인 무관 — 동일 connector 인스턴스를 두 도메인이 공유."""
        names = registry.names()
        derm_sources = get_pack("dermatology").enabled_sources
        allergy_sources = get_pack("allergy").enabled_sources

        for src in derm_sources:
            assert src in names, f"dermatology source {src!r} not in registry"
        for src in allergy_sources:
            assert src in names, f"allergy source {src!r} not in registry"

    def test_dermatology_uses_subset_of_paper_sources(self):
        """derm 은 paper 만 사용 (news 제외). 모든 paper connector 가 registry 에 있어야."""
        derm = set(get_pack("dermatology").enabled_sources)
        paper_names = {c.name for c in registry.all_of_kind(SourceKind.PAPER)}
        assert derm.issubset(paper_names), (
            f"derm sources not all paper-typed: {derm - paper_names}"
        )


# ═══════════════════ I-002d: Helper polymorphism ═══════════════════


class TestHelperPolymorphism:
    """동일 helper 메서드가 두 도메인에서 모두 동작 — API 호환성."""

    @pytest.mark.parametrize("domain_id", ["allergy", "dermatology"])
    def test_get_prompt_returns_string(self, domain_id):
        pack = get_pack(domain_id)
        body = pack.get_prompt("digest_implication")
        assert isinstance(body, str)
        assert len(body) > 50

    @pytest.mark.parametrize("domain_id", ["allergy", "dermatology"])
    def test_get_scheduler_jobs_returns_list(self, domain_id):
        pack = get_pack(domain_id)
        jobs = pack.get_scheduler_jobs()
        assert isinstance(jobs, list)
        assert len(jobs) >= 1

    @pytest.mark.parametrize("domain_id", ["allergy", "dermatology"])
    def test_get_allergens_for_day_returns_list(self, domain_id):
        """method 이름이 "allergens" 지만 도메인 무관 — topic 로테이션."""
        pack = get_pack(domain_id)
        result = pack.get_allergens_for_day(0)
        assert isinstance(result, list)

    @pytest.mark.parametrize("domain_id", ["allergy", "dermatology"])
    def test_get_guardrails_returns_list(self, domain_id):
        pack = get_pack(domain_id)
        gs = pack.get_guardrails()
        assert isinstance(gs, list)
        assert len(gs) >= 1

    @pytest.mark.parametrize("domain_id", ["allergy", "dermatology"])
    def test_feature_enabled_works(self, domain_id):
        pack = get_pack(domain_id)
        assert isinstance(pack.feature_enabled("rag_enabled"), bool)
        assert isinstance(pack.feature_enabled("nonexistent"), bool)


# ═══════════════════ I-002e: E105 cross-check 검증 ═══════════════════


class TestRotationTopicsInTaxonomy:
    """inline taxonomy 사용 시 rotation tier 의 모든 topic 이 taxonomy 에 있어야 함.

    이는 pack_linter E105 가 lint 단계에서 강제하는 사항이지만, fixture 자체의
    내부 일관성을 행동으로 검증.
    """

    def test_dermatology_rotation_topics_all_in_taxonomy(self):
        pack = get_pack("dermatology")
        taxonomy_ids = {item["id"] for item in pack.get_taxonomy_config()["items"]}
        rotation_topics: set[str] = set()
        for tier in pack.raw["sources"]["rotation"]["tiers"]:
            rotation_topics.update(tier["topics"])
        missing = rotation_topics - taxonomy_ids
        assert not missing, f"rotation topics not in taxonomy: {missing}"


# ═══════════════════ ADR-011 Trigger #1 최종 검증 ═══════════════════


class TestAdr011Trigger1:
    """ADR-011 §"분리 Trigger 조건" 의 #1 검증 — 본 테스트 전체가 통과하면 Trigger #1 충족.

    > 1. 두 번째 DomainPack 이 ``core/`` 코드 수정 없이 동작

    검증:
    - dermatology pack 은 app/domains/dermatology/ 하위 파일로만 구성
    - 모든 helper (lint, load, get_prompt, get_allergens_for_day 등) 가 도메인 무관
    - connector registry 가 두 도메인 모두 서비스
    - 도메인 격리 (prompt/rotation/taxonomy/persona 모두 다름) 가 YAML 만으로 달성
    """

    def test_summary_trigger_1_met(self):
        # 1. Pack 로드 — core 코드 무수정
        loader = DomainPackLoader()
        allergy = loader.load(ALLERGY_PACK)
        dermatology = loader.load(DERMATOLOGY_PACK)

        # 2. 핵심 helper 모두 동작
        for pack in (allergy, dermatology):
            assert pack.get_prompt("digest_implication") is not None
            assert pack.get_allergens_for_day(0) is not None
            assert pack.get_scheduler_jobs() is not None
            assert pack.get_guardrails() is not None
            assert pack.get_taxonomy_config()

        # 3. 격리 — 두 도메인 출력 명확히 다름
        assert allergy.id != dermatology.id
        assert allergy.get_prompt("digest_implication") != dermatology.get_prompt(
            "digest_implication"
        )
        assert (
            allergy.get_taxonomy_config()["source"]
            != dermatology.get_taxonomy_config()["source"]
        )

        # 4. Registry 공유 — connector 추가 변경 없이 두 도메인 서비스
        for src in dermatology.enabled_sources:
            assert src in registry.names()

        # 5. core/ 디렉토리 파일 목록 (사람 검토용 — git diff 확인 권고)
        # 본 테스트 자체는 core/ 미터치를 강제하지 않음 — git diff 검증으로 보완.
