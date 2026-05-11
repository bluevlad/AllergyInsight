"""DomainPack v1 검증 도구 (pack_linter).

규칙 카테고리:
- **E001~E005** 스키마 검증 (필수 필드, 타입, enum, 범위, 패턴)
- **E101~E109** 참조 무결성 (registry, 프롬프트, taxonomy, cron, timezone)
- **W101~W108** 일관성 / 경고 (가드레일, persona, 충돌, 비표준)

WBS: P1-G-003

상세 규칙 정의: plans/domain-pack-yaml-schema-v1.md §5
"""
from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

logger_msgs: dict[str, str] = {}

# ───────── 데이터 클래스 ─────────


class Severity(str, Enum):
    ERROR = "error"
    WARNING = "warning"


@dataclass(frozen=True)
class Issue:
    code: str                          # e.g. "E001", "W101"
    severity: Severity
    message: str
    path: str = "$"                    # JSON pointer-style, e.g. "$.sources.enabled[0]"

    def __str__(self) -> str:
        return f"[{self.code}] {self.severity.value.upper()} {self.path}: {self.message}"


@dataclass
class LintResult:
    errors: list[Issue] = field(default_factory=list)
    warnings: list[Issue] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors

    def fails(self, strict: bool = False) -> bool:
        if self.errors:
            return True
        if strict and self.warnings:
            return True
        return False

    def add(self, issue: Issue) -> None:
        if issue.severity == Severity.ERROR:
            self.errors.append(issue)
        else:
            self.warnings.append(issue)


# ───────── 상수 ─────────

_DOMAIN_ID_RE = re.compile(r"^[a-z][a-z0-9_-]{2,30}$")
_PERSONA_ID_RE = re.compile(r"^[a-z][a-z0-9_]{2,20}$")
_HEX_COLOR_RE = re.compile(r"^#[0-9a-fA-F]{6}$")
_INLINE_PROMPT_LIMIT = 100  # W106 threshold

_STATUS_VALUES = {"active", "draft", "deprecated"}
_VECTOR_BACKENDS = {"chromadb", "pgvector"}
_EMBEDDING_PROVIDERS = {"chromadb_default", "sentence_transformers", "openai"}
_CHUNK_STRATEGIES = {"fixed", "sentence", "semantic"}
_DISTANCES = {"cosine", "l2", "ip"}
_GUARDRAIL_SEVERITY = {"hard", "soft"}
_ROTATION_STRATEGIES = {"tiered", "topic_round_robin", "random", "fixed"}
_TAXONOMY_SOURCES = {"db_table", "yaml", "inline"}
_PERSONA_FREQUENCY = {"daily", "weekly", "monthly", "on_demand"}
_PERSONA_INTERESTS = {"subscriber_field", "tag_match", "embedding"}
_PERSONA_MATCHING = {"rule", "embedding", "hybrid"}
_PERSONA_CHANNEL = {"email", "slack", "webhook"}


# ───────── 유틸 ─────────


def _is_str(x: Any) -> bool:
    return isinstance(x, str)


def _is_int(x: Any) -> bool:
    return isinstance(x, int) and not isinstance(x, bool)


def _is_bool(x: Any) -> bool:
    return isinstance(x, bool)


def _is_list(x: Any) -> bool:
    return isinstance(x, list)


def _is_dict(x: Any) -> bool:
    return isinstance(x, dict)


def _get(d: Any, key: str, default: Any = None) -> Any:
    return d.get(key, default) if isinstance(d, dict) else default


def _registry_names() -> set[str]:
    """현재 등록된 connector 이름 집합 (paper + news 모두 import 됨)."""
    # 지연 import — registry 가 채워지도록 connector 패키지를 명시적으로 로드
    try:
        from app.core.sources import registry
        from app.core.sources.paper import (  # noqa: F401  (side-effect)
            pubmed, semantic_scholar, europe_pmc, openalex, biorxiv, core,
        )
        from app.core.sources.news import (  # noqa: F401
            naver_news, google_news_rss,
        )
        return set(registry.names())
    except Exception:
        return set()


def _is_valid_timezone(name: str) -> bool:
    try:
        from zoneinfo import ZoneInfo
        ZoneInfo(name)
        return True
    except Exception:
        return False


def _is_valid_cron(expr: str) -> bool:
    try:
        from apscheduler.triggers.cron import CronTrigger
        CronTrigger.from_crontab(expr)
        return True
    except Exception:
        return False


# ───────── 메인 진입점 ─────────


def validate(
    raw: dict,
    *,
    base_dir: Path | None = None,
    check_environ: bool = False,
) -> LintResult:
    """DomainPack 검증.

    Args:
        raw: yaml.safe_load 결과
        base_dir: 프롬프트 파일 / persona template 상대경로 해석 기준
        check_environ: True 시 W107 (api_key_env 환경변수) 체크

    Returns:
        LintResult — errors + warnings.
    """
    result = LintResult()

    # 1. Schema 검증 (E001~E005)
    if not _is_dict(raw):
        result.add(Issue("E002", Severity.ERROR, "최상위가 dict 가 아님", "$"))
        return result

    _check_version(raw, result)
    _check_domain(raw, result)
    sources_ok = _check_sources(raw, result)
    _check_taxonomy(raw, result)
    rag_ok = _check_rag(raw, result)
    _check_prompts(raw, result, base_dir=base_dir)
    _check_personas(raw, result, base_dir=base_dir)
    _check_scheduler(raw, result)
    _check_features(raw, result)

    # 2. Cross 검사 (필요한 항목)
    if sources_ok:
        _cross_check_sources_vs_rotation_topics(raw, result)
    _check_environment_vars(raw, result, check_environ=check_environ)

    return result


# ───────── 개별 체크 ─────────


def _check_version(raw: dict, r: LintResult) -> None:
    if "version" not in raw:
        r.add(Issue("E001", Severity.ERROR, "필수 필드 누락: version", "$.version"))
        return
    if raw["version"] != 1:
        r.add(Issue("E003", Severity.ERROR,
                    f"version 은 1 이어야 함 (받음: {raw['version']})",
                    "$.version"))


def _check_domain(raw: dict, r: LintResult) -> None:
    d = raw.get("domain")
    if not _is_dict(d):
        r.add(Issue("E001", Severity.ERROR, "필수 필드 누락 또는 dict 아님: domain", "$.domain"))
        return

    if "id" not in d:
        r.add(Issue("E001", Severity.ERROR, "필수 필드 누락: domain.id", "$.domain.id"))
    elif not _is_str(d["id"]):
        r.add(Issue("E002", Severity.ERROR, "domain.id 는 string", "$.domain.id"))
    elif not _DOMAIN_ID_RE.match(d["id"]):
        r.add(Issue("E005", Severity.ERROR,
                    f"domain.id 슬러그 형식 위반 (^[a-z][a-z0-9_-]{{2,30}}$): {d['id']!r}",
                    "$.domain.id"))

    if "name_kr" not in d:
        r.add(Issue("E001", Severity.ERROR, "필수 필드 누락: domain.name_kr", "$.domain.name_kr"))
    elif not _is_str(d["name_kr"]) or not d["name_kr"].strip():
        r.add(Issue("E002", Severity.ERROR, "domain.name_kr 는 비어있지 않은 string", "$.domain.name_kr"))

    if "status" not in d:
        r.add(Issue("E001", Severity.ERROR, "필수 필드 누락: domain.status", "$.domain.status"))
    elif d["status"] not in _STATUS_VALUES:
        r.add(Issue("E003", Severity.ERROR,
                    f"domain.status 는 {sorted(_STATUS_VALUES)} 중 하나 (받음: {d['status']!r})",
                    "$.domain.status"))

    color = d.get("accent_color")
    if color is not None and (not _is_str(color) or not _HEX_COLOR_RE.match(color)):
        r.add(Issue("E005", Severity.ERROR,
                    f"domain.accent_color 는 #RRGGBB (받음: {color!r})",
                    "$.domain.accent_color"))


def _check_sources(raw: dict, r: LintResult) -> bool:
    """returns True if sources 구조가 최소 유효 (cross-check 진행 가능)."""
    s = raw.get("sources")
    if not _is_dict(s):
        r.add(Issue("E001", Severity.ERROR, "필수 필드 누락 또는 dict 아님: sources", "$.sources"))
        return False

    enabled = s.get("enabled")
    if enabled is None:
        r.add(Issue("E001", Severity.ERROR, "필수 필드 누락: sources.enabled", "$.sources.enabled"))
        return False
    if not _is_list(enabled):
        r.add(Issue("E002", Severity.ERROR, "sources.enabled 는 list", "$.sources.enabled"))
        return False
    if len(enabled) == 0:
        r.add(Issue("W103", Severity.WARNING, "sources.enabled 가 비어있음 — 수집 불가",
                    "$.sources.enabled"))

    registered = _registry_names()
    for i, src in enumerate(enabled):
        if not _is_str(src):
            r.add(Issue("E002", Severity.ERROR, f"sources.enabled[{i}] 는 string", f"$.sources.enabled[{i}]"))
            continue
        if registered and src not in registered:
            r.add(Issue("E101", Severity.ERROR,
                        f"등록되지 않은 source: {src!r} (등록: {sorted(registered)})",
                        f"$.sources.enabled[{i}]"))

    rotation = s.get("rotation")
    if rotation is not None and _is_dict(rotation):
        strat = rotation.get("strategy")
        if strat not in _ROTATION_STRATEGIES:
            r.add(Issue("E003", Severity.ERROR,
                        f"sources.rotation.strategy 는 {sorted(_ROTATION_STRATEGIES)} 중 하나",
                        "$.sources.rotation.strategy"))
        elif strat == "tiered":
            tiers = rotation.get("tiers")
            if not _is_list(tiers) or len(tiers) == 0:
                r.add(Issue("E001", Severity.ERROR,
                            "strategy=tiered 일 때 tiers 가 필요",
                            "$.sources.rotation.tiers"))
            else:
                for i, tier in enumerate(tiers):
                    if not _is_dict(tier):
                        continue
                    pd = tier.get("period_days")
                    if not _is_int(pd) or pd < 1 or pd > 30:
                        r.add(Issue("E004", Severity.ERROR,
                                    f"period_days 는 1~30 정수",
                                    f"$.sources.rotation.tiers[{i}].period_days"))
                    if not _is_list(tier.get("topics")):
                        r.add(Issue("E001", Severity.ERROR,
                                    "tier 에 topics list 필요",
                                    f"$.sources.rotation.tiers[{i}].topics"))

    return True


def _check_taxonomy(raw: dict, r: LintResult) -> None:
    t = raw.get("taxonomy")
    if not _is_dict(t):
        r.add(Issue("E001", Severity.ERROR, "필수 필드 누락 또는 dict 아님: taxonomy", "$.taxonomy"))
        return
    src = t.get("source")
    if src not in _TAXONOMY_SOURCES:
        r.add(Issue("E003", Severity.ERROR,
                    f"taxonomy.source 는 {sorted(_TAXONOMY_SOURCES)} 중 하나 (받음: {src!r})",
                    "$.taxonomy.source"))
        return

    if src == "db_table" and "table_name" not in t:
        r.add(Issue("E001", Severity.ERROR,
                    "source=db_table 일 때 table_name 필요",
                    "$.taxonomy.table_name"))
    if src == "yaml" and "file" not in t:
        r.add(Issue("E001", Severity.ERROR,
                    "source=yaml 일 때 file 필요",
                    "$.taxonomy.file"))
    if src == "inline":
        items = t.get("items")
        if not _is_list(items) or len(items) == 0:
            r.add(Issue("E001", Severity.ERROR,
                        "source=inline 일 때 items list 필요",
                        "$.taxonomy.items"))


def _check_rag(raw: dict, r: LintResult) -> bool:
    rag = raw.get("rag")
    if not _is_dict(rag):
        r.add(Issue("E001", Severity.ERROR, "필수 필드 누락 또는 dict 아님: rag", "$.rag"))
        return False

    # vector_store
    vs = rag.get("vector_store")
    if _is_dict(vs):
        backend = vs.get("backend")
        if backend not in _VECTOR_BACKENDS:
            r.add(Issue("E003", Severity.ERROR,
                        f"rag.vector_store.backend 는 {sorted(_VECTOR_BACKENDS)} 중 하나",
                        "$.rag.vector_store.backend"))
        if "collection" not in vs:
            r.add(Issue("E001", Severity.ERROR,
                        "rag.vector_store.collection 필수",
                        "$.rag.vector_store.collection"))
        if backend == "chromadb" and "persist_path" not in vs:
            r.add(Issue("E001", Severity.ERROR,
                        "chromadb backend 는 persist_path 필요",
                        "$.rag.vector_store.persist_path"))
    else:
        r.add(Issue("E001", Severity.ERROR, "rag.vector_store dict 필요",
                    "$.rag.vector_store"))

    # embedding
    emb = rag.get("embedding")
    if _is_dict(emb):
        if emb.get("provider") not in _EMBEDDING_PROVIDERS:
            r.add(Issue("E003", Severity.ERROR,
                        f"rag.embedding.provider 는 {sorted(_EMBEDDING_PROVIDERS)} 중 하나",
                        "$.rag.embedding.provider"))

    # chunk
    chunk = rag.get("chunk")
    if _is_dict(chunk):
        size = chunk.get("size")
        overlap = chunk.get("overlap")
        if not _is_int(size) or size < 200 or size > 4000:
            r.add(Issue("E004", Severity.ERROR, "rag.chunk.size 는 200~4000 정수",
                        "$.rag.chunk.size"))
        if not _is_int(overlap) or overlap < 0:
            r.add(Issue("E004", Severity.ERROR, "rag.chunk.overlap 은 0 이상 정수",
                        "$.rag.chunk.overlap"))
        elif _is_int(size) and overlap >= size:
            r.add(Issue("E004", Severity.ERROR,
                        f"rag.chunk.overlap ({overlap}) 은 size ({size}) 보다 작아야 함",
                        "$.rag.chunk.overlap"))
        strat = chunk.get("strategy", "fixed")
        if strat not in _CHUNK_STRATEGIES:
            r.add(Issue("E003", Severity.ERROR,
                        f"rag.chunk.strategy 는 {sorted(_CHUNK_STRATEGIES)} 중 하나",
                        "$.rag.chunk.strategy"))

    # retrieval
    ret = rag.get("retrieval")
    if _is_dict(ret):
        thr = ret.get("relevance_threshold")
        if thr is not None:
            if not isinstance(thr, (int, float)) or thr < 0.0 or thr > 1.0:
                r.add(Issue("E004", Severity.ERROR,
                            "rag.retrieval.relevance_threshold 는 0.0~1.0",
                            "$.rag.retrieval.relevance_threshold"))
        dist = ret.get("distance", "cosine")
        if dist not in _DISTANCES:
            r.add(Issue("E003", Severity.ERROR,
                        f"rag.retrieval.distance 는 {sorted(_DISTANCES)} 중 하나",
                        "$.rag.retrieval.distance"))

    # guardrails (W101)
    guardrails = rag.get("guardrails", [])
    if not guardrails:
        r.add(Issue("W101", Severity.WARNING,
                    "rag.guardrails 가 정의되지 않음 — 의료/금융 도메인은 필수 권장",
                    "$.rag.guardrails"))
    else:
        for i, g in enumerate(guardrails):
            if not _is_dict(g):
                continue
            if g.get("severity") not in _GUARDRAIL_SEVERITY:
                r.add(Issue("E003", Severity.ERROR,
                            f"guardrail severity 는 {sorted(_GUARDRAIL_SEVERITY)} 중 하나",
                            f"$.rag.guardrails[{i}].severity"))
            if not g.get("text"):
                r.add(Issue("E001", Severity.ERROR, "guardrail text 필요",
                            f"$.rag.guardrails[{i}].text"))

    return True


def _check_prompts(raw: dict, r: LintResult, *, base_dir: Path | None) -> None:
    prompts = raw.get("prompts")
    if not _is_dict(prompts):
        r.add(Issue("E001", Severity.ERROR, "필수 필드 누락 또는 dict 아님: prompts",
                    "$.prompts"))
        return

    for key, p in prompts.items():
        path = f"$.prompts.{key}"
        if not _is_dict(p):
            r.add(Issue("E002", Severity.ERROR, "prompt entry 는 dict", path))
            continue

        inline = p.get("inline")
        prompt_path = p.get("path")
        ref = p.get("ref")
        provided = [k for k, v in (("inline", inline), ("path", prompt_path),
                                    ("ref", ref)) if v]

        if not provided:
            r.add(Issue("E103", Severity.ERROR,
                        f"prompt '{key}' 에 inline/path/ref 중 최소 하나 필요",
                        path))
            continue

        # E102: path 파일 존재
        if prompt_path:
            if not _is_str(prompt_path):
                r.add(Issue("E002", Severity.ERROR, "prompt path 는 string", f"{path}.path"))
            elif base_dir is not None:
                resolved = (base_dir / prompt_path).resolve()
                if not resolved.exists():
                    r.add(Issue("E102", Severity.ERROR,
                                f"prompt 파일 미존재: {resolved}",
                                f"{path}.path"))

        # W106: long inline
        if inline and _is_str(inline) and len(inline) > _INLINE_PROMPT_LIMIT:
            r.add(Issue("W106", Severity.WARNING,
                        f"inline prompt 가 {len(inline)} 자 — {_INLINE_PROMPT_LIMIT} 자 초과시 path 분리 권장",
                        f"{path}.inline"))


def _check_personas(raw: dict, r: LintResult, *, base_dir: Path | None) -> None:
    personas = raw.get("personas")
    if personas is None or personas == []:
        r.add(Issue("W102", Severity.WARNING,
                    "personas 가 정의되지 않음 — 다이제스트 발송 불가",
                    "$.personas"))
        return

    if not _is_list(personas):
        r.add(Issue("E002", Severity.ERROR, "personas 는 list", "$.personas"))
        return

    seen_ids: set[str] = set()
    for i, p in enumerate(personas):
        path = f"$.personas[{i}]"
        if not _is_dict(p):
            r.add(Issue("E002", Severity.ERROR, "persona entry 는 dict", path))
            continue

        pid = p.get("id")
        if not pid:
            r.add(Issue("E001", Severity.ERROR, "persona.id 필수", f"{path}.id"))
        elif not _is_str(pid):
            r.add(Issue("E002", Severity.ERROR, "persona.id 는 string", f"{path}.id"))
        elif not _PERSONA_ID_RE.match(pid):
            r.add(Issue("E005", Severity.ERROR,
                        f"persona.id 슬러그 형식 위반 (^[a-z][a-z0-9_]{{2,20}}$): {pid!r}",
                        f"{path}.id"))
        elif pid in seen_ids:
            r.add(Issue("E108", Severity.ERROR, f"persona.id 중복: {pid!r}", f"{path}.id"))
        else:
            seen_ids.add(pid)

        digest = p.get("digest")
        if _is_dict(digest):
            freq = digest.get("frequency")
            if freq not in _PERSONA_FREQUENCY:
                r.add(Issue("E003", Severity.ERROR,
                            f"persona.digest.frequency 는 {sorted(_PERSONA_FREQUENCY)} 중 하나",
                            f"{path}.digest.frequency"))
            elif freq != "on_demand":
                cron = digest.get("cron")
                if not cron:
                    r.add(Issue("E001", Severity.ERROR,
                                "frequency != on_demand 일 때 cron 필요",
                                f"{path}.digest.cron"))
                elif not _is_valid_cron(cron):
                    r.add(Issue("E107", Severity.ERROR,
                                f"persona.digest.cron 표현식 오류: {cron!r}",
                                f"{path}.digest.cron"))

        interests = p.get("interests")
        if _is_dict(interests):
            isrc = interests.get("source")
            if isrc not in _PERSONA_INTERESTS:
                r.add(Issue("E003", Severity.ERROR,
                            f"persona.interests.source 는 {sorted(_PERSONA_INTERESTS)} 중 하나",
                            f"{path}.interests.source"))
            matching = interests.get("matching", "rule")
            if matching not in _PERSONA_MATCHING:
                r.add(Issue("E003", Severity.ERROR,
                            f"persona.interests.matching 는 {sorted(_PERSONA_MATCHING)} 중 하나",
                            f"{path}.interests.matching"))

        delivery = p.get("delivery")
        if _is_dict(delivery):
            channel = delivery.get("channel")
            if channel not in _PERSONA_CHANNEL:
                r.add(Issue("E003", Severity.ERROR,
                            f"persona.delivery.channel 는 {sorted(_PERSONA_CHANNEL)} 중 하나",
                            f"{path}.delivery.channel"))
            tmpl = delivery.get("template")
            if not tmpl:
                r.add(Issue("E001", Severity.ERROR, "persona.delivery.template 필요",
                            f"{path}.delivery.template"))
            elif base_dir is not None and _is_str(tmpl):
                resolved = (base_dir / tmpl).resolve()
                if not resolved.exists():
                    r.add(Issue("E106", Severity.ERROR,
                                f"persona delivery template 미존재: {resolved}",
                                f"{path}.delivery.template"))


def _check_scheduler(raw: dict, r: LintResult) -> None:
    sch = raw.get("scheduler")
    if sch is None:
        return  # optional
    if not _is_dict(sch):
        r.add(Issue("E002", Severity.ERROR, "scheduler 는 dict", "$.scheduler"))
        return

    tz = sch.get("timezone")
    if not tz:
        r.add(Issue("E001", Severity.ERROR, "scheduler.timezone 필수",
                    "$.scheduler.timezone"))
    elif not _is_valid_timezone(tz):
        r.add(Issue("E109", Severity.ERROR,
                    f"scheduler.timezone 무효 (IANA TZ 가 아님): {tz!r}",
                    "$.scheduler.timezone"))

    jobs = sch.get("jobs", [])
    if not _is_list(jobs):
        r.add(Issue("E002", Severity.ERROR, "scheduler.jobs 는 list", "$.scheduler.jobs"))
        return

    seen_ids: set[str] = set()
    cron_minute_buckets: dict[str, list[str]] = {}  # "HH:MM" → [job_id...]

    for i, job in enumerate(jobs):
        path = f"$.scheduler.jobs[{i}]"
        if not _is_dict(job):
            continue
        jid = job.get("id")
        if not jid:
            r.add(Issue("E001", Severity.ERROR, "scheduler.job.id 필수", f"{path}.id"))
        elif jid in seen_ids:
            r.add(Issue("E108", Severity.ERROR,
                        f"scheduler.jobs.id 중복: {jid!r}",
                        f"{path}.id"))
        else:
            seen_ids.add(jid)

        if not job.get("task"):
            r.add(Issue("E001", Severity.ERROR, "scheduler.job.task 필수",
                        f"{path}.task"))

        cron = job.get("cron")
        if not cron:
            r.add(Issue("E001", Severity.ERROR, "scheduler.job.cron 필수",
                        f"{path}.cron"))
        elif not _is_valid_cron(cron):
            r.add(Issue("E107", Severity.ERROR,
                        f"cron 표현식 오류: {cron!r}",
                        f"{path}.cron"))
        elif jid:
            # W105: 동일 분에 5개 이상 job — 단순 분/시 추출 (DOW 동일 가정)
            parts = cron.split()
            if len(parts) >= 2:
                bucket = f"{parts[1]}:{parts[0]}"
                cron_minute_buckets.setdefault(bucket, []).append(jid)

    for bucket, ids in cron_minute_buckets.items():
        if len(ids) >= 5:
            r.add(Issue("W105", Severity.WARNING,
                        f"동일 시간 {bucket} 에 {len(ids)} 개 job — 서버 부하 우려: {ids}",
                        "$.scheduler.jobs"))


def _check_features(raw: dict, r: LintResult) -> None:
    f = raw.get("features")
    if f is None:
        return
    if not _is_dict(f):
        r.add(Issue("E002", Severity.ERROR, "features 는 dict", "$.features"))
        return
    for key in ("rag_enabled", "digest_enabled", "newsletter_enabled", "trend_analysis"):
        if key in f and not _is_bool(f[key]):
            r.add(Issue("E002", Severity.ERROR, f"features.{key} 는 bool",
                        f"$.features.{key}"))


def _cross_check_sources_vs_rotation_topics(raw: dict, r: LintResult) -> None:
    """E105: rotation.tiers 의 topic 이 inline taxonomy 에 있는지 검증."""
    taxonomy = raw.get("taxonomy", {})
    if taxonomy.get("source") != "inline":
        return  # db_table / yaml 은 runtime 검사

    valid_ids: set[str] = set()
    for item in taxonomy.get("items", []) or []:
        if _is_dict(item) and item.get("id"):
            valid_ids.add(item["id"])

    rotation = raw.get("sources", {}).get("rotation", {})
    if rotation.get("strategy") != "tiered":
        return

    for i, tier in enumerate(rotation.get("tiers", []) or []):
        if not _is_dict(tier):
            continue
        for j, topic in enumerate(tier.get("topics", []) or []):
            if topic not in valid_ids:
                r.add(Issue("E105", Severity.ERROR,
                            f"rotation topic {topic!r} 가 taxonomy 에 없음",
                            f"$.sources.rotation.tiers[{i}].topics[{j}]"))


def _check_environment_vars(
    raw: dict, r: LintResult, *, check_environ: bool
) -> None:
    """W107: source_config.*.api_key_env 환경변수 미설정 경고."""
    if not check_environ:
        return
    sc = raw.get("sources", {}).get("source_config", {}) or {}
    for src_name, cfg in sc.items():
        if not _is_dict(cfg):
            continue
        env = cfg.get("api_key_env")
        if env and env not in os.environ:
            r.add(Issue("W107", Severity.WARNING,
                        f"source '{src_name}' 의 api_key_env={env!r} 환경변수 미설정 — runtime 에서 자동 skip 됨",
                        f"$.sources.source_config.{src_name}.api_key_env"))
