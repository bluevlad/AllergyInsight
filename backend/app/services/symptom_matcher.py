"""증상 텍스트 → 알러젠 후보 매칭 (Phase 2)

사용자가 자유 텍스트로 입력한 증상에서 한국어 키워드를 추출하고,
36종 활성 알러젠의 등급별 증상 데이터에 대해 prefix 인덱스 매칭으로
관련성 높은 알러젠 후보를 점수 순으로 반환한다.

원칙:
- 진단을 내리지 않는다 — "유사 사례 매칭" 결과로 표현
- 키워드 매칭 가능성에 비례하는 score 만 제공, 확률·확신 표현 X
- 한국어 형태소 분석기 없이 단순 prefix 매칭으로 어미 변형 일부 흡수
- 매칭이 없을 수 있으며, 그때는 빈 리스트 반환 → 프론트엔드는
  "관련 알러젠을 찾지 못했습니다 — 의료진 상담 권장" 으로 안내

향후 PR에서 임베딩 기반 의미 매칭으로 교체 가능 (인터페이스 안정 유지).
"""
from __future__ import annotations

import re
from collections import defaultdict
from functools import lru_cache
from typing import Iterable

from ..data.allergen_prescription_db import (
    ALLERGEN_PRESCRIPTION_DB,
    PHASE1_ACTIVE_ALLERGENS,
)


# 등급 severity 별 가중치 — 강한 증상 매칭이 점수에 더 크게 기여
_SEVERITY_WEIGHT = {
    "mild": 1.0,
    "moderate": 2.0,
    "severe": 3.0,
    "anaphylaxis": 4.0,
}

# prefix 길이 (한글 글자 단위). 2글자 prefix가 어미 변형을 흡수.
_MIN_PREFIX_LEN = 2
_MAX_PREFIX_LEN = 3
_MIN_KEYWORD_LEN = 2

# 너무 일반적인 한국어 단어 — 알러지 도메인 시그널이 약해서 인덱싱 제외
_STOPWORDS_PREFIX: frozenset[str] = frozenset({
    "증상", "반응", "감각", "느낌", "정도", "이상", "부분", "종류",
})


def _extract_search_prefixes(text: str) -> list[str]:
    """증상 이름에서 검색용 한글 prefix 들을 추출.

    예: "입술/입안 따끔거림" → {"입술", "입안", "따끔", "따끔거"}
        "두드러기 (전신)"   → {"두드", "두드러", "두드러기"}
    """
    parts = re.split(r"[/\s()·,\-]+", text)
    out: set[str] = set()
    for raw in parts:
        token = raw.strip()
        if not token:
            continue
        # 영문/숫자만으로 된 토큰은 제외 (한글 매칭 대상이 아님)
        if re.fullmatch(r"[A-Za-z0-9]+", token):
            continue
        if len(token) < _MIN_KEYWORD_LEN:
            continue
        # 두 글자 / 세 글자 prefix
        for length in range(_MIN_PREFIX_LEN, _MAX_PREFIX_LEN + 1):
            if len(token) >= length:
                prefix = token[:length]
                if prefix in _STOPWORDS_PREFIX:
                    continue
                out.add(prefix)
        # 4글자 이상이면 원형 토큰도 인덱싱
        if len(token) >= 4:
            out.add(token)
    return list(out)


@lru_cache(maxsize=1)
def _build_keyword_index() -> dict[str, list[tuple[str, str, str]]]:
    """{prefix: [(allergen_code, severity, original_symptom)]} 인덱스 생성.

    Phase 1 활성 36종 한정. 첫 호출 시 lazy 빌드, 이후 캐시.
    """
    index: dict[str, list[tuple[str, str, str]]] = defaultdict(list)
    for code, info in ALLERGEN_PRESCRIPTION_DB.items():
        if code not in PHASE1_ACTIVE_ALLERGENS:
            continue
        symptoms_by_grade = info.get("symptoms_by_grade") or {}
        for _grade_key, grade_data in symptoms_by_grade.items():
            if not isinstance(grade_data, dict):
                continue
            severity = (grade_data.get("severity") or "mild").lower()
            for symptom in grade_data.get("symptoms") or []:
                sym_name = symptom.get("name") if isinstance(symptom, dict) else None
                if not sym_name:
                    continue
                for prefix in _extract_search_prefixes(sym_name):
                    index[prefix].append((code, severity, sym_name))
    return dict(index)


def match_symptoms(input_text: str, top_k: int = 5) -> list[dict]:
    """입력 텍스트와 매칭되는 알러젠 후보를 점수 순으로 반환.

    각 후보:
        {
            "allergen_code": str,
            "name_kr": str,
            "name_en": str,
            "category": "food" | "inhalant",
            "score": float,
            "matched_symptoms": [{"symptom", "severity", "matched_prefix"}, ...]
        }
    """
    if not input_text or not input_text.strip():
        return []

    text = input_text.strip()
    keyword_index = _build_keyword_index()

    # prefix → 매칭된 (code, severity, symptom) 목록 수집
    raw_matches_by_allergen: dict[str, list[dict]] = defaultdict(list)
    for prefix, candidates in keyword_index.items():
        if prefix in text:
            for code, severity, sym_name in candidates:
                raw_matches_by_allergen[code].append({
                    "symptom": sym_name,
                    "severity": severity,
                    "matched_prefix": prefix,
                })

    results: list[dict] = []
    for code, items in raw_matches_by_allergen.items():
        info = ALLERGEN_PRESCRIPTION_DB.get(code)
        if not info:
            continue

        # 같은 symptom이 여러 prefix로 매칭된 경우 가장 강한 severity 항목만 유지
        per_symptom: dict[str, dict] = {}
        for item in items:
            key = item["symptom"]
            current = per_symptom.get(key)
            if current is None or _SEVERITY_WEIGHT.get(item["severity"], 0) > _SEVERITY_WEIGHT.get(current["severity"], 0):
                per_symptom[key] = item

        unique_symptoms = list(per_symptom.values())
        score = sum(_SEVERITY_WEIGHT.get(s["severity"], 1.0) for s in unique_symptoms)

        results.append({
            "allergen_code": code,
            "name_kr": info.get("name_kr", code),
            "name_en": info.get("name_en", code),
            "category": info.get("category"),
            "score": round(score, 2),
            "matched_symptoms": unique_symptoms,
            "match_count": len(unique_symptoms),
        })

    results.sort(key=lambda r: (r["score"], r["match_count"]), reverse=True)
    return results[:top_k]


def get_index_stats() -> dict:
    """진단용 — 인덱스 크기 통계."""
    idx = _build_keyword_index()
    total_entries = sum(len(v) for v in idx.values())
    return {
        "active_allergens": len(PHASE1_ACTIVE_ALLERGENS),
        "unique_prefixes": len(idx),
        "total_entries": total_entries,
    }
