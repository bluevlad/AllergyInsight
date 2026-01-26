"""Professional Service Routes - 의료진 전용 API

/api/pro/* 엔드포인트를 제공합니다.
"""
from fastapi import APIRouter

from .diagnosis import router as diagnosis_router
from .patients import router as patients_router
from .research import router as research_router
from .dashboard import router as dashboard_router

router = APIRouter(prefix="/pro", tags=["Professional"])

# 하위 라우터 등록
router.include_router(diagnosis_router)
router.include_router(patients_router)
router.include_router(research_router)
router.include_router(dashboard_router)
