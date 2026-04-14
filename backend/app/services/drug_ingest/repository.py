"""Drug ingest persistence layer.

어댑터가 생산한 DrugProductCandidate 를 drug_products 테이블에 반영하고,
원본 payload 를 drug_source_raws 테이블에 이력으로 축적한다.

Dialect-agnostic: check-then-act 패턴으로 Postgres/SQLite 모두 지원.
(SQLAlchemy `ON CONFLICT` 방언 분기를 피하기 위함 — 테스트는 SQLite.)
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from sqlalchemy.orm import Session

from app.database.drug_models import DrugProduct, DrugSourceRaw
from app.utils.timezone import utc_now

from .sources.base import DrugProductCandidate


@dataclass
class UpsertResult:
    product_id: int
    created: bool  # True=insert, False=update


_CANDIDATE_FIELDS = (
    "atc_code",
    "rxcui",
    "kfda_item_seq",
    "name_kr",
    "name_en",
    "product_type",
    "is_prescription",
    "indications",
    "dosage",
    "warnings",
)


def upsert_drug_product(
    session: Session,
    candidate: DrugProductCandidate,
) -> UpsertResult:
    """DrugProductCandidate 를 drug_products 테이블에 upsert.

    unique key: (source, source_product_id).
    기존 row 가 있으면 필드를 덮어쓰고, 없으면 새로 insert 한다.
    commit 은 호출자 책임 — 배치 단위 트랜잭션을 유지하기 위함.
    """
    existing = (
        session.query(DrugProduct)
        .filter(
            DrugProduct.source == candidate.source,
            DrugProduct.source_product_id == candidate.source_product_id,
        )
        .one_or_none()
    )

    if existing is None:
        product = DrugProduct(
            source=candidate.source,
            source_product_id=candidate.source_product_id,
            routes=list(candidate.routes) if candidate.routes else None,
            raw_jsonb=dict(candidate.raw) if candidate.raw else None,
        )
        for field in _CANDIDATE_FIELDS:
            setattr(product, field, getattr(candidate, field))
        session.add(product)
        session.flush()
        return UpsertResult(product_id=product.id, created=True)

    for field in _CANDIDATE_FIELDS:
        setattr(existing, field, getattr(candidate, field))
    existing.routes = list(candidate.routes) if candidate.routes else None
    existing.raw_jsonb = dict(candidate.raw) if candidate.raw else None
    existing.updated_at = utc_now()
    session.flush()
    return UpsertResult(product_id=existing.id, created=False)


def save_raw_snapshot(
    session: Session,
    source: str,
    source_product_id: str,
    payload: dict[str, Any],
) -> int:
    """원본 응답을 drug_source_raws 에 append-only 로 저장.

    같은 (source, source_product_id) 라도 여러 스냅샷이 시간순으로 쌓인다.
    소스 API 스키마 변경에 대비한 감사·재파싱용 이력.
    """
    snapshot = DrugSourceRaw(
        source=source,
        source_product_id=source_product_id,
        fetched_at=utc_now(),
        payload=dict(payload),
    )
    session.add(snapshot)
    session.flush()
    return snapshot.id


def persist_candidate(
    session: Session,
    candidate: DrugProductCandidate,
) -> UpsertResult:
    """upsert + raw snapshot 을 한 번에 처리하는 편의 함수.

    파이프라인(Phase 3)이 어댑터 결과를 받아 이 함수 하나만 호출하도록 설계.
    """
    result = upsert_drug_product(session, candidate)
    if candidate.raw:
        save_raw_snapshot(
            session,
            source=candidate.source,
            source_product_id=candidate.source_product_id,
            payload=candidate.raw,
        )
    return result
