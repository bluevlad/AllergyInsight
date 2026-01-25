"""AllergyInsight API 서버

FastAPI 기반 REST API 서버입니다.
논문 검색, Q&A, 수집 현황 조회 기능을 제공합니다.
인증 및 진단키트 관리 기능을 포함합니다.

실행 방법:
    cd C:\GIT\AllergyInsight\backend
    uvicorn app.api.main:app --reload --port 9040
"""
from fastapi import FastAPI, HTTPException, Query, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
import asyncio
import os

from ..services import (
    PaperSearchService,
    QAEngine,
    SymptomQAInterface,
    BatchProcessor,
    AllergenItem,
    create_allergen_items,
    SmartLoader,
    PrescriptionEngine,
    DiagnosisRepository,
)
from ..services.batch_processor import ProcessingStatus
from ..data.allergen_prescription_db import get_allergen_list
from ..models.prescription import GRADE_DESCRIPTIONS

# Auth imports
from ..auth.routes import router as auth_router
from ..auth.diagnosis_routes import router as diagnosis_router
from ..auth.paper_routes import router as paper_router
from ..auth.config import auth_settings
from ..database.connection import engine, init_db
from ..database.seed_users import seed_users

# Phase 1: Organization imports
from ..organization.routes import router as organization_router

# Phase 2: Hospital imports
from ..hospital.routes import router as hospital_router

# FastAPI 앱 생성
app = FastAPI(
    title="AllergyInsight API",
    description="SGTi-Allergy Screen PLUS 기반 알러지 진단 및 처방 권고 시스템",
    version="1.1.0",
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 개발용, 프로덕션에서는 특정 도메인 지정
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Session middleware (required for OAuth)
app.add_middleware(
    SessionMiddleware,
    secret_key=auth_settings.jwt_secret_key,
)

# Include auth routers
app.include_router(auth_router, prefix="/api")
app.include_router(diagnosis_router, prefix="/api")
app.include_router(paper_router, prefix="/api")
app.include_router(organization_router, prefix="/api")
app.include_router(hospital_router, prefix="/api")

# 전역 서비스 인스턴스
_search_service: Optional[PaperSearchService] = None
_qa_engine: Optional[QAEngine] = None
_batch_processor: Optional[BatchProcessor] = None
_prescription_engine: Optional[PrescriptionEngine] = None
_diagnosis_repository: Optional[DiagnosisRepository] = None
_collection_stats: dict = {
    "total_searches": 0,
    "total_papers_found": 0,
    "total_questions": 0,
    "allergens_searched": [],
    "last_search_time": None,
    "search_history": [],
}


def get_search_service() -> PaperSearchService:
    global _search_service
    if _search_service is None:
        _search_service = PaperSearchService()
    return _search_service


def get_qa_engine() -> QAEngine:
    global _qa_engine
    if _qa_engine is None:
        _qa_engine = QAEngine()
    return _qa_engine


def get_batch_processor() -> BatchProcessor:
    global _batch_processor
    if _batch_processor is None:
        _batch_processor = BatchProcessor()
    return _batch_processor


def get_prescription_engine() -> PrescriptionEngine:
    global _prescription_engine
    if _prescription_engine is None:
        _prescription_engine = PrescriptionEngine()
    return _prescription_engine


def get_diagnosis_repository() -> DiagnosisRepository:
    global _diagnosis_repository
    if _diagnosis_repository is None:
        _diagnosis_repository = DiagnosisRepository()
    return _diagnosis_repository


# =====================
# Request/Response 모델
# =====================

class SearchRequest(BaseModel):
    """검색 요청"""
    allergen: str = Field(..., description="알러지 항원 (예: peanut, milk)")
    include_cross_reactivity: bool = Field(True, description="교차 반응 포함 여부")
    max_results: int = Field(20, ge=1, le=100, description="최대 결과 수")


class QuestionRequest(BaseModel):
    """질문 요청"""
    question: str = Field(..., description="질문 내용")
    allergen: str = Field("peanut", description="알러지 항원")
    max_citations: int = Field(5, ge=1, le=10, description="최대 인용 수")


class BatchSearchRequest(BaseModel):
    """배치 검색 요청"""
    allergens: list[str] = Field(..., description="알러지 항원 목록")
    grades: Optional[dict[str, int]] = Field(None, description="항원별 등급")
    include_cross_reactivity: bool = Field(True)


class CollectionStats(BaseModel):
    """수집 통계"""
    total_searches: int
    total_papers_found: int
    total_questions: int
    allergens_searched: list[str]
    last_search_time: Optional[str]
    cache_stats: dict


class DiagnosisResultItem(BaseModel):
    """개별 진단 결과 항목"""
    allergen: str = Field(..., description="알러젠 코드 (예: peanut)")
    grade: int = Field(..., ge=0, le=6, description="검사 등급 (0-6)")


class DiagnosisRequest(BaseModel):
    """진단 결과 입력 요청"""
    diagnosis_results: list[DiagnosisResultItem] = Field(..., description="진단 결과 목록")
    diagnosis_date: Optional[str] = Field(None, description="검사 날짜 (ISO 형식)")
    patient_info: Optional[dict] = Field(None, description="환자 정보 (선택)")


class PrescriptionRequest(BaseModel):
    """처방 권고 생성 요청"""
    diagnosis_id: Optional[str] = Field(None, description="기존 진단 ID (저장된 진단 사용 시)")
    diagnosis_results: Optional[list[DiagnosisResultItem]] = Field(None, description="진단 결과 (직접 입력 시)")
    diagnosis_date: Optional[str] = Field(None, description="검사 날짜")


# =====================
# API 엔드포인트
# =====================

@app.get("/")
async def root():
    """API 루트"""
    return {
        "name": "AllergyInsight API",
        "version": "1.1.0",
        "status": "running",
        "endpoints": {
            "search": "/api/search",
            "qa": "/api/qa",
            "stats": "/api/stats",
            "batch": "/api/batch",
            "diagnosis": "/api/diagnosis",
            "prescription": "/api/prescription",
            "sgti": "/api/sgti",
        }
    }


@app.get("/api/health")
async def health_check():
    """헬스 체크"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


# =====================
# 검색 API
# =====================

@app.post("/api/search")
async def search_papers(request: SearchRequest):
    """
    알러지 논문 검색

    PubMed와 Semantic Scholar에서 논문을 검색합니다.
    """
    global _collection_stats

    service = get_search_service()

    result = service.search_allergy(
        allergen=request.allergen,
        include_cross_reactivity=request.include_cross_reactivity,
        max_results_per_source=request.max_results // 2,
    )

    # 통계 업데이트
    _collection_stats["total_searches"] += 1
    _collection_stats["total_papers_found"] += result.total_unique
    _collection_stats["last_search_time"] = datetime.now().isoformat()

    if request.allergen not in _collection_stats["allergens_searched"]:
        _collection_stats["allergens_searched"].append(request.allergen)

    # 검색 이력 추가
    _collection_stats["search_history"].append({
        "allergen": request.allergen,
        "papers_found": result.total_unique,
        "timestamp": datetime.now().isoformat(),
    })
    # 최근 50개만 유지
    _collection_stats["search_history"] = _collection_stats["search_history"][-50:]

    return {
        "success": True,
        "query": result.query,
        "total_found": result.total_unique,
        "pubmed_count": result.pubmed_count,
        "semantic_scholar_count": result.semantic_scholar_count,
        "downloadable_count": result.downloadable_count,
        "search_time_ms": round(result.search_time_ms, 2),
        "papers": [p.to_dict() for p in result.papers],
    }


@app.get("/api/search/{allergen}")
async def search_allergen(
    allergen: str,
    cross_reactivity: bool = True,
    max_results: int = 20,
):
    """GET 방식 검색"""
    request = SearchRequest(
        allergen=allergen,
        include_cross_reactivity=cross_reactivity,
        max_results=max_results,
    )
    return await search_papers(request)


# =====================
# Q&A API
# =====================

@app.post("/api/qa")
async def ask_question(request: QuestionRequest):
    """
    논문 기반 Q&A

    질문에 대해 논문을 기반으로 답변하고 출처를 제공합니다.
    """
    global _collection_stats

    engine = get_qa_engine()

    response = engine.ask(
        question=request.question,
        allergen=request.allergen,
        max_citations=request.max_citations,
    )

    # 통계 업데이트
    _collection_stats["total_questions"] += 1

    return {
        "success": True,
        "question": response.question,
        "answer": response.answer,
        "answer_formatted": response.format_with_citations(),
        "confidence": round(response.confidence, 2),
        "citations": [c.to_dict() for c in response.citations],
        "citation_count": len(response.citations),
        "related_symptoms": [s.to_dict() for s in response.related_symptoms],
        "warnings": response.warnings,
    }


@app.get("/api/qa/questions/{allergen}")
async def get_predefined_questions(allergen: str = "peanut"):
    """사전 정의된 질문 목록 조회"""
    engine = get_qa_engine()
    questions = engine.get_predefined_questions(allergen)
    return {
        "allergen": allergen,
        "questions": questions,
    }


# =====================
# 배치 처리 API
# =====================

@app.post("/api/batch/search")
async def batch_search(request: BatchSearchRequest, background_tasks: BackgroundTasks):
    """
    배치 논문 검색

    여러 알러지 항원에 대해 동시에 검색을 수행합니다.
    """
    processor = get_batch_processor()

    # AllergenItem 생성
    allergens = create_allergen_items(request.allergens, request.grades)

    # 작업 생성
    job = processor.create_job(allergens, sort_by_priority=True)

    # 백그라운드에서 처리
    background_tasks.add_task(
        processor.process_job_sync,
        job,
        request.include_cross_reactivity,
    )

    return {
        "success": True,
        "job_id": job.job_id,
        "total_allergens": len(allergens),
        "status": "started",
        "message": f"{len(allergens)}개 항원에 대한 검색이 시작되었습니다.",
    }


@app.get("/api/batch/status/{job_id}")
async def get_batch_status(job_id: str):
    """배치 작업 상태 조회"""
    processor = get_batch_processor()
    job = processor.get_job(job_id)

    if not job:
        raise HTTPException(status_code=404, detail="작업을 찾을 수 없습니다.")

    status = job.get_status_summary()

    return {
        "success": True,
        "job_id": job_id,
        **status,
    }


@app.get("/api/batch/results/{job_id}")
async def get_batch_results(job_id: str):
    """배치 작업 결과 조회"""
    processor = get_batch_processor()
    job = processor.get_job(job_id)

    if not job:
        raise HTTPException(status_code=404, detail="작업을 찾을 수 없습니다.")

    results = processor.get_completed_results(job)

    return {
        "success": True,
        "job_id": job_id,
        "is_completed": job.is_completed,
        "results": results,
    }


# =====================
# 통계 API
# =====================

@app.get("/api/stats")
async def get_stats():
    """
    수집 통계 조회

    전체 수집 현황 및 통계를 반환합니다.
    """
    global _collection_stats

    processor = get_batch_processor()
    cache_stats = processor.cache.get_stats()

    return {
        "success": True,
        "stats": {
            "total_searches": _collection_stats["total_searches"],
            "total_papers_found": _collection_stats["total_papers_found"],
            "total_questions": _collection_stats["total_questions"],
            "unique_allergens": len(_collection_stats["allergens_searched"]),
            "allergens_searched": _collection_stats["allergens_searched"],
            "last_search_time": _collection_stats["last_search_time"],
        },
        "cache": cache_stats,
        "recent_searches": _collection_stats["search_history"][-10:],
    }


@app.get("/api/stats/summary")
async def get_summary():
    """
    요약 통계

    대시보드용 간단한 요약 정보를 반환합니다.
    """
    global _collection_stats

    processor = get_batch_processor()
    cache_stats = processor.cache.get_stats()

    # 최근 검색 항원별 논문 수
    allergen_stats = {}
    for search in _collection_stats["search_history"]:
        allergen = search["allergen"]
        if allergen not in allergen_stats:
            allergen_stats[allergen] = {"searches": 0, "papers": 0}
        allergen_stats[allergen]["searches"] += 1
        allergen_stats[allergen]["papers"] += search["papers_found"]

    return {
        "overview": {
            "total_searches": _collection_stats["total_searches"],
            "total_papers": _collection_stats["total_papers_found"],
            "total_questions": _collection_stats["total_questions"],
            "unique_allergens": len(_collection_stats["allergens_searched"]),
            "cache_entries": cache_stats["valid_entries"],
        },
        "by_allergen": allergen_stats,
        "last_activity": _collection_stats["last_search_time"],
    }


@app.delete("/api/stats/reset")
async def reset_stats():
    """통계 초기화"""
    global _collection_stats

    _collection_stats = {
        "total_searches": 0,
        "total_papers_found": 0,
        "total_questions": 0,
        "allergens_searched": [],
        "last_search_time": None,
        "search_history": [],
    }

    return {"success": True, "message": "통계가 초기화되었습니다."}


# =====================
# 알러지 정보 API
# =====================

@app.get("/api/allergens")
async def get_allergens():
    """지원하는 알러지 항원 목록 (지식베이스 기반)"""
    allergen_list = get_allergen_list()

    food = [a for a in allergen_list if a["category"] == "food"]
    inhalant = [a for a in allergen_list if a["category"] == "inhalant"]

    return {
        "food": food,
        "inhalant": inhalant,
    }


# =====================
# SGTi 정보 API
# =====================

@app.get("/api/sgti/info")
async def get_sgti_info():
    """SGTi-Allergy Screen PLUS 제품 정보"""
    return {
        "product_name": "SGTi-Allergy Screen PLUS",
        "description": "다중 알러젠 체외진단 검사 키트",
        "manufacturer": "SGTi",
        "test_method": "면역크로마토그래피법 (IgE 기반)",
        "supported_allergens": {
            "food": 9,
            "inhalant": 7,
            "total": 16,
        },
        "grade_system": {
            "range": "0-6",
            "grades": GRADE_DESCRIPTIONS,
        },
        "usage_guide": [
            "1. 검체(혈액) 채취",
            "2. 검사 키트에 검체 적용",
            "3. 지정된 시간 대기",
            "4. 결과 판독 (등급 0-6)",
            "5. AllergyInsight에 결과 입력",
        ],
    }


@app.get("/api/sgti/grades")
async def get_grade_info():
    """등급별 설명 정보"""
    return {
        "grades": GRADE_DESCRIPTIONS,
        "restriction_levels": {
            0: {"level": "none", "description": "제한 없음"},
            1: {"level": "monitor", "description": "모니터링"},
            2: {"level": "caution", "description": "주의"},
            3: {"level": "limit", "description": "제한"},
            4: {"level": "avoid", "description": "회피"},
            5: {"level": "strict_avoid", "description": "완전 회피"},
            6: {"level": "strict_avoid", "description": "완전 회피 + 응급약 휴대"},
        },
    }


# =====================
# 진단 API
# =====================

@app.post("/api/diagnosis")
async def create_diagnosis(request: DiagnosisRequest):
    """
    진단 결과 저장

    SGTi-Allergy Screen PLUS 검사 결과를 저장합니다.
    """
    repo = get_diagnosis_repository()

    # 날짜 파싱
    diagnosis_date = None
    if request.diagnosis_date:
        try:
            diagnosis_date = datetime.fromisoformat(request.diagnosis_date)
        except ValueError:
            raise HTTPException(status_code=400, detail="잘못된 날짜 형식입니다. ISO 형식을 사용하세요.")

    # 진단 결과 저장
    diagnosis = repo.save_diagnosis(
        diagnosis_results=[r.model_dump() for r in request.diagnosis_results],
        diagnosis_date=diagnosis_date,
        patient_info=request.patient_info,
    )

    return {
        "success": True,
        "diagnosis_id": diagnosis.diagnosis_id,
        "created_at": diagnosis.created_at.isoformat(),
        "message": "진단 결과가 저장되었습니다.",
    }


@app.get("/api/diagnosis/{diagnosis_id}")
async def get_diagnosis(diagnosis_id: str):
    """진단 결과 조회"""
    repo = get_diagnosis_repository()
    diagnosis = repo.get_diagnosis(diagnosis_id)

    if not diagnosis:
        raise HTTPException(status_code=404, detail="진단 결과를 찾을 수 없습니다.")

    return {
        "success": True,
        **diagnosis.to_dict(),
    }


@app.get("/api/diagnosis")
async def list_diagnoses(limit: int = 50, offset: int = 0):
    """진단 결과 목록 조회"""
    repo = get_diagnosis_repository()
    diagnoses = repo.list_diagnoses(limit=limit, offset=offset)

    return {
        "success": True,
        "total": len(diagnoses),
        "diagnoses": [d.to_dict() for d in diagnoses],
    }


@app.delete("/api/diagnosis/{diagnosis_id}")
async def delete_diagnosis(diagnosis_id: str):
    """진단 결과 삭제"""
    repo = get_diagnosis_repository()
    deleted = repo.delete_diagnosis(diagnosis_id)

    if not deleted:
        raise HTTPException(status_code=404, detail="진단 결과를 찾을 수 없습니다.")

    return {
        "success": True,
        "message": "진단 결과가 삭제되었습니다.",
    }


# =====================
# 처방 API
# =====================

@app.post("/api/prescription/generate")
async def generate_prescription(request: PrescriptionRequest):
    """
    처방 권고 생성

    진단 결과를 기반으로 음식 섭취 제한 및 처방 권고를 생성합니다.
    """
    repo = get_diagnosis_repository()
    engine = get_prescription_engine()

    # 진단 결과 확인
    diagnosis_results = None
    diagnosis_date = None
    diagnosis_id = None

    if request.diagnosis_id:
        # 저장된 진단 사용
        diagnosis = repo.get_diagnosis(request.diagnosis_id)
        if not diagnosis:
            raise HTTPException(status_code=404, detail="진단 결과를 찾을 수 없습니다.")
        diagnosis_results = diagnosis.diagnosis_results
        diagnosis_date = diagnosis.diagnosis_date
        diagnosis_id = diagnosis.diagnosis_id
    elif request.diagnosis_results:
        # 직접 입력된 진단 사용
        diagnosis_results = [r.model_dump() for r in request.diagnosis_results]
        if request.diagnosis_date:
            try:
                diagnosis_date = datetime.fromisoformat(request.diagnosis_date)
            except ValueError:
                pass
    else:
        raise HTTPException(status_code=400, detail="diagnosis_id 또는 diagnosis_results가 필요합니다.")

    # 처방 권고 생성
    prescription = engine.generate_prescription(
        diagnosis_results=diagnosis_results,
        diagnosis_date=diagnosis_date,
    )

    # 저장된 진단이 있으면 처방도 저장
    if diagnosis_id:
        repo.save_prescription(
            diagnosis_id=diagnosis_id,
            prescription_data=prescription.to_dict(),
        )

    return {
        "success": True,
        **prescription.to_dict(),
    }


@app.get("/api/prescription/{prescription_id}")
async def get_prescription(prescription_id: str):
    """처방 권고 조회"""
    repo = get_diagnosis_repository()
    prescription = repo.get_prescription(prescription_id)

    if not prescription:
        raise HTTPException(status_code=404, detail="처방 권고를 찾을 수 없습니다.")

    return {
        "success": True,
        **prescription.to_dict(),
    }


@app.get("/api/prescription/by-diagnosis/{diagnosis_id}")
async def get_prescription_by_diagnosis(diagnosis_id: str):
    """진단 ID로 처방 권고 조회"""
    repo = get_diagnosis_repository()
    prescription = repo.get_prescription_by_diagnosis(diagnosis_id)

    if not prescription:
        raise HTTPException(status_code=404, detail="해당 진단에 대한 처방 권고가 없습니다.")

    return {
        "success": True,
        **prescription.to_dict(),
    }


@app.get("/api/prescription")
async def list_prescriptions(limit: int = 50, offset: int = 0):
    """처방 권고 목록 조회"""
    repo = get_diagnosis_repository()
    prescriptions = repo.list_prescriptions(limit=limit, offset=offset)

    return {
        "success": True,
        "total": len(prescriptions),
        "prescriptions": [p.to_dict() for p in prescriptions],
    }


# =====================
# 앱 이벤트
# =====================

@app.on_event("startup")
async def startup_event():
    """앱 시작 시 데이터베이스 초기화 및 시드 데이터 생성"""
    init_db()
    seed_users()  # 테스트 사용자 시딩


@app.on_event("shutdown")
async def shutdown_event():
    """앱 종료 시 리소스 정리"""
    global _search_service, _qa_engine, _batch_processor

    if _search_service:
        _search_service.close()
    if _qa_engine:
        _qa_engine.close()
    if _batch_processor:
        _batch_processor.close()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9040)
