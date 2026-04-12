"""약물 크로스체크 엔진

2개 이상의 약물·증상이 동시에 고려될 때 5개 축으로 검증하여
주의 경고를 생성. 본 프로토타입은 DB 비의존 순수 로직으로 구현되어
pytest 단위 테스트로 완전히 검증 가능하다.

5개 체크 축:
  ① 동일 성분 중복 (RxCUI)            — 구현됨
  ② 동일 약리군 중첩 (ATC 프리픽스)    — 구현됨
  ③ 항콜린 부담 합산 (ACB Score)       — 구현됨
  ④ 약물-증상 금기 (기저질환 매트릭스)  — Phase 후속
  ⑤ 투여경로 간섭 (YAML 규칙 엔진)     — Phase 5 (별도 모듈)

참조:
- services/allergyinsight/plans/academic-drug-agent-plan.md Phase 4
- ACB Scale: Boustani 2008 (PMID 18716017), Salahudeen 2015 (PMID 26016551)
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Iterable


class Severity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

    def __lt__(self, other: "Severity") -> bool:  # type: ignore[override]
        order = {Severity.LOW: 0, Severity.MEDIUM: 1, Severity.HIGH: 2}
        return order[self] < order[other]


class CheckAxis(str, Enum):
    INGREDIENT_DUPLICATE = "ingredient_duplicate"
    CLASS_OVERLAP = "class_overlap"
    ACB_BURDEN = "acb_burden"
    CONTRAINDICATION = "contraindication"
    ROUTE_INTERFERENCE = "route_interference"


@dataclass
class PrescriptionItem:
    """크로스체크 입력 단위."""

    rxcui: str
    inn: str | None = None
    atc_code: str | None = None
    route: str | None = None  # "oral" | "topical" | "nasal" | "inhalation" | "ophthalmic"
    anticholinergic_score: int = 0
    dose_mcg_per_day: float | None = None
    duration_days: int | None = None


@dataclass
class Warning:
    """크로스체크 경고 레코드."""

    axis: CheckAxis
    severity: Severity
    rule_id: str
    message_kr: str
    message_en: str | None = None
    involved_rxcuis: list[str] = field(default_factory=list)
    evidence_pmids: list[int] = field(default_factory=list)
    details: dict[str, str | int | float] = field(default_factory=dict)


# ─────────────────────────────────────────────────────────────
# 구성 — ATC 4자리 sub-class (allergy_atc_codes.yaml 와 일치)
# ─────────────────────────────────────────────────────────────

_CLASS_OVERLAP_PREFIXES: dict[str, str] = {
    "R06AB": "1st gen antihistamine",
    "R06AD": "1st gen antihistamine (phenothiazine)",
    "R06AE": "2nd gen antihistamine",
    "R06AX": "other systemic antihistamine",
    "R03AC": "SABA/LABA",
    "R03BA": "inhaled corticosteroid",
    "R01AD": "nasal corticosteroid",
    "D07AC": "topical corticosteroid potent",
    "D07AD": "topical corticosteroid very potent",
    "S01BA": "ophthalmic corticosteroid",
    "H02AB": "systemic glucocorticoid",
    "R03DC": "leukotriene receptor antagonist",
}

# ACB Score 임계치 (Boustani 2008) — 3점 이상 임상적 의의
_ACB_CLINICAL_THRESHOLD = 3

# H1 항히스타민 계열 ATC 프리픽스 — 투여경로에 따라 분산되어 있음.
#   R06A  : 전신 H1 항히스타민
#   R01AC : 비강 국소 항알러지 (아젤라스틴·레보카바스틴)
#   S01GX : 안과 국소 항히스타민·마스트셀 안정제
_ANTIHISTAMINE_PREFIXES: tuple[str, ...] = ("R06A", "R01AC", "S01GX")


def _classify_atc_4(atc_code: str | None) -> str | None:
    """ATC 4~5자리 sub-class 매칭 (가장 구체적인 매칭 반환)."""
    if not atc_code:
        return None
    for prefix in sorted(_CLASS_OVERLAP_PREFIXES.keys(), key=len, reverse=True):
        if atc_code.startswith(prefix):
            return prefix
    return None


def _is_antihistamine(item: PrescriptionItem) -> bool:
    """ATC 코드상 H1 항히스타민(또는 마스트셀 안정제)으로 분류되는지."""
    code = item.atc_code or ""
    return any(code.startswith(p) for p in _ANTIHISTAMINE_PREFIXES)


# ─────────────────────────────────────────────────────────────
# 체크 함수 — 각 축별로 독립 구현
# ─────────────────────────────────────────────────────────────


def check_ingredient_duplicate(items: list[PrescriptionItem]) -> list[Warning]:
    """① 동일 RxCUI 중복 탐지 (복합제 펼치기는 호출자 책임)."""
    warnings: list[Warning] = []
    seen: dict[str, list[PrescriptionItem]] = {}
    for item in items:
        if not item.rxcui:
            continue
        seen.setdefault(item.rxcui, []).append(item)

    for rxcui, duped in seen.items():
        if len(duped) < 2:
            continue
        inn = duped[0].inn or "unknown"
        routes = sorted({d.route for d in duped if d.route})
        warnings.append(
            Warning(
                axis=CheckAxis.INGREDIENT_DUPLICATE,
                severity=Severity.HIGH,
                rule_id="duplicate_rxcui",
                message_kr=(
                    f"동일 성분 중복: {inn} (RxCUI={rxcui}) — 혈중농도 누적, "
                    f"용량 초과 위험. 투여경로: {', '.join(routes) or '미상'}."
                ),
                message_en=(
                    f"Duplicate ingredient {inn} across {len(duped)} prescriptions"
                ),
                involved_rxcuis=[rxcui] * len(duped),
                details={"count": len(duped), "routes": ",".join(routes)},
            )
        )
    return warnings


def check_class_overlap(items: list[PrescriptionItem]) -> list[Warning]:
    """② 동일 약리군 중첩 탐지 (ATC 4자리 기준)."""
    warnings: list[Warning] = []
    classes: dict[str, list[PrescriptionItem]] = {}
    for item in items:
        cls = _classify_atc_4(item.atc_code)
        if cls:
            classes.setdefault(cls, []).append(item)

    for cls, duped in classes.items():
        # 동일 RxCUI면 ① 에서 이미 경고 → 여기서는 서로 다른 성분만
        rxcuis = {d.rxcui for d in duped if d.rxcui}
        if len(rxcuis) < 2:
            continue
        label = _CLASS_OVERLAP_PREFIXES[cls]
        severity = Severity.HIGH if cls == "R06AB" else Severity.MEDIUM
        inns = sorted({d.inn for d in duped if d.inn})
        warnings.append(
            Warning(
                axis=CheckAxis.CLASS_OVERLAP,
                severity=severity,
                rule_id=f"class_overlap_{cls}",
                message_kr=(
                    f"동일 약리군({label}) 중첩: {', '.join(inns)} — "
                    f"효과·부작용 누적 가능."
                ),
                message_en=f"Multiple agents in class {cls} ({label})",
                involved_rxcuis=sorted(rxcuis),
                details={"class": cls, "class_label": label},
            )
        )
    return warnings


def check_antihistamine_route_duplication(
    items: list[PrescriptionItem],
) -> list[Warning]:
    """②-부속: H1 항히스타민 경구+비강·안과 병용 별도 경고."""
    warnings: list[Warning] = []
    antihist = [i for i in items if _is_antihistamine(i)]
    if len(antihist) < 2:
        return warnings
    routes = {i.route for i in antihist if i.route}
    if len(routes) >= 2:
        warnings.append(
            Warning(
                axis=CheckAxis.CLASS_OVERLAP,
                severity=Severity.MEDIUM,
                rule_id="antihistamine_multi_route",
                message_kr=(
                    f"항히스타민제를 여러 투여경로로 병용 중({', '.join(sorted(routes))}). "
                    f"진정·항콜린 부작용 누적 가능."
                ),
                message_en="Antihistamines via multiple routes — cumulative sedation/anticholinergic effect",
                involved_rxcuis=[i.rxcui for i in antihist if i.rxcui],
                details={"routes": ",".join(sorted(routes))},
            )
        )
    return warnings


def check_acb_burden(items: list[PrescriptionItem]) -> list[Warning]:
    """③ 항콜린 부담 합산 (Boustani 2008 ACB Scale)."""
    total = sum(max(0, item.anticholinergic_score or 0) for item in items)
    if total < _ACB_CLINICAL_THRESHOLD:
        return []

    involved = [
        i for i in items if (i.anticholinergic_score or 0) > 0
    ]
    severity = Severity.HIGH if total >= 5 else Severity.MEDIUM

    return [
        Warning(
            axis=CheckAxis.ACB_BURDEN,
            severity=severity,
            rule_id="acb_score_exceeds_threshold",
            message_kr=(
                f"총 항콜린 부담 점수(ACB) = {total} "
                f"(임계 {_ACB_CLINICAL_THRESHOLD} 초과). "
                f"고령자에서 인지기능 저하·구갈·요저류·변비 위험 누적."
            ),
            message_en=(
                f"Anticholinergic Cognitive Burden score = {total} "
                f"(threshold {_ACB_CLINICAL_THRESHOLD}). "
                f"Risk of cognitive decline, dry mouth, urinary retention in older adults."
            ),
            involved_rxcuis=[i.rxcui for i in involved if i.rxcui],
            evidence_pmids=[18716017, 26016551],
            details={"total_acb": total},
        )
    ]


# ─────────────────────────────────────────────────────────────
# 통합 엔진
# ─────────────────────────────────────────────────────────────


def cross_check(items: Iterable[PrescriptionItem]) -> list[Warning]:
    """5개 체크 축 중 구현된 3개를 순차 실행하여 경고를 반환.

    반환 순서: severity 내림차순 → axis → rule_id.
    """
    items = list(items)
    if len(items) < 2:
        return []

    warnings: list[Warning] = []
    warnings.extend(check_ingredient_duplicate(items))
    warnings.extend(check_class_overlap(items))
    warnings.extend(check_antihistamine_route_duplication(items))
    warnings.extend(check_acb_burden(items))

    severity_order = {Severity.HIGH: 0, Severity.MEDIUM: 1, Severity.LOW: 2}
    warnings.sort(
        key=lambda w: (severity_order[w.severity], w.axis.value, w.rule_id)
    )
    return warnings
