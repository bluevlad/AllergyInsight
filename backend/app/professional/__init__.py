"""Professional Service Module - 의료진 전용 서비스

의사, 간호사, 검사 담당자, 병원 관리자를 위한 전문 서비스입니다.

주요 기능:
- 진단 입력/관리 (diagnosis)
- 환자 관리 (patients)
- 논문 검색/Q&A (research)
- 대시보드 (dashboard)
- 조직/병원 관리 (organization, hospital)
"""

from .routes import router as professional_router

__all__ = ["professional_router"]
