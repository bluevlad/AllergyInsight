"""Tests for app.core.domains.pack_linter + loader.

WBS: P1-G-001 (schema), P1-G-002 (loader), P1-G-003 (linter),
     P1-G-004 (CLI), P1-G-005 (CI gate)
"""
from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from app.core.domains.loader import (
    DomainPack,
    DomainPackInvalid,
    DomainPackLoader,
)
from app.core.domains.pack_linter import (
    Issue,
    LintResult,
    Severity,
    validate,
)


# ───────── 유효한 최소 pack ─────────


def _minimal_pack() -> dict:
    """모든 필수 필드만 채운 최소 valid pack."""
    return {
        "version": 1,
        "domain": {
            "id": "allergy",
            "name_kr": "알러지",
            "status": "active",
            "accent_color": "#8b5cf6",
        },
        "sources": {
            "enabled": ["pubmed", "semantic_scholar"],
        },
        "taxonomy": {
            "source": "inline",
            "items": [
                {"id": "peanut", "name": "땅콩"},
            ],
        },
        "rag": {
            "vector_store": {
                "backend": "chromadb",
                "collection": "papers",
                "persist_path": "data/chromadb",
            },
            "chunk": {"size": 800, "overlap": 100, "strategy": "fixed"},
            "retrieval": {"top_k": 5, "relevance_threshold": 0.4, "distance": "cosine"},
            "guardrails": [
                {"text": "진단 금지", "severity": "hard"},
            ],
        },
        "prompts": {
            "digest_implication": {"inline": "short prompt"},
        },
        "personas": [
            {
                "id": "clinician",
                "audience": "의료진",
                "digest": {
                    "frequency": "daily",
                    "cron": "0 8 * * *",
                    "max_items": 10,
                },
                "interests": {
                    "source": "subscriber_field",
                    "field": "keywords",
                    "matching": "rule",
                },
                "delivery": {
                    "channel": "email",
                    "template": "templates/clinician.html",
                },
            },
        ],
        "scheduler": {
            "timezone": "Asia/Seoul",
            "jobs": [
                {"id": "collect", "task": "collect.papers", "cron": "0 2 * * *"},
            ],
        },
    }


# ───────── Issue / LintResult ─────────


class TestIssueAndResult:
    def test_issue_str(self):
        i = Issue("E001", Severity.ERROR, "msg", "$.x")
        assert "E001" in str(i)
        assert "ERROR" in str(i)
        assert "$.x" in str(i)

    def test_result_ok_when_no_errors(self):
        r = LintResult()
        assert r.ok is True
        assert r.fails() is False

    def test_result_strict_mode(self):
        r = LintResult()
        r.add(Issue("W101", Severity.WARNING, "w", "$"))
        assert r.ok is True  # 일반 모드 통과
        assert r.fails() is False
        assert r.fails(strict=True) is True

    def test_result_error_always_fails(self):
        r = LintResult()
        r.add(Issue("E001", Severity.ERROR, "e", "$"))
        assert r.ok is False
        assert r.fails() is True
        assert r.fails(strict=True) is True


# ───────── 유효한 pack: 통과 검증 ─────────


class TestValidPack:
    def test_minimal_pack_passes(self):
        r = validate(_minimal_pack())
        assert r.ok, f"errors: {r.errors}"

    def test_minimal_pack_no_unexpected_warnings(self):
        r = validate(_minimal_pack())
        warning_codes = {w.code for w in r.warnings}
        # 가드레일 있고 persona 있고 source 있으므로 W101/W102/W103 없어야 함
        assert "W101" not in warning_codes
        assert "W102" not in warning_codes
        assert "W103" not in warning_codes


# ───────── E001 — 필수 필드 누락 ─────────


class TestE001MissingRequired:
    def test_missing_version(self):
        p = _minimal_pack()
        del p["version"]
        r = validate(p)
        codes = {e.code for e in r.errors}
        assert "E001" in codes

    def test_missing_domain(self):
        p = _minimal_pack()
        del p["domain"]
        r = validate(p)
        assert any(e.code == "E001" for e in r.errors)

    def test_missing_domain_id(self):
        p = _minimal_pack()
        del p["domain"]["id"]
        r = validate(p)
        assert any(e.code == "E001" and "domain.id" in e.path for e in r.errors)

    def test_missing_sources_enabled(self):
        p = _minimal_pack()
        del p["sources"]["enabled"]
        r = validate(p)
        assert any(e.code == "E001" and "sources.enabled" in e.path for e in r.errors)

    def test_missing_guardrail_text(self):
        p = _minimal_pack()
        p["rag"]["guardrails"] = [{"severity": "hard"}]
        r = validate(p)
        assert any(e.code == "E001" and "guardrails" in e.path for e in r.errors)


# ───────── E002 — 타입 불일치 ─────────


class TestE002TypeMismatch:
    def test_top_level_not_dict(self):
        r = validate("not a dict")  # type: ignore[arg-type]
        assert any(e.code == "E002" for e in r.errors)

    def test_sources_enabled_not_list(self):
        p = _minimal_pack()
        p["sources"]["enabled"] = "pubmed"  # string instead of list
        r = validate(p)
        assert any(e.code == "E002" and "sources.enabled" in e.path for e in r.errors)


# ───────── E003 — enum 불일치 ─────────


class TestE003EnumMismatch:
    def test_invalid_status(self):
        p = _minimal_pack()
        p["domain"]["status"] = "ready"
        r = validate(p)
        assert any(e.code == "E003" and "status" in e.path for e in r.errors)

    def test_invalid_vector_backend(self):
        p = _minimal_pack()
        p["rag"]["vector_store"]["backend"] = "milvus"
        r = validate(p)
        assert any(e.code == "E003" and "backend" in e.path for e in r.errors)

    def test_invalid_persona_frequency(self):
        p = _minimal_pack()
        p["personas"][0]["digest"]["frequency"] = "hourly"
        r = validate(p)
        assert any(e.code == "E003" and "frequency" in e.path for e in r.errors)

    def test_version_must_be_one(self):
        p = _minimal_pack()
        p["version"] = 2
        r = validate(p)
        assert any(e.code == "E003" for e in r.errors)


# ───────── E004 — 범위 위반 ─────────


class TestE004RangeViolation:
    def test_chunk_overlap_exceeds_size(self):
        p = _minimal_pack()
        p["rag"]["chunk"]["size"] = 500
        p["rag"]["chunk"]["overlap"] = 600
        r = validate(p)
        assert any(e.code == "E004" and "overlap" in e.path for e in r.errors)

    def test_chunk_size_below_min(self):
        p = _minimal_pack()
        p["rag"]["chunk"]["size"] = 50
        r = validate(p)
        assert any(e.code == "E004" and "chunk.size" in e.path for e in r.errors)

    def test_relevance_threshold_out_of_range(self):
        p = _minimal_pack()
        p["rag"]["retrieval"]["relevance_threshold"] = 1.5
        r = validate(p)
        assert any(e.code == "E004" and "threshold" in e.path for e in r.errors)

    def test_period_days_out_of_range(self):
        p = _minimal_pack()
        p["sources"]["rotation"] = {
            "strategy": "tiered",
            "tiers": [{"period_days": 99, "topics": ["peanut"]}],
        }
        r = validate(p)
        assert any(e.code == "E004" and "period_days" in e.path for e in r.errors)


# ───────── E005 — 슬러그 형식 ─────────


class TestE005SlugFormat:
    def test_invalid_domain_id_uppercase(self):
        p = _minimal_pack()
        p["domain"]["id"] = "Allergy"
        r = validate(p)
        assert any(e.code == "E005" and "domain.id" in e.path for e in r.errors)

    def test_invalid_domain_id_too_short(self):
        p = _minimal_pack()
        p["domain"]["id"] = "ab"
        r = validate(p)
        assert any(e.code == "E005" for e in r.errors)

    def test_invalid_accent_color(self):
        p = _minimal_pack()
        p["domain"]["accent_color"] = "blue"
        r = validate(p)
        assert any(e.code == "E005" and "accent_color" in e.path for e in r.errors)

    def test_invalid_persona_id(self):
        p = _minimal_pack()
        p["personas"][0]["id"] = "Clinician-Pro"  # 대문자 + hyphen
        r = validate(p)
        assert any(e.code == "E005" and "personas" in e.path for e in r.errors)


# ───────── E101 — registry 미등록 source ─────────


class TestE101UnknownSource:
    def test_unknown_source_name(self):
        p = _minimal_pack()
        p["sources"]["enabled"] = ["pubmed", "fake_source"]
        r = validate(p)
        codes = [(e.code, e.path) for e in r.errors]
        assert any(c == "E101" and "fake_source" in str(path) or "[1]" in str(path)
                   for c, path in codes)


# ───────── E102, E103, W106 — prompts ─────────


class TestPromptChecks:
    def test_e103_missing_inline_and_path(self):
        p = _minimal_pack()
        p["prompts"] = {"weird": {"model_preference": "gemini"}}  # no inline/path/ref
        r = validate(p)
        assert any(e.code == "E103" for e in r.errors)

    def test_e102_prompt_path_not_found(self, tmp_path):
        p = _minimal_pack()
        p["prompts"]["digest_implication"] = {"path": "missing/prompt.md"}
        r = validate(p, base_dir=tmp_path)
        assert any(e.code == "E102" for e in r.errors)

    def test_e102_passes_when_file_exists(self, tmp_path):
        p = _minimal_pack()
        prompt_file = tmp_path / "p.md"
        prompt_file.write_text("system prompt body")
        p["prompts"]["digest_implication"] = {"path": "p.md"}
        r = validate(p, base_dir=tmp_path)
        assert not any(e.code == "E102" for e in r.errors)

    def test_w106_long_inline_prompt(self):
        p = _minimal_pack()
        p["prompts"]["digest_implication"] = {"inline": "x" * 200}
        r = validate(p)
        assert any(w.code == "W106" for w in r.warnings)


# ───────── E105 — rotation topic ─────────


class TestE105RotationTopic:
    def test_rotation_topic_not_in_taxonomy(self):
        p = _minimal_pack()
        p["taxonomy"] = {
            "source": "inline",
            "items": [{"id": "peanut", "name": "땅콩"}],
        }
        p["sources"]["rotation"] = {
            "strategy": "tiered",
            "tiers": [{"period_days": 2, "topics": ["peanut", "ghost_topic"]}],
        }
        r = validate(p)
        assert any(e.code == "E105" and "ghost_topic" in e.message for e in r.errors)

    def test_rotation_topic_skipped_when_db_table_taxonomy(self):
        p = _minimal_pack()
        p["taxonomy"] = {"source": "db_table", "table_name": "allergen_master"}
        p["sources"]["rotation"] = {
            "strategy": "tiered",
            "tiers": [{"period_days": 2, "topics": ["whatever"]}],
        }
        r = validate(p)
        # E105 미발생 — runtime 에서 검사
        assert not any(e.code == "E105" for e in r.errors)


# ───────── E106 — persona template ─────────


class TestE106PersonaTemplate:
    def test_template_missing(self, tmp_path):
        p = _minimal_pack()
        # persona 의 template 은 nonexistent.html
        p["personas"][0]["delivery"]["template"] = "nonexistent.html"
        r = validate(p, base_dir=tmp_path)
        assert any(e.code == "E106" for e in r.errors)

    def test_template_found(self, tmp_path):
        p = _minimal_pack()
        (tmp_path / "templates").mkdir()
        (tmp_path / "templates" / "clinician.html").write_text("html")
        r = validate(p, base_dir=tmp_path)
        assert not any(e.code == "E106" for e in r.errors)


# ───────── E107 — cron syntax ─────────


class TestE107CronSyntax:
    def test_invalid_persona_cron(self):
        p = _minimal_pack()
        p["personas"][0]["digest"]["cron"] = "this is not cron"
        r = validate(p)
        assert any(e.code == "E107" for e in r.errors)

    def test_invalid_scheduler_job_cron(self):
        p = _minimal_pack()
        p["scheduler"]["jobs"][0]["cron"] = "99 99 99 99 99"
        r = validate(p)
        assert any(e.code == "E107" for e in r.errors)

    def test_valid_cron_passes(self):
        p = _minimal_pack()
        p["scheduler"]["jobs"][0]["cron"] = "0 0 1 * *"  # 매월 1일 00:00
        r = validate(p)
        assert not any(e.code == "E107" for e in r.errors)


# ───────── E108 — duplicate id ─────────


class TestE108Duplicate:
    def test_duplicate_scheduler_job_id(self):
        p = _minimal_pack()
        p["scheduler"]["jobs"] = [
            {"id": "j1", "task": "t1", "cron": "0 1 * * *"},
            {"id": "j1", "task": "t2", "cron": "0 2 * * *"},
        ]
        r = validate(p)
        assert any(e.code == "E108" for e in r.errors)

    def test_duplicate_persona_id(self):
        p = _minimal_pack()
        p["personas"] = [
            p["personas"][0],
            dict(p["personas"][0]),  # 동일 id
        ]
        r = validate(p)
        assert any(e.code == "E108" for e in r.errors)


# ───────── E109 — invalid timezone ─────────


class TestE109Timezone:
    def test_invalid_timezone(self):
        p = _minimal_pack()
        p["scheduler"]["timezone"] = "Galactic/Earth"
        r = validate(p)
        assert any(e.code == "E109" for e in r.errors)

    def test_valid_iana_timezone(self):
        p = _minimal_pack()
        p["scheduler"]["timezone"] = "UTC"
        r = validate(p)
        assert not any(e.code == "E109" for e in r.errors)


# ───────── W101 — 가드레일 없음 ─────────


class TestW101GuardrailMissing:
    def test_no_guardrails_warns(self):
        p = _minimal_pack()
        del p["rag"]["guardrails"]
        r = validate(p)
        assert any(w.code == "W101" for w in r.warnings)


# ───────── W102 — persona 없음 ─────────


class TestW102PersonaMissing:
    def test_empty_personas_warns(self):
        p = _minimal_pack()
        p["personas"] = []
        r = validate(p)
        assert any(w.code == "W102" for w in r.warnings)


# ───────── W103 — sources.enabled 비어있음 ─────────


class TestW103EmptySources:
    def test_empty_sources_warns(self):
        p = _minimal_pack()
        p["sources"]["enabled"] = []
        r = validate(p)
        assert any(w.code == "W103" for w in r.warnings)


# ───────── W105 — cron 충돌 ─────────


class TestW105CronCollision:
    def test_five_jobs_same_minute(self):
        p = _minimal_pack()
        p["scheduler"]["jobs"] = [
            {"id": f"j{i}", "task": "t", "cron": "0 8 * * *"}
            for i in range(5)
        ]
        r = validate(p)
        assert any(w.code == "W105" for w in r.warnings)

    def test_four_jobs_same_minute_no_warning(self):
        p = _minimal_pack()
        p["scheduler"]["jobs"] = [
            {"id": f"j{i}", "task": "t", "cron": "0 8 * * *"}
            for i in range(4)
        ]
        r = validate(p)
        assert not any(w.code == "W105" for w in r.warnings)


# ───────── W107 — api_key_env 환경변수 ─────────


class TestW107ApiKeyEnv:
    def test_missing_env_with_check(self, monkeypatch):
        monkeypatch.delenv("FAKE_KEY", raising=False)
        p = _minimal_pack()
        p["sources"]["source_config"] = {
            "pubmed": {"api_key_env": "FAKE_KEY"},
        }
        r = validate(p, check_environ=True)
        assert any(w.code == "W107" for w in r.warnings)

    def test_skipped_without_check_environ(self, monkeypatch):
        monkeypatch.delenv("FAKE_KEY", raising=False)
        p = _minimal_pack()
        p["sources"]["source_config"] = {
            "pubmed": {"api_key_env": "FAKE_KEY"},
        }
        r = validate(p, check_environ=False)
        assert not any(w.code == "W107" for w in r.warnings)


# ───────── Loader ─────────


def _write_pack(tmp_path: Path, raw: dict, name: str = "pack.yaml") -> Path:
    """pack.yaml 작성 + 의존 fixture 파일 (persona delivery template) 자동 생성.

    pack_linter 가 base_dir 기준으로 template 파일 존재를 검증하므로,
    Loader/CLI 통합 테스트에서는 template 파일을 함께 만들어야 통과한다.
    """
    p = tmp_path / name
    p.write_text(yaml.safe_dump(raw, allow_unicode=True))

    # persona.delivery.template 자동 생성 (테스트 fixture 안정성)
    for persona in raw.get("personas", []) or []:
        tmpl = (persona.get("delivery") or {}).get("template")
        if tmpl:
            target = tmp_path / tmpl
            target.parent.mkdir(parents=True, exist_ok=True)
            if not target.exists():
                target.write_text("<html>template</html>")

    # prompts.*.path 도 동일 처리
    for prompt in (raw.get("prompts") or {}).values():
        path_str = prompt.get("path") if isinstance(prompt, dict) else None
        if path_str:
            target = tmp_path / path_str
            target.parent.mkdir(parents=True, exist_ok=True)
            if not target.exists():
                target.write_text("prompt body")

    return p


class TestDomainPackLoader:
    def test_load_minimal_pack(self, tmp_path):
        path = _write_pack(tmp_path, _minimal_pack())
        pack = DomainPackLoader().load(path)
        assert isinstance(pack, DomainPack)
        assert pack.id == "allergy"
        assert pack.name_kr == "알러지"
        assert pack.status == "active"
        assert "pubmed" in pack.enabled_sources

    def test_load_raises_on_invalid_pack(self, tmp_path):
        bad = _minimal_pack()
        del bad["domain"]["id"]
        path = _write_pack(tmp_path, bad)
        with pytest.raises(DomainPackInvalid) as exc:
            DomainPackLoader().load(path)
        assert any(i.code == "E001" for i in exc.value.issues)

    def test_load_file_not_found(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            DomainPackLoader().load(tmp_path / "missing.yaml")

    def test_load_all_finds_packs(self, tmp_path):
        # tmp_path/<domain1>/pack.yaml + <domain2>/pack.yaml
        for domain_id in ("allergy", "dermatology"):
            d = tmp_path / domain_id
            d.mkdir()
            raw = _minimal_pack()
            raw["domain"]["id"] = domain_id
            _write_pack(d, raw)
        packs = DomainPackLoader().load_all(tmp_path)
        assert set(packs.keys()) == {"allergy", "dermatology"}

    def test_load_all_empty_dir(self, tmp_path):
        empty = tmp_path / "nothing"
        empty.mkdir()
        assert DomainPackLoader().load_all(empty) == {}

    def test_load_all_skips_non_dirs(self, tmp_path):
        (tmp_path / "random.txt").write_text("ignore me")
        (tmp_path / "allergy").mkdir()
        _write_pack(tmp_path / "allergy", _minimal_pack())
        packs = DomainPackLoader().load_all(tmp_path)
        assert "allergy" in packs

    def test_load_all_duplicate_domain_id_raises(self, tmp_path):
        # 두 디렉토리 모두 domain.id = "allergy"
        for sub in ("a", "b"):
            d = tmp_path / sub
            d.mkdir()
            _write_pack(d, _minimal_pack())  # 둘 다 id="allergy"
        with pytest.raises(DomainPackInvalid) as exc:
            DomainPackLoader().load_all(tmp_path)
        assert any(i.code == "E108" for i in exc.value.issues)


# ───────── CLI ─────────


class TestCli:
    def test_lint_valid_pack_returns_0(self, tmp_path, capsys):
        from app.core.domains.__main__ import main

        path = _write_pack(tmp_path, _minimal_pack())
        code = main(["lint", str(path)])
        assert code == 0

    def test_lint_invalid_pack_returns_1(self, tmp_path, capsys):
        from app.core.domains.__main__ import main

        bad = _minimal_pack()
        bad["domain"]["status"] = "unknown"
        path = _write_pack(tmp_path, bad)
        code = main(["lint", str(path)])
        assert code == 1

    def test_lint_all_finds_packs(self, tmp_path, capsys):
        from app.core.domains.__main__ import main

        for domain_id in ("allergy", "dermatology"):
            d = tmp_path / domain_id
            d.mkdir()
            raw = _minimal_pack()
            raw["domain"]["id"] = domain_id
            _write_pack(d, raw)
        code = main(["lint", "--all", str(tmp_path)])
        assert code == 0

    def test_lint_all_failure(self, tmp_path):
        from app.core.domains.__main__ import main

        d = tmp_path / "broken"
        d.mkdir()
        bad = _minimal_pack()
        del bad["domain"]["id"]
        _write_pack(d, bad)
        code = main(["lint", "--all", str(tmp_path)])
        assert code == 1

    def test_strict_mode_fails_on_warning(self, tmp_path):
        from app.core.domains.__main__ import main

        p = _minimal_pack()
        p["personas"] = []  # W102 triggers
        path = _write_pack(tmp_path, p)
        # 일반 모드: warning 만 → 통과
        assert main(["lint", str(path)]) == 0
        # strict 모드: warning 도 실패
        assert main(["lint", "--strict", str(path)]) == 1
