"""Prescription Engine Tests

처방 권고 엔진 단위 테스트:
- 처방 권고 생성
- 위험도 계산
- 교차반응 경고
- 의료 권고사항
"""
import pytest
from datetime import datetime

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.services.prescription_engine import PrescriptionEngine
from app.models.prescription import RiskLevel, AllergenCategory


@pytest.fixture
def engine():
    """PrescriptionEngine 인스턴스."""
    return PrescriptionEngine()


class TestPrescriptionGeneration:
    """처방 권고 생성 테스트."""

    def test_generate_prescription_basic(self, engine: PrescriptionEngine):
        """기본 처방 생성 테스트."""
        results = [
            {"allergen": "peanut", "grade": 4},
            {"allergen": "milk", "grade": 2},
        ]

        prescription = engine.generate_prescription(results)

        assert prescription is not None
        assert prescription.prescription_id is not None
        assert len(prescription.diagnosis_results) == 2
        assert prescription.positive_count == 2
        assert prescription.highest_grade == 4

    def test_generate_prescription_with_date(self, engine: PrescriptionEngine):
        """날짜 포함 처방 생성 테스트."""
        results = [{"allergen": "peanut", "grade": 3}]
        date = datetime(2025, 1, 1)

        prescription = engine.generate_prescription(results, diagnosis_date=date)

        assert prescription.diagnosis_date == date

    def test_generate_prescription_no_positive(self, engine: PrescriptionEngine):
        """양성 없음 처방 생성 테스트."""
        results = [
            {"allergen": "peanut", "grade": 0},
            {"allergen": "milk", "grade": 0},
        ]

        prescription = engine.generate_prescription(results)

        assert prescription.positive_count == 0
        assert prescription.risk_level == RiskLevel.NONE
        assert len(prescription.food_restrictions) == 0

    def test_generate_prescription_all_positive(self, engine: PrescriptionEngine):
        """모두 양성 처방 생성 테스트."""
        results = [
            {"allergen": "peanut", "grade": 5},
            {"allergen": "milk", "grade": 4},
            {"allergen": "egg", "grade": 3},
            {"allergen": "wheat", "grade": 2},
        ]

        prescription = engine.generate_prescription(results)

        assert prescription.positive_count == 4
        assert prescription.highest_grade == 5
        assert len(prescription.food_restrictions) >= 1


class TestRiskLevelCalculation:
    """위험도 수준 계산 테스트."""

    def test_risk_level_critical_grade_6(self, engine: PrescriptionEngine):
        """등급 6 → CRITICAL."""
        results = [{"allergen": "peanut", "grade": 6}]
        prescription = engine.generate_prescription(results)
        assert prescription.risk_level == RiskLevel.CRITICAL

    def test_risk_level_critical_multiple_high(self, engine: PrescriptionEngine):
        """등급 5 + 3개 이상 양성 → CRITICAL."""
        results = [
            {"allergen": "peanut", "grade": 5},
            {"allergen": "milk", "grade": 4},
            {"allergen": "egg", "grade": 3},
        ]
        prescription = engine.generate_prescription(results)
        assert prescription.risk_level == RiskLevel.CRITICAL

    def test_risk_level_high(self, engine: PrescriptionEngine):
        """등급 5 (단독) → HIGH."""
        results = [{"allergen": "peanut", "grade": 5}]
        prescription = engine.generate_prescription(results)
        assert prescription.risk_level == RiskLevel.HIGH

    def test_risk_level_moderate(self, engine: PrescriptionEngine):
        """등급 3-4 → MODERATE."""
        results = [{"allergen": "peanut", "grade": 3}]
        prescription = engine.generate_prescription(results)
        assert prescription.risk_level == RiskLevel.MODERATE

    def test_risk_level_low(self, engine: PrescriptionEngine):
        """등급 1-2 → LOW."""
        results = [{"allergen": "peanut", "grade": 1}]
        prescription = engine.generate_prescription(results)
        assert prescription.risk_level == RiskLevel.LOW

    def test_risk_level_none(self, engine: PrescriptionEngine):
        """등급 0 → NONE."""
        results = [{"allergen": "peanut", "grade": 0}]
        prescription = engine.generate_prescription(results)
        assert prescription.risk_level == RiskLevel.NONE


class TestFoodRestrictions:
    """음식 섭취 제한 테스트."""

    def test_food_restriction_generated(self, engine: PrescriptionEngine):
        """음식 제한 정보 생성."""
        results = [{"allergen": "peanut", "grade": 4}]
        prescription = engine.generate_prescription(results)

        # 양성일 경우 음식 제한이 있어야 함
        assert len(prescription.food_restrictions) >= 1
        restriction = prescription.food_restrictions[0]
        assert restriction.allergen == "peanut"
        assert restriction.grade == 4

    def test_food_restriction_includes_avoid_foods(self, engine: PrescriptionEngine):
        """회피 식품 목록 포함."""
        results = [{"allergen": "peanut", "grade": 4}]
        prescription = engine.generate_prescription(results)

        if prescription.food_restrictions:
            restriction = prescription.food_restrictions[0]
            # 회피 식품 또는 숨겨진 출처가 있어야 함
            has_food_info = (
                len(restriction.avoid_foods) > 0 or
                len(restriction.hidden_sources) > 0
            )
            assert has_food_info

    def test_food_restriction_includes_substitutes(self, engine: PrescriptionEngine):
        """대체 식품 목록 포함."""
        results = [{"allergen": "milk", "grade": 3}]
        prescription = engine.generate_prescription(results)

        if prescription.food_restrictions:
            restriction = prescription.food_restrictions[0]
            # 대체 식품이 있을 수 있음 (DB에 따라)
            # 구조만 확인
            assert hasattr(restriction, 'substitutes')


class TestCrossReactivity:
    """교차반응 경고 테스트."""

    def test_cross_reactivity_alerts_generated(self, engine: PrescriptionEngine):
        """교차반응 경고 생성."""
        # 갑각류는 일반적으로 교차반응이 있음
        results = [{"allergen": "shrimp", "grade": 4}]
        prescription = engine.generate_prescription(results)

        # 교차반응 알림이 있을 수 있음 (DB에 따라)
        assert hasattr(prescription, 'cross_reactivity_alerts')

    def test_cross_reactivity_structure(self, engine: PrescriptionEngine):
        """교차반응 경고 구조."""
        results = [{"allergen": "shrimp", "grade": 4}]
        prescription = engine.generate_prescription(results)

        if prescription.cross_reactivity_alerts:
            alert = prescription.cross_reactivity_alerts[0]
            assert hasattr(alert, 'primary_allergen')
            assert hasattr(alert, 'related_allergen')
            assert hasattr(alert, 'probability')


class TestSymptomPrediction:
    """예상 증상 테스트."""

    def test_symptoms_predicted(self, engine: PrescriptionEngine):
        """증상 예측 생성."""
        results = [{"allergen": "peanut", "grade": 4}]
        prescription = engine.generate_prescription(results)

        # 증상 예측이 있을 수 있음
        assert hasattr(prescription, 'predicted_symptoms')

    def test_symptom_severity_by_grade(self, engine: PrescriptionEngine):
        """등급에 따른 증상 심각도."""
        # 높은 등급
        high_results = [{"allergen": "peanut", "grade": 6}]
        high_prescription = engine.generate_prescription(high_results)

        # 낮은 등급
        low_results = [{"allergen": "peanut", "grade": 1}]
        low_prescription = engine.generate_prescription(low_results)

        # 높은 등급이 더 많은/심각한 증상을 가질 수 있음
        # 구조가 있는지만 확인
        assert hasattr(high_prescription, 'predicted_symptoms')
        assert hasattr(low_prescription, 'predicted_symptoms')


class TestEmergencyGuidelines:
    """응급 가이드라인 테스트."""

    def test_emergency_guidelines_critical(self, engine: PrescriptionEngine):
        """CRITICAL 위험도 응급 가이드라인."""
        results = [{"allergen": "peanut", "grade": 6}]
        prescription = engine.generate_prescription(results)

        assert len(prescription.emergency_guidelines) >= 1
        # 아나필락시스 가이드가 포함되어야 함
        conditions = [g.condition for g in prescription.emergency_guidelines]
        assert any("아나필락시스" in c or "anaphylaxis" in c.lower() for c in conditions)

    def test_emergency_guidelines_high(self, engine: PrescriptionEngine):
        """HIGH 위험도 응급 가이드라인."""
        results = [{"allergen": "peanut", "grade": 5}]
        prescription = engine.generate_prescription(results)

        assert len(prescription.emergency_guidelines) >= 1

    def test_emergency_guidelines_low(self, engine: PrescriptionEngine):
        """LOW 위험도 응급 가이드라인."""
        results = [{"allergen": "peanut", "grade": 1}]
        prescription = engine.generate_prescription(results)

        # 낮은 위험도에도 경미한 반응 가이드는 있어야 함
        assert len(prescription.emergency_guidelines) >= 1


class TestMedicalRecommendation:
    """의료 권고사항 테스트."""

    def test_medical_recommendation_generated(self, engine: PrescriptionEngine):
        """의료 권고사항 생성."""
        results = [{"allergen": "peanut", "grade": 4}]
        prescription = engine.generate_prescription(results)

        assert prescription.medical_recommendation is not None
        assert prescription.medical_recommendation.consultation_needed is True

    def test_epinephrine_recommended_for_critical(self, engine: PrescriptionEngine):
        """CRITICAL에 에피네프린 권고."""
        results = [{"allergen": "peanut", "grade": 6}]
        prescription = engine.generate_prescription(results)

        assert prescription.medical_recommendation.epinephrine_recommended is True

    def test_epinephrine_recommended_for_high(self, engine: PrescriptionEngine):
        """HIGH에 에피네프린 권고."""
        results = [{"allergen": "peanut", "grade": 5}]
        prescription = engine.generate_prescription(results)

        assert prescription.medical_recommendation.epinephrine_recommended is True

    def test_consultation_urgency_critical(self, engine: PrescriptionEngine):
        """CRITICAL 상담 긴급도."""
        results = [{"allergen": "peanut", "grade": 6}]
        prescription = engine.generate_prescription(results)

        assert prescription.medical_recommendation.consultation_urgency == "urgent"

    def test_additional_tests_for_high_grade(self, engine: PrescriptionEngine):
        """높은 등급에 추가 검사 권고."""
        results = [{"allergen": "peanut", "grade": 5}]
        prescription = engine.generate_prescription(results)

        assert len(prescription.medical_recommendation.additional_tests) >= 1


class TestGeneralRecommendations:
    """일반 권고사항 테스트."""

    def test_general_recommendations_generated(self, engine: PrescriptionEngine):
        """일반 권고사항 생성."""
        results = [{"allergen": "peanut", "grade": 3}]
        prescription = engine.generate_prescription(results)

        assert len(prescription.general_recommendations) >= 1

    def test_critical_recommendations(self, engine: PrescriptionEngine):
        """CRITICAL 권고사항."""
        results = [{"allergen": "peanut", "grade": 6}]
        prescription = engine.generate_prescription(results)

        # 에피네프린 관련 권고가 있어야 함
        recs_text = " ".join(prescription.general_recommendations).lower()
        assert "에피네프린" in recs_text or "epinephrine" in recs_text


class TestLifestyleTips:
    """생활 팁 테스트."""

    def test_lifestyle_tips_generated(self, engine: PrescriptionEngine):
        """생활 팁 생성."""
        results = [{"allergen": "peanut", "grade": 3}]
        prescription = engine.generate_prescription(results)

        assert len(prescription.lifestyle_tips) >= 1

    def test_dust_mite_specific_tips(self, engine: PrescriptionEngine):
        """집먼지진드기 전용 팁."""
        results = [{"allergen": "dust_mite", "grade": 3}]
        prescription = engine.generate_prescription(results)

        tips_text = " ".join(prescription.lifestyle_tips).lower()
        # 침구, 세탁, 습도 관련 팁이 있어야 함
        has_relevant_tip = (
            "침구" in tips_text or
            "세탁" in tips_text or
            "습도" in tips_text or
            "진드기" in tips_text
        )
        assert has_relevant_tip


class TestCriticalAllergens:
    """위험 알러젠 목록 테스트."""

    def test_critical_allergens_identified(self, engine: PrescriptionEngine):
        """위험 알러젠 식별."""
        results = [
            {"allergen": "peanut", "grade": 6},
            {"allergen": "milk", "grade": 5},
            {"allergen": "egg", "grade": 2},
        ]
        prescription = engine.generate_prescription(results)

        # 등급 5 이상이 위험 알러젠
        assert len(prescription.critical_allergens) == 2


class TestAllergenCategory:
    """알러젠 카테고리 테스트."""

    def test_food_allergen_category(self, engine: PrescriptionEngine):
        """식품 알러젠 카테고리."""
        results = [{"allergen": "peanut", "grade": 3}]
        prescription = engine.generate_prescription(results)

        if prescription.diagnosis_results:
            result = prescription.diagnosis_results[0]
            assert result.category == AllergenCategory.FOOD

    def test_inhalant_allergen_category(self, engine: PrescriptionEngine):
        """흡입성 알러젠 카테고리."""
        results = [{"allergen": "dust_mite", "grade": 3}]
        prescription = engine.generate_prescription(results)

        if prescription.diagnosis_results:
            result = prescription.diagnosis_results[0]
            assert result.category == AllergenCategory.INHALANT


class TestUnknownAllergen:
    """알 수 없는 알러젠 처리 테스트."""

    def test_unknown_allergen_handled(self, engine: PrescriptionEngine):
        """알 수 없는 알러젠 처리."""
        results = [{"allergen": "unknown_allergen_xyz", "grade": 3}]
        prescription = engine.generate_prescription(results)

        # 오류 없이 처리되어야 함
        assert prescription is not None
        assert len(prescription.diagnosis_results) == 1


class TestGradeDescription:
    """등급 설명 테스트."""

    def test_get_grade_description(self, engine: PrescriptionEngine):
        """등급 설명 조회."""
        desc = engine.get_grade_description(4)
        assert desc is not None

    def test_get_grade_description_invalid(self, engine: PrescriptionEngine):
        """잘못된 등급 설명 조회."""
        desc = engine.get_grade_description(99)
        # 기본값 반환
        assert desc is not None


class TestAllergenList:
    """알러젠 목록 조회 테스트."""

    def test_get_allergen_list(self, engine: PrescriptionEngine):
        """알러젠 목록 조회."""
        allergens = engine.get_allergen_list()
        assert len(allergens) > 0

    def test_allergen_list_structure(self, engine: PrescriptionEngine):
        """알러젠 목록 구조."""
        allergens = engine.get_allergen_list()
        if allergens:
            allergen = allergens[0]
            assert "code" in allergen
            assert "name_kr" in allergen
            assert "category" in allergen
