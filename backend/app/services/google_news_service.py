"""Google News RSS 피드 파서

Google News RSS를 통해 뉴스를 검색합니다.
별도의 API 키 없이 사용 가능합니다.

RSS URL 패턴:
https://news.google.com/rss/search?q={query}&hl=ko&gl=KR&ceid=KR:ko
"""
import time
from typing import Optional
from datetime import datetime
from urllib.parse import quote

import feedparser

from ..models.competitor_news import NewsArticle, NewsSearchResult


class GoogleNewsService:
    """Google News RSS 파서"""

    BASE_URL = "https://news.google.com/rss/search"

    def __init__(self):
        pass

    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """RSS 날짜 파싱"""
        if not date_str:
            return None
        try:
            from email.utils import parsedate_to_datetime
            return parsedate_to_datetime(date_str)
        except Exception:
            return None

    def search(
        self,
        query: str,
        lang: str = "ko",
        country: str = "KR",
        when: str = "7d",
        max_results: int = 20,
    ) -> NewsSearchResult:
        """
        Google News RSS 검색

        Args:
            query: 검색 쿼리
            lang: 언어 코드 (ko, en 등)
            country: 국가 코드 (KR, US 등)
            when: 기간 필터 ("1d", "7d", "30d" 등)
            max_results: 최대 결과 수

        Returns:
            NewsSearchResult: 검색 결과
        """
        start_time = time.time()

        # when 파라미터를 쿼리에 포함
        search_query = f"{query} when:{when}" if when else query
        url = f"{self.BASE_URL}?q={quote(search_query)}&hl={lang}&gl={country}&ceid={country}:{lang}"

        try:
            feed = feedparser.parse(url)
        except Exception:
            return NewsSearchResult(
                articles=[], total_count=0,
                source="google",
                search_time_ms=(time.time() - start_time) * 1000,
            )

        articles = []
        for entry in feed.entries[:max_results]:
            # Google News RSS에서는 description에 HTML이 포함될 수 있음
            description = entry.get("summary", "") or entry.get("description", "")
            # 간단한 HTML 태그 제거
            import re
            description = re.sub(r"<[^>]+>", "", description).strip()

            article = NewsArticle(
                title=entry.get("title", ""),
                url=entry.get("link", ""),
                source="google",
                company="",  # 호출 측에서 설정
                description=description[:500],  # 최대 500자
                published_at=self._parse_date(entry.get("published", "")),
                search_keyword=query,
            )
            articles.append(article)

        return NewsSearchResult(
            articles=articles,
            total_count=len(articles),
            source="google",
            search_time_ms=(time.time() - start_time) * 1000,
        )
