"""Source Connector Registry.

@register("name") 데코레이터로 클래스를 등록하고,
get / all_of_kind / names 로 조회한다.

DomainPack YAML 의 sources.enabled 항목이 이 registry 의 키와 1:1 매칭된다.
"""
from __future__ import annotations

from typing import Callable, Type

from app.core.sources.base import SourceConnector, SourceKind

_REGISTRY: dict[str, Type[SourceConnector]] = {}


def register(
    name: str,
) -> Callable[[Type[SourceConnector]], Type[SourceConnector]]:
    """Connector 클래스를 registry 에 등록.

    Example:
        @register("pubmed")
        class PubMedConnector(PaperSourceConnector):
            ...

    Raises:
        ValueError: 동일 name 이 이미 등록됨.
    """

    def decorator(cls: Type[SourceConnector]) -> Type[SourceConnector]:
        if name in _REGISTRY:
            existing = _REGISTRY[name].__name__
            raise ValueError(
                f"Source '{name}' already registered as {existing}"
            )
        cls.name = name
        _REGISTRY[name] = cls
        return cls

    return decorator


def get(name: str) -> SourceConnector:
    """이름으로 connector 인스턴스 생성 (생성자 인자 없음 기준)."""
    if name not in _REGISTRY:
        raise KeyError(
            f"Source '{name}' not registered. "
            f"Registered: {sorted(_REGISTRY.keys())}"
        )
    return _REGISTRY[name]()


def all_of_kind(kind: SourceKind) -> list[SourceConnector]:
    """특정 kind 의 모든 등록 connector 인스턴스."""
    return [cls() for cls in _REGISTRY.values() if cls.kind == kind]


def names() -> list[str]:
    """등록된 connector 이름 목록 (정렬)."""
    return sorted(_REGISTRY.keys())


def unregister(name: str) -> None:
    """테스트용 — 등록 해제."""
    _REGISTRY.pop(name, None)


def clear() -> None:
    """테스트용 — 전체 registry 초기화."""
    _REGISTRY.clear()
