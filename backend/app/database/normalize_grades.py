"""기존 진단 레코드 grade 5/6 → 4 정규화 (Phase 1 1회성 마이그레이션)

MAST Class 0~4로 등급 체계 마이그레이션됨에 따라, 기존 레거시 0~6 체계로
저장된 user_diagnoses.results, diagnosis_kits.results JSON 의 grade 값을
0~4 범위로 정규화한다.

특성:
- Idempotent — 5/6 값이 없으면 noop, 매 startup마다 호출해도 안전
- 트랜잭션 — 한 번에 commit, 부분 적용 방지
- 가시성 — 변경 건수 로깅, 정합화 완료 후에는 빠르게 종료

Alembic 정식 도입은 별도 PR로 분리. 본 모듈은 init_db() 직후 startup에서 호출된다.
"""
import logging
from typing import Any

from sqlalchemy.orm import Session

from .models import DiagnosisKit, UserDiagnosis

logger = logging.getLogger(__name__)


def _normalize_value(value: Any) -> Any:
    """grade 정수만 0~4로 클램프, 비정수는 그대로 반환."""
    if not isinstance(value, int) or isinstance(value, bool):
        return value
    if value > 4:
        return 4
    if value < 0:
        return 0
    return value


def _normalize_results(results: Any) -> tuple[Any, bool]:
    """results JSON 정규화. 변경되면 (new_results, True), 아니면 (results, False)."""
    if not isinstance(results, dict):
        return results, False
    new_results = {k: _normalize_value(v) for k, v in results.items()}
    return new_results, new_results != results


def normalize_legacy_grades(db: Session) -> dict:
    """user_diagnoses 및 diagnosis_kits 의 results JSON을 정규화.

    Returns:
        {"user_diagnoses": int, "diagnosis_kits": int} — 변경된 레코드 수
    """
    counts = {"user_diagnoses": 0, "diagnosis_kits": 0}

    for diag in db.query(UserDiagnosis).all():
        new_results, changed = _normalize_results(diag.results)
        if changed:
            diag.results = new_results
            counts["user_diagnoses"] += 1

    for kit in db.query(DiagnosisKit).all():
        new_results, changed = _normalize_results(kit.results)
        if changed:
            kit.results = new_results
            counts["diagnosis_kits"] += 1

    total = sum(counts.values())
    if total > 0:
        db.commit()
        logger.info(
            "grade 정규화 완료: user_diagnoses=%d, diagnosis_kits=%d (총 %d 레코드)",
            counts["user_diagnoses"],
            counts["diagnosis_kits"],
            total,
        )

    return counts
