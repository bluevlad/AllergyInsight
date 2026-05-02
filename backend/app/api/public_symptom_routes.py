"""증상 텍스트 → 알러젠 매칭 비회원 공개 라우터 (Phase 2)

사용자가 자유 텍스트로 입력한 증상에서 키워드를 추출해, 36종 활성 알러젠
의 등급별 증상 데이터와 매칭되는 후보를 점수 순으로 반환한다.

원칙:
- 진단을 내리지 않는다 — "유사 사례 매칭" 결과로만 응답 표현
- 모든 응답에 응급 가드(safety_gate) + 의료 면책 동반
- 매칭이 없을 수 있으며, 그때는 "관련 알러젠을 찾지 못했습니다" 안내
"""
from fastapi import APIRouter, Request
from pydantic import BaseModel, Field
from slowapi import Limiter
from slowapi.util import get_remote_address

from ..services.safety_gate import assess as safety_assess
from ..services.symptom_matcher import get_index_stats, match_symptoms

router = APIRouter(prefix="/public/symptom", tags=["Public Symptom Match"])

_limiter = Limiter(key_func=get_remote_address)


_DISCLAIMER = (
    "본 응답은 의료 진단이 아닌 정보 매칭이며, 입력하신 증상과 논문·전문기관 자료에 "
    "보고된 알러지 증상 패턴 사이의 텍스트 매칭 결과를 보여줍니다. "
    "정확한 진단·처방·치료는 반드시 전문 의료진과 상담하세요."
)

_NO_MATCH_MESSAGE = (
    "입력하신 증상과 매칭되는 알러젠 후보를 찾지 못했습니다. "
    "증상이 지속되거나 악화될 경우 의료진과 상담하세요."
)


class SymptomMatchRequest(BaseModel):
    """증상 매칭 요청"""
    text: str = Field(
        ...,
        min_length=2,
        max_length=500,
        description="증상 자유 텍스트 (예: '입술이 부어서 따끔거리고 두드러기가 났어요')",
    )
    top_k: int = Field(5, ge=1, le=10, description="반환할 후보 수")


@router.get("/stats")
async def get_stats():
    """증상 매칭 인덱스 통계 (개발/관리자용)."""
    return {
        "success": True,
        **get_index_stats(),
    }


@router.post("/match")
@_limiter.limit("20/minute")
async def match(request: Request, body: SymptomMatchRequest):
    """증상 텍스트 → 알러젠 후보 매칭 (비회원 공개)

    응답:
        - matches: 점수 순 후보 리스트 (allergen_code, name_kr, name_en,
          category, score, match_count, matched_symptoms)
        - match_count: 매칭된 알러젠 수
        - safety: safety_gate 평가 (응급/주의 시 프론트엔드 배너 노출)
        - message: 결과 요약 메시지
        - disclaimer: 의료 면책 문구
    """
    safety = safety_assess(body.text)

    # 응급 시에도 매칭 정보는 함께 보내되, safety 배너가 우선시되도록 클라이언트가 처리
    matches = match_symptoms(body.text, top_k=body.top_k)

    if not matches:
        message = _NO_MATCH_MESSAGE
    elif safety.is_emergency:
        # 매칭은 보여주되, 응급 메시지를 답변 메시지로 우선 노출
        message = (
            "⚠️ 입력하신 증상에서 응급 의심 키워드가 감지되었습니다. "
            "아래 매칭 정보보다 응급 안내를 우선 확인하세요."
        )
    else:
        message = (
            f"입력하신 증상과 유사한 사례가 보고된 알러젠 {len(matches)}건을 매칭했습니다. "
            "본 결과는 의료 진단이 아닌 텍스트 매칭이며, 의료진 상담을 권장합니다."
        )

    return {
        "success": True,
        "input_text": body.text,
        "matches": matches,
        "match_count": len(matches),
        "safety": safety.to_dict(),
        "message": message,
        "disclaimer": _DISCLAIMER,
    }
