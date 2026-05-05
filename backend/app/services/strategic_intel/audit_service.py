"""Strategic Intel Audit 서비스 (Phase E)

super_admin 의 모든 조회·발행을 audit 로그에 기록. 외부 유출 추적 + 운영 가시성.

원칙:
  - audit 실패는 본 요청 흐름을 절대 막지 않음 (try/except + 로그)
  - IP/User-Agent 는 옵션 — 헤더 없으면 None
  - User email 변경 가능성을 감안해 *시점의* email 을 직접 보존 (FK X)

Strategic Intel 모듈 전용. 외부 사용자 노출 금지.
"""
from __future__ import annotations

import hashlib
import logging
from datetime import date, datetime, timedelta
from typing import Optional

from fastapi import Request
from sqlalchemy import desc
from sqlalchemy.orm import Session

from ...database.models import User
from ...database.strategic_intel_models import StrategicIntelAuditLog

logger = logging.getLogger(__name__)


def _hash_ip(ip: str | None) -> str | None:
    """IP → SHA-256 hex (앞 16자리만 — 충돌 가드 + 비식별)"""
    if not ip:
        return None
    return hashlib.sha256(ip.encode("utf-8")).hexdigest()[:16]


def _client_ip(request: Request | None) -> str | None:
    if request is None:
        return None
    # X-Forwarded-For 우선 (Nginx/CloudFront 환경)
    fwd = request.headers.get("x-forwarded-for")
    if fwd:
        return fwd.split(",")[0].strip()
    if request.client:
        return request.client.host
    return None


def record(
    db: Session,
    user: User | None,
    action_type: str,
    *,
    resource_type: str | None = None,
    resource_id: str | int | None = None,
    metadata: dict | None = None,
    request: Request | None = None,
) -> None:
    """audit 로그 1건 기록. 절대 예외를 raise 하지 않음."""
    try:
        log = StrategicIntelAuditLog(
            user_email=getattr(user, "email", None) if user else None,
            action_type=action_type,
            resource_type=resource_type,
            resource_id=str(resource_id) if resource_id is not None else None,
            metadata_json=metadata,
            ip_hash=_hash_ip(_client_ip(request)),
            user_agent=(request.headers.get("user-agent")[:500] if request else None),
            accessed_at=datetime.utcnow(),
        )
        db.add(log)
        db.commit()
    except Exception as e:
        # audit 실패가 본 흐름을 막으면 안 됨 — rollback + warn 으로 끝.
        try:
            db.rollback()
        except Exception:
            pass
        logger.warning("audit record 실패 action=%s resource=%s/%s err=%s",
                       action_type, resource_type, resource_id, e)


# ---------------------------------------------------------------------------
# 조회 (관리 패널용)
# ---------------------------------------------------------------------------


def list_logs(
    db: Session,
    *,
    user_email: Optional[str] = None,
    action_type: Optional[str] = None,
    since: Optional[datetime] = None,
    until: Optional[datetime] = None,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[StrategicIntelAuditLog], int]:
    """audit 로그 페이지네이션 조회. 최신순."""
    q = db.query(StrategicIntelAuditLog)
    if user_email:
        q = q.filter(StrategicIntelAuditLog.user_email == user_email)
    if action_type:
        q = q.filter(StrategicIntelAuditLog.action_type == action_type)
    if since:
        q = q.filter(StrategicIntelAuditLog.accessed_at >= since)
    if until:
        q = q.filter(StrategicIntelAuditLog.accessed_at <= until)
    total = q.count()
    rows = q.order_by(desc(StrategicIntelAuditLog.accessed_at)).offset(offset).limit(limit).all()
    return rows, total


def recent_summary(db: Session, *, hours: int = 24) -> dict:
    """최근 N시간 audit 요약 — Stats 패널 카드용"""
    since = datetime.utcnow() - timedelta(hours=hours)
    rows = (
        db.query(StrategicIntelAuditLog)
        .filter(StrategicIntelAuditLog.accessed_at >= since)
        .all()
    )
    by_action: dict[str, int] = {}
    distinct_users: set[str] = set()
    for r in rows:
        by_action[r.action_type] = by_action.get(r.action_type, 0) + 1
        if r.user_email:
            distinct_users.add(r.user_email)
    return {
        "window_hours": hours,
        "total": len(rows),
        "distinct_users": len(distinct_users),
        "by_action": by_action,
    }
