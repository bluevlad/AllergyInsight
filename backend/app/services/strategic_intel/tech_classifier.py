"""기술 분류기 — 논문/뉴스를 알러지 IVD 진단 키트/시약 기술 카테고리로 라벨링

LLM 기반 다중 라벨 분류 (multi-label classification).
범위: 알러지 진단 키트/시약 분야 IVD 기술만 (10개 카테고리, v1.1)

Strategic Intel 모듈 전용. 외부 사용자 노출 금지.
"""
from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass
from typing import Iterable

from sqlalchemy.orm import Session

from ...database.strategic_intel_models import (
    NewsTechLink,
    PaperTechLink,
    TechCategory,
)
from ..ollama_service import OllamaService

logger = logging.getLogger(__name__)

CLASSIFIER_VERSION = "v1-2026-05"
DEFAULT_MIN_CONFIDENCE = 0.50  # 이하 점수는 라벨 저장 안 함 (가설 트리거와 동일 임계값으로 통일)

# 백필 스크립트에서 뉴스 필터링용 — Strategic Intel 추적 4사
ALL_COMPANIES_FOR_NEWS_FILTER = ("sugentech", "greencross", "bodytech", "madx")


@dataclass
class TechLabel:
    tech_id: str
    confidence: float


# ---------------------------------------------------------------------------
# 프롬프트
# ---------------------------------------------------------------------------


def _format_taxonomy_for_prompt(categories: list[TechCategory]) -> str:
    """카테고리 목록을 LLM 프롬프트용 컴팩트 텍스트로 직렬화"""
    lines = []
    for c in categories:
        keywords = ", ".join((c.keywords_en or [])[:6])
        lines.append(
            f"- id={c.id} | {c.name_en} ({c.name_kr}) | {c.description or ''} | keywords: {keywords}"
        )
    return "\n".join(lines)


def build_classification_prompt(
    title: str,
    body: str,
    categories: list[TechCategory],
    *,
    is_paper: bool,
) -> str:
    """LLM 분류 프롬프트 (multi-label, JSON 출력)"""
    source_label = "academic paper" if is_paper else "news article"
    taxonomy = _format_taxonomy_for_prompt(categories)
    body_snippet = (body or "")[:2400]

    return f"""You are an expert classifier for **allergy IVD diagnostic kit/reagent** technology news and papers.

The taxonomy below contains the ONLY allowed category IDs. Scope: in-vitro allergy diagnostic
kits and reagents. Items unrelated to allergy IVD kits/reagents (drug therapy, immunotherapy,
clinical guidelines without diagnostic implications, pure epidemiology) MUST return an empty list.

TAXONOMY:
{taxonomy}

INPUT ({source_label}):
TITLE: {title}
TEXT: {body_snippet}

INSTRUCTIONS:
1. Read the title + text carefully.
2. Decide which of the taxonomy IDs are *substantively* discussed (not just mentioned).
3. For each match, give a confidence 0.0~1.0 reflecting how central that category is.
4. If nothing fits, return {{"labels": []}}.
5. Output STRICT JSON only — no prose, no markdown fencing.

OUTPUT FORMAT:
{{"labels": [{{"id": "<category_id>", "confidence": <float>}}]}}
"""


# ---------------------------------------------------------------------------
# 분류기
# ---------------------------------------------------------------------------


class TechClassifier:
    """알러지 IVD 진단 키트/시약 기술 카테고리 분류기 (LLM 기반)"""

    # 외부에서 참조 가능한 분류기 버전 (idempotent 재처리 판단용)
    CLASSIFIER_VERSION_USED = CLASSIFIER_VERSION

    def __init__(
        self,
        db: Session,
        llm: OllamaService | None = None,
        min_confidence: float = DEFAULT_MIN_CONFIDENCE,
    ):
        self.db = db
        self.llm = llm or OllamaService()
        self.min_confidence = min_confidence
        self._categories_cache: list[TechCategory] | None = None

    def _categories(self) -> list[TechCategory]:
        if self._categories_cache is None:
            self._categories_cache = (
                self.db.query(TechCategory)
                .filter(TechCategory.is_active.is_(True))
                .order_by(TechCategory.sort_order)
                .all()
            )
        return self._categories_cache

    def _valid_ids(self) -> set[str]:
        return {c.id for c in self._categories()}

    def classify_text(
        self,
        title: str,
        body: str,
        *,
        is_paper: bool,
    ) -> list[TechLabel]:
        """단일 텍스트 → 라벨 목록"""
        categories = self._categories()
        prompt = build_classification_prompt(title, body, categories, is_paper=is_paper)
        raw = self.llm._chat(prompt, max_tokens=400, provider="news")
        if not raw:
            logger.warning("LLM returned empty for: %s", title[:80])
            return []
        return self._parse_response(raw)

    def _parse_response(self, raw: str) -> list[TechLabel]:
        """LLM 응답 JSON 파싱 + 화이트리스트 검증"""
        valid_ids = self._valid_ids()
        cleaned = self._strip_json_fences(raw)
        try:
            data = json.loads(cleaned)
        except json.JSONDecodeError:
            # JSON 추출 시도
            match = re.search(r"\{.*\}", cleaned, re.DOTALL)
            if not match:
                logger.warning("Failed to parse LLM response: %s", raw[:200])
                return []
            try:
                data = json.loads(match.group(0))
            except json.JSONDecodeError:
                logger.warning("Failed to parse LLM JSON: %s", raw[:200])
                return []

        labels_raw = data.get("labels") if isinstance(data, dict) else None
        if not isinstance(labels_raw, list):
            return []

        # tech_id 단위 dedupe — LLM이 동일 카테고리를 다중 반환할 경우 최고 신뢰도만 채택
        best: dict[str, float] = {}
        for entry in labels_raw:
            if not isinstance(entry, dict):
                continue
            tid = entry.get("id")
            try:
                conf = float(entry.get("confidence", 0))
            except (TypeError, ValueError):
                continue
            if not isinstance(tid, str) or tid not in valid_ids:
                continue
            conf = max(0.0, min(1.0, conf))
            if conf < self.min_confidence:
                continue
            if conf > best.get(tid, 0.0):
                best[tid] = conf
        return [TechLabel(tech_id=tid, confidence=c) for tid, c in best.items()]

    @staticmethod
    def _strip_json_fences(s: str) -> str:
        s = s.strip()
        if s.startswith("```"):
            s = re.sub(r"^```(json)?\s*", "", s)
            s = re.sub(r"\s*```$", "", s)
        return s.strip()

    # ------------------------------------------------------------------
    # 영속화 (paper/news 단위)
    # ------------------------------------------------------------------

    def classify_and_save_paper(self, paper) -> list[TechLabel]:
        """Paper 객체 → 라벨링 후 paper_tech_links 저장 (idempotent + 세션 손상 가드)"""
        body = paper.abstract or paper.abstract_kr or ""
        labels = self.classify_text(paper.title, body, is_paper=True)
        try:
            self._upsert_paper_links(paper.id, labels)
        except Exception as e:
            self.db.rollback()
            logger.warning("upsert paper_tech_links failed (paper_id=%s): %s", paper.id, e)
            return []
        return labels

    def classify_and_save_news(self, news) -> list[TechLabel]:
        """CompetitorNews 객체 → 라벨링 후 news_tech_links 저장 (idempotent + 세션 손상 가드)"""
        body = news.description or news.summary or ""
        labels = self.classify_text(news.title, body, is_paper=False)
        try:
            self._upsert_news_links(news.id, labels)
        except Exception as e:
            self.db.rollback()
            logger.warning("upsert news_tech_links failed (news_id=%s): %s", news.id, e)
            return []
        return labels

    def _upsert_paper_links(self, paper_id: int, labels: Iterable[TechLabel]) -> None:
        for lab in labels:
            existing = (
                self.db.query(PaperTechLink)
                .filter(
                    PaperTechLink.paper_id == paper_id,
                    PaperTechLink.tech_category_id == lab.tech_id,
                )
                .first()
            )
            if existing:
                existing.confidence = lab.confidence
                existing.classifier_version = CLASSIFIER_VERSION
            else:
                self.db.add(
                    PaperTechLink(
                        paper_id=paper_id,
                        tech_category_id=lab.tech_id,
                        confidence=lab.confidence,
                        classifier_version=CLASSIFIER_VERSION,
                    )
                )
        self.db.commit()

    def _upsert_news_links(self, news_id: int, labels: Iterable[TechLabel]) -> None:
        for lab in labels:
            existing = (
                self.db.query(NewsTechLink)
                .filter(
                    NewsTechLink.news_id == news_id,
                    NewsTechLink.tech_category_id == lab.tech_id,
                )
                .first()
            )
            if existing:
                existing.confidence = lab.confidence
                existing.classifier_version = CLASSIFIER_VERSION
            else:
                self.db.add(
                    NewsTechLink(
                        news_id=news_id,
                        tech_category_id=lab.tech_id,
                        confidence=lab.confidence,
                        classifier_version=CLASSIFIER_VERSION,
                    )
                )
        self.db.commit()
