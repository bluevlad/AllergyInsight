"""페르소나 적응형 뉴스레터 Phase 1 — T1~T10 + 검증 보강.

상세 설계: Claude-Opus-bluevlad/services/allergyinsight/plans/
            persona-adaptive-newsletter-phase1-design.md §8
"""
import uuid

import pytest

from app.config import settings
from app.database.models import Paper
from app.database.persona_newsletter_models import (
    NewsletterPersona,
    NewsletterTopicRequest,
)
from app.database.seed_persona_newsletter import seed_persona_newsletter
from app.services.persona_newsletter import feasibility

TEST_KEY = "test-newsletter-key"
HEADERS = {"X-Newsletter-Key": TEST_KEY}
URL = "/api/public/newsletter/topic-request"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
@pytest.fixture
def newsletter_key():
    """NEWSLETTER_API_KEY 설정 (테스트 종료 시 복원)."""
    original = settings.NEWSLETTER_API_KEY
    settings.NEWSLETTER_API_KEY = TEST_KEY
    yield TEST_KEY
    settings.NEWSLETTER_API_KEY = original


@pytest.fixture
def seeded_personas(test_db):
    """6종 페르소나 시드."""
    seed_persona_newsletter(test_db)
    return test_db


@pytest.fixture
def seeded_papers(test_db):
    """논문 섹션 검증용 최소 논문 시드 (가이드라인 1 + 연구/리뷰 3)."""
    test_db.add_all(
        [
            Paper(
                title="EAACI Guideline on Food Allergy",
                title_kr="식품알레르기 진료 가이드라인",
                year=2025,
                paper_type="guideline",
                evidence_level="A",
                is_guideline=True,
                guideline_org="EAACI",
                source="pubmed",
            ),
            Paper(
                title="Peanut oral immunotherapy trial",
                title_kr="땅콩 경구면역요법 임상연구",
                year=2025,
                paper_type="research",
                evidence_level="B",
                source="pubmed",
            ),
            Paper(
                title="Milk allergy systematic review",
                title_kr="우유 알레르기 체계적 문헌고찰",
                year=2024,
                paper_type="review",
                evidence_level="B",
                source="pubmed",
            ),
            Paper(
                title="IgE biomarker discovery study",
                title_kr="IgE 바이오마커 발굴 연구",
                year=2024,
                paper_type="research",
                evidence_level="C",
                source="pubmed",
            ),
        ]
    )
    test_db.commit()
    return test_db


def _topic_request(persona_code, request_type="select", topic=None, interests=None):
    body = {
        "request_id": str(uuid.uuid4()),
        "subscriber_ref": {
            "persona_code": persona_code,
            "interests": interests or [],
        },
        "request_type": request_type,
    }
    if topic is not None:
        body["topic"] = topic
    return body


# ---------------------------------------------------------------------------
# T1 — 페르소나 카탈로그
# ---------------------------------------------------------------------------
def test_t1_personas_catalog(client, seeded_personas, newsletter_key):
    r = client.get("/api/public/newsletter/personas", headers=HEADERS)
    assert r.status_code == 200
    data = r.json()
    personas = data["data"]["personas"]
    assert len(personas) == 6
    assert data["meta"]["count"] == 6
    # display_order 정렬 — clinician 이 1번
    assert personas[0]["code"] == "clinician"
    codes = {p["code"] for p in personas}
    assert codes == {
        "clinician", "lab", "hospital_admin", "patient", "researcher", "industry",
    }
    assert personas[0]["recommended_sections"][0] == "guideline"


# ---------------------------------------------------------------------------
# T2 — select: 페르소나별 콘텐츠 구성 상이
# ---------------------------------------------------------------------------
def test_t2_select_persona_content_differs(
    client, seeded_personas, seeded_papers, newsletter_key
):
    clin = client.post(
        URL, headers=HEADERS, json=_topic_request("clinician")
    ).json()
    pat = client.post(
        URL, headers=HEADERS, json=_topic_request("patient")
    ).json()

    assert clin["coverage"] == "covered"
    assert pat["coverage"] == "covered"

    clin_sections = {s["key"] for s in clin["data"]["sections"]}
    pat_sections = {s["key"] for s in pat["data"]["sections"]}
    # clinician 은 guideline 섹션 보유, patient 은 미보유 → 구성이 다름
    assert "guideline" in clin_sections
    assert "guideline" not in pat_sections
    assert clin_sections != pat_sections


# ---------------------------------------------------------------------------
# T3 — transform: RAG 보유 주제 → covered
# ---------------------------------------------------------------------------
def test_t3_transform_covered_via_rag(
    client, seeded_personas, newsletter_key, monkeypatch
):
    monkeypatch.setattr(
        feasibility, "_default_search",
        lambda q, n=5: [{"score": 0.82, "title": "indexed paper"}],
    )
    r = client.post(
        URL,
        headers=HEADERS,
        json=_topic_request(
            "clinician", "transform", "땅콩 알러지 경구면역요법 최신 동향"
        ),
    )
    assert r.status_code == 200
    body = r.json()
    assert body["coverage"] == "covered"
    assert body["confidence"] > 0
    assert "data" in body


# ---------------------------------------------------------------------------
# T4 — transform: 도메인 밖 → unsupported / out_of_domain
# ---------------------------------------------------------------------------
def test_t4_transform_out_of_domain(
    client, seeded_personas, newsletter_key, monkeypatch
):
    monkeypatch.setattr(feasibility, "_default_search", lambda q, n=5: [])
    r = client.post(
        URL,
        headers=HEADERS,
        json=_topic_request(
            "clinician", "transform", "부동산 시장 전망과 금리 정책 변화"
        ),
    )
    body = r.json()
    assert body["coverage"] == "unsupported"
    assert body["fallback"]["reason"] == "out_of_domain"
    assert "alternatives" in body["fallback"]


# ---------------------------------------------------------------------------
# T5 — transform: 도메인 내 미보유 → expandable (Phase 2 — 크롤 확장)
# ---------------------------------------------------------------------------
def test_t5_transform_expandable(
    client, seeded_personas, newsletter_key, monkeypatch
):
    monkeypatch.setattr(feasibility, "_default_search", lambda q, n=5: [])
    r = client.post(
        URL,
        headers=HEADERS,
        json=_topic_request(
            "researcher", "transform", "새로운 알러지 면역요법 임상시험 결과"
        ),
    )
    body = r.json()
    assert body["coverage"] == "expandable"
    assert body["expansion"]["job_id"]
    assert body["expansion"]["source"] == "pubmed"


# ---------------------------------------------------------------------------
# T6 — 멱등성: 동일 request_id 재요청
# ---------------------------------------------------------------------------
def test_t6_idempotent(client, seeded_personas, newsletter_key, test_db):
    rid = str(uuid.uuid4())
    payload = {
        "request_id": rid,
        "subscriber_ref": {"persona_code": "clinician", "interests": []},
        "request_type": "select",
    }
    r1 = client.post(URL, headers=HEADERS, json=payload)
    r2 = client.post(URL, headers=HEADERS, json=payload)
    assert r1.status_code == 200 and r2.status_code == 200
    assert r1.json()["coverage"] == r2.json()["coverage"]
    count = (
        test_db.query(NewsletterTopicRequest)
        .filter(NewsletterTopicRequest.request_id == rid)
        .count()
    )
    assert count == 1


# ---------------------------------------------------------------------------
# T7 — 인증: X-Newsletter-Key 누락/오류 → 401
# ---------------------------------------------------------------------------
def test_t7_auth_required(client, seeded_personas, newsletter_key):
    assert client.get("/api/public/newsletter/personas").status_code == 401
    bad = client.get(
        "/api/public/newsletter/personas",
        headers={"X-Newsletter-Key": "wrong-key"},
    )
    assert bad.status_code == 401


# ---------------------------------------------------------------------------
# T8 — 미등록 persona_code → patient 폴백
# ---------------------------------------------------------------------------
def test_t8_unknown_persona_fallback(client, seeded_personas, newsletter_key):
    r = client.post(
        URL, headers=HEADERS, json=_topic_request("nonexistent_role")
    )
    body = r.json()
    assert body["coverage"] == "covered"
    assert body["meta"].get("persona_fallback") is True


# ---------------------------------------------------------------------------
# T9 — patient 페르소나는 financial 카테고리 제외
# ---------------------------------------------------------------------------
def test_t9_patient_excludes_financial(seeded_personas, test_db):
    patient = (
        test_db.query(NewsletterPersona)
        .filter(NewsletterPersona.code == "patient")
        .first()
    )
    assert patient is not None
    exclude = patient.section_weights.get("exclude_categories", [])
    assert "financial" in exclude
    assert "partnership" in exclude


# ---------------------------------------------------------------------------
# T10 — 모든 요청이 로깅된다
# ---------------------------------------------------------------------------
def test_t10_all_requests_logged(
    client, seeded_personas, newsletter_key, test_db
):
    before = test_db.query(NewsletterTopicRequest).count()
    for _ in range(3):
        client.post(URL, headers=HEADERS, json=_topic_request("lab"))
    after = test_db.query(NewsletterTopicRequest).count()
    assert after - before == 3


# ---------------------------------------------------------------------------
# 검증 보강 — transform 은 topic 필수 (422)
# ---------------------------------------------------------------------------
def test_transform_requires_topic(client, seeded_personas, newsletter_key):
    r = client.post(
        URL,
        headers=HEADERS,
        json={
            "request_id": str(uuid.uuid4()),
            "subscriber_ref": {"persona_code": "clinician"},
            "request_type": "transform",
        },
    )
    assert r.status_code == 422


# ---------------------------------------------------------------------------
# 검증 보강 — 시드 멱등성 (재실행해도 6종 유지)
# ---------------------------------------------------------------------------
def test_seed_idempotent(test_db):
    seed_persona_newsletter(test_db)
    seed_persona_newsletter(test_db)
    assert test_db.query(NewsletterPersona).count() == 6
