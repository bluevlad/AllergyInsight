"""콘텐츠 선택 조립 — Phase 1 (선택 모드, LLM 생성 없음).

페르소나 section_weights 에 따라 기존 데이터 소스(headlines · company-digest ·
papers · news)를 선택·정렬·필터링한다. 페르소나 간 콘텐츠 차이는 전적으로
가중치 행렬에서 발생한다. LLM 기반 생성은 Phase 3.
"""
from __future__ import annotations

import logging
from typing import Any, Optional

from sqlalchemy.orm import Session

from ...database.analytics_models import NewsAllergenLink
from ...database.competitor_models import CompetitorNews
from ...database.models import Paper
from ..company_digest_service import build_company_digest
from ..headline_selection_service import select_top_headlines

logger = logging.getLogger(__name__)

_SECTION_TITLES = {
    "headlines": "오늘의 핵심 헤드라인",
    "industry": "산업·기업 동향",
    "papers": "최신 논문",
    "guideline": "진료 가이드라인",
    "treatment_news": "치료·생활관리 뉴스",
    "diagnosis_news": "진단·검사 뉴스",
    "regulation_news": "규제·정책 뉴스",
}

# 뉴스 섹션 key → NewsAllergenLink.content_category 매핑
_NEWS_CONTENT_CATEGORIES = {
    "treatment_news": ("treatment", "epidemiology"),
    "diagnosis_news": ("diagnosis_method",),
    "regulation_news": ("regulation",),
}

_DEFAULT_DIGEST_DAYS = 7
_EVIDENCE_SCORE = {"A": 1.0, "B": 0.8, "C": 0.6, "D": 0.4}


def _trim(text: Optional[str], limit: int = 220) -> Optional[str]:
    """본문 미리보기용 절삭."""
    if not text:
        return None
    cleaned = text.strip()
    if len(cleaned) <= limit:
        return cleaned
    return cleaned[:limit].rstrip() + "…"


def _evidence_score(evidence_level: Optional[str]) -> float:
    """근거수준(GRADE) → 기본 점수. 미지정은 중간값."""
    if not evidence_level:
        return 0.5
    return _EVIDENCE_SCORE.get(evidence_level.strip().upper(), 0.5)


def _fetch_headlines(db: Session, max_items: int) -> list[dict[str, Any]]:
    headlines, _excluded, _days = select_top_headlines(
        db,
        limit=max_items,
        one_per_company=True,
        days=1,
        fallback_days=[1, 3, 7],
    )
    return [
        {
            "id": h.get("id"),
            "title": h.get("title"),
            "summary": h.get("summary"),
            "category": h.get("category"),
            "company_name": h.get("company_name"),
            "published_at": h.get("published_at"),
            "url": h.get("url"),
            "_score": float(h.get("importance_score") or 0.0),
        }
        for h in headlines
    ]


def _fetch_industry(db: Session, max_items: int) -> list[dict[str, Any]]:
    companies = build_company_digest(
        db, days=_DEFAULT_DIGEST_DAYS, max_companies=max_items
    )
    items: list[dict[str, Any]] = []
    for c in companies:
        rep = c.get("representative") or {}
        items.append(
            {
                "company_name": c.get("company_name"),
                "count_7d": c.get("count_7d"),
                "title": rep.get("title"),
                "summary": rep.get("summary"),
                "url": rep.get("url"),
                "category": c.get("event_class") or rep.get("category"),
                "published_at": rep.get("published_at"),
                "is_new_company": c.get("is_new_company"),
                "_score": float(c.get("avg_importance") or 0.0),
            }
        )
    return items


def _fetch_papers(
    db: Session, persona_code: str, section_key: str, max_items: int
) -> list[dict[str, Any]]:
    query = db.query(Paper)
    if section_key == "guideline":
        query = query.filter(Paper.is_guideline.is_(True))
    # 최신순 — year, id (NULLS 처리 차이를 피하기 위해 nullslast 미사용)
    rows = (
        query.order_by(Paper.year.desc(), Paper.id.desc())
        .limit(max_items * 3)
        .all()
    )
    is_researcher = persona_code == "researcher"
    items: list[dict[str, Any]] = []
    for p in rows:
        score = _evidence_score(p.evidence_level)
        if is_researcher:
            if (p.paper_type or "") in ("meta_analysis", "review"):
                score += 0.2
            if (p.source or "") == "biorxiv_medrxiv":
                score += 0.2
        items.append(
            {
                "id": p.id,
                "title": p.title_kr or p.title,
                "summary": p.clinical_implication or p.abstract_kr or _trim(p.abstract),
                "year": p.year,
                "evidence_level": p.evidence_level,
                "paper_type": p.paper_type,
                "is_guideline": bool(p.is_guideline),
                "guideline_org": p.guideline_org,
                "url": p.url or (f"https://doi.org/{p.doi}" if p.doi else None),
                "category": "research",
                "_score": score,
            }
        )
    return items


def _fetch_news(
    db: Session, content_categories: tuple[str, ...], max_items: int
) -> list[dict[str, Any]]:
    rows = (
        db.query(CompetitorNews, NewsAllergenLink)
        .join(NewsAllergenLink, NewsAllergenLink.news_id == CompetitorNews.id)
        .filter(NewsAllergenLink.content_category.in_(content_categories))
        .filter(CompetitorNews.is_relevant.is_(True))
        .filter(CompetitorNews.is_duplicate.is_(False))
        .order_by(CompetitorNews.importance_score.desc(), CompetitorNews.id.desc())
        .limit(max_items * 4)
        .all()
    )
    seen: set[int] = set()
    items: list[dict[str, Any]] = []
    for news, link in rows:
        if news.id in seen:
            continue
        seen.add(news.id)
        items.append(
            {
                "id": news.id,
                "title": news.title,
                "summary": news.summary or _trim(news.description),
                "category": news.category,
                "content_category": link.content_category,
                "allergen_code": link.allergen_code,
                "published_at": (
                    news.published_at.isoformat() if news.published_at else None
                ),
                "url": news.url,
                "_score": float(news.importance_score or news.relevance_score or 0.0),
            }
        )
    return items


def _fetch_section(
    db: Session, key: str, persona_code: str, max_items: int
) -> list[dict[str, Any]]:
    if key == "headlines":
        return _fetch_headlines(db, max_items)
    if key == "industry":
        return _fetch_industry(db, max_items)
    if key in ("papers", "guideline"):
        return _fetch_papers(db, persona_code, key, max_items)
    if key in _NEWS_CONTENT_CATEGORIES:
        return _fetch_news(db, _NEWS_CONTENT_CATEGORIES[key], max_items)
    logger.warning("알 수 없는 섹션 key: %s", key)
    return []


def _drop_excluded(
    items: list[dict[str, Any]], exclude: set[str]
) -> list[dict[str, Any]]:
    if not exclude:
        return items
    return [
        it
        for it in items
        if it.get("category") not in exclude
        and it.get("content_category") not in exclude
    ]


def _rerank(
    items: list[dict[str, Any]],
    category_boost: dict[str, float],
    interests: list[str],
) -> list[dict[str, Any]]:
    """category_boost + 관심 알러젠으로 항목 점수를 가산하고 내림차순 정렬."""
    for it in items:
        boost = 0.0
        for field in ("category", "content_category"):
            cat = it.get(field)
            if cat and cat in category_boost:
                boost += float(category_boost[cat])
        allergen = it.get("allergen_code")
        if interests and allergen and str(allergen).lower() in interests:
            boost += 0.15
        it["_score"] = float(it.get("_score") or 0.0) + boost
    return sorted(items, key=lambda x: -float(x.get("_score") or 0.0))


def compose(
    db: Session,
    *,
    persona: Any,
    interests: Optional[list[str]] = None,
) -> list[dict[str, Any]]:
    """페르소나 가중치에 따라 섹션을 조립한다 (선택 모드).

    Args:
        persona: NewsletterPersona ORM 인스턴스.
        interests: 관심 알러젠 코드 목록 (뉴스 리랭킹용).

    Returns:
        [{key, title, items}] — weight 내림차순 표시 순서.
    """
    weights = persona.section_weights or {}
    sections_spec = weights.get("sections", []) or []
    category_boost = weights.get("category_boost", {}) or {}
    exclude = set(weights.get("exclude_categories", []) or [])
    norm_interests = [str(i).lower() for i in (interests or []) if i]
    persona_code = getattr(persona, "code", "") or ""

    out: list[dict[str, Any]] = []
    for spec in sorted(
        sections_spec, key=lambda s: -float(s.get("weight", 0) or 0)
    ):
        key = spec.get("key")
        if not key:
            continue
        max_items = int(spec.get("max_items", 5) or 5)
        try:
            items = _fetch_section(db, key, persona_code, max_items)
        except Exception as e:  # noqa: BLE001
            logger.warning("섹션 조립 실패 (%s) — 건너뜀: %s", key, e)
            continue
        items = _drop_excluded(items, exclude)
        items = _rerank(items, category_boost, norm_interests)[:max_items]
        for it in items:
            it.pop("_score", None)  # 내부 점수는 응답에서 제거
        if items:
            out.append(
                {
                    "key": key,
                    "title": _SECTION_TITLES.get(key, key),
                    "items": items,
                }
            )
    return out


def suggest_alternatives(db: Session, max_items: int = 3) -> list[dict[str, str]]:
    """unsupported 응답용 대체 주제 제안 — 최근 핵심 헤드라인 기반."""
    try:
        headlines, _excluded, _days = select_top_headlines(
            db,
            limit=max_items,
            one_per_company=True,
            days=7,
            fallback_days=[7, 14],
        )
    except Exception as e:  # noqa: BLE001
        logger.warning("대체 주제 제안 실패: %s", e)
        return []
    out: list[dict[str, str]] = []
    for h in headlines:
        title = h.get("title")
        if title:
            out.append({"topic": title, "label": title})
    return out
