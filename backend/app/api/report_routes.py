"""알러지 리포트 공개 API (인증 불필요)"""
from fastapi import APIRouter

from .report_schemas import ReportRequest
from .report_service import generate_report

router = APIRouter(prefix="/report", tags=["Report"])


@router.post("/generate")
async def create_report(request: ReportRequest):
    """알러지 리포트 생성

    진단키트 없이 사용자가 직접 입력한 알러젠 등급을 기반으로
    식품가이드, 생활관리, 응급정보를 통합한 1회성 리포트를 생성합니다.
    """
    allergens = [item.model_dump() for item in request.allergens]
    report = generate_report(allergens, request.name)
    return {"success": True, **report}
