"""DomainPack 로더.

YAML 파일을 읽어 ``pack_linter`` 로 검증하고 ``DomainPack`` 객체로 반환한다.
``load_all()`` 은 앱 시작 시점에 호출되어 fail-fast 로딩한다.

WBS: P1-G-002
설계 문서: plans/domain-pack-yaml-schema-v1.md §6
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from app.core.domains.pack_linter import Issue, LintResult, Severity, validate

logger = logging.getLogger(__name__)


class DomainPackInvalid(Exception):
    """DomainPack 검증 실패. ``issues`` 에 모든 에러 보관."""

    def __init__(self, path: Path, issues: list[Issue]) -> None:
        self.path = path
        self.issues = issues
        msg = f"DomainPack 검증 실패: {path}\n" + "\n".join(
            f"  {i}" for i in issues
        )
        super().__init__(msg)


@dataclass(frozen=True)
class DomainPack:
    """파싱된 DomainPack — pack.yaml 의 dict 표현 + 메타데이터."""

    id: str
    name_kr: str
    raw: dict[str, Any]            # 원본 yaml dict
    path: Path                     # pack.yaml 경로
    base_dir: Path                 # pack.yaml 의 부모 디렉토리

    @property
    def version(self) -> int:
        return int(self.raw.get("version", 1))

    @property
    def status(self) -> str:
        return self.raw.get("domain", {}).get("status", "draft")

    @property
    def accent_color(self) -> str | None:
        return self.raw.get("domain", {}).get("accent_color")

    @property
    def enabled_sources(self) -> list[str]:
        return list(self.raw.get("sources", {}).get("enabled", []) or [])

    @property
    def personas(self) -> list[dict[str, Any]]:
        return list(self.raw.get("personas", []) or [])

    # ───────── Phase 1.G 마이그레이션 헬퍼 ─────────

    def get_allergens_for_day(self, day_number: int) -> list[str]:
        """결정적 로테이션 — sources.rotation.tiers 기반.

        scheduler_jobs.get_allergens_for_day 의 YAML 백엔드 (G-007).
        기존 ALLERGEN_TIERS 와 동일 알고리즘:
            for tier in tiers:
                for i, topic in enumerate(tier.topics):
                    if (day_number + i) % tier.period_days == 0:
                        include topic
        """
        rotation = self.raw.get("sources", {}).get("rotation", {})
        if rotation.get("strategy") != "tiered":
            return []
        result: list[str] = []
        for tier in rotation.get("tiers", []) or []:
            period = tier.get("period_days")
            topics = tier.get("topics") or []
            if not isinstance(period, int) or period < 1:
                continue
            for i, topic in enumerate(topics):
                if (day_number + i) % period == 0:
                    result.append(topic)
        return result

    def get_prompt(self, slot: str) -> str | None:
        """프롬프트 슬롯 (e.g. "system", "digest_implication") 본문 반환 (G-008).

        Resolution 순서: inline → path → ref.
        모두 부재 시 None.

        Returns:
            프롬프트 본문 문자열, 또는 None.
        """
        prompts = self.raw.get("prompts") or {}
        entry = prompts.get(slot)
        if not isinstance(entry, dict):
            return None

        if entry.get("inline"):
            return entry["inline"]

        path_str = entry.get("path")
        if path_str:
            resolved = (self.base_dir / path_str).resolve()
            try:
                return resolved.read_text(encoding="utf-8")
            except FileNotFoundError:
                return None

        ref = entry.get("ref")
        if ref and ref != slot:
            # 단순 참조 (cyclic detection 은 미결 D1, v1 미구현)
            return self.get_prompt(ref)

        return None

    def get_prompt_config(self, slot: str) -> dict[str, Any]:
        """프롬프트 slot 의 메타 (model_preference, max_tokens, temperature).

        본문 없이 LLM 호출 옵션만 필요할 때 사용.
        """
        prompts = self.raw.get("prompts") or {}
        entry = prompts.get(slot)
        if not isinstance(entry, dict):
            return {}
        return {
            k: v for k, v in entry.items()
            if k in ("model_preference", "max_tokens", "temperature")
        }

    def get_scheduler_jobs(self) -> list[dict[str, Any]]:
        """scheduler.jobs 목록 반환 (G-009 — 데이터 추출).

        Phase 1.G 단계에서는 YAML 이 SoT 가 되지만 실제 cron 등록은
        ``scheduler_service.py`` 가 담당. Phase 2 에서 자동 등록으로 전환 예정.
        """
        return list(self.raw.get("scheduler", {}).get("jobs", []) or [])

    def get_scheduler_timezone(self) -> str:
        return self.raw.get("scheduler", {}).get("timezone", "UTC")

    def get_taxonomy_config(self) -> dict[str, Any]:
        """taxonomy 블록 dict 반환 (G-011 — 데이터 추출).

        소비자가 source 타입 (db_table | yaml | inline) 에 따라 적절히 처리:
        - db_table: AllergenMaster 등 ORM 모델 조회
        - yaml: ``base_dir / file`` 읽기
        - inline: ``items`` 그대로 사용
        """
        return dict(self.raw.get("taxonomy", {}) or {})

    def get_guardrails(self) -> list[dict[str, Any]]:
        """rag.guardrails 목록 반환."""
        return list(self.raw.get("rag", {}).get("guardrails", []) or [])

    def feature_enabled(self, key: str, default: bool = False) -> bool:
        """features.{key} 토글 — 미정의 시 default."""
        return bool(self.raw.get("features", {}).get(key, default))


class DomainPackLoader:
    """DomainPack 로딩 + 검증 진입점.

    Usage:
        loader = DomainPackLoader()
        pack = loader.load(Path("backend/app/domains/allergy/pack.yaml"))
        # → DomainPackInvalid 가 raise 되면 startup abort

        all_packs = loader.load_all(Path("backend/app/domains"))
    """

    def __init__(
        self,
        *,
        check_environ: bool = False,
        log_warnings: bool = True,
    ):
        """
        Args:
            check_environ: W107 (api_key_env 환경변수) 체크 활성화
            log_warnings: 검증 통과 후에도 W### 를 log.warning 으로 출력
        """
        self.check_environ = check_environ
        self.log_warnings = log_warnings

    def load(self, path: Path) -> DomainPack:
        """단일 pack.yaml 로딩 + 검증.

        Raises:
            FileNotFoundError: path 미존재
            yaml.YAMLError: YAML 파싱 실패
            DomainPackInvalid: linter E### 발견 (fail-fast)
        """
        path = Path(path).resolve()
        if not path.exists():
            raise FileNotFoundError(f"DomainPack 파일 미존재: {path}")

        with open(path, "r", encoding="utf-8") as f:
            raw = yaml.safe_load(f)

        if not isinstance(raw, dict):
            raise DomainPackInvalid(
                path,
                [
                    # pack_linter 가 동일 에러를 생성하지만, 여기서 빠르게 차단
                    self._top_level_dict_error(path),
                ],
            )

        result: LintResult = validate(
            raw,
            base_dir=path.parent,
            check_environ=self.check_environ,
        )

        if not result.ok:
            raise DomainPackInvalid(path, result.errors)

        if self.log_warnings:
            for w in result.warnings:
                logger.warning("[%s] %s", path.name, w)

        domain = raw.get("domain", {})
        return DomainPack(
            id=domain["id"],
            name_kr=domain["name_kr"],
            raw=raw,
            path=path,
            base_dir=path.parent,
        )

    def load_all(self, domains_dir: Path) -> dict[str, DomainPack]:
        """``domains_dir`` 하위의 모든 ``<domain>/pack.yaml`` 일괄 로딩.

        Returns:
            domain id → DomainPack
        """
        domains_dir = Path(domains_dir).resolve()
        if not domains_dir.exists():
            logger.debug("domains 디렉토리 없음 — 빈 dict 반환: %s", domains_dir)
            return {}

        packs: dict[str, DomainPack] = {}
        for sub in sorted(domains_dir.iterdir()):
            if not sub.is_dir():
                continue
            candidate = sub / "pack.yaml"
            if not candidate.exists():
                continue
            pack = self.load(candidate)
            if pack.id in packs:
                raise DomainPackInvalid(
                    candidate,
                    [
                        Issue(
                            code="E108",
                            severity=Severity.ERROR,
                            message=(
                                f"중복된 domain.id: {pack.id!r} "
                                f"(기존: {packs[pack.id].path})"
                            ),
                            path="$.domain.id",
                        )
                    ],
                )
            packs[pack.id] = pack

        return packs

    @staticmethod
    def _top_level_dict_error(path: Path) -> Issue:
        return Issue(
            code="E002",
            severity=Severity.ERROR,
            message=f"YAML 최상위가 dict 가 아님: {path}",
            path="$",
        )
