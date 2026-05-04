"""식약처 건강기능식품 품목제조신고 어댑터

기능성원료·일일섭취량·주된기능성을 제공. product_type=supplement 로
DrugProduct 테이블에 적재된다.

라이선스: 공공누리 제1유형.
API 참조: https://www.data.go.kr/data/15100018/openapi.do

학술 Agent 관점 용도:
- 알러지 관련 보조 요법 후보(비타민D, 퀘르세틴, 프로바이오틱스 등) 카탈로그
- 건강기능식품법 제18조 준수를 위해 기능성 문구는 **식약처 고시 원문만** 사용
- "의약품 아님" 고지는 UI 렌더 단계에서 별도 처리

응답 필드 (JSON 매핑):
- PRDLST_REPORT_NO : 품목제조신고번호 (PK)
- PRDLST_NM        : 제품명
- BSSH_NM          : 업소명 — raw 전용 (ADR-007)
- POG_DAYCNT       : 소비기한
- PRIMARY_FNCLTY   : 주된 기능성 (식약처 고시 원문 인용)
- INDIV_RAW_MATRL_NM : 개별 원료 성분
- DAILY_INTK_HINT_MPB : 일일섭취량 안내
- MANUFACTURE_MTHD : 제조 방법
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


class MfdsHfoodAdapter(DrugSourceAdapter):
    """MFDS 건강기능식품 API 어댑터."""

    source_name = "mfds_hfood"
    license_tag = "kogl_type1"

    BASE_URL = (
        "https://apis.data.go.kr/1471000/HtfsInfoService03/getHtfsItem01"
    )
    REQUEST_INTERVAL = 0.3
    DEFAULT_PAGE_SIZE = 100

    ALLERGY_FUNCTIONAL_KEYWORDS: tuple[str, ...] = (
        "면역",          # 면역 기능 개선
        "알레르기",      # 알레르기 완화
        "알러지",
        "호흡기",
        "항산화",        # 퀘르세틴·폴리페놀
        "유산균",        # 프로바이오틱스
        "프로바이오틱",
        "비타민D",       # 비타민 D
        "비타민 D",
        "오메가",        # 오메가-3
        "장 건강",
        "코 건강",
        "피부",          # 피부 보호·아토피 관련
    )

    def __init__(
        self,
        api_key: str | None = None,
        timeout: float = 20.0,
        keyword_whitelist: tuple[str, ...] | None = None,
    ) -> None:
        self.api_key = api_key or os.getenv("MFDS_API_KEY")
        if not self.api_key:
            raise RuntimeError(
                "MFDS_API_KEY is not set. Apply at data.go.kr (15100018)."
            )
        self.keyword_whitelist: tuple[str, ...] = (
            keyword_whitelist or self.ALLERGY_FUNCTIONAL_KEYWORDS
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

    def __enter__(self) -> "MfdsHfoodAdapter":
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
        report_no: str | None = None,
    ) -> dict[str, Any]:
        params: dict[str, Any] = {
            "ServiceKey": self.api_key,
            "pageNo": page_no,
            "numOfRows": num_of_rows,
            "type": "json",
        }
        if report_no:
            params["prdlst_report_no"] = report_no

        self._wait()
        resp = self._get_client().get(self.BASE_URL, params=params)

        if resp.status_code != 200:
            logger.error(
                "MFDS hfood HTTP %s: %s", resp.status_code, resp.text[:300]
            )
            resp.raise_for_status()

        content_type = resp.headers.get("content-type", "")
        if "json" not in content_type.lower():
            raise RuntimeError(
                f"Unexpected content-type from MFDS hfood: {content_type}. "
                f"Body: {resp.text[:200]}"
            )

        data = resp.json()
        header = data.get("header", {})
        result_code = header.get("resultCode")
        if result_code and result_code != "00":
            raise RuntimeError(
                f"MFDS hfood API error resultCode={result_code} "
                f"msg={header.get('resultMsg')}"
            )
        return data

    def _allergy_relevant(self, item: dict[str, Any]) -> bool:
        """주된 기능성·원료에 알러지 키워드가 포함되는지 검사."""
        haystack = " ".join(
            str(item.get(key) or "")
            for key in ("PRIMARY_FNCLTY", "INDIV_RAW_MATRL_NM", "PRDLST_NM")
        )
        return any(kw in haystack for kw in self.keyword_whitelist)

    def list_updated_since(
        self,
        since: datetime | None,
        limit: int | None = None,
    ) -> Iterable[str]:
        """키워드 화이트리스트 필터링 후 PRDLST_REPORT_NO yield.

        건강기능식품 API는 갱신일 서버 필터를 제공하지 않는 경우가 많아
        페이지 순회 + 키워드 매칭 방식으로 수집한다. since 파라미터는
        응답에 permit_date/update_date 가 있을 때만 적용.
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
                report_no = item.get("PRDLST_REPORT_NO")
                if not report_no:
                    continue

                if not self._allergy_relevant(item):
                    continue

                permit_date = (
                    item.get("PRMS_DT")
                    or item.get("LCNS_NO_DT")
                    or item.get("UPDATE_DT")
                )
                if since_str and permit_date and str(permit_date) < since_str:
                    continue

                yield str(report_no)
                total_yielded += 1
                if limit is not None and total_yielded >= limit:
                    return

            total_count = int(body.get("totalCount", 0) or 0)
            if page_no * self.DEFAULT_PAGE_SIZE >= total_count:
                return
            page_no += 1

    def fetch_detail(self, source_product_id: str) -> dict[str, Any]:
        data = self._request_page(1, 1, report_no=source_product_id)
        items = data.get("body", {}).get("items") or []
        if not items:
            raise ValueError(
                f"MFDS hfood detail not found for "
                f"PRDLST_REPORT_NO={source_product_id}"
            )
        return items[0]

    def normalize(self, raw: dict[str, Any]) -> DrugProductCandidate:
        report_no = str(raw.get("PRDLST_REPORT_NO", ""))

        indications = raw.get("PRIMARY_FNCLTY") or raw.get("FNCLTY_ORGN")
        dosage = raw.get("DAILY_INTK_HINT_MPB") or raw.get("INTK_HINT1")
        warnings_text = self._combine_warnings(raw)

        return DrugProductCandidate(
            source=self.source_name,
            source_product_id=report_no,
            kfda_item_seq=report_no,
            name_kr=raw.get("PRDLST_NM"),
            product_type="supplement",
            is_prescription=False,
            indications=indications,
            dosage=dosage,
            warnings=warnings_text,
            raw=raw,
        )

    @staticmethod
    def _combine_warnings(raw: dict[str, Any]) -> str | None:
        parts: list[str] = []
        for key, label in (
            ("CSMNT", "섭취 시 주의"),
            ("PRSRV_PD", "보관 유의"),
            ("ALLERGIC_MTRL", "알레르기 유발원료"),
        ):
            text = raw.get(key)
            if text:
                parts.append(f"[{label}] {text}")
        if not parts:
            return None
        return "\n\n".join(parts)
