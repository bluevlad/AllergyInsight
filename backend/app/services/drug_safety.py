"""약물 정보 공개 API 안전 가드 (Phase 3)

비회원 공개 API에서 약물 정보를 노출할 때, 약사법·의료기기법 회피를 위한
필터링·정규화·출처 매핑 유틸리티.

원칙:
- 제품명·복용량·효능효과·주의사항은 응답에서 제외 (raw_jsonb·dosage·indications 차단)
- 성분명(INN) · 작용기전(MoA) · ATC 코드 · 알러지 약리군 · 출처(URL) 만 노출
- 알러지 치료에 사용되는 ATC 약리군 한정으로 검색 결과 필터 가능
"""
from __future__ import annotations

from typing import Optional


# ---------------------------------------------------------------------------
# ATC 알러지 약리군 화이트리스트 (drug_ingest/sources/rxnorm.py 와 동일 기준)
# ---------------------------------------------------------------------------
# Phase 3 비회원 페이지의 "알러지 치료용 한정" 필터에 사용된다.

ALLERGY_ATC_PREFIXES: tuple[str, ...] = (
    "R01",     # 비강 제제
    "R03",     # 폐쇄성 기도 질환 약물 (기관지 확장제 등)
    "R06",     # 전신 항히스타민제
    "D07",     # 국소 코르티코스테로이드
    "V01",     # 알러젠 추출물 (면역요법)
    "S01G",    # 안과용 항알러지제
    "H02AB",   # 전신 글루코코르티코이드
)


# ATC prefix → 한·영 카테고리 라벨 (UI 표시용)
ALLERGY_ATC_CATEGORIES: dict[str, dict[str, str]] = {
    "R01": {"name_kr": "비강 제제", "name_en": "Nasal preparations",
            "description": "비염·코막힘 등에 사용되는 비강 분무·점비 약물군"},
    "R03": {"name_kr": "기도질환 약물", "name_en": "Drugs for obstructive airway diseases",
            "description": "천식·만성 기관지염 등에서 기도를 확장·항염 작용하는 흡입·경구 약물군"},
    "R06": {"name_kr": "항히스타민제 (전신)", "name_en": "Systemic antihistamines",
            "description": "히스타민 H1 수용체 길항으로 알러지 증상을 완화하는 경구 약물군"},
    "D07": {"name_kr": "국소 코르티코스테로이드", "name_en": "Topical corticosteroids",
            "description": "피부 알러지·아토피 등에 사용되는 외용 스테로이드 약물군"},
    "V01": {"name_kr": "알러젠 추출물 (면역요법)", "name_en": "Allergen extracts",
            "description": "특정 알러젠에 점진 노출시켜 면역 관용을 유도하는 면역요법 제제"},
    "S01G": {"name_kr": "안과용 항알러지제", "name_en": "Ophthalmological antiallergics",
             "description": "알러지성 결막염 등에 사용되는 점안 약물군"},
    "H02AB": {"name_kr": "전신 글루코코르티코이드", "name_en": "Systemic glucocorticoids",
              "description": "중증 알러지·면역 반응에 사용되는 전신 스테로이드 약물군"},
}


# ---------------------------------------------------------------------------
# 출처(citation) URL 템플릿 — DB에 citation 컬럼을 추가하지 않고 동적 생성
# ---------------------------------------------------------------------------
# source_product_id 와 source 조합으로 공식 출처 URL을 만들 수 있는 외부 시스템들.

_SOURCE_URL_TEMPLATES: dict[str, dict[str, str]] = {
    "openfda": {
        "name": "FDA openFDA",
        "license": "CC0 Public Domain",
        "url_template": "https://api.fda.gov/drug/label.json?search=set_id:{id}",
    },
    "dailymed": {
        "name": "FDA DailyMed",
        "license": "Public Domain",
        "url_template": "https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid={id}",
    },
    "mfds_eyakeunyo": {
        "name": "식약처 e약은요",
        "license": "공공누리 1유형",
        "url_template": "https://nedrug.mfds.go.kr/pbp/CCBBB01/getItemDetail?itemSeq={id}",
    },
    "mfds_license": {
        "name": "식약처 의약품 허가정보",
        "license": "공공누리 1유형",
        "url_template": "https://nedrug.mfds.go.kr/pbp/CCBAA01/getItem?itemSeq={id}",
    },
    "mfds_hfood": {
        "name": "식약처 건강기능식품",
        "license": "공공누리 1유형",
        "url_template": "https://www.foodsafetykorea.go.kr/portal/healthyfoodlife/detail.do?itemSeq={id}",
    },
    "rxnorm": {
        "name": "NIH NLM RxNav",
        "license": "UMLS Category 0",
        "url_template": "https://mor.nlm.nih.gov/RxNav/search?searchBy=RXCUI&searchTerm={id}",
    },
    "dsld": {
        "name": "NIH DSLD",
        "license": "Public Domain",
        "url_template": "https://dsld.od.nih.gov/dsld/lblDetail.jsp?id={id}",
    },
}


def build_citation(source: str | None, source_product_id: str | None) -> Optional[dict]:
    """source + source_product_id 조합으로 공식 출처 메타를 생성.

    None/공백/미지원 source 면 None.
    """
    if not source or not source_product_id:
        return None
    template = _SOURCE_URL_TEMPLATES.get(source.lower())
    if not template:
        return None
    return {
        "source": source.lower(),
        "source_id": str(source_product_id),
        "source_name": template["name"],
        "license": template["license"],
        "url": template["url_template"].format(id=source_product_id),
    }


def build_rxnorm_citation(rxcui: str | None) -> Optional[dict]:
    """RxNorm rxcui 단독으로 RxNav 공식 URL 생성."""
    if not rxcui:
        return None
    return build_citation("rxnorm", rxcui)


def get_atc_category(atc_code: str | None) -> Optional[dict]:
    """ATC 코드의 prefix 매칭으로 알러지 카테고리 정보 반환.

    매칭되지 않으면 None — 해당 성분은 알러지 약리군 외 분류이거나 코드 미상.
    """
    if not atc_code:
        return None
    code = atc_code.strip().upper()
    # 가장 긴 prefix 부터 시도 (S01G > S01 등)
    for prefix in sorted(ALLERGY_ATC_PREFIXES, key=len, reverse=True):
        if code.startswith(prefix):
            cat = ALLERGY_ATC_CATEGORIES.get(prefix)
            if cat:
                return {
                    "atc_prefix": prefix,
                    "name_kr": cat["name_kr"],
                    "name_en": cat["name_en"],
                    "description": cat["description"],
                }
    return None


def is_allergy_related(atc_code: str | None) -> bool:
    """ATC 코드가 알러지 약리군 화이트리스트에 속하는지."""
    return get_atc_category(atc_code) is not None


def list_allergy_categories() -> list[dict]:
    """전체 알러지 약리군 목록 (카탈로그용)."""
    out: list[dict] = []
    for prefix in ALLERGY_ATC_PREFIXES:
        cat = ALLERGY_ATC_CATEGORIES.get(prefix)
        if cat:
            out.append({
                "atc_prefix": prefix,
                "name_kr": cat["name_kr"],
                "name_en": cat["name_en"],
                "description": cat["description"],
            })
    return out


# ---------------------------------------------------------------------------
# 응답 포맷터 — DrugIngredient ORM 또는 dict → 공개 응답 dict
# ---------------------------------------------------------------------------

PUBLIC_DISCLAIMER = (
    "본 정보는 약물 성분(INN) · 작용기전 · 분류에 대한 교육 · 정보 제공 목적이며, "
    "특정 제품·복용량·복약 지시는 제공하지 않습니다. 약물 사용은 반드시 처방·복약 지도를 받으세요."
)


def serialize_ingredient_public(ingredient, extra_citations: list[dict] | None = None) -> dict:
    """DrugIngredient ORM 또는 호환 dict → 비회원 공개 응답 dict.

    제품 정보(name_kr/name_en/dosage/indications/warnings)는 절대 포함하지 않는다.
    """
    def _get(obj, attr, default=None):
        if isinstance(obj, dict):
            return obj.get(attr, default)
        return getattr(obj, attr, default)

    rxcui = _get(ingredient, "rxcui")
    atc_code = _get(ingredient, "atc_code")

    citations: list[dict] = []
    rx_cite = build_rxnorm_citation(rxcui)
    if rx_cite:
        citations.append(rx_cite)
    if extra_citations:
        citations.extend(extra_citations)

    return {
        "id": _get(ingredient, "id"),
        "rxcui": rxcui,
        "inn": _get(ingredient, "inn"),
        "atc_code": atc_code,
        "atc_category": get_atc_category(atc_code),
        "moa": _get(ingredient, "moa"),
        "anticholinergic_score": _get(ingredient, "anticholinergic_score"),
        "is_allergy_related": is_allergy_related(atc_code),
        "citations": citations,
        "disclaimer": PUBLIC_DISCLAIMER,
    }
