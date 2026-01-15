"""PDF 다운로드, 텍스트 추출 및 요약 서비스

PDF 논문을 다운로드하고, 텍스트를 추출하며,
원하는 섹션을 찾아 요약본을 생성합니다.
"""
import os
import re
import hashlib
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, field
from datetime import datetime

import requests

# PDF 파싱 라이브러리
try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False

try:
    import pdfplumber
    PDFPLUMBER_AVAILABLE = True
except ImportError:
    PDFPLUMBER_AVAILABLE = False


@dataclass
class PDFSection:
    """PDF 섹션 (챕터/섹션 단위)"""
    title: str
    content: str
    page_start: int
    page_end: int


@dataclass
class PDFDocument:
    """추출된 PDF 문서"""
    file_path: str
    title: str
    full_text: str
    pages: list[str]  # 페이지별 텍스트
    sections: list[PDFSection]  # 섹션별 분리
    metadata: dict = field(default_factory=dict)

    # 통계
    total_pages: int = 0
    total_chars: int = 0
    total_words: int = 0

    def get_section_by_keyword(self, keyword: str) -> list[PDFSection]:
        """키워드가 포함된 섹션 찾기"""
        keyword_lower = keyword.lower()
        return [s for s in self.sections if keyword_lower in s.content.lower()]

    def search_text(self, keyword: str, context_chars: int = 200) -> list[dict]:
        """
        키워드 검색 및 주변 컨텍스트 반환

        Args:
            keyword: 검색할 키워드
            context_chars: 앞뒤로 포함할 문자 수

        Returns:
            list[dict]: 검색 결과 목록
        """
        results = []
        keyword_lower = keyword.lower()
        text_lower = self.full_text.lower()

        start = 0
        while True:
            pos = text_lower.find(keyword_lower, start)
            if pos == -1:
                break

            # 컨텍스트 추출
            ctx_start = max(0, pos - context_chars)
            ctx_end = min(len(self.full_text), pos + len(keyword) + context_chars)

            results.append({
                "position": pos,
                "context": self.full_text[ctx_start:ctx_end],
                "keyword": self.full_text[pos:pos + len(keyword)],
            })

            start = pos + 1

        return results


@dataclass
class PDFSummary:
    """PDF 요약본"""
    source_file: str
    title: str
    abstract: str
    key_sections: list[PDFSection]
    keywords_found: dict[str, list[str]]  # 키워드 -> 관련 문장들
    created_at: datetime = field(default_factory=datetime.now)


class PDFService:
    """PDF 다운로드 및 처리 서비스"""

    # 논문 섹션 패턴 (영문)
    SECTION_PATTERNS = [
        r"^(?:Abstract|ABSTRACT)\s*$",
        r"^(?:\d+\.?\s*)?(?:Introduction|INTRODUCTION)\s*$",
        r"^(?:\d+\.?\s*)?(?:Background|BACKGROUND)\s*$",
        r"^(?:\d+\.?\s*)?(?:Methods?|METHODS?|Materials?\s+and\s+Methods?)\s*$",
        r"^(?:\d+\.?\s*)?(?:Results?|RESULTS?)\s*$",
        r"^(?:\d+\.?\s*)?(?:Discussion|DISCUSSION)\s*$",
        r"^(?:\d+\.?\s*)?(?:Conclusions?|CONCLUSIONS?)\s*$",
        r"^(?:\d+\.?\s*)?(?:References?|REFERENCES?)\s*$",
        r"^(?:\d+\.?\s*)?(?:Acknowledgements?|ACKNOWLEDGEMENTS?)\s*$",
    ]

    def __init__(self, download_dir: str = "./downloads/papers"):
        """
        Args:
            download_dir: PDF 다운로드 디렉토리
        """
        self.download_dir = Path(download_dir)
        self.download_dir.mkdir(parents=True, exist_ok=True)

        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AllergyInsight/1.0"
        })

    def download_pdf(
        self,
        url: str,
        filename: Optional[str] = None,
        overwrite: bool = False,
    ) -> Optional[str]:
        """
        PDF 다운로드

        Args:
            url: PDF URL
            filename: 저장할 파일명 (없으면 URL에서 추출 또는 해시)
            overwrite: 기존 파일 덮어쓰기

        Returns:
            저장된 파일 경로 또는 None
        """
        try:
            # 파일명 결정
            if not filename:
                # URL에서 파일명 추출 시도
                url_path = url.split("?")[0]
                if url_path.endswith(".pdf"):
                    filename = url_path.split("/")[-1]
                else:
                    # URL 해시로 파일명 생성
                    url_hash = hashlib.md5(url.encode()).hexdigest()[:12]
                    filename = f"paper_{url_hash}.pdf"

            file_path = self.download_dir / filename

            # 이미 존재하고 덮어쓰기 안 할 경우
            if file_path.exists() and not overwrite:
                return str(file_path)

            # 다운로드
            response = self.session.get(url, timeout=60, stream=True)
            response.raise_for_status()

            # Content-Type 확인
            content_type = response.headers.get("Content-Type", "")
            if "pdf" not in content_type.lower() and not url.endswith(".pdf"):
                # PDF가 아닐 수 있음
                pass

            # 파일 저장
            with open(file_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            return str(file_path)

        except Exception as e:
            print(f"PDF 다운로드 실패: {url} - {e}")
            return None

    def extract_text(self, pdf_path: str) -> Optional[PDFDocument]:
        """
        PDF에서 텍스트 추출

        Args:
            pdf_path: PDF 파일 경로

        Returns:
            PDFDocument 또는 None
        """
        if PYMUPDF_AVAILABLE:
            return self._extract_with_pymupdf(pdf_path)
        elif PDFPLUMBER_AVAILABLE:
            return self._extract_with_pdfplumber(pdf_path)
        else:
            raise RuntimeError("PDF 파싱 라이브러리가 설치되지 않았습니다. "
                             "pip install PyMuPDF 또는 pip install pdfplumber")

    def _extract_with_pymupdf(self, pdf_path: str) -> Optional[PDFDocument]:
        """PyMuPDF로 텍스트 추출"""
        try:
            doc = fitz.open(pdf_path)

            pages = []
            full_text_parts = []

            for page_num, page in enumerate(doc):
                text = page.get_text()
                pages.append(text)
                full_text_parts.append(text)

            full_text = "\n\n".join(full_text_parts)

            # 메타데이터
            metadata = doc.metadata or {}
            title = metadata.get("title", "") or Path(pdf_path).stem

            # 섹션 분리
            sections = self._extract_sections(full_text, len(pages))

            doc.close()

            return PDFDocument(
                file_path=pdf_path,
                title=title,
                full_text=full_text,
                pages=pages,
                sections=sections,
                metadata=metadata,
                total_pages=len(pages),
                total_chars=len(full_text),
                total_words=len(full_text.split()),
            )

        except Exception as e:
            print(f"PyMuPDF 추출 실패: {pdf_path} - {e}")
            return None

    def _extract_with_pdfplumber(self, pdf_path: str) -> Optional[PDFDocument]:
        """pdfplumber로 텍스트 추출"""
        try:
            with pdfplumber.open(pdf_path) as pdf:
                pages = []
                full_text_parts = []

                for page in pdf.pages:
                    text = page.extract_text() or ""
                    pages.append(text)
                    full_text_parts.append(text)

                full_text = "\n\n".join(full_text_parts)

                # 메타데이터
                metadata = pdf.metadata or {}
                title = metadata.get("Title", "") or Path(pdf_path).stem

                # 섹션 분리
                sections = self._extract_sections(full_text, len(pages))

                return PDFDocument(
                    file_path=pdf_path,
                    title=title,
                    full_text=full_text,
                    pages=pages,
                    sections=sections,
                    metadata=metadata,
                    total_pages=len(pages),
                    total_chars=len(full_text),
                    total_words=len(full_text.split()),
                )

        except Exception as e:
            print(f"pdfplumber 추출 실패: {pdf_path} - {e}")
            return None

    def _extract_sections(self, text: str, total_pages: int) -> list[PDFSection]:
        """
        텍스트에서 섹션 분리

        Args:
            text: 전체 텍스트
            total_pages: 총 페이지 수

        Returns:
            list[PDFSection]: 섹션 목록
        """
        sections = []
        lines = text.split("\n")

        current_section = None
        current_content = []
        section_regex = re.compile("|".join(self.SECTION_PATTERNS), re.IGNORECASE)

        for i, line in enumerate(lines):
            stripped = line.strip()

            # 섹션 헤더 체크
            if stripped and len(stripped) < 100 and section_regex.match(stripped):
                # 이전 섹션 저장
                if current_section:
                    sections.append(PDFSection(
                        title=current_section,
                        content="\n".join(current_content).strip(),
                        page_start=0,  # 정확한 페이지는 추후 계산
                        page_end=0,
                    ))

                current_section = stripped
                current_content = []
            else:
                current_content.append(line)

        # 마지막 섹션 저장
        if current_section:
            sections.append(PDFSection(
                title=current_section,
                content="\n".join(current_content).strip(),
                page_start=0,
                page_end=0,
            ))

        # 섹션이 없으면 전체를 하나의 섹션으로
        if not sections:
            sections.append(PDFSection(
                title="Full Text",
                content=text,
                page_start=1,
                page_end=total_pages,
            ))

        return sections

    def create_summary(
        self,
        pdf_doc: PDFDocument,
        keywords: list[str],
        max_sentences_per_keyword: int = 5,
    ) -> PDFSummary:
        """
        PDF 요약본 생성

        Args:
            pdf_doc: 추출된 PDF 문서
            keywords: 관심 키워드 목록
            max_sentences_per_keyword: 키워드당 최대 문장 수

        Returns:
            PDFSummary: 요약본
        """
        # Abstract 추출
        abstract = ""
        for section in pdf_doc.sections:
            if "abstract" in section.title.lower():
                abstract = section.content[:2000]  # 최대 2000자
                break

        # 주요 섹션 (Introduction, Methods, Results, Discussion, Conclusion)
        key_section_names = ["introduction", "methods", "results", "discussion", "conclusion"]
        key_sections = []
        for section in pdf_doc.sections:
            section_lower = section.title.lower()
            for name in key_section_names:
                if name in section_lower:
                    key_sections.append(section)
                    break

        # 키워드별 관련 문장 추출
        keywords_found = {}
        for keyword in keywords:
            sentences = self._find_sentences_with_keyword(
                pdf_doc.full_text,
                keyword,
                max_sentences_per_keyword,
            )
            if sentences:
                keywords_found[keyword] = sentences

        return PDFSummary(
            source_file=pdf_doc.file_path,
            title=pdf_doc.title,
            abstract=abstract,
            key_sections=key_sections,
            keywords_found=keywords_found,
        )

    def _find_sentences_with_keyword(
        self,
        text: str,
        keyword: str,
        max_sentences: int = 5,
    ) -> list[str]:
        """
        키워드가 포함된 문장 추출

        Args:
            text: 전체 텍스트
            keyword: 검색 키워드
            max_sentences: 최대 문장 수

        Returns:
            list[str]: 관련 문장 목록
        """
        # 문장 분리 (간단한 방식)
        sentences = re.split(r'(?<=[.!?])\s+', text)

        keyword_lower = keyword.lower()
        found = []

        for sentence in sentences:
            if keyword_lower in sentence.lower():
                # 문장 정리
                cleaned = " ".join(sentence.split())
                if 20 < len(cleaned) < 1000:  # 너무 짧거나 긴 문장 제외
                    found.append(cleaned)
                    if len(found) >= max_sentences:
                        break

        return found

    def extract_tables(self, pdf_path: str) -> list[dict]:
        """
        PDF에서 테이블 추출 (pdfplumber 필요)

        Args:
            pdf_path: PDF 파일 경로

        Returns:
            list[dict]: 테이블 목록
        """
        if not PDFPLUMBER_AVAILABLE:
            raise RuntimeError("테이블 추출에는 pdfplumber가 필요합니다. "
                             "pip install pdfplumber")

        tables = []

        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page_num, page in enumerate(pdf.pages, 1):
                    page_tables = page.extract_tables()
                    for table_idx, table in enumerate(page_tables):
                        if table:
                            tables.append({
                                "page": page_num,
                                "table_index": table_idx,
                                "data": table,
                            })
        except Exception as e:
            print(f"테이블 추출 실패: {e}")

        return tables

    def process_paper(
        self,
        pdf_url: str,
        keywords: list[str],
        filename: Optional[str] = None,
    ) -> Optional[PDFSummary]:
        """
        논문 전체 처리 파이프라인

        1. PDF 다운로드
        2. 텍스트 추출
        3. 요약본 생성

        Args:
            pdf_url: PDF URL
            keywords: 관심 키워드
            filename: 저장할 파일명

        Returns:
            PDFSummary 또는 None
        """
        # 1. 다운로드
        pdf_path = self.download_pdf(pdf_url, filename)
        if not pdf_path:
            return None

        # 2. 텍스트 추출
        pdf_doc = self.extract_text(pdf_path)
        if not pdf_doc:
            return None

        # 3. 요약본 생성
        summary = self.create_summary(pdf_doc, keywords)

        return summary


# 편의 함수
def format_summary_as_text(summary: PDFSummary) -> str:
    """요약본을 텍스트로 포맷팅"""
    lines = []
    lines.append(f"# {summary.title}")
    lines.append("")

    if summary.abstract:
        lines.append("## Abstract")
        lines.append(summary.abstract)
        lines.append("")

    if summary.keywords_found:
        lines.append("## 키워드별 관련 내용")
        for keyword, sentences in summary.keywords_found.items():
            lines.append(f"\n### {keyword}")
            for i, sentence in enumerate(sentences, 1):
                lines.append(f"{i}. {sentence}")
        lines.append("")

    if summary.key_sections:
        lines.append("## 주요 섹션")
        for section in summary.key_sections:
            lines.append(f"\n### {section.title}")
            # 섹션 내용 요약 (첫 500자)
            content_preview = section.content[:500]
            if len(section.content) > 500:
                content_preview += "..."
            lines.append(content_preview)

    return "\n".join(lines)


def format_summary_as_markdown(summary: PDFSummary) -> str:
    """요약본을 마크다운으로 포맷팅"""
    return format_summary_as_text(summary)  # 동일한 포맷 사용
