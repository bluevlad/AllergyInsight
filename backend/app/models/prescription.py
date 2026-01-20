"""처방 권고 모델

SGTi-Allergy Screen PLUS 진단 결과를 기반으로
음식 섭취 제한 및 처방 권고를 생성하기 위한 데이터 모델입니다.
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from enum import Enum


class RestrictionLevel(str, Enum):
    """섭취 제한 수준"""
    NONE = "none"           # 제한 없음 (등급 0)
    MONITOR = "monitor"     # 모니터링 (등급 1)
    CAUTION = "caution"     # 주의 (등급 2)
    LIMIT = "limit"         # 제한 (등급 3)
    AVOID = "avoid"         # 회피 (등급 4)
    STRICT_AVOID = "strict_avoid"  # 완전 회피 (등급 5-6)


class RiskLevel(str, Enum):
    """전체 위험도 수준"""
    NONE = "none"           # 위험 없음
    LOW = "low"             # 낮음
    MODERATE = "moderate"   # 중간
    HIGH = "high"           # 높음
    CRITICAL = "critical"   # 치명적 (아나필락시스 위험)


class AllergenCategory(str, Enum):
    """알러젠 카테고리"""
    FOOD = "food"           # 식품 알러지
    INHALANT = "inhalant"   # 흡입성 알러지


@dataclass
class DiagnosisResult:
    """개별 항원 진단 결과"""
    allergen: str           # 항원 코드 (예: "peanut")
    allergen_kr: str        # 항원 한글명 (예: "땅콩")
    grade: int              # 등급 (0-6)
    category: AllergenCategory

    @property
    def is_positive(self) -> bool:
        """양성 여부"""
        return self.grade >= 1

    @property
    def restriction_level(self) -> RestrictionLevel:
        """등급별 제한 수준"""
        if self.grade == 0:
            return RestrictionLevel.NONE
        elif self.grade == 1:
            return RestrictionLevel.MONITOR
        elif self.grade == 2:
            return RestrictionLevel.CAUTION
        elif self.grade == 3:
            return RestrictionLevel.LIMIT
        elif self.grade == 4:
            return RestrictionLevel.AVOID
        else:  # 5-6
            return RestrictionLevel.STRICT_AVOID

    def to_dict(self) -> dict:
        return {
            "allergen": self.allergen,
            "allergen_kr": self.allergen_kr,
            "grade": self.grade,
            "category": self.category.value,
            "is_positive": self.is_positive,
            "restriction_level": self.restriction_level.value,
        }


@dataclass
class FoodSubstitute:
    """대체 식품"""
    original: str           # 원래 식품
    substitutes: list[str]  # 대체 식품 목록
    notes: str = ""         # 참고사항

    def to_dict(self) -> dict:
        return {
            "original": self.original,
            "substitutes": self.substitutes,
            "notes": self.notes,
        }


@dataclass
class FoodRestriction:
    """음식 섭취 제한 정보"""
    allergen: str                     # 항원 코드
    allergen_kr: str                  # 항원 한글명
    restriction_level: RestrictionLevel
    grade: int                        # 진단 등급

    # 회피해야 할 식품
    avoid_foods: list[str] = field(default_factory=list)  # 직접 회피 식품
    hidden_sources: list[str] = field(default_factory=list)  # 숨겨진 알러젠 포함 식품

    # 대체 식품
    substitutes: list[FoodSubstitute] = field(default_factory=list)

    # 외식 주의
    restaurant_cautions: list[str] = field(default_factory=list)

    # 라벨 확인 키워드
    label_keywords: list[str] = field(default_factory=list)
    label_keywords_en: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "allergen": self.allergen,
            "allergen_kr": self.allergen_kr,
            "restriction_level": self.restriction_level.value,
            "grade": self.grade,
            "avoid_foods": self.avoid_foods,
            "hidden_sources": self.hidden_sources,
            "substitutes": [s.to_dict() for s in self.substitutes],
            "restaurant_cautions": self.restaurant_cautions,
            "label_keywords": self.label_keywords,
            "label_keywords_en": self.label_keywords_en,
        }


@dataclass
class CrossReactivityAlert:
    """교차반응 경고"""
    primary_allergen: str       # 양성 판정 항원
    primary_allergen_kr: str    # 양성 판정 항원 한글명
    related_allergen: str       # 교차반응 가능 항원
    related_allergen_kr: str    # 교차반응 가능 항원 한글명
    probability: str            # 교차반응 확률 (예: "25-40%")
    common_protein: str = ""    # 공통 단백질/원인
    related_foods: list[str] = field(default_factory=list)  # 관련 식품
    recommendation: str = ""    # 권고사항

    def to_dict(self) -> dict:
        return {
            "primary_allergen": self.primary_allergen,
            "primary_allergen_kr": self.primary_allergen_kr,
            "related_allergen": self.related_allergen,
            "related_allergen_kr": self.related_allergen_kr,
            "probability": self.probability,
            "common_protein": self.common_protein,
            "related_foods": self.related_foods,
            "recommendation": self.recommendation,
        }


@dataclass
class SymptomPrediction:
    """등급별 예상 증상"""
    symptom: str                # 증상 영문명
    symptom_kr: str             # 증상 한글명
    probability: str            # 발생 확률 (예: "70-80%")
    onset_time: str             # 발현 시간 (예: "섭취 후 30분 이내")
    severity: str               # 심각도 (mild, moderate, severe, anaphylaxis)
    description: str = ""       # 상세 설명

    def to_dict(self) -> dict:
        return {
            "symptom": self.symptom,
            "symptom_kr": self.symptom_kr,
            "probability": self.probability,
            "onset_time": self.onset_time,
            "severity": self.severity,
            "description": self.description,
        }


@dataclass
class EmergencyGuideline:
    """응급 대처 가이드"""
    condition: str              # 상태 (예: "아나필락시스")
    condition_en: str           # 영문 상태
    symptoms: list[str]         # 증상 목록
    immediate_actions: list[str]  # 즉각 대처법
    medication_info: str = ""   # 약물 정보
    when_to_call_119: str = ""  # 119 호출 기준

    def to_dict(self) -> dict:
        return {
            "condition": self.condition,
            "condition_en": self.condition_en,
            "symptoms": self.symptoms,
            "immediate_actions": self.immediate_actions,
            "medication_info": self.medication_info,
            "when_to_call_119": self.when_to_call_119,
        }


@dataclass
class MedicalRecommendation:
    """의료 권고사항"""
    consultation_needed: bool       # 전문의 상담 필요 여부
    consultation_urgency: str       # 긴급도 (routine, recommended, urgent)
    specialist_type: str            # 전문의 종류 (예: "알러지 전문의")
    epinephrine_recommended: bool   # 에피네프린 처방 권고
    follow_up_period: str           # 추적 검사 주기
    additional_tests: list[str] = field(default_factory=list)  # 추가 검사 권고
    notes: list[str] = field(default_factory=list)  # 추가 참고사항

    def to_dict(self) -> dict:
        return {
            "consultation_needed": self.consultation_needed,
            "consultation_urgency": self.consultation_urgency,
            "specialist_type": self.specialist_type,
            "epinephrine_recommended": self.epinephrine_recommended,
            "follow_up_period": self.follow_up_period,
            "additional_tests": self.additional_tests,
            "notes": self.notes,
        }


@dataclass
class AllergyPrescription:
    """종합 처방 권고"""
    prescription_id: str
    created_at: datetime

    # 진단 정보
    diagnosis_date: Optional[datetime] = None
    diagnosis_results: list[DiagnosisResult] = field(default_factory=list)

    # 요약 정보
    positive_count: int = 0
    highest_grade: int = 0
    risk_level: RiskLevel = RiskLevel.NONE
    critical_allergens: list[str] = field(default_factory=list)  # 고위험 항원

    # 처방 내용
    food_restrictions: list[FoodRestriction] = field(default_factory=list)
    cross_reactivity_alerts: list[CrossReactivityAlert] = field(default_factory=list)
    predicted_symptoms: list[SymptomPrediction] = field(default_factory=list)
    emergency_guidelines: list[EmergencyGuideline] = field(default_factory=list)
    medical_recommendation: Optional[MedicalRecommendation] = None

    # 일반 권고사항
    general_recommendations: list[str] = field(default_factory=list)
    lifestyle_tips: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "prescription_id": self.prescription_id,
            "created_at": self.created_at.isoformat(),
            "diagnosis_date": self.diagnosis_date.isoformat() if self.diagnosis_date else None,
            "diagnosis_results": [d.to_dict() for d in self.diagnosis_results],
            "summary": {
                "positive_count": self.positive_count,
                "highest_grade": self.highest_grade,
                "risk_level": self.risk_level.value,
                "critical_allergens": self.critical_allergens,
            },
            "food_restrictions": [f.to_dict() for f in self.food_restrictions],
            "cross_reactivity_alerts": [c.to_dict() for c in self.cross_reactivity_alerts],
            "predicted_symptoms": [s.to_dict() for s in self.predicted_symptoms],
            "emergency_guidelines": [e.to_dict() for e in self.emergency_guidelines],
            "medical_recommendation": self.medical_recommendation.to_dict() if self.medical_recommendation else None,
            "general_recommendations": self.general_recommendations,
            "lifestyle_tips": self.lifestyle_tips,
        }


# 등급별 제한 수준 설명
GRADE_DESCRIPTIONS = {
    0: {
        "level": "음성",
        "description": "알러지 반응 없음",
        "action": "제한 없이 섭취 가능",
        "color": "green",
    },
    1: {
        "level": "약양성",
        "description": "매우 약한 반응",
        "action": "섭취 후 증상 관찰 권장",
        "color": "lightgreen",
    },
    2: {
        "level": "양성",
        "description": "약한 반응",
        "action": "소량 섭취 시 주의 관찰",
        "color": "yellow",
    },
    3: {
        "level": "양성",
        "description": "중등도 반응",
        "action": "섭취 제한 권고",
        "color": "orange",
    },
    4: {
        "level": "강양성",
        "description": "강한 반응",
        "action": "섭취 회피 권고",
        "color": "orangered",
    },
    5: {
        "level": "강양성",
        "description": "매우 강한 반응",
        "action": "완전 회피 필수",
        "color": "red",
    },
    6: {
        "level": "최강양성",
        "description": "극심한 반응, 아나필락시스 위험",
        "action": "완전 회피 + 응급약 휴대 필수",
        "color": "darkred",
    },
}
