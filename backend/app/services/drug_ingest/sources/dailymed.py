"""DailyMed SPL 어댑터

NIH NLM DailyMed 는 FDA 에 제출된 Structured Product Labeling (SPL) 을
공개한다. openFDA drug/label 과 유사하지만 SPL set_id 단위로 구조화된
원본 라벨과 RxCUI 매핑을 제공해 Phase 2 정규화의 교차 검증 소스로 쓰인다.

라이선스: Public Domain.
API 참조: https://dailymed.nlm.nih.gov/dailymed/services.cfm

엔드포인트:
- GET /services/v2/spls.json?drug_name=cetirizine&pagesize=100&page=1
- GET /services/v2/spls/{setid}.json

DailyMed 는 SPL 전량이 대단히 크기 때문에 알러지 관련 성분명 화이트리스트를
drug_name 파라미터로 나눠 호출한다. 화이트리스트는 RxNorm / ATC 기반으로
확장 가능하도록 클래스 변수로 분리.
"""
from __future__ import annotations

import logging
import time
from datetime import datetime
from typing import Any, Iterable

import httpx

from .base import DrugProductCandidate, DrugSourceAdapter

logger = logging.getLogger(__name__)


class DailyMedAdapter(DrugSourceAdapter):
    """DailyMed v2 SPL 수집 어댑터."""

    source_name = "dailymed"
    license_tag = "public_domain"

    BASE_URL = "https://dailymed.nlm.nih.gov/dailymed/services/v2"
    REQUEST_INTERVAL = 0.3
    DEFAULT_PAGE_SIZE = 100

    ALLERGY_INGREDIENT_WHITELIST: tuple[str, ...] = (
        # H1 항히스타민 (R06)
        "cetirizine",
        "loratadine",
        "fexofenadine",
        "desloratadine",
        "levocetirizine",
        "diphenhydramine",
        "chlorpheniramine",
        "bilastine",
        # 비강 / 흡입 스테로이드 (R01AD / R03BA)
        "fluticasone",
        "mometasone",
        "budesonide",
        "beclomethasone",
        "triamcinolone",
        "ciclesonide",
        # β2 작용제 (R03AC / R03CC)
        "albuterol",
        "salbutamol",
        "salmeterol",
        "formoterol",
        "indacaterol",
        # Leukotriene 길항제 (R03DC)
        "montelukast",
        "zafirlukast",
        "pranlukast",
        # 생물학적 제제 (R03DX / D11AH)
        "omalizumab",
        "mepolizumab",
        "benralizumab",
        "reslizumab",
        "dupilumab",
        "tezepelumab",
        # Mast cell stabilizers / 기타
        "cromolyn",
        "nedocromil",
        "epinephrine",
        "tacrolimus",
        "pimecrolimus",
    )

    def __init__(
        self,
        timeout: float = 30.0,
        ingredient_whitelist: tuple[str, ...] | None = None,
    ) -> None:
        self.ingredient_whitelist: tuple[str, ...] = (
            ingredient_whitelist or self.ALLERGY_INGREDIENT_WHITELIST
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

    def __enter__(self) -> "DailyMedAdapter":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    def _wait(self) -> None:
        elapsed = time.time() - self._last_request_time
        if elapsed < self.REQUEST_INTERVAL:
            time.sleep(self.REQUEST_INTERVAL - elapsed)
        self._last_request_time = time.time()

    def _request_list(
        self,
        drug_name: str,
        page: int,
        published_since: datetime | None,
    ) -> dict[str, Any]:
        params: dict[str, Any] = {
            "drug_name": drug_name,
            "pagesize": self.DEFAULT_PAGE_SIZE,
            "page": page,
        }
        if published_since is not None:
            params["published_date"] = published_since.strftime("%Y-%m-%d")
            params["published_date_comparison"] = "gte"

        self._wait()
        resp = self._get_client().get(f"{self.BASE_URL}/spls.json", params=params)

        if resp.status_code == 404:
            return {"data": [], "metadata": {"total_pages": 0}}
        if resp.status_code != 200:
            logger.error(
                "DailyMed list HTTP %s: %s", resp.status_code, resp.text[:300]
            )
            resp.raise_for_status()
        return resp.json()

    def list_updated_since(
        self,
        since: datetime | None,
        limit: int | None = None,
    ) -> Iterable[str]:
        """성분명 화이트리스트 × 페이지 순회 증분 수집.

        DailyMed 는 성분 단위 `drug_name` 파라미터를 지원하며 published_date
        필터를 함께 쓰면 증분 수집이 가능하다. 응답의 data[].setid 를 제품
        식별자로 사용한다.
        """
        total_yielded = 0
        seen: set[str] = set()

        for ingredient in self.ingredient_whitelist:
            if limit is not None and total_yielded >= limit:
                return

            page = 1
            while True:
                if limit is not None and total_yielded >= limit:
                    return

                data = self._request_list(
                    drug_name=ingredient,
                    page=page,
                    published_since=since,
                )
                items = data.get("data") or []
                if not items:
                    break

                for item in items:
                    setid = item.get("setid") or item.get("set_id")
                    if not setid:
                        continue
                    if setid in seen:
                        continue
                    seen.add(setid)
                    yield setid
                    total_yielded += 1
                    if limit is not None and total_yielded >= limit:
                        return

                meta = data.get("metadata") or {}
                total_pages = int(meta.get("total_pages") or 0)
                if total_pages and page >= total_pages:
                    break
                if not items:
                    break
                page += 1

    def fetch_detail(self, source_product_id: str) -> dict[str, Any]:
        self._wait()
        resp = self._get_client().get(
            f"{self.BASE_URL}/spls/{source_product_id}.json"
        )
        if resp.status_code == 404:
            raise ValueError(
                f"DailyMed detail not found for setid={source_product_id}"
            )
        resp.raise_for_status()
        payload = resp.json()
        data = payload.get("data") or payload
        if isinstance(data, list):
            if not data:
                raise ValueError(
                    f"DailyMed detail empty for setid={source_product_id}"
                )
            data = data[0]
        return data

    def normalize(self, raw: dict[str, Any]) -> DrugProductCandidate:
        """DailyMed SPL 응답 → DrugProductCandidate.

        DailyMed detail 응답은 title, set_id, published_date, active_ingredients,
        products[{product_name, generic_name, route, dea_schedule, ...}] 등을
        포함한다. 필드 유무는 제품별로 편차가 있어 모두 None-safe 로 처리.
        """
        set_id = str(raw.get("setid") or raw.get("set_id") or "")
        title = raw.get("title")
        products = raw.get("products") or []
        first_product = products[0] if products else {}

        generic_name = (
            first_product.get("generic_name")
            or raw.get("generic_name")
            or None
        )
        brand_name = first_product.get("product_name") or title

        active_ingredients = first_product.get("active_ingredients") or []
        rxcui = None
        if active_ingredients:
            rxcui = active_ingredients[0].get("rxcui")

        route_list = []
        raw_routes = first_product.get("route") or raw.get("route")
        if isinstance(raw_routes, list):
            route_list = [str(r).lower() for r in raw_routes if r]
        elif isinstance(raw_routes, str):
            route_list = [raw_routes.lower()]

        schedule = first_product.get("dea_schedule") or first_product.get("marketing_category")
        is_prescription = self._infer_is_prescription(schedule, title)

        return DrugProductCandidate(
            source=self.source_name,
            source_product_id=set_id,
            rxcui=str(rxcui) if rxcui else None,
            name_en=generic_name or brand_name,
            product_type="drug",
            is_prescription=is_prescription,
            routes=route_list,
            indications=self._first_text(raw.get("indications_and_usage")),
            dosage=self._first_text(raw.get("dosage_and_administration")),
            warnings=self._first_text(raw.get("warnings")),
            raw=raw,
        )

    @staticmethod
    def _infer_is_prescription(schedule: Any, title: Any) -> bool:
        blob = f"{schedule or ''} {title or ''}".upper()
        if "OTC" in blob or "ANDA" in blob:
            return False
        if "PRESCRIPTION" in blob or "NDA" in blob or "BLA" in blob:
            return True
        return False

    @staticmethod
    def _first_text(value: Any) -> str | None:
        if value is None:
            return None
        if isinstance(value, list):
            return value[0] if value else None
        if isinstance(value, dict):
            return value.get("text") or value.get("value")
        if isinstance(value, str):
            return value
        return None
