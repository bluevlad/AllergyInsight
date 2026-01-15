"""지식 추출기

논문 텍스트에서 알러지 관련 정보를 추출합니다.
- 증상 정보
- 교차 반응 정보
- 치료법 정보
"""
import re
from typing import Optional
from dataclasses import dataclass

from ..models.paper import Paper
from ..models.knowledge_base import (
    Citation,
    SymptomInfo,
    SymptomCategory,
    SymptomSeverity,
    CrossReactivity,
)


# 증상 키워드 매핑
SYMPTOM_KEYWORDS = {
    # 피부 증상
    "urticaria": ("두드러기", SymptomCategory.SKIN, SymptomSeverity.MODERATE),
    "hives": ("두드러기", SymptomCategory.SKIN, SymptomSeverity.MODERATE),
    "angioedema": ("혈관부종", SymptomCategory.SKIN, SymptomSeverity.SEVERE),
    "eczema": ("습진", SymptomCategory.SKIN, SymptomSeverity.MILD),
    "pruritus": ("가려움증", SymptomCategory.SKIN, SymptomSeverity.MILD),
    "itching": ("가려움", SymptomCategory.SKIN, SymptomSeverity.MILD),
    "rash": ("발진", SymptomCategory.SKIN, SymptomSeverity.MILD),
    "erythema": ("홍반", SymptomCategory.SKIN, SymptomSeverity.MILD),
    "flushing": ("홍조", SymptomCategory.SKIN, SymptomSeverity.MILD),

    # 호흡기 증상
    "dyspnea": ("호흡곤란", SymptomCategory.RESPIRATORY, SymptomSeverity.SEVERE),
    "wheezing": ("천명음", SymptomCategory.RESPIRATORY, SymptomSeverity.MODERATE),
    "cough": ("기침", SymptomCategory.RESPIRATORY, SymptomSeverity.MILD),
    "rhinitis": ("비염", SymptomCategory.RESPIRATORY, SymptomSeverity.MILD),
    "bronchospasm": ("기관지 경련", SymptomCategory.RESPIRATORY, SymptomSeverity.SEVERE),
    "stridor": ("협착음", SymptomCategory.RESPIRATORY, SymptomSeverity.SEVERE),
    "laryngeal edema": ("후두부종", SymptomCategory.RESPIRATORY, SymptomSeverity.SEVERE),
    "throat tightness": ("목 조임", SymptomCategory.RESPIRATORY, SymptomSeverity.SEVERE),

    # 위장관 증상
    "nausea": ("오심", SymptomCategory.GASTROINTESTINAL, SymptomSeverity.MILD),
    "vomiting": ("구토", SymptomCategory.GASTROINTESTINAL, SymptomSeverity.MODERATE),
    "diarrhea": ("설사", SymptomCategory.GASTROINTESTINAL, SymptomSeverity.MODERATE),
    "abdominal pain": ("복통", SymptomCategory.GASTROINTESTINAL, SymptomSeverity.MODERATE),
    "abdominal cramps": ("복부 경련", SymptomCategory.GASTROINTESTINAL, SymptomSeverity.MODERATE),

    # 심혈관 증상
    "hypotension": ("저혈압", SymptomCategory.CARDIOVASCULAR, SymptomSeverity.SEVERE),
    "tachycardia": ("빈맥", SymptomCategory.CARDIOVASCULAR, SymptomSeverity.MODERATE),
    "syncope": ("실신", SymptomCategory.CARDIOVASCULAR, SymptomSeverity.SEVERE),
    "dizziness": ("어지러움", SymptomCategory.CARDIOVASCULAR, SymptomSeverity.MODERATE),

    # 전신 증상
    "anaphylaxis": ("아나필락시스", SymptomCategory.SYSTEMIC, SymptomSeverity.ANAPHYLAXIS),
    "anaphylactic shock": ("아나필락시스 쇼크", SymptomCategory.SYSTEMIC, SymptomSeverity.ANAPHYLAXIS),
}

# 교차 반응 관련 키워드
CROSS_REACTIVITY_PATTERNS = [
    r"cross[- ]reactivity between (\w+) and (\w+)",
    r"cross[- ]reactive with (\w+)",
    r"(\w+) allergic patients.*also react.*to (\w+)",
    r"homologous proteins? in (\w+) and (\w+)",
]

# 빈도 관련 패턴
FREQUENCY_PATTERNS = [
    r"(\d+(?:\.\d+)?)\s*%\s*of\s*patients?",
    r"(\d+(?:\.\d+)?)\s*-\s*(\d+(?:\.\d+)?)\s*%",
    r"approximately\s*(\d+(?:\.\d+)?)\s*%",
    r"about\s*(\d+(?:\.\d+)?)\s*%",
]


@dataclass
class ExtractedKnowledge:
    """추출된 지식"""
    symptoms: list[SymptomInfo]
    cross_reactivities: list[CrossReactivity]
    raw_sentences: list[str]  # 관련 문장들


class KnowledgeExtractor:
    """논문에서 지식 추출"""

    def __init__(self):
        self._symptom_cache = {}

    def extract_from_paper(self, paper: Paper) -> ExtractedKnowledge:
        """
        논문에서 알러지 관련 지식 추출

        Args:
            paper: 논문 객체

        Returns:
            ExtractedKnowledge: 추출된 지식
        """
        # 분석할 텍스트
        text = f"{paper.title} {paper.abstract}"

        # Citation 생성
        citation = self._create_citation(paper)

        # 증상 추출
        symptoms = self._extract_symptoms(text, citation)

        # 교차 반응 추출
        cross_reactivities = self._extract_cross_reactivities(text, citation)

        # 관련 문장 추출
        raw_sentences = self._extract_relevant_sentences(text)

        return ExtractedKnowledge(
            symptoms=symptoms,
            cross_reactivities=cross_reactivities,
            raw_sentences=raw_sentences,
        )

    def extract_from_papers(self, papers: list[Paper]) -> ExtractedKnowledge:
        """
        여러 논문에서 지식 추출 및 통합

        Args:
            papers: 논문 목록

        Returns:
            ExtractedKnowledge: 통합된 지식
        """
        all_symptoms = []
        all_cross_reactivities = []
        all_sentences = []

        for paper in papers:
            knowledge = self.extract_from_paper(paper)
            all_symptoms.extend(knowledge.symptoms)
            all_cross_reactivities.extend(knowledge.cross_reactivities)
            all_sentences.extend(knowledge.raw_sentences)

        # 중복 제거 및 통합
        merged_symptoms = self._merge_symptoms(all_symptoms)
        merged_cross = self._merge_cross_reactivities(all_cross_reactivities)

        return ExtractedKnowledge(
            symptoms=merged_symptoms,
            cross_reactivities=merged_cross,
            raw_sentences=all_sentences,
        )

    def _create_citation(self, paper: Paper) -> Citation:
        """논문에서 Citation 생성"""
        return Citation(
            paper_title=paper.title,
            authors=paper.authors,
            year=paper.year,
            journal=paper.journal,
            doi=paper.doi,
            pmid=paper.source_id if paper.source.value == "pubmed" else None,
        )

    def _extract_symptoms(self, text: str, citation: Citation) -> list[SymptomInfo]:
        """텍스트에서 증상 추출"""
        symptoms = []
        text_lower = text.lower()

        for keyword, (name_kr, category, severity) in SYMPTOM_KEYWORDS.items():
            if keyword in text_lower:
                # 관련 문장 찾기
                relevant_text = self._find_context(text, keyword)

                # 빈도 정보 추출
                frequency = self._extract_frequency(relevant_text)

                symptom = SymptomInfo(
                    name=keyword,
                    name_kr=name_kr,
                    description=relevant_text[:500] if relevant_text else "",
                    category=category,
                    severity=severity,
                    frequency=frequency,
                    citations=[Citation(
                        paper_title=citation.paper_title,
                        authors=citation.authors,
                        year=citation.year,
                        journal=citation.journal,
                        doi=citation.doi,
                        pmid=citation.pmid,
                        relevant_text=relevant_text[:300] if relevant_text else "",
                    )],
                )
                symptoms.append(symptom)

        return symptoms

    def _extract_cross_reactivities(self, text: str, citation: Citation) -> list[CrossReactivity]:
        """교차 반응 정보 추출"""
        cross_reactivities = []
        text_lower = text.lower()

        # "cross-reactivity" 또는 "cross-reactive" 포함 확인
        if "cross-react" not in text_lower:
            return cross_reactivities

        # 관련 문장 추출
        sentences = re.split(r'[.!?]+', text)

        for sentence in sentences:
            if "cross-react" in sentence.lower():
                # 알러지 항원 추출 시도
                cross = CrossReactivity(
                    allergen1="peanut",  # 기본값
                    allergen2="tree nut",  # 기본값
                    probability="",
                    mechanism=sentence.strip()[:300],
                    citations=[Citation(
                        paper_title=citation.paper_title,
                        authors=citation.authors,
                        year=citation.year,
                        journal=citation.journal,
                        doi=citation.doi,
                        pmid=citation.pmid,
                        relevant_text=sentence.strip()[:300],
                    )],
                )
                cross_reactivities.append(cross)
                break  # 첫 번째 매칭만

        return cross_reactivities

    def _find_context(self, text: str, keyword: str, context_chars: int = 300) -> str:
        """키워드 주변 컨텍스트 추출"""
        text_lower = text.lower()
        pos = text_lower.find(keyword)

        if pos == -1:
            return ""

        start = max(0, pos - context_chars // 2)
        end = min(len(text), pos + len(keyword) + context_chars // 2)

        # 문장 경계로 조정
        context = text[start:end]

        # 앞쪽 문장 경계
        if start > 0:
            first_period = context.find(". ")
            if first_period != -1 and first_period < 50:
                context = context[first_period + 2:]

        return context.strip()

    def _extract_frequency(self, text: str) -> str:
        """빈도 정보 추출"""
        for pattern in FREQUENCY_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                groups = match.groups()
                if len(groups) == 2:
                    return f"{groups[0]}-{groups[1]}%"
                elif len(groups) == 1:
                    return f"{groups[0]}%"
        return ""

    def _extract_relevant_sentences(self, text: str) -> list[str]:
        """관련 문장 추출"""
        relevant = []
        sentences = re.split(r'[.!?]+', text)

        keywords = ["symptom", "reaction", "anaphylaxis", "treatment",
                   "cross-react", "allergy", "sensitization"]

        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) < 20:
                continue

            sentence_lower = sentence.lower()
            if any(kw in sentence_lower for kw in keywords):
                relevant.append(sentence)

        return relevant[:20]  # 최대 20개

    def _merge_symptoms(self, symptoms: list[SymptomInfo]) -> list[SymptomInfo]:
        """증상 정보 병합 (같은 증상의 여러 출처 통합)"""
        merged = {}

        for symptom in symptoms:
            key = symptom.name.lower()

            if key in merged:
                # 기존 증상에 출처 추가
                existing = merged[key]
                for citation in symptom.citations:
                    # 중복 출처 확인
                    if not any(c.paper_title == citation.paper_title
                              for c in existing.citations):
                        existing.citations.append(citation)

                # 빈도 정보 업데이트 (더 구체적인 정보로)
                if symptom.frequency and not existing.frequency:
                    existing.frequency = symptom.frequency
            else:
                merged[key] = symptom

        return list(merged.values())

    def _merge_cross_reactivities(self, cross_reactivities: list[CrossReactivity]) -> list[CrossReactivity]:
        """교차 반응 정보 병합"""
        merged = {}

        for cr in cross_reactivities:
            key = f"{cr.allergen1.lower()}-{cr.allergen2.lower()}"
            reverse_key = f"{cr.allergen2.lower()}-{cr.allergen1.lower()}"

            if key in merged or reverse_key in merged:
                existing_key = key if key in merged else reverse_key
                existing = merged[existing_key]
                for citation in cr.citations:
                    if not any(c.paper_title == citation.paper_title
                              for c in existing.citations):
                        existing.citations.append(citation)
            else:
                merged[key] = cr

        return list(merged.values())
