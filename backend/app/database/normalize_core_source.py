"""CORE 출처 1회성 마이그레이션 (Step 1.C-002).

기존 ``CoreService`` 가 CORE 전용 enum 부재로 ``source=MANUAL_UPLOAD`` 로
저장한 행들을 ``source=CORE`` 로 보정한다.

식별 키: ``source_id`` 가 ``"core:"`` prefix 로 시작.

특성:
- **Idempotent** — 매 startup 호출 안전, 보정 대상 0건이면 즉시 종료
- **트랜잭션** — 한 번에 commit, 부분 적용 방지
- **사용자 업로드 보존** — source_id 가 ``"core:"`` 가 아닌 manual_upload 행은
  손대지 않음 (실제 PDF 직접 업로드 데이터)
- **가시성** — 변경 건수 로깅

Rollback (필요 시):
    UPDATE papers SET source = 'manual_upload'
    WHERE source = 'core' AND source_id LIKE 'core:%';

설계 문서: plans/phase1-source-connector-abc.md §7 Step 1.4
"""
import logging

from sqlalchemy import text
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

# 안전을 위해 raw SQL — Paper ORM 의존 회피, 컬럼 변경 영향 최소화
_COUNT_SQL = text(
    """
    SELECT COUNT(*) FROM papers
    WHERE source = 'manual_upload' AND source_id LIKE 'core:%'
    """
)

_UPDATE_SQL = text(
    """
    UPDATE papers SET source = 'core'
    WHERE source = 'manual_upload' AND source_id LIKE 'core:%'
    """
)


def normalize_core_source(db: Session) -> int:
    """CORE 행의 source enum 정규화. 변경된 행 수 반환.

    Returns:
        보정된 행 수 (0 이면 noop — 이미 정규화됐거나 CORE 데이터 없음).
    """
    try:
        pending = db.execute(_COUNT_SQL).scalar() or 0
    except Exception as e:
        # papers 테이블 부재 (마이그레이션 미실행 환경) 등은 무시
        logger.debug("normalize_core_source: 사전 검사 실패 (무시): %s", e)
        return 0

    if pending == 0:
        logger.debug("normalize_core_source: 보정 대상 0건 — noop")
        return 0

    try:
        result = db.execute(_UPDATE_SQL)
        db.commit()
        affected = result.rowcount if result.rowcount is not None else pending
        logger.info(
            "normalize_core_source: %d 건의 manual_upload → core 보정 완료",
            affected,
        )
        return affected
    except Exception as e:
        db.rollback()
        logger.error("normalize_core_source: 보정 실패, 롤백: %s", e)
        raise
