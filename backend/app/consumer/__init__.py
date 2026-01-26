"""Consumer Service Module - 일반 사용자 전용 서비스

환자/일반 사용자를 위한 서비스입니다.

주요 기능:
- 내 진단 결과 조회 (my_diagnosis)
- 식품/생활 가이드 (guide)
- 응급 대처 정보 (emergency)
- 키트 등록 (kit)
"""

from .routes import router as consumer_router

__all__ = ["consumer_router"]
