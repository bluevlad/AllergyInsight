"""프로젝트 공용 타임존 유틸리티

저장은 UTC, 표시는 KST 원칙을 따릅니다.
- DB/로그 저장: utc_now() 사용
- 사용자 표시: kst_now() 사용
"""
from datetime import datetime, timezone, timedelta

KST = timezone(timedelta(hours=9))


def utc_now() -> datetime:
    """Timezone-aware UTC 현재 시각 (DB 저장용)"""
    return datetime.now(timezone.utc)


def kst_now() -> datetime:
    """Timezone-aware KST 현재 시각 (사용자 표시용)"""
    return datetime.now(KST)
