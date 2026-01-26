"""Consumer Service Routes - 일반 사용자 전용 API

/api/consumer/* 엔드포인트를 제공합니다.
"""
from fastapi import APIRouter

from .my_diagnosis import router as my_diagnosis_router
from .guide import router as guide_router
from .emergency import router as emergency_router
from .kit import router as kit_router

router = APIRouter(prefix="/consumer", tags=["Consumer"])

# 하위 라우터 등록
router.include_router(my_diagnosis_router)
router.include_router(guide_router)
router.include_router(emergency_router)
router.include_router(kit_router)
