"""식약처 의약품개요정보(e약은요) API 어댑터

한국 식품의약품안전처가 제공하는 일반인 대상 의약품 개요 정보.
라이선스: 공공누리 제1유형 (출처 표시 조건, 재배포 허용).
API 문서: https://www.data.go.kr/data/15075057/openapi.do

응답 필드 (2026-04 기준):
- itemSeq: 품목기준코드 (KFDA 유일 식별자)
- itemName: 제품명
- entpName: 업체명 (**내부 메타데이터만, UI 비노출 — ADR-007**)
- efcyQesitm: 효능·효과 (사용자용 설명)
- useMethodQesitm: 용법·용량
- atpnWarnQesitm: 복용 전 경고
- atpnQesitm: 일반 주의사항
- intrcQesitm: 상호작용
- seQesitm: 부작용
- depositMethodQesitm: 보관 방법
- updateDe: 최종 갱신일 (YYYY-MM-DD)

Rate limit: 공공데이터포털 개발계정 기본 10,000건/일.
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


class MfdsEyakeunyoAdapter(DrugSourceAdapter):
    """e약은요 API 어댑터."""

    source_name = "mfds_eyakeunyo"
    license_tag = "kogl_type1"

    BASE_URL = (
        "https://apis.data.go.kr/1471000/DrbEasyDrugInfoService/getDrbEasyDrugList"
    )
    REQUEST_INTERVAL = 0.3
    DEFAULT_PAGE_SIZE = 100

    def __init__(
        self,
        api_key: str | None = None,
        timeout: float = 20.0,
    ) -> None:
        self.api_key = api_key or os.getenv("MFDS_API_KEY")
        if not self.api_key:
            raise RuntimeError(
                "MFDS_API_KEY is not set. Apply at data.go.kr (15075057)."
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

    def __enter__(self) -> "MfdsEyakeunyoAdapter":
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
        item_seq: str | None = None,
    ) -> dict[str, Any]:
        params: dict[str, Any] = {
            "serviceKey": self.api_key,
            "pageNo": page_no,
            "numOfRows": num_of_rows,
            "type": "json",
        }
        if item_seq:
            params["itemSeq"] = item_seq

        self._wait()
        resp = self._get_client().get(self.BASE_URL, params=params)

        if resp.status_code != 200:
            logger.error(
                "MFDS e약은요 HTTP %s: %s",
                resp.status_code,
                resp.text[:300],
            )
            resp.raise_for_status()

        content_type = resp.headers.get("content-type", "")
        if "json" not in content_type.lower():
            raise RuntimeError(
                f"Unexpected content-type from MFDS: {content_type}. "
                f"Body: {resp.text[:200]}"
            )

        data = resp.json()
        header = data.get("header", {})
        result_code = header.get("resultCode")
        if result_code and result_code != "00":
            raise RuntimeError(
                f"MFDS API error resultCode={result_code} "
                f"msg={header.get('resultMsg')}"
            )
        return data

    def list_updated_since(
        self,
        since: datetime | None,
        limit: int | None = None,
    ) -> Iterable[str]:
        """itemSeq 목록 산출.

        e약은요 API는 updateDe 필터링을 직접 지원하지 않으므로
        전체 페이지를 순회하면서 updateDe >= since 항목만 yield한다.
        since=None 이면 전체 반환.
        """
        page_no = 1
        total_yielded = 0
        since_str = since.strftime("%Y-%m-%d") if since else None

        while True:
            if limit is not None and total_yielded >= limit:
                return

            data = self._request_page(page_no, self.DEFAULT_PAGE_SIZE)
            body = data.get("body", {})
            items = body.get("items") or []
            if not items:
                return

            for item in items:
                item_seq = item.get("itemSeq")
                if not item_seq:
                    continue

                update_de = item.get("updateDe")
                if since_str and update_de and update_de < since_str:
                    continue

                yield item_seq
                total_yielded += 1
                if limit is not None and total_yielded >= limit:
                    return

            total_count = int(body.get("totalCount", 0) or 0)
            if page_no * self.DEFAULT_PAGE_SIZE >= total_count:
                return
            page_no += 1

    def fetch_detail(self, source_product_id: str) -> dict[str, Any]:
        """itemSeq로 개별 제품 상세 조회."""
        data = self._request_page(1, 1, item_seq=source_product_id)
        items = data.get("body", {}).get("items") or []
        if not items:
            raise ValueError(
                f"MFDS e약은요 detail not found for itemSeq={source_product_id}"
            )
        return items[0]

    def normalize(self, raw: dict[str, Any]) -> DrugProductCandidate:
        """e약은요 응답 → DrugProductCandidate."""
        item_seq = str(raw.get("itemSeq", ""))

        # ADR-007: 업체명(entpName)은 상업정보 — UI 노출 금지, 감사 추적만.
        # 정규화 단계에서는 raw에 보관하되 name_* 필드에는 복사하지 않는다.

        indications = raw.get("efcyQesitm")
        dosage = raw.get("useMethodQesitm")
        warnings_text = self._combine_warnings(raw)

        return DrugProductCandidate(
            source=self.source_name,
            source_product_id=item_seq,
            kfda_item_seq=item_seq,
            name_kr=raw.get("itemName"),
            product_type="drug",
            # e약은요는 일반인용 DB이므로 전문의약품 여부가 필드에 없다.
            # 수집 단계에서는 False로 두고, 이후 제품허가정보 API와 조인하여 갱신.
            is_prescription=False,
            indications=indications,
            dosage=dosage,
            warnings=warnings_text,
            raw=raw,
        )

    @staticmethod
    def _combine_warnings(raw: dict[str, Any]) -> str | None:
        """경고 관련 필드를 합쳐 warnings 로."""
        parts: list[str] = []
        for key, label in (
            ("atpnWarnQesitm", "경고"),
            ("atpnQesitm", "주의사항"),
            ("intrcQesitm", "상호작용"),
            ("seQesitm", "부작용"),
        ):
            text = raw.get(key)
            if text:
                parts.append(f"[{label}] {text}")
        if not parts:
            return None
        return "\n\n".join(parts)
