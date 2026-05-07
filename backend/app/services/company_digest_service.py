"""뉴스레터 기업 동향 집계 서비스

헤드라인에 선정되지 않은 기사를 기업별로 누적 타임라인으로 요약.

NEWSLETTER_REDESIGN_SPEC § 2.2:
- 데이터 풀: 헤드라인 excluded_ids 를 제외한 잔여 기사
- company_name IS NOT NULL 인 기사만 대상
- 기업별 최근 days일 기사 수, 대표 기사 1건, 중요도 평균

B1 확장:
- exclude_companies: 회사명(name_kr) 풀 단계 차단
- category_mix: 같은 event_class 가 max_per_category 를 넘지 않도록 다양성 강제
- since_date: 풀 기준일 (이 시점 이후 published_at 만 집계)
- 응답 필드: event_class, is_new_company
"""
from __future__ import annotations

import logging
from datetime import date, datetime, timedelta
from typing import Any

from sqlalchemy.orm import Session

from ..database.competitor_models import CompetitorCompany, CompetitorNews
from ..utils.timezone import utc_now

logger = logging.getLogger(__name__)


def _resolve_event_class(rep_category: str | None, categories: set[str]) -> str:
    """대표 기사 카테고리 → categories 첫 항목 → 'general' 순으로 폴백."""
    ec = (rep_category or "").strip()
    if not ec and categories:
        ec = sorted(categories)[0]
    return (ec or "general").lower()


def build_company_digest(
    session: Session,
    *,
    days: int = 7,
    exclude_ids: set[int] | None = None,
    limit_per_company: int = 1,
    max_companies: int = 20,
    # B1 신규 (모두 default = 무동작, backwards compatible)
    exclude_companies: set[str] | None = None,
    category_mix: bool = False,
    max_per_category: int = 3,
    since_date: date | None = None,
) -> list[dict[str, Any]]:
    """기업별 동향 다이제스트.

    Args:
        session: SQLAlchemy session.
        days: 집계 기간 (일). since_date 가 주어지면 days 는 무시.
        exclude_ids: 헤드라인에 선정된 기사 id set — disjoint 보장용.
        limit_per_company: 대표 기사 수 (기본 1).
        max_companies: 최대 기업 수.
        exclude_companies: 풀에서 제외할 회사명(name_kr) set. strip 후 동등 매칭.
        category_mix: True 면 event_class 별 max_per_category 한도로 다양성 강제.
        max_per_category: category_mix=True 일 때 한 event_class 당 최대 기업 수.
        since_date: 이 날짜 이후 published_at 만 풀에 포함 (UTC 자정 기준).
            제공 시 days 와 함께 적용되지 않고 since_date 가 우선.
            응답 회사별 is_new_company 도 since_date 이전 기사 0건 기준으로 산출.

    Returns:
        기업별 다이제스트 리스트. 각 항목:
          {company_name, count_7d, avg_importance, representative,
           categories, event_class, is_new_company}
        — count_7d 필드명은 backwards compatibility 유지 (실제 윈도는 days/since_date).
    """
    exclude_ids = exclude_ids or set()
    exclude_companies = {(c or "").strip() for c in (exclude_companies or set()) if c}

    if since_date is not None:
        # date → naive datetime at midnight (utc_now() 도 naive UTC 기준)
        since_dt = datetime.combine(since_date, datetime.min.time())
    else:
        since_dt = utc_now() - timedelta(days=days)

    base_query = (
        session.query(CompetitorNews, CompetitorCompany)
        .join(CompetitorCompany, CompetitorNews.company_id == CompetitorCompany.id)
        .filter(
            CompetitorNews.is_processed == True,   # noqa: E712
            CompetitorNews.is_relevant == True,     # noqa: E712
            CompetitorNews.is_duplicate == False,    # noqa: E712
            CompetitorNews.published_at >= since_dt,
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
                "cid": cid,
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

    # since_date 가 주어진 경우 — 그 이전에 처리완료 기사가 1건이라도 있는
    # 회사 id 집합을 한 번에 조회 (is_new_company 산출용).
    pre_existing_company_ids: set[int] = set()
    if since_date is not None and company_buckets:
        cid_list = list(company_buckets.keys())
        pre_rows = (
            session.query(CompetitorNews.company_id)
            .filter(
                CompetitorNews.is_processed == True,  # noqa: E712
                CompetitorNews.published_at < since_dt,
                CompetitorNews.company_id.in_(cid_list),
            )
            .distinct()
            .all()
        )
        pre_existing_company_ids = {row[0] for row in pre_rows}

    sorted_companies = sorted(
        company_buckets.values(),
        key=lambda b: len(b["articles"]),
        reverse=True,
    )

    result: list[dict[str, Any]] = []
    cat_counts: dict[str, int] = {}

    for bucket in sorted_companies:
        if bucket["company_name"] in exclude_companies:
            continue

        articles = bucket["articles"]
        count = len(articles)
        if count == 0:
            continue
        representative = articles[0]
        event_class = _resolve_event_class(
            representative.category, bucket["categories"]
        )

        if category_mix:
            if cat_counts.get(event_class, 0) >= max_per_category:
                continue
            cat_counts[event_class] = cat_counts.get(event_class, 0) + 1

        avg_importance = (
            round(bucket["importance_sum"] / count, 2) if count else 0.0
        )

        rep_dict = {
            "id": representative.id,
            "title": representative.title,
            "summary": representative.summary,
            "url": representative.url,
            "category": representative.category,
            "published_at": (
                representative.published_at.isoformat()
                if representative.published_at
                else None
            ),
        }

        is_new_company = (
            since_date is not None
            and bucket["cid"] not in pre_existing_company_ids
        )

        result.append({
            "company_name": bucket["company_name"],
            "count_7d": count,
            "avg_importance": avg_importance,
            "representative": rep_dict,
            "categories": sorted(bucket["categories"]),
            "event_class": event_class,
            "is_new_company": is_new_company,
        })

        if len(result) >= max_companies:
            break

    logger.info(
        "company_digest: days=%d since_date=%s exclude_ids=%d "
        "exclude_companies=%d category_mix=%s companies=%d",
        days,
        since_date.isoformat() if since_date else None,
        len(exclude_ids),
        len(exclude_companies),
        category_mix,
        len(result),
    )
    return result
