"""알러지 리포트 생성 서비스

진단키트 없이 사용자가 직접 입력한 알러젠 등급을 기반으로
식품가이드, 생활관리, 응급정보를 통합한 1회성 리포트를 생성합니다.
"""
from datetime import datetime

from ..core.allergen import (
    ALLERGEN_NAMES_KR,
    EMERGENCY_GUIDELINES,
    get_allergen_info,
)


def _grade_to_severity(grade: int) -> str:
    """등급을 심각도로 변환"""
    if grade <= 2:
        return "mild"
    elif grade <= 4:
        return "moderate"
    else:
        return "severe"


def _grade_to_range_key(grade: int) -> str:
    """등급을 symptoms_by_grade 키로 변환"""
    if grade <= 2:
        return "1-2"
    elif grade <= 4:
        return "3-4"
    else:
        return "5-6"


SEVERITY_LABELS = {
    "mild": "경미",
    "moderate": "중등도",
    "severe": "심각",
}


def generate_report(allergens: list[dict], name: str | None = None) -> dict:
    """알러지 리포트 생성

    Args:
        allergens: [{"code": "peanut", "grade": 4}, ...]
        name: 사용자 이름 (선택)

    Returns:
        통합 리포트 딕셔너리
    """
    positive = [a for a in allergens if a["grade"] > 0]
    positive.sort(key=lambda x: x["grade"], reverse=True)

    # 요약 정보
    summary_items = []
    for item in positive:
        code = item["code"]
        grade = item["grade"]
        info = get_allergen_info(code)
        category = info.get("category", "unknown") if info else "unknown"
        severity = _grade_to_severity(grade)
        summary_items.append({
            "code": code,
            "name": ALLERGEN_NAMES_KR.get(code, code),
            "grade": grade,
            "category": category,
            "severity": severity,
            "severity_label": SEVERITY_LABELS[severity],
        })

    max_grade = max((a["grade"] for a in positive), default=0)

    # 식품 가이드
    avoid_foods = []
    substitutes = []
    hidden_sources = []
    cross_reactivity = []

    for item in positive:
        code = item["code"]
        info = get_allergen_info(code)
        if not info or info.get("category") != "food":
            continue

        name_kr = ALLERGEN_NAMES_KR.get(code, code)

        if info.get("avoid_foods"):
            avoid_foods.append({
                "allergen": name_kr,
                "allergen_code": code,
                "foods": info["avoid_foods"],
            })

        if info.get("substitutes"):
            for sub in info["substitutes"]:
                substitutes.append({
                    "allergen": name_kr,
                    "allergen_code": code,
                    "original": sub.get("original", ""),
                    "alternatives": sub.get("alternatives", []),
                    "notes": sub.get("notes", ""),
                })

        if info.get("hidden_sources"):
            hidden_sources.append({
                "allergen": name_kr,
                "allergen_code": code,
                "sources": info["hidden_sources"],
            })

        if info.get("cross_reactivity"):
            for cross in info["cross_reactivity"]:
                cross_reactivity.append({
                    "from_allergen": name_kr,
                    "to_allergen": cross.get("allergen_kr", ""),
                    "probability": cross.get("probability", ""),
                    "related_foods": cross.get("related_foods", []),
                })

    # 생활 관리
    allergen_specific_tips = []
    for item in positive:
        code = item["code"]
        info = get_allergen_info(code)
        if not info:
            continue

        name_kr = ALLERGEN_NAMES_KR.get(code, code)

        # 흡입 알러젠: management_tips
        if info.get("management_tips"):
            allergen_specific_tips.append({
                "allergen": name_kr,
                "allergen_code": code,
                "tips": info["management_tips"],
            })

        # 흡입 알러젠: avoid_exposure
        if info.get("avoid_exposure"):
            allergen_specific_tips.append({
                "allergen": f"{name_kr} - 회피 환경",
                "allergen_code": code,
                "tips": info["avoid_exposure"],
            })

        # 식품 알러젠: restaurant_cautions
        if info.get("restaurant_cautions"):
            allergen_specific_tips.append({
                "allergen": f"{name_kr} - 외식 주의",
                "allergen_code": code,
                "tips": info["restaurant_cautions"],
            })

    common_tips = [
        {
            "category": "실내 환경",
            "title": "실내 공기 관리",
            "tips": [
                "정기적으로 환기하되 꽃가루 시즌에는 주의",
                "공기청정기 사용 (HEPA 필터 권장)",
                "습도 40-50% 유지",
                "카펫보다 마루 바닥 선호",
            ],
        },
        {
            "category": "청소",
            "title": "청소 습관",
            "tips": [
                "물걸레 청소 권장",
                "진공청소기는 HEPA 필터 장착",
                "침구류 주 1회 이상 55도 이상에서 세탁",
                "먼지가 쌓이기 쉬운 곳 정기 청소",
            ],
        },
        {
            "category": "외출",
            "title": "외출 시 주의사항",
            "tips": [
                "마스크 착용 (KF94 권장)",
                "꽃가루 시즌에는 외출 후 샤워",
                "외출복은 침실에 두지 않기",
                "응급약 항상 휴대",
            ],
        },
    ]

    # 증상 정보
    symptoms_by_allergen = []
    for item in positive:
        code = item["code"]
        grade = item["grade"]
        info = get_allergen_info(code)
        if not info:
            continue

        name_kr = ALLERGEN_NAMES_KR.get(code, code)
        range_key = _grade_to_range_key(grade)
        grade_data = info.get("symptoms_by_grade", {}).get(range_key, {})

        symptoms_by_allergen.append({
            "allergen": name_kr,
            "allergen_code": code,
            "grade": grade,
            "severity": grade_data.get("severity", _grade_to_severity(grade)),
            "symptoms": grade_data.get("symptoms", []),
        })

    # 응급 정보 - 최대 심각도에 따라 관련 가이드라인 선택
    emergency = {}
    if max_grade >= 5:
        emergency = {
            "level": "severe",
            "primary": EMERGENCY_GUIDELINES.get("anaphylaxis", {}),
            "secondary": EMERGENCY_GUIDELINES.get("moderate_reaction", {}),
        }
    elif max_grade >= 3:
        emergency = {
            "level": "moderate",
            "primary": EMERGENCY_GUIDELINES.get("moderate_reaction", {}),
            "secondary": EMERGENCY_GUIDELINES.get("mild_reaction", {}),
        }
    else:
        emergency = {
            "level": "mild",
            "primary": EMERGENCY_GUIDELINES.get("mild_reaction", {}),
        }

    emergency["contacts"] = [
        {"name": "응급 (119)", "number": "119"},
        {"name": "독극물 상담 (1339)", "number": "1339"},
    ]

    return {
        "generated_at": datetime.now().isoformat(),
        "name": name,
        "summary": {
            "total_input": len(allergens),
            "positive_count": len(positive),
            "high_risk_count": sum(1 for a in positive if a["grade"] >= 4),
            "moderate_risk_count": sum(1 for a in positive if 2 <= a["grade"] <= 3),
            "low_risk_count": sum(1 for a in positive if a["grade"] == 1),
            "max_severity": _grade_to_severity(max_grade),
            "allergens": summary_items,
        },
        "food_guide": {
            "avoid_foods": avoid_foods,
            "substitutes": substitutes,
            "hidden_sources": hidden_sources,
            "cross_reactivity": cross_reactivity,
        },
        "lifestyle": {
            "allergen_specific": allergen_specific_tips,
            "common_tips": common_tips,
        },
        "symptoms": symptoms_by_allergen,
        "emergency": emergency,
        "disclaimer": "본 리포트는 의학적 진단을 대체하지 않으며, 참고 정보로만 활용하시기 바랍니다. 정확한 진단과 치료를 위해 반드시 전문 의료진과 상담하세요.",
    }
