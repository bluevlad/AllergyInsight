"""뉴스 리포트 생성기

Jinja2 템플릿을 사용하여 이메일 리포트를 생성합니다.
"""
import os
import logging
from datetime import datetime, date
from typing import Optional
from pathlib import Path

logger = logging.getLogger(__name__)

# 템플릿 디렉토리
TEMPLATE_DIR = Path(__file__).parent.parent.parent / "templates" / "email"


def _format_date(value):
    """날짜 포맷 필터"""
    if value is None:
        return ""
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d %H:%M")
    if isinstance(value, date):
        return value.strftime("%Y-%m-%d")
    return str(value)


def _truncate_text(value, length=100):
    """텍스트 자르기 필터"""
    if not value:
        return ""
    if len(value) <= length:
        return value
    return value[:length] + "..."


class NewsReportGenerator:
    """뉴스 리포트 생성기"""

    def __init__(self):
        self._env = None

    def _get_env(self):
        """Jinja2 Environment (lazy 초기화)"""
        if self._env is None:
            try:
                from jinja2 import Environment, FileSystemLoader
                self._env = Environment(
                    loader=FileSystemLoader(str(TEMPLATE_DIR)),
                    autoescape=True,
                )
                self._env.filters["format_date"] = _format_date
                self._env.filters["truncate_text"] = _truncate_text
            except ImportError:
                logger.warning("jinja2 패키지가 설치되지 않았습니다")
                self._env = None
        return self._env

    def generate_daily_report(
        self,
        articles: list[dict],
        report_date: Optional[str] = None,
        unsubscribe_url: Optional[str] = None,
    ) -> str:
        """일일 리포트 HTML 생성

        Args:
            articles: 기사 목록 (dict 리스트)
            report_date: 리포트 날짜 문자열
            unsubscribe_url: 구독 해지 URL

        Returns:
            HTML 문자열
        """
        if report_date is None:
            report_date = datetime.now().strftime("%Y년 %m월 %d일")

        # 카테고리별 분류
        category_names = {
            "regulatory": "규제/인허가",
            "market": "시장/산업",
            "technology": "기술/R&D",
            "competitor": "경쟁사",
            "product": "제품/서비스",
            "general": "일반",
        }
        categories = {}
        for article in articles:
            cat = article.get("category", "general")
            cat_name = category_names.get(cat, cat)
            if cat_name not in categories:
                categories[cat_name] = []
            categories[cat_name].append(article)

        # 중요 기사 수
        important_count = sum(
            1 for a in articles
            if (a.get("importance_score") or 0) >= 0.7
        )

        context = {
            "title": f"AllergyInsight Daily Report - {report_date}",
            "report_date": report_date,
            "total_articles": len(articles),
            "new_articles": len(articles),
            "important_articles": important_count,
            "categories": categories,
            "unsubscribe_url": unsubscribe_url,
        }

        return self._render("email_report.html", context)

    def generate_summary_report(
        self,
        articles: list[dict],
        report_date: Optional[str] = None,
        unsubscribe_url: Optional[str] = None,
        manage_url: Optional[str] = None,
    ) -> str:
        """뉴스 브리핑 HTML 생성"""
        if report_date is None:
            report_date = datetime.now().strftime("%Y년 %m월 %d일")

        context = {
            "report_date": report_date,
            "total_articles": len(articles),
            "articles": articles,
            "unsubscribe_url": unsubscribe_url,
            "manage_url": manage_url,
        }

        return self._render("news_briefing.html", context)

    def generate_subscription_key_email(
        self,
        verification_code: str,
        expires_minutes: int = 30,
    ) -> str:
        """구독 인증 키 이메일 HTML 생성"""
        context = {
            "verification_code": verification_code,
            "expires_minutes": expires_minutes,
        }
        return self._render("subscription_key.html", context)

    def _render(self, template_name: str, context: dict) -> str:
        """템플릿 렌더링"""
        env = self._get_env()
        if env is None:
            return self._fallback_html(context)

        try:
            template = env.get_template(template_name)
            return template.render(**context)
        except Exception as e:
            logger.warning(f"템플릿 렌더링 실패 ({template_name}): {e}")
            return self._fallback_html(context)

    def _fallback_html(self, context: dict) -> str:
        """Jinja2 사용 불가 시 기본 HTML"""
        title = context.get("title", "AllergyInsight Report")
        report_date = context.get("report_date", "")
        articles = context.get("articles", [])

        article_html = ""
        for article in articles:
            title_text = article.get("title", "")
            url = article.get("url", "#")
            article_html += f'<li><a href="{url}">{title_text}</a></li>\n'

        return f"""
        <html><body>
        <h1>{title}</h1>
        <p>{report_date}</p>
        <ul>{article_html}</ul>
        <p style="font-size:12px;color:#999">AllergyInsight</p>
        </body></html>
        """
