"""Feature flags

환경변수 기반 기능 토글의 단일 진입점.

LEGACY_MODULES_ENABLED:
    Phase 1 피벗 과정에서 회원가입/조직관리/진단키트 CRUD 등
    레거시 모듈을 활성화할지 결정. 디폴트 false.
"""
import os


def _truthy(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in ("1", "true", "yes", "on")


LEGACY_MODULES_ENABLED: bool = _truthy(os.getenv("LEGACY_MODULES_ENABLED"), default=False)
