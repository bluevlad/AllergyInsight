"""Source connector 표준 예외.

모든 connector 는 외부 호출 실패 시 SourceSearchResult.empty(error=...)
를 반환하거나, 명시적으로 SourceError 류를 raise 한다.
"""


class SourceError(Exception):
    """모든 source 에러의 베이스."""


class SourceUnavailableError(SourceError):
    """is_available()=False 인 connector 가 호출됨 — API 키 미설정 등."""


class RateLimitError(SourceError):
    """429 또는 source 의 자체 rate limit 도달."""


class SourceTimeoutError(SourceError):
    """timeout 초과."""


class SourceAuthError(SourceError):
    """API 키 무효 / 401 / 403."""
