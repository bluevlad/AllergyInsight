"""ClinicalImplicationService + OllamaService.extract_clinical_implication 단위 테스트.

LLM 호출은 monkeypatch 로 mock 한다 — 실제 LLM 호출 없음.

핵심 검증:
- abstract 가 너무 짧으면 None
- 정상 응답: 임상 함의 1~2문장 반환, 잡음 제거
- 빈 응답 / LLM 예외 → None, 240자 트림
- 단일 추출 + 배치: skip_extracted, limit, errors 카운트
"""
from __future__ import annotations

from unittest.mock import patch

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.database.connection import Base
from app.database.models import Paper
from app.services.ollama_service import OllamaService
from app.services.clinical_implication_service import (
    ClinicalImplicationService,
)


@pytest.fixture
def session():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    _Session = sessionmaker(bind=engine)
    sess = _Session()
    yield sess
    sess.close()


def _make_paper(
    session: Session,
    title: str = "Sample paper",
    abstract: str = "x" * 400,
    implication: str | None = None,
) -> Paper:
    p = Paper(
        title=title,
        abstract=abstract,
        clinical_implication=implication,
        paper_type="research",
        is_verified=True,
    )
    session.add(p)
    session.commit()
    return p


# ────────────────────────────────────────────────────────────────────
# OllamaService.extract_clinical_implication — 추출 정책
# ────────────────────────────────────────────────────────────────────


def test_extract_skips_short_abstract():
    svc = OllamaService.__new__(OllamaService)
    # _chat 호출되면 안 됨 — short-circuit
    with patch.object(OllamaService, "_chat", side_effect=AssertionError("LLM should not be called")):
        result = svc.extract_clinical_implication("title", "too short " * 5)
    assert result is None


def test_extract_returns_none_if_abstract_empty():
    svc = OllamaService.__new__(OllamaService)
    assert svc.extract_clinical_implication("t", "") is None
    assert svc.extract_clinical_implication("t", None) is None


def test_extract_strips_noise_and_returns_text():
    svc = OllamaService.__new__(OllamaService)
    abs_long = "background. " * 30  # 360+ chars
    raw = '  **임상 함의:** "땅콩 OIT 가 IgE 매개 알러지 환자에서 증상 점수 30% 감소를 보였다."  '
    with patch.object(OllamaService, "_chat", return_value=raw):
        result = svc.extract_clinical_implication("Peanut OIT", abs_long)
    assert result is not None
    assert "임상 함의" not in result  # 머리말 제거
    assert "**" not in result          # markdown 제거
    assert result.startswith("땅콩 OIT")
    assert result.endswith("감소를 보였다.")


def test_extract_truncates_long_output():
    svc = OllamaService.__new__(OllamaService)
    abs_long = "x" * 400
    long_response = "긴 임상 함의 문장. " * 50  # 매우 긴 응답
    with patch.object(OllamaService, "_chat", return_value=long_response):
        result = svc.extract_clinical_implication("t", abs_long)
    assert result is not None
    # 240자 + ellipsis 정도
    assert len(result) <= 245
    assert result.endswith("…")


def test_extract_returns_none_on_empty_llm_response():
    svc = OllamaService.__new__(OllamaService)
    with patch.object(OllamaService, "_chat", return_value=""):
        assert svc.extract_clinical_implication("t", "x" * 400) is None
    with patch.object(OllamaService, "_chat", return_value=None):
        assert svc.extract_clinical_implication("t", "x" * 400) is None


def test_extract_returns_none_on_llm_exception():
    svc = OllamaService.__new__(OllamaService)
    with patch.object(OllamaService, "_chat", side_effect=RuntimeError("api down")):
        assert svc.extract_clinical_implication("t", "x" * 400) is None


def test_extract_returns_none_when_only_noise():
    """LLM 응답이 모두 잡음(머리말+따옴표만)이면 None."""
    svc = OllamaService.__new__(OllamaService)
    with patch.object(OllamaService, "_chat", return_value='  "임상 함의:" '):
        assert svc.extract_clinical_implication("t", "x" * 400) is None


# ────────────────────────────────────────────────────────────────────
# ClinicalImplicationService — DB 영속화 + 배치
# ────────────────────────────────────────────────────────────────────


def test_extract_for_paper_persists(session: Session):
    p = _make_paper(session, abstract="abstract " * 60)  # 540+ chars
    svc = ClinicalImplicationService()
    fake = "땅콩 OIT 가 IgE 매개 알러지 환자에서 증상 30% 감소."
    with patch(
        "app.services.clinical_implication_service.get_ollama_service"
    ) as g:
        g.return_value.extract_clinical_implication.return_value = fake
        result = svc.extract_for_paper(session, p.id)
    assert result == fake
    session.refresh(p)
    assert p.clinical_implication == fake


def test_extract_for_paper_no_abstract_returns_none(session: Session):
    p = Paper(title="t", abstract=None, paper_type="research", is_verified=True)
    session.add(p)
    session.commit()
    svc = ClinicalImplicationService()
    assert svc.extract_for_paper(session, p.id) is None
    session.refresh(p)
    assert p.clinical_implication is None


def test_extract_for_paper_missing_returns_none(session: Session):
    svc = ClinicalImplicationService()
    assert svc.extract_for_paper(session, 99999) is None


def test_batch_extract_skips_already_extracted(session: Session):
    _make_paper(session, title="A", abstract="abs " * 60, implication="기존 함의")
    p2 = _make_paper(session, title="B", abstract="abs " * 60)
    svc = ClinicalImplicationService()
    with patch(
        "app.services.clinical_implication_service.get_ollama_service"
    ) as g:
        g.return_value.extract_clinical_implication.return_value = "신규 함의"
        stats = svc.extract_from_papers(session, limit=10, skip_extracted=True)
    assert stats["processed"] == 1   # B 만
    assert stats["extracted"] == 1
    session.refresh(p2)
    assert p2.clinical_implication == "신규 함의"


def test_batch_extract_respects_limit(session: Session):
    for i in range(5):
        _make_paper(session, title=f"P{i}", abstract="abs " * 60)
    svc = ClinicalImplicationService()
    with patch(
        "app.services.clinical_implication_service.get_ollama_service"
    ) as g:
        g.return_value.extract_clinical_implication.return_value = "함의"
        stats = svc.extract_from_papers(session, limit=2, skip_extracted=True)
    assert stats["processed"] == 2
    assert stats["extracted"] == 2


def test_batch_extract_counts_skipped_when_llm_returns_none(session: Session):
    _make_paper(session, title="A", abstract="abs " * 60)
    _make_paper(session, title="B", abstract="abs " * 60)
    svc = ClinicalImplicationService()
    # 첫 호출 None, 두번째 호출 "ok" — alternating
    with patch(
        "app.services.clinical_implication_service.get_ollama_service"
    ) as g:
        g.return_value.extract_clinical_implication.side_effect = [None, "ok"]
        stats = svc.extract_from_papers(session, limit=10, skip_extracted=True)
    assert stats["processed"] == 2
    assert stats["extracted"] == 1
    assert stats["skipped"] == 1
    assert stats["errors"] == 0


def test_batch_extract_counts_errors(session: Session):
    _make_paper(session, title="A", abstract="abs " * 60)
    svc = ClinicalImplicationService()
    with patch(
        "app.services.clinical_implication_service.get_ollama_service"
    ) as g:
        g.return_value.extract_clinical_implication.side_effect = RuntimeError("x")
        stats = svc.extract_from_papers(session, limit=10, skip_extracted=True)
    assert stats["errors"] == 1
    assert stats["extracted"] == 0


def test_batch_extract_no_papers_returns_zero(session: Session):
    svc = ClinicalImplicationService()
    stats = svc.extract_from_papers(session, limit=10)
    assert stats == {"processed": 0, "extracted": 0, "skipped": 0, "errors": 0}


# ────────────────────────────────────────────────────────────────────
# Throttle (interval_ms) — 무료 티어 RPM 한도 회피
# ────────────────────────────────────────────────────────────────────


def test_batch_throttle_sleeps_between_calls(session: Session):
    """interval_ms > 0 → 첫 호출 외에는 매 호출 전에 sleep."""
    for i in range(3):
        _make_paper(session, title=f"P{i}", abstract="abs " * 60)
    svc = ClinicalImplicationService()
    sleep_calls: list[float] = []
    with patch(
        "app.services.clinical_implication_service.time.sleep",
        side_effect=lambda s: sleep_calls.append(s),
    ), patch(
        "app.services.clinical_implication_service.get_ollama_service"
    ) as g:
        g.return_value.extract_clinical_implication.return_value = "ok"
        stats = svc.extract_from_papers(
            session, limit=3, skip_extracted=True, interval_ms=200
        )
    # 3건 처리 → 사이 sleep 2회 (마지막 직후엔 sleep 안 함)
    assert stats["processed"] == 3
    assert stats["extracted"] == 3
    assert len(sleep_calls) == 2
    assert all(abs(s - 0.2) < 1e-9 for s in sleep_calls)


def test_batch_no_throttle_when_interval_zero(session: Session):
    """interval_ms=0 (기본) → time.sleep 호출 없음."""
    for i in range(2):
        _make_paper(session, title=f"P{i}", abstract="abs " * 60)
    svc = ClinicalImplicationService()
    with patch(
        "app.services.clinical_implication_service.time.sleep"
    ) as mock_sleep, patch(
        "app.services.clinical_implication_service.get_ollama_service"
    ) as g:
        g.return_value.extract_clinical_implication.return_value = "ok"
        svc.extract_from_papers(
            session, limit=2, skip_extracted=True, interval_ms=0
        )
    assert mock_sleep.call_count == 0


def test_batch_throttle_commits_per_iteration(session: Session):
    """interval_ms > 0 모드: 매 iteration commit — 중간 abort 시 작업 보존.

    order_by(year desc, id desc) 라 처리 순서는 (p2 → p1) 이지만 본 테스트는
    순서와 무관하게 *두 행 모두* 커밋된 결과가 DB 에 남았는지만 검증한다.
    LLM mock 은 호출별로 다른 문자열을 반환해, 두 행이 같은 값으로 덮여쓰지
    않았음(= 별개 호출 + 별개 commit) 을 함께 확인한다.
    """
    p1 = _make_paper(session, title="A", abstract="abs " * 60)
    p2 = _make_paper(session, title="B", abstract="abs " * 60)
    p1_id, p2_id = p1.id, p2.id

    svc = ClinicalImplicationService()
    call_count = [0]

    def fake_extract(*args, **kwargs):
        call_count[0] += 1
        return f"impl-{call_count[0]}"

    with patch(
        "app.services.clinical_implication_service.time.sleep"
    ), patch(
        "app.services.clinical_implication_service.get_ollama_service"
    ) as g:
        g.return_value.extract_clinical_implication.side_effect = fake_extract
        svc.extract_from_papers(
            session, limit=2, skip_extracted=True, interval_ms=100
        )

    # 별도 read 로 영속화 확인 (commit 안 되었으면 None 일 것)
    p1 = session.query(Paper).filter(Paper.id == p1_id).one()
    p2 = session.query(Paper).filter(Paper.id == p2_id).one()
    assert p1.clinical_implication is not None
    assert p2.clinical_implication is not None
    # 두 행이 각자 다른 mock 응답 — 별개 호출 + 별개 commit
    assert p1.clinical_implication != p2.clinical_implication
    assert {p1.clinical_implication, p2.clinical_implication} == {
        "impl-1",
        "impl-2",
    }
