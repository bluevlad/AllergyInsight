"""Q&A 엔진

논문 기반으로 알러지 증상에 대한 질문에 답변합니다.
모든 답변에 출처(Citation)를 포함하여 검증 가능하게 합니다.
"""
import re
from typing import Optional
from dataclasses import dataclass, field

from ..models.paper import Paper
from ..models.knowledge_base import (
    Citation,
    SymptomInfo,
    SymptomCategory,
    SymptomSeverity,
    CrossReactivity,
    QAResponse,
)
from .paper_search_service import PaperSearchService
from .knowledge_extractor import KnowledgeExtractor, ExtractedKnowledge


@dataclass
class AllergenKnowledgeBase:
    """알러지 항원별 지식 베이스"""
    allergen: str
    papers: list[Paper]
    knowledge: ExtractedKnowledge
    last_updated: str = ""


class QAEngine:
    """논문 기반 Q&A 엔진"""

    # 사전 정의된 질문 템플릿
    QUESTION_TEMPLATES = {
        "symptoms": [
            "땅콩 알러지의 주요 증상은 무엇인가요?",
            "땅콩 알러지 반응이 나타나면 어떤 증상이 있나요?",
            "peanut allergy symptoms",
        ],
        "severity": [
            "땅콩 알러지가 얼마나 위험한가요?",
            "땅콩 알러지로 인한 심각한 반응은?",
            "아나필락시스 위험이 있나요?",
        ],
        "cross_reactivity": [
            "땅콩 알러지가 있으면 다른 음식도 조심해야 하나요?",
            "교차 반응이 있는 음식은?",
            "땅콩과 견과류 알러지의 관계는?",
        ],
        "onset": [
            "땅콩 알러지 증상은 얼마나 빨리 나타나나요?",
            "반응 시간은 어떻게 되나요?",
        ],
        "treatment": [
            "땅콩 알러지 치료법은?",
            "응급 상황에서 어떻게 해야 하나요?",
        ],
    }

    def __init__(
        self,
        search_service: Optional[PaperSearchService] = None,
    ):
        self.search_service = search_service or PaperSearchService()
        self.extractor = KnowledgeExtractor()
        self._knowledge_cache: dict[str, AllergenKnowledgeBase] = {}

    def build_knowledge_base(
        self,
        allergen: str,
        max_papers: int = 20,
        include_cross_reactivity: bool = True,
    ) -> AllergenKnowledgeBase:
        """
        특정 알러지 항원에 대한 지식 베이스 구축

        Args:
            allergen: 알러지 항원 (예: "peanut")
            max_papers: 검색할 최대 논문 수
            include_cross_reactivity: 교차 반응 논문 포함

        Returns:
            AllergenKnowledgeBase: 구축된 지식 베이스
        """
        # 캐시 확인
        cache_key = f"{allergen}:{include_cross_reactivity}"
        if cache_key in self._knowledge_cache:
            return self._knowledge_cache[cache_key]

        # 논문 검색
        result = self.search_service.search_allergy(
            allergen=allergen,
            include_cross_reactivity=include_cross_reactivity,
            max_results_per_source=max_papers,
        )

        papers = result.papers

        # 지식 추출
        knowledge = self.extractor.extract_from_papers(papers)

        # 지식 베이스 생성
        kb = AllergenKnowledgeBase(
            allergen=allergen,
            papers=papers,
            knowledge=knowledge,
        )

        # 캐시 저장
        self._knowledge_cache[cache_key] = kb

        return kb

    def ask(
        self,
        question: str,
        allergen: str = "peanut",
        max_citations: int = 5,
    ) -> QAResponse:
        """
        질문에 대한 답변 생성

        Args:
            question: 사용자 질문
            allergen: 알러지 항원
            max_citations: 최대 인용 수

        Returns:
            QAResponse: 답변 및 출처
        """
        # 지식 베이스 로드/구축
        kb = self.build_knowledge_base(allergen)

        # 질문 유형 분류
        question_type = self._classify_question(question)

        # 관련 정보 수집
        relevant_symptoms = []
        relevant_cross = []
        relevant_citations = []

        if question_type in ["symptoms", "severity", "onset"]:
            relevant_symptoms = kb.knowledge.symptoms
            relevant_citations = self._collect_symptom_citations(
                relevant_symptoms, max_citations
            )

        if question_type in ["cross_reactivity"]:
            relevant_cross = kb.knowledge.cross_reactivities
            relevant_citations = self._collect_cross_citations(
                relevant_cross, max_citations
            )

        if question_type == "treatment":
            # 치료 관련 논문에서 정보 추출
            relevant_citations = self._search_treatment_info(kb, max_citations)

        # 답변 생성
        answer = self._generate_answer(
            question_type,
            allergen,
            relevant_symptoms,
            relevant_cross,
            kb,
        )

        # 출처가 없으면 논문 abstract에서 추가
        if not relevant_citations and kb.papers:
            relevant_citations = self._get_general_citations(kb.papers[:max_citations])

        # 주의사항 생성
        warnings = self._generate_warnings(relevant_symptoms)

        return QAResponse(
            question=question,
            answer=answer,
            confidence=self._calculate_confidence(relevant_citations),
            citations=relevant_citations,
            related_symptoms=relevant_symptoms[:5],
            related_cross_reactivities=relevant_cross[:3],
            warnings=warnings,
        )

    def _classify_question(self, question: str) -> str:
        """질문 유형 분류"""
        question_lower = question.lower()

        # 키워드 기반 분류
        if any(kw in question_lower for kw in ["증상", "symptom", "반응", "reaction"]):
            return "symptoms"
        if any(kw in question_lower for kw in ["위험", "심각", "severe", "anaphylaxis", "아나필락시스"]):
            return "severity"
        if any(kw in question_lower for kw in ["교차", "cross", "다른 음식", "견과류", "tree nut"]):
            return "cross_reactivity"
        if any(kw in question_lower for kw in ["시간", "빨리", "onset", "얼마나"]):
            return "onset"
        if any(kw in question_lower for kw in ["치료", "treatment", "응급", "에피네프린"]):
            return "treatment"

        return "symptoms"  # 기본값

    def _generate_answer(
        self,
        question_type: str,
        allergen: str,
        symptoms: list[SymptomInfo],
        cross_reactivities: list[CrossReactivity],
        kb: AllergenKnowledgeBase,
    ) -> str:
        """답변 텍스트 생성"""

        if question_type == "symptoms":
            return self._generate_symptoms_answer(allergen, symptoms)

        elif question_type == "severity":
            return self._generate_severity_answer(allergen, symptoms)

        elif question_type == "cross_reactivity":
            return self._generate_cross_reactivity_answer(allergen, cross_reactivities)

        elif question_type == "onset":
            return self._generate_onset_answer(allergen, symptoms)

        elif question_type == "treatment":
            return self._generate_treatment_answer(allergen)

        return f"{allergen} 알러지에 대한 정보를 논문에서 찾을 수 없습니다."

    def _generate_symptoms_answer(self, allergen: str, symptoms: list[SymptomInfo]) -> str:
        """증상 관련 답변 생성"""
        if not symptoms:
            return f"{allergen} 알러지의 증상 정보를 찾지 못했습니다."

        # 심각도별 분류
        by_severity = {
            SymptomSeverity.MILD: [],
            SymptomSeverity.MODERATE: [],
            SymptomSeverity.SEVERE: [],
            SymptomSeverity.ANAPHYLAXIS: [],
        }

        for s in symptoms:
            by_severity[s.severity].append(s)

        lines = [f"## {allergen.upper()} 알러지의 주요 증상\n"]

        if by_severity[SymptomSeverity.ANAPHYLAXIS]:
            lines.append("### 🚨 아나필락시스 (즉시 응급 처치 필요)")
            for s in by_severity[SymptomSeverity.ANAPHYLAXIS]:
                freq = f" (발생률: {s.frequency})" if s.frequency else ""
                lines.append(f"- **{s.name_kr}** ({s.name}){freq}")
            lines.append("")

        if by_severity[SymptomSeverity.SEVERE]:
            lines.append("### ⚠️ 심각한 증상")
            for s in by_severity[SymptomSeverity.SEVERE]:
                freq = f" (발생률: {s.frequency})" if s.frequency else ""
                lines.append(f"- **{s.name_kr}** ({s.name}){freq}")
            lines.append("")

        if by_severity[SymptomSeverity.MODERATE]:
            lines.append("### 중등도 증상")
            for s in by_severity[SymptomSeverity.MODERATE]:
                freq = f" (발생률: {s.frequency})" if s.frequency else ""
                lines.append(f"- **{s.name_kr}** ({s.name}){freq}")
            lines.append("")

        if by_severity[SymptomSeverity.MILD]:
            lines.append("### 경미한 증상")
            for s in by_severity[SymptomSeverity.MILD]:
                freq = f" (발생률: {s.frequency})" if s.frequency else ""
                lines.append(f"- **{s.name_kr}** ({s.name}){freq}")
            lines.append("")

        return "\n".join(lines)

    def _generate_severity_answer(self, allergen: str, symptoms: list[SymptomInfo]) -> str:
        """심각도 관련 답변 생성"""
        severe_symptoms = [s for s in symptoms
                         if s.severity in [SymptomSeverity.SEVERE, SymptomSeverity.ANAPHYLAXIS]]

        lines = [f"## {allergen.upper()} 알러지의 위험성\n"]

        if severe_symptoms:
            lines.append(f"{allergen} 알러지는 **심각한 반응**을 일으킬 수 있습니다.\n")
            lines.append("### 주요 위험 증상:")
            for s in severe_symptoms:
                lines.append(f"- **{s.name_kr}**: {s.description[:100]}..." if s.description else f"- **{s.name_kr}**")

            # 아나필락시스 경고
            anaphylaxis = [s for s in severe_symptoms if s.severity == SymptomSeverity.ANAPHYLAXIS]
            if anaphylaxis:
                lines.append("\n### 🚨 아나필락시스 위험")
                lines.append("아나필락시스는 생명을 위협하는 전신 알러지 반응입니다.")
                lines.append("증상 발현 시 **즉시 에피네프린 투여**가 필요합니다.")
        else:
            lines.append(f"{allergen} 알러지는 일반적으로 경미한 증상을 보입니다.")
            lines.append("그러나 개인에 따라 심각한 반응이 나타날 수 있으므로 주의가 필요합니다.")

        return "\n".join(lines)

    def _generate_cross_reactivity_answer(
        self,
        allergen: str,
        cross_reactivities: list[CrossReactivity]
    ) -> str:
        """교차 반응 관련 답변 생성"""
        lines = [f"## {allergen.upper()} 알러지의 교차 반응\n"]

        # 땅콩 특화 정보
        if allergen.lower() == "peanut":
            lines.append("땅콩 알러지가 있는 경우 다음 식품에 주의가 필요합니다:\n")
            lines.append("### 교차 반응 가능 식품")
            lines.append("- **견과류 (Tree nuts)**: 호두, 아몬드, 캐슈넛 등")
            lines.append("  - 땅콩 알러지 환자의 약 25-40%가 견과류에도 반응")
            lines.append("- **콩류 (Legumes)**: 대두, 렌틸콩, 병아리콩")
            lines.append("  - 같은 콩과 식물로 단백질 구조 유사")
            lines.append("- **루핀 (Lupin)**: 유럽에서 밀가루 대용으로 사용")
            lines.append("")

        if cross_reactivities:
            lines.append("### 논문에서 확인된 교차 반응:")
            for cr in cross_reactivities[:5]:
                prob = f" ({cr.probability})" if cr.probability else ""
                lines.append(f"- {cr.allergen1} ↔ {cr.allergen2}{prob}")
                if cr.mechanism:
                    lines.append(f"  > {cr.mechanism[:100]}...")
        else:
            lines.append("### 주의사항")
            lines.append("교차 반응은 개인마다 다를 수 있으며, 의료 전문가와 상담을 권장합니다.")

        return "\n".join(lines)

    def _generate_onset_answer(self, allergen: str, symptoms: list[SymptomInfo]) -> str:
        """발현 시간 관련 답변 생성"""
        lines = [f"## {allergen.upper()} 알러지 반응 시간\n"]

        lines.append("### 일반적인 발현 시간")
        lines.append("- **즉시형 반응**: 섭취 후 **수 분 ~ 2시간** 이내")
        lines.append("- **지연형 반응**: 섭취 후 **4-6시간** (드물게)")
        lines.append("")
        lines.append("### 증상별 발현 시간")
        lines.append("- 피부 증상 (두드러기, 가려움): 수 분 ~ 30분")
        lines.append("- 위장관 증상 (구토, 복통): 30분 ~ 2시간")
        lines.append("- 호흡기 증상 (천명, 호흡곤란): 수 분 ~ 1시간")
        lines.append("- 아나필락시스: **수 분 이내** (가장 빠름)")
        lines.append("")
        lines.append("⚠️ 아나필락시스는 매우 빠르게 진행되므로 즉각적인 대응이 필요합니다.")

        return "\n".join(lines)

    def _generate_treatment_answer(self, allergen: str) -> str:
        """치료 관련 답변 생성"""
        lines = [f"## {allergen.upper()} 알러지 치료 및 대처\n"]

        lines.append("### 🚨 응급 상황 대처")
        lines.append("1. **에피네프린 자가 주사기** (EpiPen) 즉시 투여")
        lines.append("2. 119 응급 서비스 호출")
        lines.append("3. 환자를 눕히고 다리를 올림")
        lines.append("4. 필요시 5-15분 후 에피네프린 2차 투여")
        lines.append("")
        lines.append("### 경미한 증상 대처")
        lines.append("- **항히스타민제**: 가려움, 두드러기 완화")
        lines.append("- **스테로이드**: 염증 반응 억제")
        lines.append("")
        lines.append("### 장기 관리")
        lines.append("- **회피 요법**: 원인 식품 철저히 회피")
        lines.append("- **면역 치료**: 경구 면역 치료 (OIT) - 전문의 상담 필요")
        lines.append("- **교육**: 식품 라벨 읽기, 응급 상황 대처법 숙지")
        lines.append("")
        lines.append("⚠️ 치료는 반드시 전문 의료진과 상담 후 진행하세요.")

        return "\n".join(lines)

    def _collect_symptom_citations(
        self,
        symptoms: list[SymptomInfo],
        max_count: int
    ) -> list[Citation]:
        """증상 정보에서 인용 수집"""
        citations = []
        seen_titles = set()

        for symptom in symptoms:
            for citation in symptom.citations:
                if citation.paper_title not in seen_titles:
                    citations.append(citation)
                    seen_titles.add(citation.paper_title)
                    if len(citations) >= max_count:
                        return citations

        return citations

    def _collect_cross_citations(
        self,
        cross_reactivities: list[CrossReactivity],
        max_count: int
    ) -> list[Citation]:
        """교차 반응 정보에서 인용 수집"""
        citations = []
        seen_titles = set()

        for cr in cross_reactivities:
            for citation in cr.citations:
                if citation.paper_title not in seen_titles:
                    citations.append(citation)
                    seen_titles.add(citation.paper_title)
                    if len(citations) >= max_count:
                        return citations

        return citations

    def _search_treatment_info(
        self,
        kb: AllergenKnowledgeBase,
        max_count: int
    ) -> list[Citation]:
        """치료 관련 정보 검색"""
        citations = []

        for paper in kb.papers:
            text_lower = (paper.title + " " + paper.abstract).lower()
            if any(kw in text_lower for kw in ["treatment", "therapy", "epinephrine", "immunotherapy"]):
                citation = Citation(
                    paper_title=paper.title,
                    authors=paper.authors,
                    year=paper.year,
                    journal=paper.journal,
                    doi=paper.doi,
                    pmid=paper.source_id,
                    relevant_text=paper.abstract[:300] if paper.abstract else "",
                )
                citations.append(citation)
                if len(citations) >= max_count:
                    break

        return citations

    def _get_general_citations(self, papers: list[Paper]) -> list[Citation]:
        """일반 인용 생성"""
        return [
            Citation(
                paper_title=p.title,
                authors=p.authors,
                year=p.year,
                journal=p.journal,
                doi=p.doi,
                pmid=p.source_id,
                relevant_text=p.abstract[:300] if p.abstract else "",
            )
            for p in papers
        ]

    def _generate_warnings(self, symptoms: list[SymptomInfo]) -> list[str]:
        """주의사항 생성"""
        warnings = []

        # 아나필락시스 경고
        if any(s.severity == SymptomSeverity.ANAPHYLAXIS for s in symptoms):
            warnings.append(
                "이 알러지는 아나필락시스를 유발할 수 있습니다. "
                "항상 에피네프린 자가 주사기를 휴대하세요."
            )

        # 심각한 증상 경고
        severe = [s for s in symptoms if s.severity == SymptomSeverity.SEVERE]
        if severe:
            warnings.append(
                "호흡곤란, 혈압저하 등 심각한 증상이 나타나면 즉시 응급실을 방문하세요."
            )

        # 일반 주의사항
        warnings.append(
            "본 정보는 의학 논문을 기반으로 작성되었으나, "
            "정확한 진단과 치료는 전문 의료진과 상담하세요."
        )

        return warnings

    def _calculate_confidence(self, citations: list[Citation]) -> float:
        """신뢰도 계산"""
        if not citations:
            return 0.3

        # 인용 수에 따른 기본 점수
        base_score = min(len(citations) / 5, 1.0) * 0.5

        # DOI가 있는 논문 비율
        doi_ratio = sum(1 for c in citations if c.doi) / len(citations)
        doi_score = doi_ratio * 0.3

        # 최근 논문 비율 (2020년 이후)
        recent_ratio = sum(1 for c in citations if c.year and c.year >= 2020) / len(citations)
        recent_score = recent_ratio * 0.2

        return min(base_score + doi_score + recent_score, 1.0)

    def get_predefined_questions(self, allergen: str = "peanut") -> dict[str, list[str]]:
        """사전 정의된 질문 목록 반환"""
        questions = {}
        for category, templates in self.QUESTION_TEMPLATES.items():
            questions[category] = [
                t.replace("땅콩", allergen).replace("peanut", allergen)
                for t in templates
            ]
        return questions

    def close(self):
        """리소스 정리"""
        self.search_service.close()
