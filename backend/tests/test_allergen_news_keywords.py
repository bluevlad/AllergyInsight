"""Tests for allergen news keyword builder.

allergen-trend-followup-plan §2.
"""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from app.services.allergen_news_keywords import (
    _format_search_keywords,
    build_allergen_search_keywords,
)


class TestFormatSearchKeywords:
    def test_strips_korean_parentheses(self):
        kws = _format_search_keywords("집먼지진드기(Dp)", "D. pteronyssinus")
        assert kws[0] == "집먼지진드기 알레르기"

    def test_lowercases_english(self):
        kws = _format_search_keywords("땅콩", "Peanut")
        assert "peanut allergy" in kws

    def test_returns_both_locales(self):
        kws = _format_search_keywords("우유", "Milk")
        assert len(kws) == 2
        assert "우유 알레르기" in kws
        assert "milk allergy" in kws


class TestBuildAllergenSearchKeywords:
    def test_without_db_uses_fallback(self):
        result = build_allergen_search_keywords(db=None, allergen_codes=["peanut", "milk"])
        assert "peanut" in result
        assert "땅콩 알레르기" in result["peanut"]
        assert "peanut allergy" in result["peanut"]
        assert "우유 알레르기" in result["milk"]

    def test_unknown_code_dropped(self):
        result = build_allergen_search_keywords(
            db=None, allergen_codes=["__no_such_allergen__"],
        )
        assert "__no_such_allergen__" not in result

    def test_db_lookup_takes_precedence(self):
        """AllergenMaster 행이 있으면 fallback 보다 우선 사용."""
        from app.database.allergen_models import AllergenMaster

        mock_row = AllergenMaster(
            code="f13",
            name_kr="땅콩(생)",
            name_en="Arachis hypogaea, Peanut",
            category="seed_nut",
            type="food",
            is_active=True,
        )
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.all.return_value = [mock_row]

        result = build_allergen_search_keywords(
            db=mock_db, allergen_codes=["peanut"],
        )
        # name_kr 의 괄호가 stripped 되어야 함
        assert any("땅콩" in kw for kw in result["peanut"])
        # name_en 의 콤마 앞 첫 표현만 사용
        assert any("arachis hypogaea" in kw.lower() for kw in result["peanut"])
