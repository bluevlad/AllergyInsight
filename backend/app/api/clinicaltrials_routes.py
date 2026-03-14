"""ClinicalTrials.gov 임상시험 검색 API (인증 불필요)

알러지 관련 임상시험 데이터를 검색합니다.
"""
from fastapi import APIRouter, Request, Query
from typing import Optional

from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

router = APIRouter(prefix="/clinicaltrials", tags=["Clinical Trials"])


@router.get("/search")
@limiter.limit("20/minute")
async def search_trials(
    request: Request,
    allergen: str = Query(..., description="알러젠 (예: peanut, milk, egg)"),
    max_results: int = Query(20, ge=1, le=50, description="최대 결과 수"),
    status: Optional[str] = Query(None, description="시험 상태 (RECRUITING, COMPLETED 등)"),
):
    """알러지 관련 임상시험 검색"""
    from ..services.clinicaltrials_service import ClinicalTrialsService

    svc = ClinicalTrialsService()
    try:
        result = svc.search_allergy(allergen, max_results=max_results)

        trials = []
        for p in result.papers:
            trial = p.to_dict()
            trial["nct_id"] = p.source_id
            trials.append(trial)

        return {
            "success": True,
            "allergen": allergen,
            "total": result.total_count,
            "trials": trials,
            "search_time_ms": round(result.search_time_ms, 1),
        }
    finally:
        svc.close()


@router.get("/study/{nct_id}")
@limiter.limit("30/minute")
async def get_study(request: Request, nct_id: str):
    """NCT ID로 임상시험 상세 조회"""
    from ..services.clinicaltrials_service import ClinicalTrialsService

    svc = ClinicalTrialsService()
    try:
        paper = svc.get_study(nct_id)
        if not paper:
            return {"success": False, "error": f"NCT ID '{nct_id}'를 찾을 수 없습니다."}

        trial = paper.to_dict()
        trial["nct_id"] = paper.source_id
        return {"success": True, "trial": trial}
    finally:
        svc.close()


@router.get("/recruiting")
@limiter.limit("20/minute")
async def search_recruiting(
    request: Request,
    allergen: str = Query(..., description="알러젠"),
    max_results: int = Query(20, ge=1, le=50),
):
    """모집 중인 알러지 임상시험 검색"""
    from ..services.clinicaltrials_service import ClinicalTrialsService

    svc = ClinicalTrialsService()
    try:
        result = svc.search_recruiting(allergen, max_results=max_results)

        trials = []
        for p in result.papers:
            trial = p.to_dict()
            trial["nct_id"] = p.source_id
            trials.append(trial)

        return {
            "success": True,
            "allergen": allergen,
            "status_filter": "RECRUITING",
            "total": result.total_count,
            "trials": trials,
        }
    finally:
        svc.close()
