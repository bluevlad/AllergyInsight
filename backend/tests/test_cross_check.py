"""cross_check_service 단위 테스트

DB 비의존. 순수 로직만 검증."""
from __future__ import annotations

import pytest

from app.services.drug_agent.cross_check_service import (
    CheckAxis,
    PrescriptionItem,
    Severity,
    check_acb_burden,
    check_antihistamine_route_duplication,
    check_class_overlap,
    check_ingredient_duplicate,
    cross_check,
)


# ─────────────────────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────────────────────

CETIRIZINE = PrescriptionItem(
    rxcui="20610",
    inn="cetirizine",
    atc_code="R06AE07",
    route="oral",
    anticholinergic_score=1,
)
LORATADINE = PrescriptionItem(
    rxcui="28889",
    inn="loratadine",
    atc_code="R06AX13",
    route="oral",
    anticholinergic_score=0,
)
DIPHENHYDRAMINE = PrescriptionItem(
    rxcui="3498",
    inn="diphenhydramine",
    atc_code="R06AA02",
    route="oral",
    anticholinergic_score=3,
)
AZELASTINE_NASAL = PrescriptionItem(
    rxcui="1172",
    inn="azelastine",
    atc_code="R01AC03",
    route="nasal",
    anticholinergic_score=0,
)

FLUTICASONE_INHALED = PrescriptionItem(
    rxcui="41126",
    inn="fluticasone",
    atc_code="R03BA05",
    route="inhalation",
    dose_mcg_per_day=500.0,
)
BUDESONIDE_INHALED = PrescriptionItem(
    rxcui="19831",
    inn="budesonide",
    atc_code="R03BA02",
    route="inhalation",
    dose_mcg_per_day=400.0,
)
MOMETASONE_NASAL = PrescriptionItem(
    rxcui="108118",
    inn="mometasone",
    atc_code="R01AD09",
    route="nasal",
    dose_mcg_per_day=200.0,
)

OXYBUTYNIN = PrescriptionItem(
    rxcui="7816",
    inn="oxybutynin",
    atc_code="G04BD04",
    route="oral",
    anticholinergic_score=3,
)


# ─────────────────────────────────────────────────────────────
# ① Ingredient duplicate
# ─────────────────────────────────────────────────────────────


def test_duplicate_ingredient_detected():
    warnings = check_ingredient_duplicate([CETIRIZINE, CETIRIZINE])
    assert len(warnings) == 1
    assert warnings[0].axis == CheckAxis.INGREDIENT_DUPLICATE
    assert warnings[0].severity == Severity.HIGH
    assert "cetirizine" in warnings[0].message_kr


def test_different_ingredients_no_duplicate():
    warnings = check_ingredient_duplicate([CETIRIZINE, LORATADINE])
    assert warnings == []


def test_duplicate_requires_rxcui():
    item = PrescriptionItem(rxcui="", inn="?")
    warnings = check_ingredient_duplicate([item, item])
    assert warnings == []


# ─────────────────────────────────────────────────────────────
# ② Class overlap
# ─────────────────────────────────────────────────────────────


def test_antihistamine_class_overlap_2nd_gen():
    # 세티리진(R06AE) + 로라타딘(R06AX) → 서로 다른 sub-prefix 라 R06A 직접 매칭 안됨.
    # 본 매핑에서는 _CLASS_OVERLAP_PREFIXES에 R06AE와 R06AX가 있으므로
    # 각각 다른 sub 그룹. 따라서 class overlap으로는 안 잡히고
    # antihistamine_multi_route 경로로 탐지되어야 함.
    warnings = check_class_overlap([CETIRIZINE, LORATADINE])
    # R06AE vs R06AX → 다른 서브클래스 → 경고 없음
    assert warnings == []


def test_class_overlap_same_sub_class():
    # 두 개의 흡입 ICS (R03BA) → 동일 sub class 중첩
    warnings = check_class_overlap([FLUTICASONE_INHALED, BUDESONIDE_INHALED])
    assert len(warnings) == 1
    assert warnings[0].axis == CheckAxis.CLASS_OVERLAP
    assert warnings[0].rule_id == "class_overlap_R03BA"
    assert warnings[0].severity == Severity.MEDIUM
    assert "fluticasone" in warnings[0].message_kr
    assert "budesonide" in warnings[0].message_kr


def test_1st_gen_antihistamine_class_severity_high():
    item_a = PrescriptionItem(
        rxcui="3498", inn="diphenhydramine", atc_code="R06AB02", route="oral",
    )
    item_b = PrescriptionItem(
        rxcui="6931", inn="chlorpheniramine", atc_code="R06AB04", route="oral",
    )
    warnings = check_class_overlap([item_a, item_b])
    assert len(warnings) == 1
    assert warnings[0].severity == Severity.HIGH


def test_single_ingredient_no_class_overlap():
    warnings = check_class_overlap([FLUTICASONE_INHALED])
    assert warnings == []


# ─────────────────────────────────────────────────────────────
# ②-부속 Antihistamine multi-route
# ─────────────────────────────────────────────────────────────


def test_antihistamine_oral_plus_nasal_triggers_multi_route():
    warnings = check_antihistamine_route_duplication([CETIRIZINE, AZELASTINE_NASAL])
    assert len(warnings) == 1
    assert warnings[0].rule_id == "antihistamine_multi_route"
    assert warnings[0].severity == Severity.MEDIUM
    assert "oral" in warnings[0].details["routes"]
    assert "nasal" in warnings[0].details["routes"]


def test_antihistamine_same_route_no_multi_route_warning():
    warnings = check_antihistamine_route_duplication([CETIRIZINE, LORATADINE])
    assert warnings == []


# ─────────────────────────────────────────────────────────────
# ③ ACB burden
# ─────────────────────────────────────────────────────────────


def test_acb_below_threshold_no_warning():
    warnings = check_acb_burden([CETIRIZINE, LORATADINE])
    assert warnings == []


def test_acb_meets_threshold_medium():
    warnings = check_acb_burden([DIPHENHYDRAMINE])
    assert len(warnings) == 1
    assert warnings[0].severity == Severity.MEDIUM
    assert warnings[0].details["total_acb"] == 3


def test_acb_high_threshold():
    warnings = check_acb_burden([DIPHENHYDRAMINE, OXYBUTYNIN])
    assert len(warnings) == 1
    assert warnings[0].severity == Severity.HIGH
    assert warnings[0].details["total_acb"] == 6
    assert 18716017 in warnings[0].evidence_pmids


# ─────────────────────────────────────────────────────────────
# 통합 cross_check — 정렬 + 다축 동시 탐지
# ─────────────────────────────────────────────────────────────


def test_cross_check_empty_input():
    assert cross_check([]) == []


def test_cross_check_single_item():
    assert cross_check([CETIRIZINE]) == []


def test_cross_check_asthma_rhinitis_combo():
    """천식(ICS) + 비염(nasal steroid) 조합에서 R03BA 중첩은 없어야 함.

    플루티카손 흡입 + 모메타손 비강은 각각 R03BA, R01AD로 서로 다른 sub-class.
    총 스테로이드 부하 계산은 별도 YAML 규칙 엔진(Phase 5)이 담당.
    """
    warnings = cross_check([FLUTICASONE_INHALED, MOMETASONE_NASAL])
    assert warnings == []


def test_cross_check_sorts_by_severity():
    warnings = cross_check([
        CETIRIZINE, CETIRIZINE,               # ① HIGH
        FLUTICASONE_INHALED, BUDESONIDE_INHALED,  # ② MEDIUM
        DIPHENHYDRAMINE, OXYBUTYNIN,          # ③ HIGH
    ])

    severities = [w.severity for w in warnings]
    # HIGH들이 먼저
    assert severities.count(Severity.HIGH) >= 2
    assert severities[0] == Severity.HIGH
    # MEDIUM이 그 다음
    assert Severity.MEDIUM in severities
    # HIGH가 MEDIUM보다 먼저 오는지
    first_medium_idx = severities.index(Severity.MEDIUM)
    for s in severities[:first_medium_idx]:
        assert s == Severity.HIGH


def test_cross_check_multi_axis_detection():
    """하나의 처방에서 여러 축의 경고가 동시에 생성되는지."""
    warnings = cross_check([DIPHENHYDRAMINE, CETIRIZINE, AZELASTINE_NASAL])
    axes = {w.axis for w in warnings}
    # 1세대(R06AB) + 2세대(R06AE) → class overlap 안 잡힘 (다른 sub-class)
    # 항히스타민 경구+비강 → multi-route
    # ACB total = 3 + 1 = 4 → burden warning
    assert CheckAxis.CLASS_OVERLAP in axes  # multi_route는 CLASS_OVERLAP 축
    assert CheckAxis.ACB_BURDEN in axes
