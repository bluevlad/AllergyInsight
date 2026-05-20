"""페르소나 적응형 뉴스레터 Phase 3/4 — 생성·수요분석·운영자 제안.

G1~G5: Phase 3 (페르소나 조건부 편집 생성 + 가드레일).
E1~E7: Phase 4 (인게이지먼트·수요분석·제안·운영자 admin API).
상위 플랜: persona-adaptive-newsletter-plan.md §4 Phase 3·4.
"""
import uuid

import pytest

from app.config import settings
from app.database.models import Paper
from app.database.persona_newsletter_models import (
    EvolutionProposal,
    NewsletterContentBlock,
    NewsletterEngagement,
    NewsletterPersona,
    NewsletterTopicRequest,
)
from app.database.seed_persona_newsletter import seed_persona_newsletter
from app.services.persona_newsletter import evolution, generator

TEST_KEY = "test-newsletter-key"
HEADERS = {"X-Newsletter-Key": TEST_KEY}
TOPIC_URL = "/api/public/newsletter/topic-request"
ADMIN_BASE = "/api/admin/newsletter"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
@pytest.fixture
def newsletter_key():
    original = settings.NEWSLETTER_API_KEY
    settings.NEWSLETTER_API_KEY = TEST_KEY
    yield TEST_KEY
    settings.NEWSLETTER_API_KEY = original


@pytest.fixture
def seeded_personas(test_db):
    seed_persona_newsletter(test_db)
    return test_db


@pytest.fixture
def seeded_papers(test_db):
    test_db.add_all(
        [
            Paper(
                title="EAACI Guideline on Food Allergy",
                title_kr="식품알레르기 진료 가이드라인",
                year=2025,
                paper_type="guideline",
                evidence_level="A",
                is_guideline=True,
                source="pubmed",
            ),
            Paper(
                title="Peanut OIT trial",
                title_kr="땅콩 경구면역요법 연구",
                year=2025,
                paper_type="research",
                evidence_level="B",
                source="pubmed",
            ),
        ]
    )
    test_db.commit()
    return test_db


def _persona(test_db, code="clinician") -> NewsletterPersona:
    return (
        test_db.query(NewsletterPersona)
        .filter(NewsletterPersona.code == code)
        .first()
    )


def _add_topic_requests(test_db, *, n, topic, topic_hash, coverage, persona="clinician"):
    for i in range(n):
        test_db.add(
            NewsletterTopicRequest(
                request_id=f"req-{topic_hash}-{i}-{uuid.uuid4().hex[:6]}",
                tenant_id="allergy-insight",
                persona_code=persona,
                request_type="transform",
                topic=topic,
                topic_hash=topic_hash,
                coverage=coverage,
                served=False,
            )
        )
    test_db.commit()


# ===========================================================================
# Phase 3 — 페르소나 조건부 생성
# ===========================================================================
def test_g1_generate_editorial(test_db, seeded_personas):
    persona = _persona(test_db, "clinician")
    sections = [
        {
            "key": "papers",
            "title": "최신 논문",
            "items": [{"title": "땅콩 알러지 경구면역요법 연구"}],
        }
    ]
    result = generator.get_or_generate_editorial(
        test_db,
        persona=persona,
        sections=sections,
        generate_fn=lambda p: "이번 호는 땅콩 알러지 경구면역요법 연구를 다룹니다.",
    )
    assert result is not None
    assert result["cached"] is False
    assert "땅콩" in result["text"]
    block = (
        test_db.query(NewsletterContentBlock)
        .filter(NewsletterContentBlock.persona_code == "clinician")
        .first()
    )
    assert block is not None
    assert block.block_type == "editorial"


def test_g2_editorial_cached(test_db, seeded_personas):
    persona = _persona(test_db, "lab")
    sections = [
        {"key": "papers", "title": "논문", "items": [{"title": "검사법 연구"}]}
    ]
    calls = []

    def gen(prompt):
        calls.append(1)
        return "검사법 동향 요약."

    r1 = generator.get_or_generate_editorial(
        test_db, persona=persona, sections=sections, generate_fn=gen
    )
    r2 = generator.get_or_generate_editorial(
        test_db, persona=persona, sections=sections, generate_fn=gen
    )
    assert r1["cached"] is False
    assert r2["cached"] is True
    assert len(calls) == 1  # 두 번째는 캐시 — LLM 미호출


def test_g3_editorial_llm_unavailable(test_db, seeded_personas):
    persona = _persona(test_db, "patient")
    sections = [{"key": "papers", "title": "논문", "items": [{"title": "x"}]}]
    result = generator.get_or_generate_editorial(
        test_db, persona=persona, sections=sections, generate_fn=lambda p: None
    )
    assert result is None  # LLM 미가용 → graceful degrade


def test_g4_topic_request_includes_editorial(
    client, seeded_personas, seeded_papers, newsletter_key, monkeypatch
):
    monkeypatch.setattr(
        generator, "_llm_generate", lambda p: "이번 호 핵심: 가이드라인 갱신."
    )
    r = client.post(
        TOPIC_URL,
        headers=HEADERS,
        json={
            "request_id": str(uuid.uuid4()),
            "subscriber_ref": {"persona_code": "clinician"},
            "request_type": "select",
        },
    )
    body = r.json()
    assert body["coverage"] == "covered"
    assert "editorial" in body["data"]
    assert "가이드라인" in body["data"]["editorial"]["text"]


def test_g5_guardrail_consumer_vs_professional(test_db, seeded_personas):
    consumer = _persona(test_db, "patient")  # guardrail_profile=consumer
    professional = _persona(test_db, "clinician")  # professional
    sections = [{"key": "papers", "title": "논문", "items": [{"title": "연구"}]}]
    consumer_prompt = generator._build_prompt(consumer, sections)
    pro_prompt = generator._build_prompt(professional, sections)
    assert "의료진과 상담" in consumer_prompt  # consumer 강한 면책
    assert "의료진과 상담" not in pro_prompt


# ===========================================================================
# Phase 4 — 인게이지먼트·수요분석·제안·admin
# ===========================================================================
def test_e1_engagement_recorded(client, seeded_personas, newsletter_key, test_db):
    r = client.post(
        "/api/public/newsletter/engagement",
        headers=HEADERS,
        json={
            "events": [
                {"persona_code": "clinician", "section_type": "papers", "event": "open"},
                {
                    "persona_code": "clinician",
                    "section_type": "papers",
                    "content_ref": "p1",
                    "event": "click",
                },
            ]
        },
    )
    assert r.status_code == 200
    assert r.json()["data"]["recorded"] == 2
    assert test_db.query(NewsletterEngagement).count() == 2


def test_e2_analyze_demand(test_db):
    _add_topic_requests(
        test_db, n=3, topic="신규 알러지 약물", topic_hash="hash-drug",
        coverage="unsupported",
    )
    summary = evolution.analyze_demand(test_db, since_days=30)
    assert summary["total_requests"] == 3
    assert summary["coverage_counts"].get("unsupported") == 3
    assert summary["unsupported_clusters"][0]["count"] == 3


def test_e3_generate_proposals(test_db):
    _add_topic_requests(
        test_db, n=3, topic="알러지 진단 신기술", topic_hash="hash-diag",
        coverage="unsupported",
    )
    created = evolution.generate_proposals(
        test_db, since_days=30, llm_fn=lambda p: "신규 크롤 소스를 검토하세요."
    )
    assert len(created) >= 1
    assert created[0].proposal_type == "new_source"
    assert created[0].status == "pending"
    # 재실행 — pending 중복 스킵
    again = evolution.generate_proposals(
        test_db, since_days=30, llm_fn=lambda p: "x"
    )
    assert len(again) == 0


def test_e4_admin_list_proposals(client, test_db, admin_headers):
    test_db.add(
        EvolutionProposal(
            proposal_type="new_source",
            title="[new_source] 테스트 주제",
            recommended_action="신규 소스 검토",
            priority="high",
            status="pending",
        )
    )
    test_db.commit()
    r = client.get(f"{ADMIN_BASE}/evolution-proposals", headers=admin_headers)
    assert r.status_code == 200
    assert r.json()["meta"]["count"] >= 1


def test_e5_admin_approve_proposal(client, test_db, admin_headers):
    proposal = EvolutionProposal(
        proposal_type="keyword_expansion",
        title="[keyword_expansion] 승인 테스트",
        recommended_action="키워드 보강",
        priority="medium",
        status="pending",
    )
    test_db.add(proposal)
    test_db.commit()
    test_db.refresh(proposal)

    r = client.post(
        f"{ADMIN_BASE}/evolution-proposals/{proposal.id}/approve",
        headers=admin_headers,
        json={"note": "승인함"},
    )
    assert r.status_code == 200
    assert r.json()["data"]["status"] == "approved"

    # 이미 처리된 제안 재승인 → 409
    r2 = client.post(
        f"{ADMIN_BASE}/evolution-proposals/{proposal.id}/approve",
        headers=admin_headers,
        json={},
    )
    assert r2.status_code == 409


def test_e6_admin_auth_required(client, test_db):
    r = client.get(f"{ADMIN_BASE}/evolution-proposals")
    assert r.status_code == 401


def test_e7_admin_demand_stats(client, test_db, admin_headers):
    r = client.get(f"{ADMIN_BASE}/demand-stats", headers=admin_headers)
    assert r.status_code == 200
    assert "total_requests" in r.json()["data"]
