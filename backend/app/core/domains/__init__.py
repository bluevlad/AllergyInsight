"""DomainPack framework — Vertical Insight Framework 의 도메인 정의 계층.

설계 문서:
- plans/domain-pack-yaml-schema-v1.md
- adr/011-vertical-insight-framework.md

DomainPack 은 도메인별 차이 (sources, taxonomy, prompts, personas, scheduler)
를 코드 밖 YAML 로 선언한다. ``DomainPackLoader.load_all()`` 이 앱 시작 시점에
호출되어 fail-fast 로딩한다.

모듈 레벨 accessor:
    get_pack(domain_id) — 캐시된 DomainPack 반환 (없으면 lazy load 시도)
    preload_packs() — 앱 startup 에서 호출, 모든 pack 일괄 로드
"""
from __future__ import annotations

import logging
from pathlib import Path

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

logger = logging.getLogger(__name__)

# 모듈 캐시 — preload_packs / get_pack 가 채움
_LOADED: dict[str, DomainPack] = {}


def _default_domains_dir() -> Path:
    """기본 domains 디렉토리 — ``backend/app/domains``."""
    # this file: backend/app/core/domains/__init__.py
    # → 부모 4번 위로: backend/app/
    return Path(__file__).resolve().parents[2] / "domains"


def preload_packs(
    domains_dir: Path | None = None,
    *,
    fatal: bool = False,
) -> dict[str, DomainPack]:
    """``domains_dir`` 하위 모든 pack 을 로드해 모듈 캐시에 채움 (G-012).

    Args:
        domains_dir: None 이면 backend/app/domains 사용
        fatal: True 시 검증 실패가 예외로 전파 (운영 — fail-fast).
               False (default) 시 log.warning 만 출력 (개발/마이그레이션).

    Returns:
        도메인 id → DomainPack
    """
    target = Path(domains_dir) if domains_dir else _default_domains_dir()
    try:
        loader = DomainPackLoader()
        packs = loader.load_all(target)
    except DomainPackInvalid as e:
        if fatal:
            raise
        logger.warning("DomainPack 로드 실패 (무시): %s", e)
        return dict(_LOADED)
    except Exception as e:
        if fatal:
            raise
        logger.warning("DomainPack 로드 예외 (무시): %s", e)
        return dict(_LOADED)

    _LOADED.update(packs)
    logger.info(
        "DomainPack preload: %d 개 로드 (ids=%s)",
        len(packs),
        sorted(packs.keys()),
    )
    return packs


def get_pack(domain_id: str = "allergy") -> DomainPack | None:
    """캐시된 DomainPack 반환 (캐시 미존재 시 lazy load 시도).

    소비자 (scheduler_jobs, ollama_service 등) 는 이 함수를 통해 pack 에 접근.
    pack 미존재 시 None — 호출자는 legacy 폴백 사용.
    """
    if domain_id in _LOADED:
        return _LOADED[domain_id]

    candidate = _default_domains_dir() / domain_id / "pack.yaml"
    if not candidate.exists():
        return None

    try:
        pack = DomainPackLoader().load(candidate)
    except Exception as e:
        logger.warning("lazy DomainPack 로드 실패 (%s): %s", domain_id, e)
        return None

    _LOADED[domain_id] = pack
    return pack


def clear_pack_cache() -> None:
    """테스트용 — 캐시 초기화."""
    _LOADED.clear()


__all__ = [
    "DomainPack",
    "DomainPackInvalid",
    "DomainPackLoader",
    "Issue",
    "LintResult",
    "Severity",
    "validate",
    "get_pack",
    "preload_packs",
    "clear_pack_cache",
]
