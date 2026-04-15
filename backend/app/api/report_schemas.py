"""알러지 리포트 스키마 (공개 API, 인증 불필요)"""
from pydantic import BaseModel, Field
from typing import Optional


class AllergenGradeItem(BaseModel):
    """개별 알러젠 등급 항목"""
    code: str = Field(..., description="알러젠 코드 (예: peanut, dust_mite)")
    grade: int = Field(..., ge=0, le=6, description="등급 (0-6)")


class ReportRequest(BaseModel):
    """리포트 생성 요청"""
    allergens: list[AllergenGradeItem] = Field(..., min_length=1, description="알러젠 등급 목록")
    name: Optional[str] = Field(None, max_length=50, description="사용자 이름 (선택)")
