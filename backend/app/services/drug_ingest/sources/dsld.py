"""DSLD (Dietary Supplement Label Database) 어댑터

NIH ODS 가 운영하는 미국 시판 보충제 라벨 DB. 보충제 제품의 성분 · 정량 ·
기능성 주장(claim) 을 구조화해 제공한다.

라이선스: Public Domain.
API 참조: https://dsld.od.nih.gov/api-documentation

엔드포인트 (v9):
- GET /dsld/v9/search-filter?q=<keyword>&size=100&from=0
- GET /dsld/v9/label/{dsld_id}

알러지 학술 Agent 관점 용도:
- 비타민D · 퀘르세틴 · 프로바이오틱스 · 오메가3 등 알러지 관련 보조 요법
  후보의 용량·형태 카탈로그 확보
- 규제 논증상 "식이보충제" 카테고리 분리가 필수 → product_type=supplement
"""
from __future__ import annotations

import logging
import time
from datetime import datetime
from typing import Any, Iterable

import httpx

from .base import DrugProductCandidate, DrugSourceAdapter

logger = logging.getLogger(__name__)


class DsldAdapter(DrugSourceAdapter):
    """DSLD 보충제 라벨 수집 어댑터."""

    source_name = "dsld"
    license_tag = "public_domain"

    BASE_URL = "https://api.ods.od.nih.gov/dsld/v9"
    REQUEST_INTERVAL = 0.3
    DEFAULT_PAGE_SIZE = 100

    ALLERGY_SUPPLEMENT_QUERIES: tuple[str, ...] = (
        "vitamin D",
        "quercetin",
        "omega-3",
        "probiotic",
        "lactobacillus",
        "bifidobacterium",
        "nigella sativa",
        "butterbur",
        "bromelain",
        "nettle",
        "spirulina",
        "zinc",
        "magnesium",
        "vitamin C",
    )

    def __init__(
        self,
        timeout: float = 30.0,
        search_queries: tuple[str, ...] | None = None,
    ) -> None:
        self.search_queries: tuple[str, ...] = (
            search_queries or self.ALLERGY_SUPPLEMENT_QUERIES
        )
        self._client: httpx.Client | None = None
        self._last_request_time = 0.0
        self._timeout = timeout

    def _get_client(self) -> httpx.Client:
        if self._client is None:
            self._client = httpx.Client(timeout=self._timeout)
        return self._client

    def close(self) -> None:
        if self._client is not None:
            self._client.close()
            self._client = None

    def __enter__(self) -> "DsldAdapter":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    def _wait(self) -> None:
        elapsed = time.time() - self._last_request_time
        if elapsed < self.REQUEST_INTERVAL:
            time.sleep(self.REQUEST_INTERVAL - elapsed)
        self._last_request_time = time.time()

    def _request_search(
        self,
        query: str,
        offset: int,
        since: datetime | None,
    ) -> dict[str, Any]:
        params: dict[str, Any] = {
            "q": query,
            "size": self.DEFAULT_PAGE_SIZE,
            "from": offset,
        }
        if since is not None:
            params["modified_since"] = since.strftime("%Y-%m-%d")

        self._wait()
        resp = self._get_client().get(
            f"{self.BASE_URL}/search-filter", params=params
        )

        if resp.status_code == 404:
            return {"hits": [], "total": 0}
        if resp.status_code != 200:
            logger.error(
                "DSLD search HTTP %s: %s", resp.status_code, resp.text[:300]
            )
            resp.raise_for_status()

        data = resp.json()
        if "hits" not in data and "data" in data:
            data = {"hits": data.get("data") or [], "total": data.get("total", 0)}
        return data

    def list_updated_since(
        self,
        since: datetime | None,
        limit: int | None = None,
    ) -> Iterable[str]:
        """검색 쿼리 화이트리스트 × offset 페이지네이션."""
        total_yielded = 0
        seen: set[str] = set()

        for query in self.search_queries:
            if limit is not None and total_yielded >= limit:
                return

            offset = 0
            while True:
                if limit is not None and total_yielded >= limit:
                    return

                data = self._request_search(
                    query=query, offset=offset, since=since
                )
                hits = data.get("hits") or data.get("data") or []
                if not hits:
                    break

                for hit in hits:
                    src = hit.get("_source") if isinstance(hit, dict) and "_source" in hit else hit
                    dsld_id = (
                        (src or {}).get("DSLD_ID")
                        or (src or {}).get("dsld_id")
                        or hit.get("id")
                    )
                    if not dsld_id:
                        continue
                    dsld_id = str(dsld_id)
                    if dsld_id in seen:
                        continue
                    seen.add(dsld_id)
                    yield dsld_id
                    total_yielded += 1
                    if limit is not None and total_yielded >= limit:
                        return

                total = int(data.get("total") or 0)
                offset += self.DEFAULT_PAGE_SIZE
                if total and offset >= total:
                    break
                if len(hits) < self.DEFAULT_PAGE_SIZE:
                    break

    def fetch_detail(self, source_product_id: str) -> dict[str, Any]:
        self._wait()
        resp = self._get_client().get(
            f"{self.BASE_URL}/label/{source_product_id}"
        )
        if resp.status_code == 404:
            raise ValueError(
                f"DSLD label not found for DSLD_ID={source_product_id}"
            )
        resp.raise_for_status()
        payload = resp.json()
        if isinstance(payload, dict) and "data" in payload:
            return payload["data"]
        return payload

    def normalize(self, raw: dict[str, Any]) -> DrugProductCandidate:
        """DSLD label → DrugProductCandidate (product_type=supplement).

        라벨 응답은 productName, brandName, statements[], ingredientRows[] 등을
        포함한다. 제조사(brandName) 는 UI 비노출 — raw 에만 보존 (ADR-007).
        """
        dsld_id = str(raw.get("DSLD_ID") or raw.get("dsld_id") or raw.get("id") or "")
        product_name = raw.get("productName") or raw.get("product_name")

        # 기능성 주장은 건강기능식품법 논리대로 "원문 그대로"만 인용.
        statements = raw.get("statements") or raw.get("claims") or []
        if isinstance(statements, list):
            indications = " | ".join(
                str(s.get("statement") if isinstance(s, dict) else s)
                for s in statements
                if s
            )
            indications = indications or None
        elif isinstance(statements, str):
            indications = statements
        else:
            indications = None

        dosage = (
            raw.get("servingSizeDescription")
            or raw.get("serving_size")
            or raw.get("suggestedUse")
        )

        warnings_text = raw.get("cautions") or raw.get("warnings")
        if isinstance(warnings_text, list):
            warnings_text = "\n".join(str(w) for w in warnings_text if w) or None

        return DrugProductCandidate(
            source=self.source_name,
            source_product_id=dsld_id,
            name_en=product_name,
            product_type="supplement",
            is_prescription=False,
            indications=indications,
            dosage=dosage,
            warnings=warnings_text,
            raw=raw,
        )
