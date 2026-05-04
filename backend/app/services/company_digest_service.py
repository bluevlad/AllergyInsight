"""뉴스레터 기업 동향 집계 서비스

헤드라인에 선정되지 않은 기사를 기업별로 7일 누적 타임라인으로 요약.

NEWSLETTER_REDESIGN_SPEC § 2.2:
- 데이터 풀: 헤드라인 excluded_ids 를 제외한 잔여 기사
- company_name IS NOT NULL 인 기사만 대상
- 기업별 최근 days일 기사 수, 대표 기사 1건, 중요도 평균
"""
from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

from sqlalchemy import func
from sqlalchemy.orm import Session

from ..database.competitor_models import CompetitorCompany, CompetitorNews
from ..utils.timezone import utc_now

logger = logging.getLogger(__name__)


def build_company_digest(
    session: Session,
    *,
    days: int = 7,
    exclude_ids: set[int] | None = None,
    limit_per_company: int = 1,
    max_companies: int = 20,
) -> list[dict[str, Any]]:
    """기업별 동향 다이제스트.

    Args:
        session: SQLAlchemy session.
        days: 집계 기간 (일).
        exclude_ids: 헤드라인에 선정된 기사 id set — disjoint 보장용.
        limit_per_company: 대표 기사 수 (기본 1).
        max_companies: 최대 기업 수.

    Returns:
        기업별 다이제스트 리스트 (§ 3.2.2 응답 스키마).
    """
    since = utc_now() - timedelta(days=days)
    exclude_ids = exclude_ids or set()

    base_query = (
        session.query(CompetitorNews, CompetitorCompany)
        .join(CompetitorCompany, CompetitorNews.company_id == CompetitorCompany.id)
        .filter(
            CompetitorNews.is_processed == True,   # noqa: E712
            CompetitorNews.is_relevant == True,     # noqa: E712
            CompetitorNews.is_duplicate == False,    # noqa: E712
            CompetitorNews.published_at >= since,
        )
    )

    if exclude_ids:
        base_query = base_query.filter(
            CompetitorNews.id.notin_(exclude_ids)
        )

    rows = base_query.order_by(
        CompetitorNews.company_id,
        CompetitorNews.importance_score.desc(),
    ).all()

    company_buckets: dict[int, dict[str, Any]] = {}

    for news, company in rows:
        cid = company.id
        if cid not in company_buckets:
            company_buckets[cid] = {
                "company_name": company.name_kr,
                "articles": [],
                "importance_sum": 0.0,
                "categories": set(),
            }
        bucket = company_buckets[cid]
        bucket["articles"].append(news)
        bucket["importance_sum"] += (news.importance_score or 0.0)
        if news.category:
            bucket["categories"].add(news.category)

    result: list[dict[str, Any]] = []
    sorted_companies = sorted(
        company_buckets.values(),
        key=lambda b: len(b["articles"]),
        reverse=True,
    )

    for bucket in sorted_companies[:max_companies]:
        articles = bucket["articles"]
        count = len(articles)
        avg_importance = round(bucket["importance_sum"] / count, 2) if count else 0.0

        representative = articles[0]
        rep_dict = {
            "title": representative.title,
            "summary": representative.summary,
            "url": representative.url,
            "published_at": (
                representative.published_at.isoformat()
                if representative.published_at
                else None
            ),
        }

        result.append({
            "company_name": bucket["company_name"],
            "count_7d": count,
            "avg_importance": avg_importance,
            "representative": rep_dict,
            "categories": sorted(bucket["categories"]),
        })

    logger.info(
        "company_digest: days=%d exclude=%d companies=%d",
        days,
        len(exclude_ids),
        len(result),
    )
    return result
