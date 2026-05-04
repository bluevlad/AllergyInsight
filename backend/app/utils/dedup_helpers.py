"""중복 제거 유틸리티 — URL 정규화 · 제목 MinHash

headline_selection_service 및 deduplication_service 양쪽에서 재사용.
외부 의존성 없이 hashlib 만으로 경량 MinHash 를 구현한다.
"""
from __future__ import annotations

import hashlib
import re
import struct
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

_TRACKING_PARAMS = frozenset({
    "utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content",
    "fbclid", "gclid", "ref", "ref_src", "ref_url",
    "nclid", "mc_cid", "mc_eid",
})

_NUM_PERM = 128
_HASH_SEEDS = list(range(_NUM_PERM))
_MAX_HASH = (1 << 32) - 1


def canonical_url(url: str) -> str:
    """URL 정규화 — 트래킹 파라미터 제거, 소문자, trailing slash 제거."""
    parsed = urlparse(url.strip().lower())
    query = sorted(
        (k, v)
        for k, v in parse_qsl(parsed.query)
        if k not in _TRACKING_PARAMS
    )
    path = parsed.path.rstrip("/")
    return urlunparse(parsed._replace(
        query=urlencode(query),
        path=path,
        fragment="",
    ))


def canonical_url_hash(url: str) -> str:
    """canonical URL → SHA256 64-char hex."""
    canonical = canonical_url(url)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:64]


def _shingles(text: str, k: int = 3) -> set[str]:
    """k-character shingles from normalized text."""
    text = re.sub(r"\s+", " ", text.strip().lower())
    if len(text) < k:
        return {text}
    return {text[i: i + k] for i in range(len(text) - k + 1)}


def _hash_shingle(shingle: str, seed: int) -> int:
    """Seeded hash for MinHash permutation."""
    data = struct.pack("<I", seed) + shingle.encode("utf-8")
    return int.from_bytes(
        hashlib.md5(data).digest()[:4], byteorder="little"
    )


def title_minhash(title: str) -> list[int]:
    """제목 문자열 → MinHash 시그니처 (128 permutations).

    Returns:
        길이 128 의 int 리스트. jaccard_from_minhash 로 비교.
    """
    shingles = _shingles(title)
    if not shingles:
        return [_MAX_HASH] * _NUM_PERM

    sig: list[int] = []
    for seed in _HASH_SEEDS:
        min_val = min(_hash_shingle(s, seed) for s in shingles)
        sig.append(min_val)
    return sig


def jaccard_from_minhash(sig_a: list[int], sig_b: list[int]) -> float:
    """두 MinHash 시그니처 간 추정 Jaccard 유사도 (0.0 ~ 1.0)."""
    if len(sig_a) != len(sig_b):
        raise ValueError("signature length mismatch")
    if not sig_a:
        return 0.0
    matches = sum(a == b for a, b in zip(sig_a, sig_b))
    return matches / len(sig_a)
