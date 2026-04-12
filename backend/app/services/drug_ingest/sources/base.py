"""약물 정보 소스 어댑터 ABC

모든 소스 어댑터는 본 인터페이스를 구현한다.
소스별 API·XML·HTML 차이를 어댑터 내부에 캡슐화하고,
파이프라인은 DrugProductCandidate 표준 포맷만 다룬다.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Iterable


@dataclass
class DrugProductCandidate:
    """소스 어댑터가 파이프라인에 전달하는 정규화 후보.

    파이프라인(pipeline.py)이 이를 drug_products 테이블에 upsert한다.
    """

    source: str
    source_product_id: str

    atc_code: str | None = None
    rxcui: str | None = None
    kfda_item_seq: str | None = None

    name_kr: str | None = None
    name_en: str | None = None

    product_type: str = "drug"  # "drug" | "supplement"
    is_prescription: bool = False

    routes: list[str] = field(default_factory=list)
    indications: str | None = None
    dosage: str | None = None
    warnings: str | None = None

    raw: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.product_type not in ("drug", "supplement"):
            raise ValueError(
                f"product_type must be 'drug' or 'supplement', got: {self.product_type}"
            )


class DrugSourceAdapter(ABC):
    """모든 소스 어댑터의 공통 인터페이스."""

    source_name: str = ""
    license_tag: str = ""  # "cc0" | "public_domain" | "kogl_type1" | ...

    @abstractmethod
    def list_updated_since(
        self,
        since: datetime | None,
        limit: int | None = None,
    ) -> Iterable[str]:
        """since 이후 갱신된 제품의 source_product_id 목록.

        since=None 이면 전체 수집 (초기 적재용).
        """

    @abstractmethod
    def fetch_detail(self, source_product_id: str) -> dict[str, Any]:
        """개별 제품의 원본 응답을 그대로 반환 (JSON/XML → dict)."""

    @abstractmethod
    def normalize(self, raw: dict[str, Any]) -> DrugProductCandidate:
        """원본 응답 → DrugProductCandidate."""

    def fetch_and_normalize(self, source_product_id: str) -> DrugProductCandidate:
        raw = self.fetch_detail(source_product_id)
        return self.normalize(raw)
