"""AllergyInsight API 서버

FastAPI 기반 REST API 서버입니다.
논문 검색, Q&A, 수집 현황 조회 기능을 제공합니다.

실행 방법:
    cd C:\GIT\AllergyInsight\backend
    uvicorn app.api.main:app --reload --port 9040
"""
from fastapi import FastAPI, HTTPException, Query, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
import asyncio

from ..services import (
    PaperSearchService,
    QAEngine,
    SymptomQAInterface,
    BatchProcessor,
    AllergenItem,
    create_allergen_items,
    SmartLoader,
)
from ..services.batch_processor import ProcessingStatus

# FastAPI 앱 생성
app = FastAPI(
    title="AllergyInsight API",
    description="알러지 논문 검색 및 Q&A 시스템 API",
    version="1.0.0",
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 개발용, 프로덕션에서는 특정 도메인 지정
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 전역 서비스 인스턴스
_search_service: Optional[PaperSearchService] = None
_qa_engine: Optional[QAEngine] = None
_batch_processor: Optional[BatchProcessor] = None
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


# =====================
# API 엔드포인트
# =====================

@app.get("/")
async def root():
    """API 루트"""
    return {
        "name": "AllergyInsight API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "search": "/api/search",
            "qa": "/api/qa",
            "stats": "/api/stats",
            "batch": "/api/batch",
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
    """지원하는 알러지 항원 목록"""
    return {
        "food": [
            {"name": "peanut", "name_kr": "땅콩", "category": "견과류"},
            {"name": "milk", "name_kr": "우유", "category": "유제품"},
            {"name": "egg", "name_kr": "계란", "category": "동물성"},
            {"name": "wheat", "name_kr": "밀", "category": "곡류"},
            {"name": "soy", "name_kr": "대두", "category": "콩류"},
            {"name": "fish", "name_kr": "생선", "category": "해산물"},
            {"name": "shellfish", "name_kr": "갑각류", "category": "해산물"},
            {"name": "tree nut", "name_kr": "견과류", "category": "견과류"},
            {"name": "sesame", "name_kr": "참깨", "category": "씨앗"},
        ],
        "inhalant": [
            {"name": "dust mite", "name_kr": "집먼지진드기", "category": "흡입성"},
            {"name": "cat", "name_kr": "고양이", "category": "동물"},
            {"name": "dog", "name_kr": "개", "category": "동물"},
            {"name": "pollen", "name_kr": "꽃가루", "category": "식물"},
            {"name": "mold", "name_kr": "곰팡이", "category": "진균"},
        ],
    }


# =====================
# 앱 이벤트
# =====================

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
