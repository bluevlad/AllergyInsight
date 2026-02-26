"""뉴스 카테고리 정의"""
from enum import Enum


class NewsCategoryType(str, Enum):
    """뉴스 카테고리 분류"""
    REGULATORY = "regulatory"
    MARKET = "market"
    TECHNOLOGY = "technology"
    COMPETITOR = "competitor"
    PRODUCT = "product"
    GENERAL = "general"


# 카테고리별 키워드 매핑 (AI 분류 fallback용)
CATEGORY_KEYWORDS = {
    NewsCategoryType.REGULATORY: [
        "허가", "인허가", "규제", "식약처", "FDA", "CE", "승인", "인증",
        "approval", "regulatory", "clearance", "certification",
    ],
    NewsCategoryType.MARKET: [
        "시장", "매출", "수주", "계약", "인수", "합병", "투자", "IPO",
        "market", "revenue", "acquisition", "investment", "funding",
    ],
    NewsCategoryType.TECHNOLOGY: [
        "기술", "개발", "연구", "특허", "혁신", "AI", "플랫폼",
        "technology", "R&D", "patent", "innovation", "platform",
    ],
    NewsCategoryType.COMPETITOR: [
        "경쟁", "점유율", "비교", "대비",
        "competitor", "market share", "comparison",
    ],
    NewsCategoryType.PRODUCT: [
        "제품", "출시", "키트", "장비", "신제품", "업그레이드",
        "product", "launch", "kit", "device", "release",
    ],
}


def classify_by_keywords(text: str) -> NewsCategoryType:
    """키워드 기반 카테고리 분류 (fallback)"""
    text_lower = text.lower()
    scores = {}

    for category, keywords in CATEGORY_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw.lower() in text_lower)
        if score > 0:
            scores[category] = score

    if scores:
        return max(scores, key=scores.get)
    return NewsCategoryType.GENERAL
