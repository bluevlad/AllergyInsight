"""페르소나 적응형 뉴스레터 Phase 2 — 크롤 확장 (expandable).

P1~P9: expandable 진단·크롤 job 생명주기·webhook·조회 API.
상위 플랜: persona-adaptive-newsletter-plan.md §4 Phase 2.
"""
import uuid

import pytest

from app.config import settings
from app.database.persona_newsletter_models import CrawlExpansionJob
from app.database.seed_persona_newsletter import seed_persona_newsletter
from app.services.persona_newsletter import crawl_job, feasibility

TEST_KEY = "test-newsletter-key"
HEADERS = {"X-Newsletter-Key": TEST_KEY}
URL = "/api/public/newsletter/topic-request"


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


def _transform_body(topic, persona_code="clinician", request_id=None):
    return {
        "request_id": request_id or str(uuid.uuid4()),
        "subscriber_ref": {"persona_code": persona_code, "interests": []},
        "request_type": "transform",
        "topic": topic,
    }


# ---------------------------------------------------------------------------
# P1 — transform 미보유 → expandable + 크롤 job 생성
# ---------------------------------------------------------------------------
def test_p1_transform_expandable(
    client, seeded_personas, newsletter_key, monkeypatch, test_db
):
    monkeypatch.setattr(feasibility, "_default_search", lambda q, n=5: [])
    rid = str(uuid.uuid4())
    r = client.post(
        URL, headers=HEADERS,
        json=_transform_body("땅콩 알러지 신규 진단법", request_id=rid),
    )
    assert r.status_code == 200
    body = r.json()
    assert body["coverage"] == "expandable"
    exp = body["expansion"]
    assert exp["feasible"] is True
    assert exp["source"] == "pubmed"
    assert exp["job_id"]
    assert exp["eta_minutes"] == crawl_job.ETA_MINUTES
    # 크롤 job 행 생성 확인
    job = (
        test_db.query(CrawlExpansionJob)
        .filter(CrawlExpansionJob.job_id == exp["job_id"])
        .first()
    )
    assert job is not None
    assert job.request_id == rid
    assert job.source == "pubmed"


# ---------------------------------------------------------------------------
# P2 — GET /topic-request/{job_id} 상태 조회
# ---------------------------------------------------------------------------
def test_p2_get_job_status(client, seeded_personas, newsletter_key, monkeypatch):
    monkeypatch.setattr(feasibility, "_default_search", lambda q, n=5: [])
    r = client.post(
        URL, headers=HEADERS, json=_transform_body("알러지 검사 키트 동향")
    )
    job_id = r.json()["expansion"]["job_id"]
    g = client.get(f"{URL}/{job_id}", headers=HEADERS)
    assert g.status_code == 200
    data = g.json()
    assert data["job_id"] == job_id
    assert data["status"] in ("pending", "collecting", "ready", "failed")
    assert data["source"] == "pubmed"


# ---------------------------------------------------------------------------
# P3 — GET 미존재 job_id → 404
# ---------------------------------------------------------------------------
def test_p3_get_job_not_found(client, seeded_personas, newsletter_key):
    g = client.get(f"{URL}/nonexistent-job-id", headers=HEADERS)
    assert g.status_code == 404


# ---------------------------------------------------------------------------
# P4 — expandable 멱등성: 동일 request_id → 동일 job
# ---------------------------------------------------------------------------
def test_p4_expandable_idempotent(
    client, seeded_personas, newsletter_key, monkeypatch, test_db
):
    monkeypatch.setattr(feasibility, "_default_search", lambda q, n=5: [])
    rid = str(uuid.uuid4())
    payload = _transform_body("알러지 면역요법 신규 연구", "lab", request_id=rid)
    r1 = client.post(URL, headers=HEADERS, json=payload)
    r2 = client.post(URL, headers=HEADERS, json=payload)
    assert r1.json()["expansion"]["job_id"] == r2.json()["expansion"]["job_id"]
    count = (
        test_db.query(CrawlExpansionJob)
        .filter(CrawlExpansionJob.request_id == rid)
        .count()
    )
    assert count == 1


# ---------------------------------------------------------------------------
# P5 — run_expansion_job 성공 → status ready
# ---------------------------------------------------------------------------
def test_p5_run_job_success(test_db):
    job = crawl_job.create_job(
        test_db,
        request_id="req-p5",
        tenant_id="allergy-insight",
        topic="땅콩 알러지",
        topic_hash="hash-p5",
        source="pubmed",
        callback_url=None,
    )

    def stub_crawl(topic, source):
        return {"source": source, "papers_found": 7, "indexed": 7}

    crawl_job.run_expansion_job(job.job_id, crawl_fn=stub_crawl, db=test_db)
    test_db.refresh(job)
    assert job.status == "ready"
    assert job.result_summary["papers_found"] == 7
    assert job.started_at is not None
    assert job.finished_at is not None


# ---------------------------------------------------------------------------
# P6 — run_expansion_job 크롤 실패 → status failed
# ---------------------------------------------------------------------------
def test_p6_run_job_failure(test_db):
    job = crawl_job.create_job(
        test_db,
        request_id="req-p6",
        tenant_id="allergy-insight",
        topic="우유 알러지",
        topic_hash="hash-p6",
        source="pubmed",
        callback_url=None,
    )

    def stub_crawl(topic, source):
        raise RuntimeError("crawl boom")

    crawl_job.run_expansion_job(job.job_id, crawl_fn=stub_crawl, db=test_db)
    test_db.refresh(job)
    assert job.status == "failed"
    assert "boom" in (job.error or "")


# ---------------------------------------------------------------------------
# P7 — job 완료 시 webhook 콜백 발신
# ---------------------------------------------------------------------------
def test_p7_webhook_fired(test_db, monkeypatch):
    captured = {}

    def fake_webhook(job):
        captured["job_id"] = job.job_id
        captured["status"] = job.status

    monkeypatch.setattr(crawl_job, "_fire_webhook", fake_webhook)
    job = crawl_job.create_job(
        test_db,
        request_id="req-p7",
        tenant_id="allergy-insight",
        topic="알러지 진단",
        topic_hash="hash-p7",
        source="pubmed",
        callback_url="https://nlp.example/callback",
    )
    crawl_job.run_expansion_job(
        job.job_id, crawl_fn=lambda t, s: {"papers_found": 1}, db=test_db
    )
    assert captured.get("job_id") == job.job_id
    assert captured.get("status") == "ready"


# ---------------------------------------------------------------------------
# P8 — 회귀: 도메인 밖 transform 은 여전히 unsupported
# ---------------------------------------------------------------------------
def test_p8_out_of_domain_still_unsupported(
    client, seeded_personas, newsletter_key, monkeypatch
):
    monkeypatch.setattr(feasibility, "_default_search", lambda q, n=5: [])
    r = client.post(
        URL, headers=HEADERS, json=_transform_body("주식 시장 전망과 환율 정책")
    )
    body = r.json()
    assert body["coverage"] == "unsupported"
    assert body["fallback"]["reason"] == "out_of_domain"


# ---------------------------------------------------------------------------
# P9 — feasibility.diagnose 4-튜플 (expandable / covered)
# ---------------------------------------------------------------------------
def test_p9_diagnose_returns_expandable(test_db):
    coverage, conf, reason, source = feasibility.diagnose(
        test_db,
        topic="알러지 면역요법 최신 연구",
        request_type="transform",
        search_fn=lambda q, n=5: [],
    )
    assert coverage == "expandable"
    assert source == "pubmed"
    assert reason is None

    cov2, _conf2, _reason2, src2 = feasibility.diagnose(
        test_db, topic=None, request_type="select"
    )
    assert cov2 == "covered"
    assert src2 is None
