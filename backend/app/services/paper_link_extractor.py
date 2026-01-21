"""논문 링크 자동 추출 서비스

논문 Abstract와 Title에서 키워드를 분석하여
PaperAllergenLink의 specific_item을 자동 추출합니다.
"""
import re
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass

from ..data.paper_keywords import (
    SYMPTOM_KEYWORDS,
    AVOID_FOOD_KEYWORDS,
    SUBSTITUTE_KEYWORDS,
    CROSS_REACTIVITY_KEYWORDS,
    MANAGEMENT_KEYWORDS,
    PAPER_TYPE_KEYWORDS,
)


@dataclass
class ExtractedLink:
    """추출된 논문 링크 정보"""
    allergen_code: str
    link_type: str  # symptom, dietary, substitute, cross_reactivity, management, emergency
    specific_item: str  # 한국어 구체적 항목
    relevance_score: int  # 0-100
    matched_keyword: str  # 매칭된 영어 키워드
    context: Optional[str] = None  # 키워드 주변 문맥


class PaperLinkExtractor:
    """논문에서 알러젠 링크 정보를 자동 추출하는 서비스"""

    # 알러젠 코드와 관련 영어 키워드
    ALLERGEN_KEYWORDS = {
        "peanut": ["peanut", "arachis", "ara h"],
        "milk": ["milk", "dairy", "cow's milk", "casein", "whey", "lactose"],
        "egg": ["egg", "ovalbumin", "ovomucoid", "hen's egg"],
        "wheat": ["wheat", "gluten", "gliadin", "triticum"],
        "soy": ["soy", "soybean", "soja"],
        "fish": ["fish", "cod", "salmon", "tuna", "parvalbumin"],
        "shellfish": ["shellfish", "shrimp", "crab", "lobster", "crustacean", "tropomyosin"],
        "tree_nuts": ["tree nut", "almond", "walnut", "cashew", "hazelnut", "pistachio"],
        "sesame": ["sesame", "sesamum"],
        "dust_mite": ["dust mite", "dermatophagoides", "house dust"],
        "pollen": ["pollen", "birch", "grass pollen", "ragweed", "hay fever"],
        "mold": ["mold", "mould", "fungal", "aspergillus", "alternaria"],
        "pet_dander": ["pet dander", "cat allergen", "dog allergen", "fel d", "can f"],
        "cockroach": ["cockroach", "bla g"],
        "latex": ["latex", "hevea"],
        "bee_venom": ["bee venom", "hymenoptera", "api m"],
    }

    def __init__(self):
        # 키워드를 소문자로 정규화
        self._symptom_keywords = {k.lower(): v for k, v in SYMPTOM_KEYWORDS.items()}
        self._avoid_food_keywords = {k.lower(): v for k, v in AVOID_FOOD_KEYWORDS.items()}
        self._substitute_keywords = {k.lower(): v for k, v in SUBSTITUTE_KEYWORDS.items()}
        self._management_keywords = {k.lower(): v for k, v in MANAGEMENT_KEYWORDS.items()}
        self._paper_type_keywords = {k.lower(): v for k, v in PAPER_TYPE_KEYWORDS.items()}

    def extract_links(
        self,
        title: str,
        abstract: str,
        keywords: Optional[List[str]] = None,
        target_allergen: Optional[str] = None
    ) -> List[ExtractedLink]:
        """
        논문에서 링크 정보 추출

        Args:
            title: 논문 제목
            abstract: 논문 초록
            keywords: 논문 키워드 목록 (있으면)
            target_allergen: 특정 알러젠만 대상으로 할 경우

        Returns:
            추출된 링크 목록
        """
        text = f"{title} {abstract}".lower()
        if keywords:
            text += " " + " ".join(keywords).lower()

        extracted_links = []

        # 1. 관련 알러젠 찾기
        allergens = self._detect_allergens(text, target_allergen)

        for allergen_code in allergens:
            # 2. 증상 추출
            symptom_links = self._extract_symptoms(text, allergen_code)
            extracted_links.extend(symptom_links)

            # 3. 회피 식품 추출
            avoid_links = self._extract_avoid_foods(text, allergen_code)
            extracted_links.extend(avoid_links)

            # 4. 대체 식품 추출
            substitute_links = self._extract_substitutes(text, allergen_code)
            extracted_links.extend(substitute_links)

            # 5. 환경 관리 추출 (흡입성 알러젠)
            management_links = self._extract_management(text, allergen_code)
            extracted_links.extend(management_links)

        # 6. 교차반응 추출
        cross_links = self._extract_cross_reactivity(text, allergens)
        extracted_links.extend(cross_links)

        # 중복 제거 및 정렬
        extracted_links = self._deduplicate_links(extracted_links)
        extracted_links.sort(key=lambda x: (-x.relevance_score, x.allergen_code))

        return extracted_links

    def _detect_allergens(
        self,
        text: str,
        target_allergen: Optional[str] = None
    ) -> List[str]:
        """텍스트에서 알러젠 감지"""
        if target_allergen:
            return [target_allergen]

        detected = []
        for allergen_code, keywords in self.ALLERGEN_KEYWORDS.items():
            for kw in keywords:
                if kw.lower() in text:
                    detected.append(allergen_code)
                    break

        return list(set(detected))

    def _extract_symptoms(self, text: str, allergen_code: str) -> List[ExtractedLink]:
        """증상 키워드 추출"""
        links = []

        for en_keyword, kr_name in self._symptom_keywords.items():
            if en_keyword in text:
                # 관련도 계산: 제목에 있으면 더 높은 점수
                relevance = 75
                if en_keyword in text[:200]:  # 제목 또는 초록 앞부분
                    relevance = 90

                # 아나필락시스는 응급으로 분류
                link_type = "emergency" if "anaphyla" in en_keyword else "symptom"

                links.append(ExtractedLink(
                    allergen_code=allergen_code,
                    link_type=link_type,
                    specific_item=kr_name,
                    relevance_score=relevance,
                    matched_keyword=en_keyword,
                ))

        return links

    def _extract_avoid_foods(self, text: str, allergen_code: str) -> List[ExtractedLink]:
        """회피 식품 키워드 추출"""
        links = []

        for en_keyword, (kr_name, related_allergen) in self._avoid_food_keywords.items():
            if related_allergen != allergen_code:
                continue

            if en_keyword in text:
                relevance = 70
                if en_keyword in text[:200]:
                    relevance = 85

                links.append(ExtractedLink(
                    allergen_code=allergen_code,
                    link_type="dietary",
                    specific_item=kr_name,
                    relevance_score=relevance,
                    matched_keyword=en_keyword,
                ))

        return links

    def _extract_substitutes(self, text: str, allergen_code: str) -> List[ExtractedLink]:
        """대체 식품 키워드 추출"""
        links = []

        for en_keyword, (kr_name, related_allergen) in self._substitute_keywords.items():
            if related_allergen != allergen_code:
                continue

            if en_keyword in text:
                relevance = 70
                if en_keyword in text[:200]:
                    relevance = 85

                links.append(ExtractedLink(
                    allergen_code=allergen_code,
                    link_type="substitute",
                    specific_item=kr_name,
                    relevance_score=relevance,
                    matched_keyword=en_keyword,
                ))

        return links

    def _extract_management(self, text: str, allergen_code: str) -> List[ExtractedLink]:
        """환경 관리 키워드 추출"""
        links = []

        for en_keyword, (kr_name, related_allergen) in self._management_keywords.items():
            if related_allergen != allergen_code and related_allergen != "general":
                continue

            if en_keyword in text:
                relevance = 75
                if en_keyword in text[:200]:
                    relevance = 90

                # 에피펜/에피네프린은 응급으로 분류
                link_type = "emergency" if related_allergen == "general" else "management"

                links.append(ExtractedLink(
                    allergen_code=allergen_code,
                    link_type=link_type,
                    specific_item=kr_name,
                    relevance_score=relevance,
                    matched_keyword=en_keyword,
                ))

        return links

    def _extract_cross_reactivity(
        self,
        text: str,
        allergens: List[str]
    ) -> List[ExtractedLink]:
        """교차반응 키워드 추출"""
        links = []

        # 교차반응 관련 문구 감지
        cross_patterns = [
            r"cross[- ]?react",
            r"cross[- ]?sensitiz",
            r"co[- ]?sensitiz",
            r"cross[- ]?allerg",
        ]

        has_cross_mention = any(re.search(p, text) for p in cross_patterns)

        if has_cross_mention:
            for allergen in allergens:
                links.append(ExtractedLink(
                    allergen_code=allergen,
                    link_type="cross_reactivity",
                    specific_item="교차반응",
                    relevance_score=80,
                    matched_keyword="cross-reactivity",
                ))

        return links

    def _deduplicate_links(self, links: List[ExtractedLink]) -> List[ExtractedLink]:
        """중복 링크 제거 (같은 allergen + link_type + specific_item)"""
        seen = set()
        unique_links = []

        for link in links:
            key = (link.allergen_code, link.link_type, link.specific_item)
            if key not in seen:
                seen.add(key)
                unique_links.append(link)

        return unique_links

    def detect_paper_type(self, title: str, abstract: str) -> str:
        """논문 타입 감지"""
        text = f"{title} {abstract}".lower()

        for keyword, paper_type in self._paper_type_keywords.items():
            if keyword in text:
                return paper_type

        return "research"  # 기본값

    def extract_links_batch(
        self,
        papers: List[Dict],
        target_allergen: Optional[str] = None
    ) -> Dict[str, List[ExtractedLink]]:
        """
        여러 논문에서 일괄 추출

        Args:
            papers: [{"id": ..., "title": ..., "abstract": ..., "keywords": [...]}]
            target_allergen: 특정 알러젠만 대상

        Returns:
            {paper_id: [ExtractedLink, ...]}
        """
        results = {}

        for paper in papers:
            paper_id = paper.get("id") or paper.get("pmid") or paper.get("doi")
            links = self.extract_links(
                title=paper.get("title", ""),
                abstract=paper.get("abstract", ""),
                keywords=paper.get("keywords"),
                target_allergen=target_allergen,
            )
            results[paper_id] = links

        return results


# 싱글톤 인스턴스
_extractor_instance = None


def get_extractor() -> PaperLinkExtractor:
    """추출기 싱글톤 인스턴스 반환"""
    global _extractor_instance
    if _extractor_instance is None:
        _extractor_instance = PaperLinkExtractor()
    return _extractor_instance
