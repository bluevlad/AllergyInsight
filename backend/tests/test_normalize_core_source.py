"""Tests for normalize_core_source migration script.

WBS: P1-C-002
"""
from __future__ import annotations

from datetime import datetime, timezone

import pytest
from sqlalchemy import text

from app.database.models import Paper
from app.database.normalize_core_source import normalize_core_source
from app.models.paper import PaperSource


# ───────── PaperSource enum ─────────


class TestPaperSourceEnum:
    def test_core_value_exists(self):
        assert PaperSource.CORE.value == "core"

    def test_core_is_distinct_from_manual_upload(self):
        assert PaperSource.CORE != PaperSource.MANUAL_UPLOAD
        assert PaperSource("core") == PaperSource.CORE
        assert PaperSource("manual_upload") == PaperSource.MANUAL_UPLOAD

    def test_all_existing_values_preserved(self):
        values = {s.value for s in PaperSource}
        assert {
            "pubmed",
            "semantic_scholar",
            "europe_pmc",
            "openalex",
            "clinicaltrials",
            "biorxiv_medrxiv",
            "core",
            "manual_upload",
        } <= values


# ───────── 마이그레이션 헬퍼 ─────────


def _insert_paper(db, *, source: str, source_id: str | None, title: str) -> int:
    """테스트용 paper 행 삽입. id 반환."""
    p = Paper(
        title=title,
        abstract=f"abstract for {title}",
        authors="A",
        source=source,
        source_id=source_id,
        created_at=datetime.now(timezone.utc),
    )
    db.add(p)
    db.commit()
    db.refresh(p)
    return p.id


def _get_source(db, paper_id: int) -> str:
    row = db.execute(
        text("SELECT source FROM papers WHERE id = :id"),
        {"id": paper_id},
    ).fetchone()
    return row[0] if row else None


# ───────── 정상 마이그레이션 ─────────


class TestHappyPath:
    def test_migrates_only_core_prefixed_manual_upload(self, test_db):
        # CORE 잘못된 분류 행 (보정 대상)
        core_id = _insert_paper(
            test_db,
            source="manual_upload",
            source_id="core:12345",
            title="CORE paper",
        )
        # 실제 사용자 업로드 (손대지 않아야 함)
        upload_id = _insert_paper(
            test_db,
            source="manual_upload",
            source_id="user_uploaded.pdf",
            title="User upload",
        )
        upload_no_id = _insert_paper(
            test_db,
            source="manual_upload",
            source_id=None,
            title="User upload no id",
        )
        # PubMed (관련 없음)
        pubmed_id = _insert_paper(
            test_db,
            source="pubmed",
            source_id="pmid:9999",
            title="PubMed paper",
        )

        affected = normalize_core_source(test_db)

        assert affected == 1
        assert _get_source(test_db, core_id) == "core"
        assert _get_source(test_db, upload_id) == "manual_upload"
        assert _get_source(test_db, upload_no_id) == "manual_upload"
        assert _get_source(test_db, pubmed_id) == "pubmed"

    def test_handles_multiple_core_rows(self, test_db):
        ids = [
            _insert_paper(
                test_db,
                source="manual_upload",
                source_id=f"core:{n}",
                title=f"CORE {n}",
            )
            for n in range(5)
        ]

        affected = normalize_core_source(test_db)

        assert affected == 5
        for pid in ids:
            assert _get_source(test_db, pid) == "core"

    def test_empty_db_is_noop(self, test_db):
        # papers 테이블은 있되 데이터 0건
        affected = normalize_core_source(test_db)
        assert affected == 0


# ───────── Idempotency ─────────


class TestIdempotency:
    def test_re_run_is_noop(self, test_db):
        core_id = _insert_paper(
            test_db,
            source="manual_upload",
            source_id="core:abc",
            title="CORE",
        )

        first = normalize_core_source(test_db)
        second = normalize_core_source(test_db)
        third = normalize_core_source(test_db)

        assert first == 1
        assert second == 0
        assert third == 0
        assert _get_source(test_db, core_id) == "core"

    def test_already_correct_rows_untouched(self, test_db):
        # 이미 source='core' 인 행 (즉, 이전 마이그레이션이 이미 적용됨)
        _insert_paper(
            test_db,
            source="core",
            source_id="core:existing",
            title="Existing CORE",
        )

        affected = normalize_core_source(test_db)
        assert affected == 0


# ───────── 안전성 ─────────


class TestSafety:
    def test_does_not_touch_pubmed_with_core_like_id(self, test_db):
        """source != 'manual_upload' 인 행은 source_id 가 core: prefix 여도 손대지 않음."""
        weird_id = _insert_paper(
            test_db,
            source="pubmed",
            source_id="core:notreallycore",  # 비정상 데이터지만 source 기준이 우선
            title="Weird PubMed",
        )

        normalize_core_source(test_db)
        assert _get_source(test_db, weird_id) == "pubmed"

    def test_does_not_touch_partial_match(self, test_db):
        """source_id 가 'core' 단어를 포함하지만 prefix 가 아니면 미보정."""
        partial = _insert_paper(
            test_db,
            source="manual_upload",
            source_id="user.core.pdf",  # core 포함하지만 'core:' prefix 아님
            title="Partial match",
        )

        normalize_core_source(test_db)
        assert _get_source(test_db, partial) == "manual_upload"


# ───────── CoreService 가 새 enum 을 쓰는지 ─────────


class TestCoreServiceUsesNewEnum:
    """CoreService 의 코드 자체가 PaperSource.CORE 로 교체됐는지 (회귀 방지)."""

    def test_search_empty_result_uses_core_enum(self, monkeypatch):
        """api_key 없을 때 빈 결과의 source 가 CORE 인지."""
        from app.services.core_service import CoreService

        monkeypatch.delenv("CORE_API_KEY", raising=False)
        svc = CoreService()
        result = svc.search("anything")

        assert result.source == PaperSource.CORE
        assert result.papers == []

    def test_parse_result_uses_core_enum(self):
        """API 응답 파싱 시 Paper.source 가 CORE 인지."""
        from app.services.core_service import CoreService

        svc = CoreService()
        item = {
            "id": "777",
            "title": "Sample",
            "abstract": "abs",
            "authors": [{"name": "A B"}],
            "doi": "10.1/x",
            "yearPublished": 2024,
            "publisher": "Pub",
        }
        paper = svc._parse_result(item)
        assert paper is not None
        assert paper.source == PaperSource.CORE
        assert paper.source_id == "core:777"
