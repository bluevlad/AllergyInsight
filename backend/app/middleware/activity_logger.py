"""환자 행동 로깅 미들웨어

Module C: 환자 인식 추적
- API 호출을 자동으로 행동 로그로 기록
- 비식별화: IP는 해시 처리
"""
import hashlib
import logging
import re
from datetime import datetime
from typing import Optional

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from ..database.connection import SessionLocal
from ..database.analytics_models import PatientActivityLog

logger = logging.getLogger(__name__)

# 로깅 대상 API 패턴 → (action_type, resource_type)
TRACKED_ROUTES = [
    # 진단 관련
    (r"^/api/consumer/my/diagnoses$", "GET", "view", "diagnosis"),
    (r"^/api/consumer/my/diagnoses/\d+$", "GET", "view", "diagnosis"),
    (r"^/api/diagnosis/[\w-]+$", "GET", "view", "diagnosis"),
    (r"^/api/pro/diagnosis/\d+$", "GET", "view", "diagnosis"),

    # 처방 관련
    (r"^/api/prescription/generate$", "POST", "view", "prescription"),
    (r"^/api/prescription/[\w-]+$", "GET", "view", "prescription"),
    (r"^/api/prescription/by-diagnosis/[\w-]+$", "GET", "view", "prescription"),

    # 논문 관련
    (r"^/api/papers/\d+$", "GET", "view", "paper"),
    (r"^/api/pro/research/papers/\d+$", "GET", "view", "paper"),
    (r"^/api/pro/research/search$", "POST", "search", "paper"),

    # Q&A 관련
    (r"^/api/qa$", "POST", "search", "qa"),
    (r"^/api/consumer/guide/qa$", "POST", "search", "qa"),

    # 논문 검색
    (r"^/api/search$", "POST", "search", "paper"),
    (r"^/api/search/\w+$", "GET", "search", "paper"),

    # 뉴스 관련 (관리자)
    (r"^/api/admin/news/\d+/read$", "PUT", "toggle", "news_read"),
    (r"^/api/admin/news/\d+/important$", "PUT", "toggle", "news_important"),

    # 인증
    (r"^/api/auth/login", "POST", "login", None),
    (r"^/api/auth/google", "POST", "login", None),

    # 킷 등록
    (r"^/api/consumer/kit/register$", "POST", "register", "kit"),
]


def _hash_ip(ip: str) -> str:
    """IP 주소를 SHA-256 해시로 비식별화"""
    return hashlib.sha256(ip.encode()).hexdigest()[:16]


def _extract_resource_id(path: str) -> Optional[str]:
    """URL 경로에서 리소스 ID 추출"""
    # /api/.../123 또는 /api/.../uuid-format
    match = re.search(r'/(\d+|[\w]{8}-[\w]{4}-[\w]{4}-[\w]{4}-[\w]{12})(?:/\w+)?$', path)
    if match:
        return match.group(1)
    return None


class ActivityLoggerMiddleware(BaseHTTPMiddleware):
    """API 호출을 자동으로 행동 로그에 기록하는 미들웨어"""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        # 성공 응답만 로깅 (2xx)
        if not (200 <= response.status_code < 300):
            return response

        # 추적 대상 확인
        path = request.url.path
        method = request.method

        for pattern, target_method, action_type, resource_type in TRACKED_ROUTES:
            if method == target_method and re.match(pattern, path):
                try:
                    self._log_activity(request, action_type, resource_type)
                except Exception as e:
                    logger.warning(f"Activity logging failed: {e}")
                break

        return response

    def _log_activity(self, request: Request, action_type: str, resource_type: Optional[str]):
        """행동 로그를 DB에 기록"""
        # 사용자 ID 추출 (JWT에서)
        user_id = None
        if hasattr(request.state, "user_id"):
            user_id = request.state.user_id
        elif hasattr(request.state, "user"):
            user_id = getattr(request.state.user, "id", None)

        # IP 해시
        client_ip = request.client.host if request.client else "unknown"
        ip_hash = _hash_ip(client_ip)

        # User-Agent
        user_agent = request.headers.get("user-agent", "")[:200]

        # 리소스 ID
        resource_id = _extract_resource_id(request.url.path)

        # DB 저장
        db = SessionLocal()
        try:
            log = PatientActivityLog(
                user_id=user_id,
                action_type=action_type,
                resource_type=resource_type,
                resource_id=resource_id,
                ip_hash=ip_hash,
                user_agent=user_agent,
                created_at=datetime.utcnow(),
            )
            db.add(log)
            db.commit()
        except Exception as e:
            db.rollback()
            logger.warning(f"Failed to save activity log: {e}")
        finally:
            db.close()
