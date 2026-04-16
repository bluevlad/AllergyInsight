"""식약처 의약품 제품허가정보 어댑터

일반·전문의약품 품목허가 공식 마스터. e약은요(환자용)와 달리 ATC 코드,
전문/일반 구분(ETC_OTC_CODE), 주성분(MAIN_ITEM_INGR)을 포함해
Phase 2 RxNorm 정규화의 한국 측 기준점이 된다.

라이선스: 공공누리 제1유형 (출처 표시).
API 참조: https://www.data.go.kr/data/15095677/openapi.do

응답 필드 (JSON 매핑):
- ITEM_SEQ        품목기준코드 (PK, e약은요와 조인 키)
- ITEM_NAME       품목명
- ENTP_NAME       업체명 — **raw 보관 전용, UI 비노출** (ADR-007)
- MAIN_ITEM_INGR  주성분명
- MATERIAL_NAME   원료 성분 (복합제 펼치기용)
- ATC_CODE        ATC 코드
- ETC_OTC_CODE    전문/일반 구분 (전문=전문의약품)
- CHNG_DATE       변경 이력 일자 (YYYYMMDD)

Rate limit: 개발계정 10,000건/일. 실제 쿼터는 e약은요와 공유.
"""
from __future__ import annotations

import logging
import os
import time
from datetime import datetime
from typing import Any, Iterable

import httpx

from .base import DrugProductCandidate, DrugSourceAdapter

logger = logging.getLogger(__name__)


class MfdsLicenseAdapter(DrugSourceAdapter):
    """MFDS 제품허가정보 API 어댑터."""

    source_name = "mfds_license"
    license_tag = "kogl_type1"

    BASE_URL = (
        "https://apis.data.go.kr/1471000/DrugPrdtPrmsnInfoService06/"
        "getDrugPrdtPrmsnDtlInq05"
    )
    REQUEST_INTERVAL = 0.3
    DEFAULT_PAGE_SIZE = 100

    ALLERGY_ATC_PREFIXES: tuple[str, ...] = (
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
        api_key: str | None = None,
        timeout: float = 20.0,
        atc_prefixes: tuple[str, ...] | None = None,
    ) -> None:
        self.api_key = api_key or os.getenv("MFDS_API_KEY")
        if not self.api_key:
            raise RuntimeError(
                "MFDS_API_KEY is not set. Apply at data.go.kr (15095677)."
            )
        self.atc_prefixes: tuple[str, ...] = (
            atc_prefixes or self.ALLERGY_ATC_PREFIXES
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

    def __enter__(self) -> "MfdsLicenseAdapter":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    def _wait(self) -> None:
        elapsed = time.time() - self._last_request_time
        if elapsed < self.REQUEST_INTERVAL:
            time.sleep(self.REQUEST_INTERVAL - elapsed)
        self._last_request_time = time.time()

    def _request_page(
        self,
        page_no: int,
        num_of_rows: int,
        *,
        item_seq: str | None = None,
    ) -> dict[str, Any]:
        params: dict[str, Any] = {
            "serviceKey": self.api_key,
            "pageNo": page_no,
            "numOfRows": num_of_rows,
            "type": "json",
        }
        if item_seq:
            params["item_seq"] = item_seq

        self._wait()
        resp = self._get_client().get(self.BASE_URL, params=params)

        if resp.status_code != 200:
            logger.error(
                "MFDS license HTTP %s: %s", resp.status_code, resp.text[:300]
            )
            resp.raise_for_status()

        content_type = resp.headers.get("content-type", "")
        if "json" not in content_type.lower():
            raise RuntimeError(
                f"Unexpected content-type from MFDS license: {content_type}. "
                f"Body: {resp.text[:200]}"
            )

        data = resp.json()
        header = data.get("header", {})
        result_code = header.get("resultCode")
        if result_code and result_code != "00":
            raise RuntimeError(
                f"MFDS license API error resultCode={result_code} "
                f"msg={header.get('resultMsg')}"
            )
        return data

    def _atc_allowed(self, atc_code: str | None) -> bool:
        if not atc_code:
            return False
        return any(atc_code.startswith(prefix) for prefix in self.atc_prefixes)

    def list_updated_since(
        self,
        since: datetime | None,
        limit: int | None = None,
    ) -> Iterable[str]:
        """ATC prefix 화이트리스트 + CHNG_DATE 증분 필터.

        MFDS 허가정보 API는 서버측 필터가 제한적이므로 페이지 순회 중
        ATC prefix 화이트리스트와 CHNG_DATE 비교를 클라이언트에서 수행한다.
        """
        page_no = 1
        total_yielded = 0
        since_str = since.strftime("%Y%m%d") if since else None

        while True:
            if limit is not None and total_yielded >= limit:
                return

            data = self._request_page(page_no, self.DEFAULT_PAGE_SIZE)
            body = data.get("body", {})
            items = body.get("items") or []
            if not items:
                return

            for item in items:
                item_seq = item.get("ITEM_SEQ")
                if not item_seq:
                    continue

                if not self._atc_allowed(item.get("ATC_CODE")):
                    continue

                chng_date = item.get("CHNG_DATE")
                if since_str and chng_date and str(chng_date) < since_str:
                    continue

                yield str(item_seq)
                total_yielded += 1
                if limit is not None and total_yielded >= limit:
                    return

            total_count = int(body.get("totalCount", 0) or 0)
            if page_no * self.DEFAULT_PAGE_SIZE >= total_count:
                return
            page_no += 1

    def fetch_detail(self, source_product_id: str) -> dict[str, Any]:
        """ITEM_SEQ 로 상세 조회."""
        data = self._request_page(1, 1, item_seq=source_product_id)
        items = data.get("body", {}).get("items") or []
        if not items:
            raise ValueError(
                f"MFDS license detail not found for ITEM_SEQ={source_product_id}"
            )
        return items[0]

    def normalize(self, raw: dict[str, Any]) -> DrugProductCandidate:
        """MFDS 허가정보 응답 → DrugProductCandidate.

        - ENTP_NAME(업체명): UI 비노출, raw 만 보존 (ADR-007)
        - ETC_OTC_CODE/NAME: "전문" → is_prescription=True
        - MAIN_ITEM_INGR: 주성분명. 정규화 실패 시 Phase 2 unmapped 큐로.
        """
        item_seq = str(raw.get("ITEM_SEQ", ""))
        etc_otc = (
            raw.get("ETC_OTC_NAME")
            or raw.get("ETC_OTC_CODE")
            or ""
        )
        is_prescription = "전문" in str(etc_otc)

        atc_code = raw.get("ATC_CODE") or None
        if atc_code:
            atc_code = str(atc_code).strip().upper() or None

        return DrugProductCandidate(
            source=self.source_name,
            source_product_id=item_seq,
            atc_code=atc_code,
            kfda_item_seq=item_seq,
            name_kr=raw.get("ITEM_NAME"),
            product_type="drug",
            is_prescription=is_prescription,
            indications=raw.get("EE_DOC_DATA") or raw.get("INDICATIONS"),
            dosage=raw.get("UD_DOC_DATA") or raw.get("DOSAGE"),
            warnings=raw.get("NB_DOC_DATA") or raw.get("WARNINGS"),
            raw=raw,
        )
