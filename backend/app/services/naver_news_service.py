"""네이버 뉴스 검색 API 연동 서비스

네이버 개발자 센터에서 발급받은 Client ID/Secret으로
뉴스 검색 API를 호출합니다.

API 문서: https://developers.naver.com/docs/serviceapi/search/news/news.md
"""
import os
import re
import time
from typing import Optional
from datetime import datetime

import requests

from ..models.competitor_news import NewsArticle, NewsSearchResult


class NaverNewsService:
    """네이버 뉴스 검색 API 클라이언트"""

    BASE_URL = "https://openapi.naver.com/v1/search/news.json"

    def __init__(
        self,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
    ):
        self.client_id = client_id or os.getenv("NAVER_CLIENT_ID", "")
        self.client_secret = client_secret or os.getenv("NAVER_CLIENT_SECRET", "")
        self.session = requests.Session()
        self.session.headers.update({
            "X-Naver-Client-Id": self.client_id,
            "X-Naver-Client-Secret": self.client_secret,
            "User-Agent": "AllergyInsight/1.0",
        })

    def _strip_html(self, text: str) -> str:
        """네이버 API 응답의 HTML 태그 제거"""
        if not text:
            return ""
        clean = re.sub(r"<[^>]+>", "", text)
        clean = clean.replace("&quot;", '"').replace("&amp;", "&")
        clean = clean.replace("&lt;", "<").replace("&gt;", ">")
        clean = clean.replace("&apos;", "'")
        return clean.strip()

    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """네이버 뉴스 날짜 파싱 (RFC 822 형식)"""
        if not date_str:
            return None
        try:
            # 예: "Mon, 10 Feb 2025 09:00:00 +0900"
            from email.utils import parsedate_to_datetime
            return parsedate_to_datetime(date_str)
        except Exception:
            return None

    def search(
        self,
        query: str,
        display: int = 20,
        start: int = 1,
        sort: str = "date",
    ) -> NewsSearchResult:
        """
        네이버 뉴스 검색

        Args:
            query: 검색 쿼리
            display: 결과 수 (최대 100)
            start: 시작 위치 (최대 1000)
            sort: 정렬 ("date": 최신순, "sim": 정확도순)

        Returns:
            NewsSearchResult: 검색 결과
        """
        if not self.client_id or not self.client_secret:
            return NewsSearchResult(
                articles=[], total_count=0,
                source="naver", search_time_ms=0,
            )

        start_time = time.time()

        params = {
            "query": query,
            "display": min(display, 100),
            "start": start,
            "sort": sort,
        }

        try:
            response = self.session.get(
                self.BASE_URL,
                params=params,
                timeout=10,
            )
            response.raise_for_status()
            data = response.json()
        except Exception:
            return NewsSearchResult(
                articles=[], total_count=0,
                source="naver",
                search_time_ms=(time.time() - start_time) * 1000,
            )

        articles = []
        for item in data.get("items", []):
            article = NewsArticle(
                title=self._strip_html(item.get("title", "")),
                url=item.get("link", ""),
                source="naver",
                company="",  # 호출 측에서 설정
                description=self._strip_html(item.get("description", "")),
                published_at=self._parse_date(item.get("pubDate", "")),
                search_keyword=query,
            )
            articles.append(article)

        return NewsSearchResult(
            articles=articles,
            total_count=int(data.get("total", 0)),
            source="naver",
            search_time_ms=(time.time() - start_time) * 1000,
        )
