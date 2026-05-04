"""RxNorm / RxNav 어댑터

NIH NLM RxNorm 은 미국 의약품 성분·제품의 표준 어휘 체계. Phase 2 성분
정규화의 기준점이 되지만, Phase 1 에서는 **ATC 알러지 약리군에 속하는
Ingredient 개념 카탈로그** 만 우선 수집해 drug_products 테이블에 적재한다.

라이선스: UMLS Category 0 (무제한 재배포 가능).
API 참조: https://rxnav.nlm.nih.gov/RxNormAPIs.html

전략:
1) /rxclass/classMembers.json?classId=<ATC>&relaSource=ATC  (ATC 클래스 멤버)
2) 각 멤버의 rxcui 로 /rxcui/{rxcui}/properties.json 호출
3) Ingredient 성분 1건당 DrugProductCandidate(product_type="drug",
   source="rxnorm", source_product_id=rxcui, rxcui=rxcui, atc_code=prefix)
   로 정규화

주의: RxNorm 은 product 가 아닌 ingredient concept 이므로 indications/
dosage 는 None. 이후 Phase 2 에서 DrugIngredient 테이블 병합의 키 역할.
"""
from __future__ import annotations

import logging
import time
from datetime import datetime
from typing import Any, Iterable

import httpx

from .base import DrugProductCandidate, DrugSourceAdapter

logger = logging.getLogger(__name__)


class RxNormAdapter(DrugSourceAdapter):
    """RxNav REST 기반 RxNorm 개념 카탈로그 어댑터."""

    source_name = "rxnorm"
    license_tag = "umls_cat0"

    BASE_URL = "https://rxnav.nlm.nih.gov/REST"
    REQUEST_INTERVAL = 0.1  # 공식 20 req/sec 제한 대비 여유

    ALLERGY_ATC_CLASS_IDS: tuple[str, ...] = (
        "R01",  # Nasal preparations
        "R03",  # Drugs for obstructive airway diseases
        "R06",  # Antihistamines
        "D07",  # Topical corticosteroids
        "V01",  # Allergen extracts
        "S01G", # Ophthalmological antiallergics
        "H02AB",# Systemic glucocorticoids
    )

    def __init__(
        self,
        timeout: float = 20.0,
        atc_class_ids: tuple[str, ...] | None = None,
    ) -> None:
        self.atc_class_ids: tuple[str, ...] = (
            atc_class_ids or self.ALLERGY_ATC_CLASS_IDS
        )
        self._client: httpx.Client | None = None
        self._last_request_time = 0.0
        self._timeout = timeout
        # 멤버 listing 단계에서 해당 rxcui 의 ATC 를 알고 있어야 normalize
        # 시점에 재조회가 필요 없음 → 소스 루프 동안만 유지되는 캐시.
        self._atc_cache: dict[str, str] = {}

    def _get_client(self) -> httpx.Client:
        if self._client is None:
            self._client = httpx.Client(timeout=self._timeout)
        return self._client

    def close(self) -> None:
        if self._client is not None:
            self._client.close()
            self._client = None
        self._atc_cache.clear()

    def __enter__(self) -> "RxNormAdapter":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    def _wait(self) -> None:
        elapsed = time.time() - self._last_request_time
        if elapsed < self.REQUEST_INTERVAL:
            time.sleep(self.REQUEST_INTERVAL - elapsed)
        self._last_request_time = time.time()

    def _get(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        self._wait()
        resp = self._get_client().get(f"{self.BASE_URL}{path}", params=params or {})
        if resp.status_code == 404:
            return {}
        if resp.status_code != 200:
            logger.error(
                "RxNav %s HTTP %s: %s",
                path,
                resp.status_code,
                resp.text[:300],
            )
            resp.raise_for_status()
        return resp.json() or {}

    def list_updated_since(
        self,
        since: datetime | None,
        limit: int | None = None,
    ) -> Iterable[str]:
        """ATC 알러지 클래스별 Ingredient 멤버 rxcui 수집.

        RxNorm 은 갱신 시점 기준 필터를 지원하지 않는다. since 는 무시하고
        소스 전량을 재방문하되, repository 단의 upsert 가 멱등성을 보장한다.
        `limit` 은 전체 yield 상한.
        """
        total_yielded = 0
        seen: set[str] = set()

        for class_id in self.atc_class_ids:
            if limit is not None and total_yielded >= limit:
                return

            data = self._get(
                "/rxclass/classMembers.json",
                params={
                    "classId": class_id,
                    "relaSource": "ATC",
                    "ttys": "IN",
                },
            )
            members = (
                (data.get("drugMemberGroup") or {}).get("drugMember") or []
            )
            for member in members:
                min_concept = member.get("minConcept") or {}
                rxcui = min_concept.get("rxcui")
                if not rxcui:
                    continue
                rxcui = str(rxcui)
                if rxcui in seen:
                    continue
                seen.add(rxcui)
                self._atc_cache[rxcui] = class_id
                yield rxcui
                total_yielded += 1
                if limit is not None and total_yielded >= limit:
                    return

    def fetch_detail(self, source_product_id: str) -> dict[str, Any]:
        data = self._get(f"/rxcui/{source_product_id}/properties.json")
        props = data.get("properties")
        if not props:
            raise ValueError(
                f"RxNorm properties not found for rxcui={source_product_id}"
            )
        props["_classified_atc"] = self._atc_cache.get(str(source_product_id))
        return props

    def normalize(self, raw: dict[str, Any]) -> DrugProductCandidate:
        """RxNorm properties → DrugProductCandidate.

        properties 응답 필드:
        - rxcui, name, synonym, tty (term type), language, suppress, umlscui
        """
        rxcui = str(raw.get("rxcui", ""))
        inn = raw.get("name") or raw.get("synonym")
        atc_code = raw.get("_classified_atc")

        return DrugProductCandidate(
            source=self.source_name,
            source_product_id=rxcui,
            rxcui=rxcui,
            atc_code=atc_code,
            name_en=inn,
            product_type="drug",
            is_prescription=False,
            raw=raw,
        )
