"""openFDA drug/label API 어댑터

FDA 공개 의약품 라벨 데이터. 라이선스: CC0 (Public Domain).
API 키 선택: 키 없음 240 req/min·1000/day, 키 있음 240 req/min·120000/day.

API 문서: https://open.fda.gov/apis/drug/label/
필드 참조: https://open.fda.gov/apis/drug/label/searchable-fields/
"""
from __future__ import annotations

import logging
import os
import time
from datetime import datetime
from typing import Any, Iterable

import httpx

from .base import DrugSourceAdapter, DrugProductCandidate

logger = logging.getLogger(__name__)


class OpenFdaLabelAdapter(DrugSourceAdapter):
    """openFDA drug/label 수집 어댑터."""

    source_name = "openfda"
    license_tag = "cc0"

    BASE_URL = "https://api.fda.gov/drug/label.json"
    REQUEST_INTERVAL = 0.3  # 키 없음 240/min ≈ 0.25s, 여유 있게 0.3s
    DEFAULT_LIMIT = 100  # openFDA max per request

    # 수집 범위 — openFDA pharm_class_epc 필드의 실제 EPC 클래스명.
    # 각 값은 openFDA 실측(count=openfda.pharm_class_epc.exact)으로 검증됨.
    # 따옴표 phrase match 로 쿼리될 때 [EPC] 접미사는 생략해도 토크나이저가 매칭함.
    DEFAULT_PHARM_CLASS_EPC_VALUES: tuple[str, ...] = (
        # 알러지 치료제
        "Histamine-1 Receptor Antagonist",          # H1 antihistamine
        "Corticosteroid",                            # 국소/흡입/전신 스테로이드 (광범위)
        "Leukotriene Receptor Antagonist",           # montelukast 등
        "beta-Adrenergic Agonist",                   # 기관지 확장제 (SABA/LABA, epinephrine)
        "Anti-IgE",                                  # omalizumab
        # 알러겐 추출물 (면역요법)
        "Standardized Chemical Allergen",
        "Non-Standardized Food Allergenic Extract",
        "Non-Standardized Plant Allergenic Extract",
        "Standardized Insect Venom Allergenic Extract",
        "Non-Standardized Fungal Allergenic Extract",
        "Non-Standardized Chemical Allergen",
    )

    def __init__(
        self,
        api_key: str | None = None,
        timeout: float = 30.0,
        pharm_class_epc_values: list[str] | None = None,
    ) -> None:
        self.api_key = api_key or os.getenv("OPENFDA_API_KEY")
        self._client: httpx.Client | None = None
        self._last_request_time = 0.0
        self._timeout = timeout
        self.pharm_class_epc_values: list[str] = list(
            pharm_class_epc_values or self.DEFAULT_PHARM_CLASS_EPC_VALUES
        )

    def _get_client(self) -> httpx.Client:
        if self._client is None:
            self._client = httpx.Client(timeout=self._timeout)
        return self._client

    def close(self) -> None:
        if self._client is not None:
            self._client.close()
            self._client = None

    def __enter__(self) -> "OpenFdaLabelAdapter":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    def _wait(self) -> None:
        elapsed = time.time() - self._last_request_time
        if elapsed < self.REQUEST_INTERVAL:
            time.sleep(self.REQUEST_INTERVAL - elapsed)
        self._last_request_time = time.time()

    def _build_search(self, since: datetime | None) -> str:
        """pharm_class_epc 화이트리스트 + effective_time 증분 필터.

        Lucene 쿼리 규약:
        - 각 클래스명은 따옴표로 phrase match 하여 정확히 매칭.
        - range 구문은 `[X TO Y]` 공백 필수. `+` 문자는 Lucene MUST operator 로
          해석되어 range 파싱이 깨지므로 반드시 공백을 쓴다.
        - httpx 는 공백을 `%20` 으로 percent-encode 하므로 openFDA 서버측에서
          올바르게 디코딩된다.
        """
        pharm_clauses = [
            f'openfda.pharm_class_epc:"{value}"' for value in self.pharm_class_epc_values
        ]
        pharm_filter = "(" + " OR ".join(pharm_clauses) + ")"
        query_parts: list[str] = [pharm_filter]

        if since is not None:
            ymd = since.strftime("%Y%m%d")
            query_parts.append(f"effective_time:[{ymd} TO 99991231]")

        return " AND ".join(query_parts)

    def list_updated_since(
        self,
        since: datetime | None,
        limit: int | None = None,
    ) -> Iterable[str]:
        """effective_time 기준 증분 수집.

        openFDA는 SPL set_id가 제품 식별자 역할.
        """
        client = self._get_client()
        search = self._build_search(since)
        skip = 0
        total_yielded = 0
        page_size = self.DEFAULT_LIMIT

        while True:
            if limit is not None and total_yielded >= limit:
                return

            params: dict[str, Any] = {
                "search": search,
                "limit": page_size,
                "skip": skip,
            }
            if self.api_key:
                params["api_key"] = self.api_key

            self._wait()
            try:
                resp = client.get(self.BASE_URL, params=params)
                if resp.status_code == 404:
                    # 검색 결과 없음 — openFDA는 404를 반환
                    return
                resp.raise_for_status()
            except httpx.HTTPStatusError as e:
                logger.error("openFDA list failed status=%s body=%s", e.response.status_code, e.response.text[:500])
                raise

            data = resp.json()
            results = data.get("results", [])
            if not results:
                return

            for item in results:
                set_id = item.get("set_id") or item.get("id")
                if not set_id:
                    continue
                yield set_id
                total_yielded += 1
                if limit is not None and total_yielded >= limit:
                    return

            total_found = data.get("meta", {}).get("results", {}).get("total", 0)
            skip += page_size
            if skip >= total_found:
                return

    def fetch_detail(self, source_product_id: str) -> dict[str, Any]:
        """set_id로 개별 라벨 원본 조회."""
        client = self._get_client()
        params: dict[str, Any] = {
            "search": f'set_id:"{source_product_id}"',
            "limit": 1,
        }
        if self.api_key:
            params["api_key"] = self.api_key

        self._wait()
        resp = client.get(self.BASE_URL, params=params)
        resp.raise_for_status()
        data = resp.json()
        results = data.get("results", [])
        if not results:
            raise ValueError(f"openFDA detail not found for set_id={source_product_id}")
        return results[0]

    def normalize(self, raw: dict[str, Any]) -> DrugProductCandidate:
        """openFDA label 응답 → DrugProductCandidate.

        openFDA 응답 구조:
        - openfda: { product_ndc, brand_name, generic_name, rxcui, route, ... }
        - indications_and_usage: [str]
        - dosage_and_administration: [str]
        - warnings: [str]
        """
        openfda = raw.get("openfda", {}) or {}
        set_id = raw.get("set_id") or raw.get("id", "")

        generic_name_list = openfda.get("generic_name") or []
        brand_name_list = openfda.get("brand_name") or []
        rxcui_list = openfda.get("rxcui") or []
        route_list = openfda.get("route") or []

        # 처방전 필요 여부: product_type="HUMAN PRESCRIPTION DRUG"
        product_type_field = openfda.get("product_type") or []
        is_rx = any("PRESCRIPTION" in str(pt).upper() for pt in product_type_field)

        indications = self._first_text(raw.get("indications_and_usage"))
        dosage = self._first_text(raw.get("dosage_and_administration"))
        warnings = self._first_text(raw.get("warnings"))

        return DrugProductCandidate(
            source=self.source_name,
            source_product_id=set_id,
            rxcui=rxcui_list[0] if rxcui_list else None,
            name_en=(generic_name_list[0] if generic_name_list else
                     (brand_name_list[0] if brand_name_list else None)),
            product_type="drug",
            is_prescription=is_rx,
            routes=[r.lower() for r in route_list],
            indications=indications,
            dosage=dosage,
            warnings=warnings,
            raw=raw,
        )

    @staticmethod
    def _first_text(value: Any) -> str | None:
        if value is None:
            return None
        if isinstance(value, list):
            return value[0] if value else None
        if isinstance(value, str):
            return value
        return None
