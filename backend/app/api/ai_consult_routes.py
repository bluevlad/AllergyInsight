"""알러지 AI 상담 공개 API (인증 불필요)

일반 사용자가 알러지 관련 질문을 하면
수집된 논문 기반으로 AI 답변을 제공합니다.
"""
from fastapi import APIRouter, Request
from pydantic import BaseModel, Field
from typing import Optional

from slowapi import Limiter
from slowapi.util import get_remote_address

from ..data.allergen_prescription_db import get_allergen_list

limiter = Limiter(key_func=get_remote_address)

router = APIRouter(prefix="/ai/consult", tags=["AI Consult"])


class ConsultRequest(BaseModel):
    """AI 상담 질문 요청"""
    question: str = Field(..., min_length=2, max_length=500, description="질문 내용")
    allergen: str = Field("peanut", description="알러젠 코드")
    max_citations: int = Field(5, ge=1, le=10, description="최대 인용 수")


class ConsultQuickQuestion(BaseModel):
    """빠른 질문 항목"""
    category: str
    category_kr: str
    questions: list[str]


CATEGORY_LABELS = {
    "symptoms": "증상",
    "severity": "위험도",
    "cross_reactivity": "교차반응",
    "onset": "발현시간",
    "treatment": "치료/대처",
}


@router.post("/ask")
@limiter.limit("10/minute")
async def ask_question(request: ConsultRequest, http_request: Request):
    """알러지 AI 상담 질문

    논문 기반으로 알러지 관련 질문에 답변합니다.
    일반 사용자도 이용 가능합니다 (인증 불필요).
    """
    from .main import get_qa_engine

    engine = get_qa_engine()
    response = engine.ask(
        question=request.question,
        allergen=request.allergen,
        max_citations=request.max_citations,
    )

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


@router.get("/questions/{allergen}")
async def get_quick_questions(allergen: str = "peanut"):
    """알러젠별 빠른 질문 목록

    사전 정의된 질문 템플릿을 카테고리별로 반환합니다.
    """
    from .main import get_qa_engine

    engine = get_qa_engine()
    questions = engine.get_predefined_questions(allergen)

    result = []
    for category, q_list in questions.items():
        result.append({
            "category": category,
            "category_kr": CATEGORY_LABELS.get(category, category),
            "questions": q_list,
        })

    return {
        "success": True,
        "allergen": allergen,
        "categories": result,
    }


@router.post("/ask/rag")
@limiter.limit("10/minute")
async def ask_question_rag(request: ConsultRequest, http_request: Request):
    """RAG 기반 알러지 AI 상담 질문

    ChromaDB 벡터 검색 + LLM으로 논문 기반 답변을 생성합니다.
    기존 /ask 대비 시맨틱 검색으로 더 정확한 논문 매칭을 제공합니다.
    """
    from ..services.rag_service import get_rag_service

    rag = get_rag_service()
    if not rag.is_available:
        # RAG 미가용 시 기존 Q&A 엔진으로 fallback
        return await ask_question(request, http_request)

    result = rag.ask(
        question=request.question,
        allergen=request.allergen,
        n_context=request.max_citations,
    )

    return {
        "success": True,
        "question": request.question,
        "answer": result["answer"],
        "confidence": result["confidence"],
        "sources": result["sources"],
        "source_count": len(result["sources"]),
        "engine": "rag",
    }


@router.get("/rag/stats")
async def get_rag_stats():
    """RAG 인덱스 통계"""
    from ..services.rag_service import get_rag_service

    rag = get_rag_service()
    stats = rag.get_stats()

    return {
        "success": True,
        **stats,
    }


@router.post("/rag/index")
@limiter.limit("2/minute")
async def trigger_rag_indexing(request: Request, batch_size: int = 100):
    """RAG 인덱싱 트리거 (미인덱싱 논문을 벡터 DB에 추가)"""
    from ..services.rag_service import get_rag_service
    from ..database.connection import SessionLocal

    rag = get_rag_service()
    if not rag.is_available:
        return {"success": False, "error": "ChromaDB 초기화 실패"}

    db = SessionLocal()
    try:
        result = rag.index_papers_from_db(db, batch_size=batch_size)
        return {"success": True, **result}
    finally:
        db.close()


@router.get("/allergens")
async def get_allergen_options():
    """상담 가능한 알러젠 목록"""
    allergen_list = get_allergen_list()

    food = [a for a in allergen_list if a["category"] == "food"]
    inhalant = [a for a in allergen_list if a["category"] == "inhalant"]

    return {
        "success": True,
        "food": food,
        "inhalant": inhalant,
        "total": len(allergen_list),
    }
