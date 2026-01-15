"""지식 베이스 모델

논문에서 추출한 정보를 구조화하여 저장하고,
증상 질문에 대한 답변을 생성할 때 사용합니다.
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from enum import Enum


class SymptomSeverity(str, Enum):
    """증상 심각도"""
    MILD = "mild"           # 경미 (피부 발진, 가려움)
    MODERATE = "moderate"   # 중등도 (두드러기, 부종)
    SEVERE = "severe"       # 심각 (호흡곤란, 혈압저하)
    ANAPHYLAXIS = "anaphylaxis"  # 아나필락시스 (생명 위협)


class SymptomCategory(str, Enum):
    """증상 카테고리"""
    SKIN = "skin"               # 피부 증상
    RESPIRATORY = "respiratory"  # 호흡기 증상
    GASTROINTESTINAL = "gastrointestinal"  # 위장관 증상
    CARDIOVASCULAR = "cardiovascular"  # 심혈관 증상
    NEUROLOGICAL = "neurological"  # 신경계 증상
    SYSTEMIC = "systemic"       # 전신 증상


@dataclass
class Citation:
    """논문 인용 정보"""
    paper_title: str
    authors: list[str]
    year: Optional[int]
    journal: Optional[str]
    doi: Optional[str]
    pmid: Optional[str]
    source_url: Optional[str] = None

    # 인용 위치 정보
    relevant_text: str = ""      # 관련 원문 텍스트
    page_or_section: str = ""    # 페이지 또는 섹션

    def format_apa(self) -> str:
        """APA 스타일 인용"""
        author_str = ", ".join(self.authors[:3])
        if len(self.authors) > 3:
            author_str += " et al."

        year_str = f"({self.year})" if self.year else "(n.d.)"
        journal_str = f" {self.journal}." if self.journal else ""
        doi_str = f" https://doi.org/{self.doi}" if self.doi else ""

        return f"{author_str} {year_str}. {self.paper_title}.{journal_str}{doi_str}"

    def format_short(self) -> str:
        """짧은 인용 형식"""
        first_author = self.authors[0].split()[-1] if self.authors else "Unknown"
        year = self.year or "n.d."
        return f"{first_author} et al., {year}"

    def to_dict(self) -> dict:
        return {
            "paper_title": self.paper_title,
            "authors": self.authors,
            "year": self.year,
            "journal": self.journal,
            "doi": self.doi,
            "pmid": self.pmid,
            "source_url": self.source_url,
            "relevant_text": self.relevant_text,
            "format_apa": self.format_apa(),
            "format_short": self.format_short(),
        }


@dataclass
class SymptomInfo:
    """증상 정보"""
    name: str                    # 증상명
    name_kr: str                 # 한글명
    description: str             # 설명
    category: SymptomCategory
    severity: SymptomSeverity
    frequency: str = ""          # 발생 빈도 (예: "70-80%")
    onset_time: str = ""         # 발현 시간 (예: "섭취 후 30분 이내")
    duration: str = ""           # 지속 시간
    citations: list[Citation] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "name_kr": self.name_kr,
            "description": self.description,
            "category": self.category.value,
            "severity": self.severity.value,
            "frequency": self.frequency,
            "onset_time": self.onset_time,
            "duration": self.duration,
            "citations": [c.to_dict() for c in self.citations],
        }


@dataclass
class CrossReactivity:
    """교차 반응 정보"""
    allergen1: str               # 첫 번째 알러지 항원
    allergen2: str               # 두 번째 알러지 항원
    probability: str             # 교차 반응 확률 (예: "50-70%")
    mechanism: str               # 교차 반응 메커니즘
    common_protein: str = ""     # 공통 단백질
    clinical_significance: str = ""  # 임상적 의의
    citations: list[Citation] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "allergen1": self.allergen1,
            "allergen2": self.allergen2,
            "probability": self.probability,
            "mechanism": self.mechanism,
            "common_protein": self.common_protein,
            "clinical_significance": self.clinical_significance,
            "citations": [c.to_dict() for c in self.citations],
        }


@dataclass
class QAResponse:
    """질문-답변 응답"""
    question: str                # 원본 질문
    answer: str                  # 답변 내용
    confidence: float            # 신뢰도 (0.0 ~ 1.0)
    citations: list[Citation]    # 출처 목록
    related_symptoms: list[SymptomInfo] = field(default_factory=list)
    related_cross_reactivities: list[CrossReactivity] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)  # 주의사항
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict:
        return {
            "question": self.question,
            "answer": self.answer,
            "confidence": self.confidence,
            "citations": [c.to_dict() for c in self.citations],
            "related_symptoms": [s.to_dict() for s in self.related_symptoms],
            "related_cross_reactivities": [cr.to_dict() for cr in self.related_cross_reactivities],
            "warnings": self.warnings,
            "citation_count": len(self.citations),
            "created_at": self.created_at.isoformat(),
        }

    def format_with_citations(self) -> str:
        """인용 포함 포맷팅"""
        lines = [self.answer, ""]

        if self.citations:
            lines.append("---")
            lines.append("**출처 (References):**")
            for i, citation in enumerate(self.citations, 1):
                lines.append(f"[{i}] {citation.format_apa()}")
                if citation.relevant_text:
                    # 관련 텍스트 미리보기
                    preview = citation.relevant_text[:200]
                    if len(citation.relevant_text) > 200:
                        preview += "..."
                    lines.append(f"    > \"{preview}\"")

        if self.warnings:
            lines.append("")
            lines.append("**주의사항:**")
            for warning in self.warnings:
                lines.append(f"⚠️ {warning}")

        return "\n".join(lines)
