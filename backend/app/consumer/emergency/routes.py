"""Consumer Emergency Routes - 응급 대처 정보 API

알러지 응급 상황 대처 정보를 제공합니다.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel

from ...database.connection import get_db
from ...database.models import User
from ...core.auth import require_consumer
from ...core.allergen import EMERGENCY_GUIDELINES

router = APIRouter(prefix="/emergency", tags=["Consumer - Emergency"])


# ============================================================================
# Endpoints
# ============================================================================

@router.get("/guidelines")
async def get_emergency_guidelines(
    user: User = Depends(require_consumer),
    db: Session = Depends(get_db)
):
    """응급 대처 가이드라인 조회"""
    return {
        "guidelines": EMERGENCY_GUIDELINES,
        "emergency_contacts": {
            "emergency": "119",
            "poison_control": "1339",
            "hospital_info": "1577-1234",
        },
        "important_notes": [
            "아나필락시스 의심 시 즉시 119에 연락하세요",
            "에피펜이 있다면 즉시 사용하세요",
            "환자를 눕히고 다리를 높이세요",
            "호흡 곤란 시 앉은 자세가 도움됩니다",
            "의식이 없으면 회복 자세를 취하세요",
        ],
    }


@router.get("/action-plan")
async def get_action_plan(
    severity: str = "all",  # mild, moderate, severe, all
    user: User = Depends(require_consumer),
    db: Session = Depends(get_db)
):
    """상황별 행동 계획 조회"""
    action_plans = {
        "mild": {
            "title": "경미한 증상 (가려움, 발진, 콧물)",
            "symptoms": [
                "피부 가려움증",
                "두드러기 (국소적)",
                "콧물, 재채기",
                "눈 가려움",
            ],
            "actions": [
                "원인 물질 접촉 중단",
                "항히스타민제 복용",
                "증상 부위 냉찜질",
                "증상 변화 관찰 (30분~1시간)",
            ],
            "when_to_call_doctor": "증상이 2시간 이상 지속되거나 악화되는 경우",
        },
        "moderate": {
            "title": "중등도 증상 (전신 두드러기, 구토)",
            "symptoms": [
                "전신 두드러기",
                "얼굴 부종",
                "복통, 구토, 설사",
                "기침, 천명음",
            ],
            "actions": [
                "항히스타민제 복용",
                "증상이 심해지면 에피펜 사용 준비",
                "편안한 자세 유지",
                "응급실 방문 고려",
            ],
            "when_to_call_119": "호흡 곤란이 동반되거나 증상이 빠르게 악화되는 경우",
        },
        "severe": {
            "title": "심각한 증상 (아나필락시스)",
            "symptoms": [
                "호흡 곤란, 천명음",
                "목이 조이는 느낌",
                "혈압 저하, 어지러움",
                "의식 저하",
                "입술/혀 부종",
            ],
            "actions": [
                "즉시 119 신고",
                "에피펜 즉시 사용 (허벅지 바깥쪽)",
                "환자를 눕히고 다리 올리기",
                "호흡 곤란 시 앉은 자세 유지",
                "2차 반응 대비 병원 관찰 필요",
            ],
            "epinephrine_instructions": [
                "에피펜을 허벅지 바깥쪽에 수직으로 찌르기",
                "10초간 유지 후 제거",
                "주사 부위 마사지",
                "증상 지속 시 5-15분 후 재투여 가능",
            ],
        },
    }

    if severity == "all":
        return {"action_plans": action_plans}
    elif severity in action_plans:
        return {"action_plan": action_plans[severity]}
    else:
        return {"action_plans": action_plans}


@router.get("/epinephrine-guide")
async def get_epinephrine_guide(
    user: User = Depends(require_consumer),
    db: Session = Depends(get_db)
):
    """에피네프린(에피펜) 사용 가이드"""
    return {
        "what_is_epinephrine": {
            "description": "에피네프린은 아나필락시스 응급 치료제입니다.",
            "brands": ["에피펜(EpiPen)", "젝스트(Jext)", "아우비큐(Auvi-Q)"],
            "prescription_required": True,
        },
        "when_to_use": [
            "아나필락시스 증상이 나타날 때",
            "호흡 곤란, 목 조임",
            "의식 저하, 혈압 저하",
            "심각한 전신 두드러기와 다른 증상 동반 시",
        ],
        "how_to_use": {
            "preparation": [
                "에피펜을 케이스에서 꺼내기",
                "파란색 안전캡 제거",
            ],
            "injection": [
                "허벅지 바깥쪽 근육에 수직으로 강하게 찌르기",
                "옷 위로도 투여 가능",
                "10초간 유지",
            ],
            "after_injection": [
                "바늘 제거 후 주사 부위 마사지",
                "즉시 119 신고",
                "사용한 에피펜 병원에 가져가기",
            ],
        },
        "storage": [
            "15-25°C 상온 보관",
            "직사광선 피하기",
            "냉장 보관 금지",
            "유효기간 확인 (약액이 변색되면 사용 금지)",
        ],
        "important_reminders": [
            "항상 2개 이상 휴대 권장",
            "주변 사람에게 위치와 사용법 알리기",
            "유효기간 만료 전 교체",
            "에피펜 사용 후에도 반드시 병원 방문",
        ],
    }


@router.get("/hospital-checklist")
async def get_hospital_checklist(
    user: User = Depends(require_consumer),
    db: Session = Depends(get_db)
):
    """병원 방문 시 체크리스트"""
    return {
        "before_visit": [
            "알러지 검사 결과지 준비",
            "현재 복용 중인 약 목록",
            "증상 발생 시간 및 경과 기록",
            "의심되는 원인 물질 (식품 라벨 등)",
            "이전 응급 처치 내용",
        ],
        "questions_for_doctor": [
            "에피펜 처방이 필요한가요?",
            "응급 행동 계획을 세워주세요",
            "정기 검진 주기는 어떻게 되나요?",
            "식이 제한 범위를 알려주세요",
            "면역치료 가능성이 있나요?",
        ],
        "documents_to_request": [
            "알러지 응급 행동 계획서",
            "약 처방전",
            "알러지 증명서 (학교/직장용)",
            "식이 제한 목록",
        ],
    }
