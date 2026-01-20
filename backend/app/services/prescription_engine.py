"""처방 권고 엔진

SGTi-Allergy Screen PLUS 진단 결과를 기반으로
음식 섭취 제한 및 처방 권고를 생성합니다.
"""
import uuid
from datetime import datetime
from typing import Optional

from ..models.prescription import (
    RestrictionLevel,
    RiskLevel,
    AllergenCategory,
    DiagnosisResult,
    FoodSubstitute,
    FoodRestriction,
    CrossReactivityAlert,
    SymptomPrediction,
    EmergencyGuideline,
    MedicalRecommendation,
    AllergyPrescription,
    GRADE_DESCRIPTIONS,
)
from ..data.allergen_prescription_db import (
    ALLERGEN_PRESCRIPTION_DB,
    FOOD_ALLERGENS,
    INHALANT_ALLERGENS,
    EMERGENCY_GUIDELINES,
    get_allergen_info,
    get_cross_reactivities,
)


class PrescriptionEngine:
    """
    진단 결과 기반 처방 권고 생성 엔진
    """

    def __init__(self):
        self.allergen_db = ALLERGEN_PRESCRIPTION_DB
        self.emergency_guidelines = EMERGENCY_GUIDELINES

    def generate_prescription(
        self,
        diagnosis_results: list[dict],
        diagnosis_date: Optional[datetime] = None,
    ) -> AllergyPrescription:
        """
        진단 결과를 기반으로 종합 처방 권고 생성

        Args:
            diagnosis_results: [{"allergen": "peanut", "grade": 5}, ...]
            diagnosis_date: 검사 날짜

        Returns:
            AllergyPrescription: 종합 처방 권고
        """
        # 진단 결과 파싱
        parsed_results = self._parse_diagnosis_results(diagnosis_results)

        # 양성 항원만 필터링
        positive_results = [r for r in parsed_results if r.is_positive]

        # 요약 정보 계산
        highest_grade = max((r.grade for r in parsed_results), default=0)
        critical_allergens = [r.allergen_kr for r in positive_results if r.grade >= 5]
        risk_level = self._calculate_risk_level(highest_grade, len(positive_results))

        # 처방 권고 생성
        prescription = AllergyPrescription(
            prescription_id=str(uuid.uuid4()),
            created_at=datetime.now(),
            diagnosis_date=diagnosis_date,
            diagnosis_results=parsed_results,
            positive_count=len(positive_results),
            highest_grade=highest_grade,
            risk_level=risk_level,
            critical_allergens=critical_allergens,
        )

        # 양성 항원에 대한 처방 정보 생성
        for result in positive_results:
            # 음식 섭취 제한
            food_restriction = self._generate_food_restriction(result)
            if food_restriction:
                prescription.food_restrictions.append(food_restriction)

            # 예상 증상
            symptoms = self._predict_symptoms(result)
            prescription.predicted_symptoms.extend(symptoms)

            # 교차반응 경고
            cross_alerts = self._generate_cross_reactivity_alerts(result)
            prescription.cross_reactivity_alerts.extend(cross_alerts)

        # 응급 가이드라인 (고위험군에 대해)
        prescription.emergency_guidelines = self._generate_emergency_guidelines(risk_level)

        # 의료 권고사항
        prescription.medical_recommendation = self._generate_medical_recommendation(
            highest_grade, len(positive_results), risk_level
        )

        # 일반 권고사항
        prescription.general_recommendations = self._generate_general_recommendations(
            positive_results, risk_level
        )

        # 생활 팁
        prescription.lifestyle_tips = self._generate_lifestyle_tips(positive_results)

        return prescription

    def _parse_diagnosis_results(self, raw_results: list[dict]) -> list[DiagnosisResult]:
        """진단 결과 파싱"""
        parsed = []

        for item in raw_results:
            allergen_code = item.get("allergen", "")
            grade = item.get("grade", 0)

            # 알러젠 정보 조회
            allergen_info = get_allergen_info(allergen_code)

            if allergen_info:
                category = AllergenCategory.FOOD if allergen_code in FOOD_ALLERGENS else AllergenCategory.INHALANT
                parsed.append(DiagnosisResult(
                    allergen=allergen_code,
                    allergen_kr=allergen_info["name_kr"],
                    grade=grade,
                    category=category,
                ))
            else:
                # 알 수 없는 알러젠은 기본값으로 처리
                parsed.append(DiagnosisResult(
                    allergen=allergen_code,
                    allergen_kr=allergen_code,
                    grade=grade,
                    category=AllergenCategory.FOOD,
                ))

        return parsed

    def _calculate_risk_level(self, highest_grade: int, positive_count: int) -> RiskLevel:
        """위험도 수준 계산"""
        if highest_grade >= 6 or (highest_grade >= 5 and positive_count >= 3):
            return RiskLevel.CRITICAL
        elif highest_grade >= 5 or (highest_grade >= 4 and positive_count >= 3):
            return RiskLevel.HIGH
        elif highest_grade >= 3 or positive_count >= 2:
            return RiskLevel.MODERATE
        elif highest_grade >= 1:
            return RiskLevel.LOW
        else:
            return RiskLevel.NONE

    def _generate_food_restriction(self, result: DiagnosisResult) -> Optional[FoodRestriction]:
        """음식 섭취 제한 정보 생성"""
        allergen_info = get_allergen_info(result.allergen)
        if not allergen_info:
            return None

        # 식품 알러지가 아닌 경우
        if result.category != AllergenCategory.FOOD:
            # 흡입성 알러지의 경우 food_cautions 반환
            if "food_cautions" in allergen_info and allergen_info["food_cautions"]:
                return FoodRestriction(
                    allergen=result.allergen,
                    allergen_kr=result.allergen_kr,
                    restriction_level=result.restriction_level,
                    grade=result.grade,
                    avoid_foods=[],
                    hidden_sources=allergen_info.get("food_cautions", []),
                    substitutes=[],
                    restaurant_cautions=[],
                    label_keywords=[],
                    label_keywords_en=[],
                )
            return None

        # 대체 식품 변환
        substitutes = []
        for sub in allergen_info.get("substitutes", []):
            substitutes.append(FoodSubstitute(
                original=sub.get("original", ""),
                substitutes=sub.get("alternatives", []),
                notes=sub.get("notes", ""),
            ))

        return FoodRestriction(
            allergen=result.allergen,
            allergen_kr=result.allergen_kr,
            restriction_level=result.restriction_level,
            grade=result.grade,
            avoid_foods=allergen_info.get("avoid_foods", []),
            hidden_sources=allergen_info.get("hidden_sources", []),
            substitutes=substitutes,
            restaurant_cautions=allergen_info.get("restaurant_cautions", []),
            label_keywords=allergen_info.get("label_keywords_kr", []),
            label_keywords_en=allergen_info.get("label_keywords_en", []),
        )

    def _predict_symptoms(self, result: DiagnosisResult) -> list[SymptomPrediction]:
        """등급별 예상 증상 예측"""
        allergen_info = get_allergen_info(result.allergen)
        if not allergen_info:
            return []

        symptoms_data = allergen_info.get("symptoms_by_grade", {})

        # 등급 범위 결정
        if result.grade <= 2:
            grade_key = "1-2"
        elif result.grade <= 4:
            grade_key = "3-4"
        else:
            grade_key = "5-6"

        grade_symptoms = symptoms_data.get(grade_key, {})
        symptom_list = grade_symptoms.get("symptoms", [])
        severity = grade_symptoms.get("severity", "mild")

        predictions = []
        for symptom in symptom_list:
            predictions.append(SymptomPrediction(
                symptom=symptom.get("name_en", ""),
                symptom_kr=symptom.get("name", ""),
                probability=symptom.get("probability", ""),
                onset_time=symptom.get("onset", ""),
                severity=severity,
                description=f"{result.allergen_kr} 노출 시 발생 가능한 증상",
            ))

        return predictions

    def _generate_cross_reactivity_alerts(self, result: DiagnosisResult) -> list[CrossReactivityAlert]:
        """교차반응 경고 생성"""
        allergen_info = get_allergen_info(result.allergen)
        if not allergen_info:
            return []

        cross_data = allergen_info.get("cross_reactivity", [])
        alerts = []

        for cross in cross_data:
            alerts.append(CrossReactivityAlert(
                primary_allergen=result.allergen,
                primary_allergen_kr=result.allergen_kr,
                related_allergen=cross.get("allergen", ""),
                related_allergen_kr=cross.get("allergen_kr", ""),
                probability=cross.get("probability", ""),
                common_protein=cross.get("common_protein", ""),
                related_foods=cross.get("related_foods", []),
                recommendation=f"{cross.get('allergen_kr', '')}에 대해서도 주의가 필요합니다.",
            ))

        return alerts

    def _generate_emergency_guidelines(self, risk_level: RiskLevel) -> list[EmergencyGuideline]:
        """응급 가이드라인 생성"""
        guidelines = []

        if risk_level in [RiskLevel.CRITICAL, RiskLevel.HIGH]:
            # 아나필락시스 가이드
            ana_guide = self.emergency_guidelines.get("anaphylaxis", {})
            guidelines.append(EmergencyGuideline(
                condition=ana_guide.get("condition", "아나필락시스"),
                condition_en=ana_guide.get("condition_en", "Anaphylaxis"),
                symptoms=ana_guide.get("symptoms", []),
                immediate_actions=ana_guide.get("immediate_actions", []),
                medication_info=ana_guide.get("medication_info", ""),
                when_to_call_119=ana_guide.get("when_to_call_119", ""),
            ))

        if risk_level in [RiskLevel.CRITICAL, RiskLevel.HIGH, RiskLevel.MODERATE]:
            # 중등도 반응 가이드
            mod_guide = self.emergency_guidelines.get("moderate_reaction", {})
            guidelines.append(EmergencyGuideline(
                condition=mod_guide.get("condition", "중등도 알러지 반응"),
                condition_en=mod_guide.get("condition_en", "Moderate Allergic Reaction"),
                symptoms=mod_guide.get("symptoms", []),
                immediate_actions=mod_guide.get("immediate_actions", []),
                medication_info=mod_guide.get("medication_info", ""),
                when_to_call_119=mod_guide.get("when_to_call_119", ""),
            ))

        # 경미한 반응 가이드 (모든 경우)
        if risk_level != RiskLevel.NONE:
            mild_guide = self.emergency_guidelines.get("mild_reaction", {})
            guidelines.append(EmergencyGuideline(
                condition=mild_guide.get("condition", "경미한 알러지 반응"),
                condition_en=mild_guide.get("condition_en", "Mild Allergic Reaction"),
                symptoms=mild_guide.get("symptoms", []),
                immediate_actions=mild_guide.get("immediate_actions", []),
                medication_info=mild_guide.get("medication_info", ""),
                when_to_call_119=mild_guide.get("when_to_call_119", ""),
            ))

        return guidelines

    def _generate_medical_recommendation(
        self,
        highest_grade: int,
        positive_count: int,
        risk_level: RiskLevel,
    ) -> MedicalRecommendation:
        """의료 권고사항 생성"""
        # 상담 필요성 및 긴급도 결정
        if risk_level == RiskLevel.CRITICAL:
            consultation_needed = True
            consultation_urgency = "urgent"
            epinephrine_recommended = True
            follow_up_period = "3개월"
        elif risk_level == RiskLevel.HIGH:
            consultation_needed = True
            consultation_urgency = "recommended"
            epinephrine_recommended = True
            follow_up_period = "6개월"
        elif risk_level == RiskLevel.MODERATE:
            consultation_needed = True
            consultation_urgency = "recommended"
            epinephrine_recommended = False
            follow_up_period = "6-12개월"
        else:
            consultation_needed = positive_count > 0
            consultation_urgency = "routine"
            epinephrine_recommended = False
            follow_up_period = "12개월"

        # 추가 검사 권고
        additional_tests = []
        if highest_grade >= 3:
            additional_tests.append("피부단자검사 (Skin Prick Test)")
        if highest_grade >= 4:
            additional_tests.append("경구유발검사 (Oral Food Challenge) - 전문의 판단 하에")
        if positive_count >= 3:
            additional_tests.append("알러지 성분 검사 (Component-resolved diagnostics)")

        # 참고사항
        notes = []
        if epinephrine_recommended:
            notes.append("에피네프린 자가주사기(에피펜) 처방 및 사용법 교육 필요")
        if highest_grade >= 5:
            notes.append("응급상황 대비 행동 계획 수립 권장")
            notes.append("학교/직장에 알러지 정보 공유 권장")
        if positive_count >= 2:
            notes.append("영양사 상담을 통한 식단 관리 권장")

        return MedicalRecommendation(
            consultation_needed=consultation_needed,
            consultation_urgency=consultation_urgency,
            specialist_type="알러지 전문의 (알레르기내과 또는 소아알레르기)",
            epinephrine_recommended=epinephrine_recommended,
            follow_up_period=follow_up_period,
            additional_tests=additional_tests,
            notes=notes,
        )

    def _generate_general_recommendations(
        self,
        positive_results: list[DiagnosisResult],
        risk_level: RiskLevel,
    ) -> list[str]:
        """일반 권고사항 생성"""
        recommendations = []

        # 기본 권고사항
        if positive_results:
            recommendations.append("식품 구매 시 반드시 성분표를 확인하세요.")
            recommendations.append("외식 시 알러지 정보를 미리 알리고 확인하세요.")

        # 위험도별 권고사항
        if risk_level == RiskLevel.CRITICAL:
            recommendations.append("에피네프린 자가주사기를 항상 휴대하세요.")
            recommendations.append("알러지 의료 경고 팔찌/목걸이 착용을 권장합니다.")
            recommendations.append("가족, 친구, 동료에게 응급 대처법을 교육하세요.")
            recommendations.append("응급상황 시 행동 계획을 문서화하여 휴대하세요.")
        elif risk_level == RiskLevel.HIGH:
            recommendations.append("에피네프린 자가주사기 처방을 의사와 상담하세요.")
            recommendations.append("알러지 응급 키트를 준비해 두세요.")
            recommendations.append("응급 연락처를 휴대폰에 저장해 두세요.")
        elif risk_level == RiskLevel.MODERATE:
            recommendations.append("항히스타민제를 상비해 두세요.")
            recommendations.append("증상 발생 시 기록을 남기세요.")

        # 식품 관련 권고
        food_allergens = [r for r in positive_results if r.category == AllergenCategory.FOOD]
        if food_allergens:
            recommendations.append("가공식품에 숨겨진 알러젠에 주의하세요.")
            recommendations.append("조리 도구의 교차 오염에 주의하세요.")

        # 흡입성 알러젠 관련 권고
        inhalant_allergens = [r for r in positive_results if r.category == AllergenCategory.INHALANT]
        if inhalant_allergens:
            recommendations.append("실내 환경 관리에 신경 쓰세요.")
            recommendations.append("공기청정기 사용을 고려하세요.")

        return recommendations

    def _generate_lifestyle_tips(self, positive_results: list[DiagnosisResult]) -> list[str]:
        """생활 팁 생성"""
        tips = []

        allergen_codes = [r.allergen for r in positive_results]

        # 식품 알러지 관련 팁
        if any(code in FOOD_ALLERGENS for code in allergen_codes):
            tips.append("집에서 직접 요리하면 알러젠 노출을 더 잘 통제할 수 있습니다.")
            tips.append("외식 시 '알러지 카드'를 준비하면 의사소통이 쉬워집니다.")
            tips.append("여행 시 현지 언어로 된 알러지 정보를 준비하세요.")

        # 집먼지진드기
        if "dust_mite" in allergen_codes:
            tips.append("침구류를 주 1회 60°C 이상의 물로 세탁하세요.")
            tips.append("진드기 방지 침구 커버 사용을 권장합니다.")
            tips.append("카펫 대신 나무/타일 바닥을 권장합니다.")
            tips.append("실내 습도를 50% 이하로 유지하세요.")

        # 꽃가루
        if "pollen" in allergen_codes:
            tips.append("꽃가루 예보를 확인하고 농도가 높은 날은 외출을 자제하세요.")
            tips.append("외출 시 마스크와 선글라스를 착용하세요.")
            tips.append("외출 후에는 샤워하고 옷을 갈아입으세요.")
            tips.append("창문을 닫고 에어컨을 사용하세요.")

        # 곰팡이
        if "mold" in allergen_codes:
            tips.append("욕실과 주방의 환기를 자주 하세요.")
            tips.append("제습기를 사용하여 습도를 관리하세요.")
            tips.append("곰팡이가 발생하면 즉시 제거하세요.")

        # 반려동물
        if any(code in allergen_codes for code in ["cat", "dog", "pet_dander"]):
            tips.append("반려동물을 침실에 들이지 마세요.")
            tips.append("반려동물을 정기적으로 목욕시키세요.")
            tips.append("HEPA 필터 공기청정기를 사용하세요.")
            tips.append("손을 자주 씻으세요.")

        return tips

    def get_grade_description(self, grade: int) -> dict:
        """등급 설명 조회"""
        return GRADE_DESCRIPTIONS.get(grade, GRADE_DESCRIPTIONS[0])

    def get_allergen_list(self) -> list[dict]:
        """알러젠 목록 조회"""
        result = []

        for code, info in FOOD_ALLERGENS.items():
            result.append({
                "code": code,
                "name_kr": info["name_kr"],
                "name_en": info["name_en"],
                "category": "food",
            })

        for code, info in INHALANT_ALLERGENS.items():
            result.append({
                "code": code,
                "name_kr": info["name_kr"],
                "name_en": info["name_en"],
                "category": "inhalant",
            })

        return result
