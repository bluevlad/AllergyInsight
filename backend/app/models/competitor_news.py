"""경쟁사 뉴스 데이터 모델"""
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class NewsSource(str, Enum):
    """뉴스 출처"""
    NAVER = "naver"
    GOOGLE = "google"


class CompanyCategory(str, Enum):
    """업체 구분"""
    SELF = "self"
    OVERSEAS = "overseas"
    DOMESTIC = "domestic"
    INDUSTRY = "industry"


@dataclass
class NewsArticle:
    """뉴스 기사 모델"""
    title: str
    url: str
    source: str  # 'naver', 'google'
    company: str  # 'sugentech', 'phadia' 등
    description: str
    published_at: Optional[datetime] = None
    search_keyword: str = ""

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "url": self.url,
            "source": self.source,
            "company": self.company,
            "description": self.description,
            "published_at": self.published_at.isoformat() if self.published_at else None,
            "search_keyword": self.search_keyword,
        }


@dataclass
class NewsSearchResult:
    """뉴스 검색 결과"""
    articles: list[NewsArticle]
    total_count: int
    source: str
    search_time_ms: float

    def to_dict(self) -> dict:
        return {
            "articles": [a.to_dict() for a in self.articles],
            "total_count": self.total_count,
            "source": self.source,
            "search_time_ms": self.search_time_ms,
        }


# 기본 경쟁사 목록 및 검색 키워드
DEFAULT_COMPETITORS = {
    "sugentech": {
        "name_kr": "수젠텍",
        "name_en": "Sugentech",
        "category": CompanyCategory.SELF,
        "keywords": ["수젠텍", "Sugentech", "SGTi"],
        "homepage_url": "https://www.sugentech.com",
    },
    "phadia": {
        "name_kr": "파디아/써모피셔",
        "name_en": "Phadia/Thermo Fisher",
        "category": CompanyCategory.OVERSEAS,
        "keywords": ["Phadia", "ImmunoCap", "Thermo Fisher 알러지"],
        "homepage_url": "https://www.thermofisher.com",
    },
    "siemens": {
        "name_kr": "지멘스 헬시니어스",
        "name_en": "Siemens Healthineers",
        "category": CompanyCategory.OVERSEAS,
        "keywords": ["Siemens 알러지", "Atellica"],
        "homepage_url": "https://www.siemens-healthineers.com",
    },
    "hycor": {
        "name_kr": "하이코어 바이오메디컬",
        "name_en": "Hycor Biomedical",
        "category": CompanyCategory.OVERSEAS,
        "keywords": ["Hycor", "NOVEOS"],
        "homepage_url": "https://www.hycorbiomedical.com",
    },
    "madx": {
        "name_kr": "MADx",
        "name_en": "Macro Array Diagnostics",
        "category": CompanyCategory.OVERSEAS,
        "keywords": ["ALEX2", "MADx"],
        "homepage_url": "https://www.macroarraydx.com",
    },
    "lgchem": {
        "name_kr": "LG화학",
        "name_en": "LG Chem",
        "category": CompanyCategory.DOMESTIC,
        "keywords": ["LG화학 체외진단"],
        "homepage_url": "https://www.lgchem.com",
    },
    "greencross": {
        "name_kr": "녹십자MS",
        "name_en": "Green Cross MS",
        "category": CompanyCategory.DOMESTIC,
        "keywords": ["녹십자MS 체외진단", "녹십자MS 알러지"],
        "homepage_url": "https://www.greencrossms.com",
    },
    "bodytech": {
        "name_kr": "바디텍메드",
        "name_en": "Boditech Med",
        "category": CompanyCategory.DOMESTIC,
        "keywords": ["바디텍메드 진단"],
        "homepage_url": "https://www.boditech.co.kr",
    },
    "industry": {
        "name_kr": "업계 공통",
        "name_en": "Industry",
        "category": CompanyCategory.INDUSTRY,
        "keywords": ["알러지 진단", "체외진단 알러지", "IVD allergy"],
        "homepage_url": None,
    },
}
