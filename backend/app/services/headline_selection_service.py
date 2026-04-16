"""뉴스레터 헤드라인 선정 서비스

오늘의 핵심 헤드라인 Top N 을 겹침 없이 선정한다.

선정 규칙 (NEWSLETTER_REDESIGN_SPEC § 2.1 / § 6.1):
1. importance_score DESC 정렬
2. 1기업 1헤드라인 — 이미 선정된 company_id 는 스킵
3. 제목 MinHash 유사도 ≥ 0.90 이면 스킵
4. URL canonical 해시가 선정 리스트에 존재하면 스킵
5. 상위 N건. 부족 시 남은 슬롯 비움 (임의 채움 금지)
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import func
from sqlalchemy.orm import Session

from ..database.competitor_models import CompetitorCompany, CompetitorNews
from ..utils.dedup_helpers import (
    canonical_url_hash,
    jaccard_from_minhash,
    title_minhash,
)
from ..utils.timezone import utc_now

logger = logging.getLogger(__name__)

MINHASH_THRESHOLD = 0.90


def _importance_level(score: float | None) -> str:
    if score is None:
        return "저"
    if score >= 0.7:
        return "고"
    if score >= 0.4:
        return "중"
    return "저"


def _category_color(category: str | None) -> str:
    _map = {
        "regulatory": "#2e7d32",
        "product": "#1565c0",
        "financial": "#ef6c00",
        "partnership": "#6a1b9a",
        "technology": "#00838f",
        "competitor": "#c62828",
        "market": "#ef6c00",
        "general": "#757575",
    }
    return _map.get(category or "general", "#757575")


def select_top_headlines(
    session: Session,
    *,
    limit: int = 5,
    one_per_company: bool = True,
    days: int = 1,
) -> tuple[list[dict[str, Any]], set[int]]:
    """핵심 헤드라인 선정.

    Args:
        session: SQLAlchemy session.
        limit: 최대 선정 건수.
        one_per_company: 1기업 1헤드라인 규칙 적용 여부.
        days: 오늘로부터 며칠 이내 기사를 대상으로 할지.

    Returns:
        (headlines_list, excluded_id_set)
        - headlines_list: 선정된 기사 dict 리스트 (§ 3.2.1 응답 스키마)
        - excluded_id_set: 선정된 기사 id 집합 (company-digest 호출 시 전달)
    """
    since = utc_now() - timedelta(days=days)

    pool = (
        session.query(CompetitorNews, CompetitorCompany)
        .join(CompetitorCompany, CompetitorNews.company_id == CompetitorCompany.id)
        .filter(
            CompetitorNews.is_processed == True,  # noqa: E712
            CompetitorNews.is_relevant == True,    # noqa: E712
            CompetitorNews.is_duplicate == False,  # noqa: E712
            CompetitorNews.published_at >= since,
            CompetitorNews.importance_score.isnot(None),
        )
        .order_by(CompetitorNews.importance_score.desc())
        .limit(500)
        .all()
    )

    pool_size = len(pool)
    selected: list[dict[str, Any]] = []
    excluded_ids: set[int] = set()
    seen_companies: set[int] = set()
    seen_url_hashes: set[str] = set()
    seen_minhashes: list[list[int]] = []

    for news, company in pool:
        if len(selected) >= limit:
            break

        if one_per_company and news.company_id in seen_companies:
            continue

        url_hash = canonical_url_hash(news.url)
        if url_hash in seen_url_hashes:
            continue

        mh = title_minhash(news.title)
        if any(
            jaccard_from_minhash(mh, prev) >= MINHASH_THRESHOLD
            for prev in seen_minhashes
        ):
            continue

        headline = {
            "id": news.id,
            "title": news.title,
            "summary": news.summary,
            "category": news.category or "general",
            "category_color": _category_color(news.category),
            "company_name": company.name_kr,
            "importance_score": round(news.importance_score, 2),
            "importance_level": _importance_level(news.importance_score),
            "published_at": (
                news.published_at.isoformat() if news.published_at else None
            ),
            "source": news.source,
            "url": news.url,
        }
        selected.append(headline)
        excluded_ids.add(news.id)
        seen_companies.add(news.company_id)
        seen_url_hashes.add(url_hash)
        seen_minhashes.append(mh)

    logger.info(
        "headline_selection: pool=%d selected=%d", pool_size, len(selected)
    )
    return selected, excluded_ids
