"""안전 가드레일 — 응급 키워드 감지 및 119 안내

알러지 챗봇/증상 매칭 입력에서 아나필락시스 의심 또는 응급 의료 개입이 필요한
키워드가 감지되면, 일반 답변 생성 대신 119 호출 안내를 우선 노출한다.

설계 원칙:
- 보수적 감지: false positive(과도한 응급 알림)가 false negative보다 안전
- 단순 키워드 매칭: LLM 호출 전에 동작해야 하므로 빠르고 결정적
- 한·영 표현 동시 지원
- 의료 진단 행위가 아니라 "응급 가능성 안내"로만 제한

응급 레벨:
  - "emergency"  : 즉시 119 — 본 답변 차단, 응급 안내로 대체
  - "concern"    : 주의 — 답변 + 응급 가능성 배너 동반
  - "none"       : 정상 처리
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Iterable

# ---------------------------------------------------------------------------
# 키워드 사전
# ---------------------------------------------------------------------------
# 한국어 표현 + 일부 영문/한자(혼용 입력 대응). 키워드는 정규식으로 매칭되며
# 단어 경계나 한국어 특성상 부분 일치도 허용한다.

# emergency: 아나필락시스 직접 시사 또는 즉시 119가 필요한 표현
_EMERGENCY_PATTERNS: tuple[str, ...] = (
    # 아나필락시스 / 쇼크
    r"아나필락시스",
    r"anaphyla",                                # anaphylaxis / anaphylactic
    r"과민성\s*쇼크",
    r"알러지\s*쇼크",
    r"쇼크",
    # 호흡 / 기도
    r"숨\s*막",                                  # 숨막힘 / 숨이 막혀
    r"숨\s*못\s*쉬",
    r"호흡\s*곤란",
    r"숨이?\s*안\s*[쉬쉽]",                       # 숨(이) 안 쉬어진다
    r"기도\s*막",
    r"질식",
    # 의식 / 순환
    r"의식.{0,5}(저하|잃|흐|혼미|몽롱|희미)",
    r"기절",
    r"실신",
    r"맥박.{0,5}(없|약)",
    r"심정지",
    # 부종 — 기도 관련 (한국어 조사·공백·활용 허용)
    r"입술.{0,5}(부었|부어|부종|붓)",
    r"혀.{0,5}(부었|부어|부종|붓)",
    r"목.{0,5}(부었|부어|부종|붓)",
    r"인후.{0,5}(부었|부어|부종|붓)",
    r"얼굴.{0,5}(부었|부어|부종|붓)",
)

# concern: 답변 제공은 하되 응급 가능성을 함께 알려야 하는 표현
_CONCERN_PATTERNS: tuple[str, ...] = (
    r"두드러기.*전신",
    r"전신.*두드러기",
    r"전신\s*발진",
    r"심한\s*가려움",
    r"구토.*어지(럽|러)",
    r"어지(럽|러).*구토",
    r"혈압.*저하",
    r"빠른\s*맥박",
    r"심한\s*복통",
    r"숨.{0,3}(가쁨|가쁩|가빠)",
)


# 컴파일된 패턴 캐시
_EMERGENCY_REGEX = [re.compile(p, re.IGNORECASE) for p in _EMERGENCY_PATTERNS]
_CONCERN_REGEX = [re.compile(p, re.IGNORECASE) for p in _CONCERN_PATTERNS]


EMERGENCY_MESSAGE = (
    "🚨 응급 상황이 의심됩니다. 본 챗봇의 일반 답변을 기다리지 말고, 즉시 다음을 시행하세요.\n"
    "\n"
    "1. **119 즉시 호출** — 응급 알러지 반응 가능성을 알리세요.\n"
    "2. 에피네프린 자가주사기(에피펜)가 있다면 **즉시 사용** 후 119 호출.\n"
    "3. 환자를 눕히고 다리를 올려 혈압 유지를 도우세요.\n"
    "4. 의식이 없으면 회복 자세로 두고 호흡을 확인하세요.\n"
    "\n"
    "본 서비스는 응급 의료 서비스가 아니며, 응급 상황에서는 119/의료진이 우선입니다."
)

CONCERN_MESSAGE = (
    "⚠️ 입력하신 증상 중 일부는 응급 알러지 반응으로 진행될 가능성이 있는 항목입니다. "
    "증상이 빠르게 악화되거나 호흡곤란·의식저하·전신 증상이 동반되면 즉시 119에 전화하세요. "
    "에피네프린 자가주사기(에피펜)가 처방되어 있다면 즉시 사용을 고려하세요."
)


@dataclass
class SafetyAssessment:
    """입력 텍스트의 응급 위험도 평가 결과."""
    level: str = "none"  # "emergency" | "concern" | "none"
    matched_keywords: list[str] = field(default_factory=list)

    @property
    def is_emergency(self) -> bool:
        return self.level == "emergency"

    @property
    def is_concern(self) -> bool:
        return self.level == "concern"

    @property
    def needs_emergency_banner(self) -> bool:
        """프론트엔드에 응급 배너를 노출해야 하는 수준인지."""
        return self.level in ("emergency", "concern")

    def message(self) -> str:
        """레벨에 맞는 사용자 안내 메시지."""
        if self.level == "emergency":
            return EMERGENCY_MESSAGE
        if self.level == "concern":
            return CONCERN_MESSAGE
        return ""

    def to_dict(self) -> dict:
        return {
            "level": self.level,
            "matched_keywords": self.matched_keywords,
            "message": self.message(),
        }


def assess(text: str | None) -> SafetyAssessment:
    """텍스트에서 응급/주의 키워드를 감지해 SafetyAssessment 반환.

    None 또는 빈 문자열은 항상 level=none. emergency가 하나라도 매칭되면
    concern 매칭 여부와 무관하게 emergency로 격상.
    """
    if not text:
        return SafetyAssessment()

    matched_emergency: list[str] = []
    for pattern, regex in zip(_EMERGENCY_PATTERNS, _EMERGENCY_REGEX):
        if regex.search(text):
            matched_emergency.append(pattern)

    if matched_emergency:
        return SafetyAssessment(level="emergency", matched_keywords=matched_emergency)

    matched_concern: list[str] = []
    for pattern, regex in zip(_CONCERN_PATTERNS, _CONCERN_REGEX):
        if regex.search(text):
            matched_concern.append(pattern)

    if matched_concern:
        return SafetyAssessment(level="concern", matched_keywords=matched_concern)

    return SafetyAssessment()


def assess_many(texts: Iterable[str | None]) -> SafetyAssessment:
    """여러 텍스트(질문, 증상 입력 등)를 합쳐서 평가. 가장 높은 레벨 반환."""
    parts = [t for t in texts if t]
    if not parts:
        return SafetyAssessment()
    return assess(" ".join(parts))
