"""RAG (Retrieval-Augmented Generation) 서비스

ChromaDB 벡터 DB + 로컬 LLM을 사용한 논문 기반 시맨틱 검색 및 답변 생성.

아키텍처:
    논문 DB (PostgreSQL) → 텍스트 청킹 → ChromaDB 임베딩 저장
    사용자 질문 → ChromaDB 유사 검색 → 관련 논문 컨텍스트 → LLM 답변 생성
"""
import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)

# ChromaDB 데이터 저장 경로
_CHROMA_PERSIST_DIR = os.getenv(
    "CHROMA_PERSIST_DIR",
    os.path.join(os.path.dirname(__file__), "..", "..", "data", "chromadb"),
)
_COLLECTION_NAME = "allergy_papers"
_CHUNK_SIZE = 800
_CHUNK_OVERLAP = 100


def _chunk_text(text: str, chunk_size: int = _CHUNK_SIZE, overlap: int = _CHUNK_OVERLAP) -> list[str]:
    """텍스트를 오버랩 청킹

    Args:
        text: 원본 텍스트
        chunk_size: 청크 크기 (문자 수)
        overlap: 오버랩 크기

    Returns:
        청크 리스트
    """
    if not text or len(text) <= chunk_size:
        return [text] if text else []

    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        if chunk.strip():
            chunks.append(chunk.strip())
        start += chunk_size - overlap

    return chunks


class RAGService:
    """논문 기반 RAG 서비스"""

    def __init__(self):
        self._client = None
        self._collection = None
        self._available: Optional[bool] = None

    def _get_collection(self):
        """ChromaDB 컬렉션 (lazy 초기화)"""
        if self._collection is not None:
            return self._collection

        try:
            import chromadb

            persist_dir = os.path.abspath(_CHROMA_PERSIST_DIR)
            os.makedirs(persist_dir, exist_ok=True)

            self._client = chromadb.PersistentClient(path=persist_dir)
            self._collection = self._client.get_or_create_collection(
                name=_COLLECTION_NAME,
                metadata={"hnsw:space": "cosine"},
            )
            self._available = True
            logger.info(
                f"ChromaDB 초기화 완료: {persist_dir} "
                f"(문서 수: {self._collection.count()})"
            )
        except Exception as e:
            logger.warning(f"ChromaDB 초기화 실패: {e}")
            self._available = False

        return self._collection

    @property
    def is_available(self) -> bool:
        if self._available is None or self._available is False:
            # 실패 시에도 재시도 허용 (디렉토리 권한 등 런타임 해결 가능)
            self._available = None
            self._collection = None
            self._get_collection()
        return self._available

    @property
    def document_count(self) -> int:
        """저장된 문서(청크) 수"""
        col = self._get_collection()
        return col.count() if col else 0

    def index_paper(
        self,
        paper_id: int,
        title: str,
        abstract: str,
        allergen_codes: Optional[list[str]] = None,
        year: Optional[int] = None,
        doi: Optional[str] = None,
    ) -> int:
        """논문을 벡터 DB에 인덱싱

        Args:
            paper_id: papers 테이블 PK
            title: 논문 제목
            abstract: 논문 초록
            allergen_codes: 관련 알러젠 코드 리스트
            year: 발행 연도
            doi: DOI

        Returns:
            인덱싱된 청크 수
        """
        col = self._get_collection()
        if not col:
            return 0

        # 기존 인덱스 삭제 (재인덱싱 방지)
        try:
            existing = col.get(where={"paper_id": paper_id})
            if existing and existing["ids"]:
                col.delete(ids=existing["ids"])
        except Exception:
            pass

        # 텍스트 구성: 제목 + 초록
        full_text = f"{title}\n\n{abstract}" if abstract else title
        chunks = _chunk_text(full_text)

        if not chunks:
            return 0

        # 메타데이터 구성
        base_meta = {
            "paper_id": paper_id,
            "title": title[:200],
            "year": year or 0,
            "doi": doi or "",
            "allergens": ",".join(allergen_codes) if allergen_codes else "",
        }

        ids = []
        documents = []
        metadatas = []

        for i, chunk in enumerate(chunks):
            chunk_id = f"paper_{paper_id}_chunk_{i}"
            ids.append(chunk_id)
            documents.append(chunk)
            metadatas.append({**base_meta, "chunk_index": i})

        col.add(ids=ids, documents=documents, metadatas=metadatas)
        return len(chunks)

    def index_papers_from_db(self, db, batch_size: int = 100) -> dict:
        """PostgreSQL papers 테이블에서 미인덱싱 논문을 벡터 DB에 배치 인덱싱

        Args:
            db: SQLAlchemy 세션
            batch_size: 한 번에 처리할 논문 수

        Returns:
            {"indexed": int, "skipped": int, "total_chunks": int}
        """
        col = self._get_collection()
        if not col:
            return {"indexed": 0, "skipped": 0, "total_chunks": 0}

        from ..database.models import Paper as PaperORM
        from ..database.models import PaperAllergenLink

        # 이미 인덱싱된 paper_id 조회
        indexed_ids = set()
        try:
            all_meta = col.get(include=["metadatas"])
            for meta in (all_meta.get("metadatas") or []):
                if meta and "paper_id" in meta:
                    indexed_ids.add(meta["paper_id"])
        except Exception:
            pass

        # 미인덱싱 논문 조회
        query = (
            db.query(PaperORM)
            .filter(PaperORM.abstract.isnot(None))
            .filter(PaperORM.abstract != "")
        )

        if indexed_ids:
            query = query.filter(~PaperORM.id.in_(indexed_ids))

        papers = query.order_by(PaperORM.created_at.desc()).limit(batch_size).all()

        indexed = 0
        total_chunks = 0

        for paper in papers:
            # 알러젠 코드 조회
            links = (
                db.query(PaperAllergenLink.allergen_code)
                .filter(PaperAllergenLink.paper_id == paper.id)
                .all()
            )
            allergen_codes = [link.allergen_code for link in links]

            chunks = self.index_paper(
                paper_id=paper.id,
                title=paper.title,
                abstract=paper.abstract,
                allergen_codes=allergen_codes,
                year=paper.year,
                doi=paper.doi,
            )
            if chunks > 0:
                indexed += 1
                total_chunks += chunks

        skipped = len(indexed_ids)
        logger.info(
            f"RAG 인덱싱 완료: {indexed}건 신규, {skipped}건 기존, "
            f"총 {total_chunks}개 청크"
        )

        return {"indexed": indexed, "skipped": skipped, "total_chunks": total_chunks}

    def search(
        self,
        query: str,
        n_results: int = 5,
        allergen_filter: Optional[str] = None,
    ) -> list[dict]:
        """시맨틱 검색

        Args:
            query: 검색 쿼리
            n_results: 반환할 결과 수
            allergen_filter: 특정 알러젠으로 필터링

        Returns:
            [{"paper_id", "title", "text", "score", "year", "allergens"}]
        """
        col = self._get_collection()
        if not col or col.count() == 0:
            return []

        where_filter = None
        if allergen_filter:
            where_filter = {"allergens": {"$contains": allergen_filter}}

        try:
            results = col.query(
                query_texts=[query],
                n_results=n_results,
                where=where_filter,
            )
        except Exception as e:
            logger.warning(f"ChromaDB 검색 실패: {e}")
            return []

        items = []
        if results and results["ids"] and results["ids"][0]:
            for i, doc_id in enumerate(results["ids"][0]):
                meta = results["metadatas"][0][i] if results["metadatas"] else {}
                distance = results["distances"][0][i] if results["distances"] else 1.0
                score = max(0.0, 1.0 - distance)  # cosine distance → similarity

                items.append({
                    "paper_id": meta.get("paper_id"),
                    "title": meta.get("title", ""),
                    "text": results["documents"][0][i] if results["documents"] else "",
                    "score": round(score, 4),
                    "year": meta.get("year", 0),
                    "doi": meta.get("doi", ""),
                    "allergens": meta.get("allergens", ""),
                })

        return items

    def ask(
        self,
        question: str,
        allergen: Optional[str] = None,
        n_context: int = 5,
    ) -> dict:
        """RAG 기반 질의응답

        Args:
            question: 사용자 질문
            allergen: 알러젠 필터 (선택)
            n_context: 컨텍스트로 사용할 논문 청크 수

        Returns:
            {"answer": str, "sources": list, "confidence": float}
        """
        from .ollama_service import get_ollama_service

        # 1) 관련 논문 검색
        search_results = self.search(
            query=question,
            n_results=n_context,
            allergen_filter=allergen,
        )

        if not search_results:
            return {
                "answer": "관련 논문을 찾을 수 없습니다. 다른 질문을 시도해 주세요.",
                "sources": [],
                "confidence": 0.0,
            }

        # 2) 컨텍스트 구성
        context_parts = []
        for i, result in enumerate(search_results, 1):
            year_str = f" ({result['year']})" if result.get("year") else ""
            context_parts.append(
                f"[{i}] {result['title']}{year_str}\n{result['text']}"
            )
        context = "\n\n".join(context_parts)

        # 3) LLM 답변 생성
        llm = get_ollama_service()
        if not llm.is_available:
            # LLM 미가용 시 검색 결과만 반환
            return {
                "answer": "LLM 서버에 연결할 수 없어 검색 결과만 표시합니다.",
                "sources": search_results,
                "confidence": 0.3,
            }

        prompt = (
            "당신은 알러지/면역학 전문 의학 AI 어시스턴트입니다.\n"
            "아래 학술 논문 자료를 참고하여 질문에 정확하고 근거 있게 답변하세요.\n"
            "반드시 출처 번호 [1], [2] 등을 인용하세요.\n"
            "논문에 없는 내용은 추측하지 마세요.\n\n"
            f"=== 참고 논문 ===\n{context}\n\n"
            f"=== 질문 ===\n{question}\n\n"
            "=== 답변 (한국어) ==="
        )

        answer = llm._chat(prompt, max_tokens=1000)
        if not answer:
            answer = "답변을 생성할 수 없습니다."

        # 4) 신뢰도 계산
        avg_score = sum(r["score"] for r in search_results) / len(search_results)
        confidence = min(1.0, avg_score * 1.2)

        # 5) 소스 정보
        sources = [
            {
                "paper_id": r["paper_id"],
                "title": r["title"],
                "year": r["year"],
                "doi": r["doi"],
                "relevance": r["score"],
            }
            for r in search_results
        ]

        return {
            "answer": answer,
            "sources": sources,
            "confidence": round(confidence, 3),
        }

    def get_stats(self) -> dict:
        """RAG 인덱스 통계"""
        col = self._get_collection()
        if not col:
            return {"available": False, "total_chunks": 0, "total_papers": 0}

        total_chunks = col.count()

        # 고유 paper_id 수 계산
        paper_ids = set()
        try:
            all_meta = col.get(include=["metadatas"])
            for meta in (all_meta.get("metadatas") or []):
                if meta and "paper_id" in meta:
                    paper_ids.add(meta["paper_id"])
        except Exception:
            pass

        return {
            "available": True,
            "total_chunks": total_chunks,
            "total_papers": len(paper_ids),
        }


# 싱글톤
_rag_service: Optional[RAGService] = None


def get_rag_service() -> RAGService:
    """RAGService 싱글톤"""
    global _rag_service
    if _rag_service is None:
        _rag_service = RAGService()
    return _rag_service
