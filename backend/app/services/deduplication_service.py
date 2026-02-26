"""뉴스 중복 제거 서비스

SHA256 해시 기반 중복 검출을 제공합니다.
sentence-transformers는 선택적으로 사용합니다.
"""
import hashlib
import logging
from functools import lru_cache
from typing import Optional

logger = logging.getLogger(__name__)


class DeduplicationService:
    """뉴스 중복 제거 서비스"""

    def __init__(self):
        self._hash_cache: dict[str, str] = {}
        self._max_cache_size = 10000

    def compute_hash(self, title: str, url: str) -> str:
        """콘텐츠 해시 계산 (SHA256)

        제목 + URL 조합으로 해시를 생성합니다.
        """
        content = f"{title.strip().lower()}|{url.strip().lower()}"
        return hashlib.sha256(content.encode("utf-8")).hexdigest()[:64]

    def check_duplicate(self, title: str, url: str, existing_hashes: set[str]) -> tuple[bool, str]:
        """중복 여부 확인

        Args:
            title: 기사 제목
            url: 기사 URL
            existing_hashes: DB에 저장된 기존 해시 집합

        Returns:
            (is_duplicate, content_hash)
        """
        content_hash = self.compute_hash(title, url)

        # 캐시 확인
        if content_hash in self._hash_cache:
            return True, content_hash

        # DB 해시 확인
        if content_hash in existing_hashes:
            self._add_to_cache(content_hash, url)
            return True, content_hash

        # 신규
        self._add_to_cache(content_hash, url)
        return False, content_hash

    def _add_to_cache(self, content_hash: str, url: str):
        """캐시에 해시 추가 (LRU 제한)"""
        if len(self._hash_cache) >= self._max_cache_size:
            # 가장 오래된 항목 제거 (간단한 FIFO)
            oldest_key = next(iter(self._hash_cache))
            del self._hash_cache[oldest_key]
        self._hash_cache[content_hash] = url

    def clear_cache(self):
        """캐시 초기화"""
        self._hash_cache.clear()


# 싱글톤
_dedup_service: Optional[DeduplicationService] = None


def get_deduplication_service() -> DeduplicationService:
    """DeduplicationService 싱글톤"""
    global _dedup_service
    if _dedup_service is None:
        _dedup_service = DeduplicationService()
    return _dedup_service
