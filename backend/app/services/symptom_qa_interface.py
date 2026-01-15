"""증상 질문 인터페이스

대화형으로 알러지 증상에 대해 질문하고 답변을 받는 인터페이스입니다.
모든 답변에 논문 출처가 포함됩니다.
"""
import json
from typing import Optional
from dataclasses import dataclass, field
from datetime import datetime

from ..models.knowledge_base import QAResponse, Citation
from .qa_engine import QAEngine


@dataclass
class ConversationMessage:
    """대화 메시지"""
    role: str  # "user" or "assistant"
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    citations: list[Citation] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)


@dataclass
class ConversationSession:
    """대화 세션"""
    session_id: str
    allergen: str
    messages: list[ConversationMessage] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)

    def add_user_message(self, content: str):
        """사용자 메시지 추가"""
        self.messages.append(ConversationMessage(
            role="user",
            content=content,
        ))

    def add_assistant_message(self, content: str, citations: list[Citation] = None):
        """어시스턴트 메시지 추가"""
        self.messages.append(ConversationMessage(
            role="assistant",
            content=content,
            citations=citations or [],
        ))

    def to_dict(self) -> dict:
        return {
            "session_id": self.session_id,
            "allergen": self.allergen,
            "messages": [
                {
                    "role": m.role,
                    "content": m.content,
                    "timestamp": m.timestamp.isoformat(),
                    "citations": [c.to_dict() for c in m.citations],
                }
                for m in self.messages
            ],
            "created_at": self.created_at.isoformat(),
        }


class SymptomQAInterface:
    """증상 질문 인터페이스"""

    # 빠른 질문 버튼
    QUICK_QUESTIONS = {
        "ko": [
            ("증상", "주요 증상은 무엇인가요?"),
            ("위험성", "얼마나 위험한가요?"),
            ("교차반응", "다른 음식도 조심해야 하나요?"),
            ("응급처치", "응급 상황에서 어떻게 해야 하나요?"),
            ("발현시간", "증상이 얼마나 빨리 나타나나요?"),
        ],
        "en": [
            ("Symptoms", "What are the main symptoms?"),
            ("Severity", "How dangerous is it?"),
            ("Cross-reactivity", "Should I avoid other foods?"),
            ("Emergency", "What should I do in an emergency?"),
            ("Onset", "How quickly do symptoms appear?"),
        ],
    }

    def __init__(self, allergen: str = "peanut", language: str = "ko"):
        """
        Args:
            allergen: 알러지 항원 (예: "peanut", "milk")
            language: 언어 ("ko" 또는 "en")
        """
        self.allergen = allergen
        self.language = language
        self.qa_engine = QAEngine()
        self._sessions: dict[str, ConversationSession] = {}
        self._current_session: Optional[ConversationSession] = None

    def start_session(self) -> ConversationSession:
        """새 대화 세션 시작"""
        import hashlib
        import time

        session_id = hashlib.md5(f"{time.time()}".encode()).hexdigest()[:12]

        session = ConversationSession(
            session_id=session_id,
            allergen=self.allergen,
        )

        # 환영 메시지
        welcome = self._get_welcome_message()
        session.add_assistant_message(welcome)

        self._sessions[session_id] = session
        self._current_session = session

        return session

    def _get_welcome_message(self) -> str:
        """환영 메시지 생성"""
        allergen_kr = self._get_allergen_korean(self.allergen)

        if self.language == "ko":
            return f"""안녕하세요! **{allergen_kr} ({self.allergen}) 알러지**에 대해 질문해주세요.

논문 기반으로 답변드리며, 모든 정보에 **출처(Reference)**가 포함됩니다.

### 빠른 질문
{self._format_quick_questions()}

또는 자유롭게 질문해주세요!"""
        else:
            return f"""Hello! Ask me about **{self.allergen} allergy**.

All answers are based on scientific papers with **citations**.

### Quick Questions
{self._format_quick_questions()}

Or feel free to ask anything!"""

    def _format_quick_questions(self) -> str:
        """빠른 질문 포맷팅"""
        questions = self.QUICK_QUESTIONS.get(self.language, self.QUICK_QUESTIONS["en"])
        lines = []
        for i, (label, question) in enumerate(questions, 1):
            lines.append(f"{i}. **{label}**: {question}")
        return "\n".join(lines)

    def _get_allergen_korean(self, allergen: str) -> str:
        """알러지 항원 한글명"""
        mapping = {
            "peanut": "땅콩",
            "milk": "우유",
            "egg": "계란",
            "wheat": "밀",
            "soy": "대두",
            "fish": "생선",
            "shellfish": "갑각류",
            "tree nut": "견과류",
        }
        return mapping.get(allergen.lower(), allergen)

    def ask(self, question: str, session_id: Optional[str] = None) -> QAResponse:
        """
        질문하기

        Args:
            question: 사용자 질문
            session_id: 세션 ID (없으면 현재 세션 사용)

        Returns:
            QAResponse: 답변 및 출처
        """
        # 세션 확인
        if session_id and session_id in self._sessions:
            session = self._sessions[session_id]
        elif self._current_session:
            session = self._current_session
        else:
            session = self.start_session()

        # 사용자 메시지 추가
        session.add_user_message(question)

        # 빠른 질문 번호 처리
        question = self._handle_quick_question(question)

        # Q&A 엔진으로 답변 생성
        response = self.qa_engine.ask(
            question=question,
            allergen=self.allergen,
            max_citations=5,
        )

        # 어시스턴트 메시지 추가
        formatted_answer = response.format_with_citations()
        session.add_assistant_message(formatted_answer, response.citations)

        return response

    def _handle_quick_question(self, question: str) -> str:
        """빠른 질문 번호를 실제 질문으로 변환"""
        question = question.strip()

        # 숫자만 입력된 경우
        if question.isdigit():
            idx = int(question) - 1
            questions = self.QUICK_QUESTIONS.get(self.language, self.QUICK_QUESTIONS["en"])
            if 0 <= idx < len(questions):
                return questions[idx][1]

        return question

    def get_session_history(self, session_id: Optional[str] = None) -> list[dict]:
        """세션 대화 기록 조회"""
        if session_id and session_id in self._sessions:
            session = self._sessions[session_id]
        elif self._current_session:
            session = self._current_session
        else:
            return []

        return [
            {
                "role": m.role,
                "content": m.content,
                "timestamp": m.timestamp.isoformat(),
                "citation_count": len(m.citations),
            }
            for m in session.messages
        ]

    def export_session(self, session_id: Optional[str] = None, format: str = "json") -> str:
        """세션 내보내기"""
        if session_id and session_id in self._sessions:
            session = self._sessions[session_id]
        elif self._current_session:
            session = self._current_session
        else:
            return ""

        if format == "json":
            return json.dumps(session.to_dict(), ensure_ascii=False, indent=2)

        elif format == "markdown":
            lines = [
                f"# {self._get_allergen_korean(self.allergen)} 알러지 Q&A",
                f"세션 ID: {session.session_id}",
                f"생성일: {session.created_at.strftime('%Y-%m-%d %H:%M')}",
                "",
                "---",
                "",
            ]

            for msg in session.messages:
                role_label = "👤 질문" if msg.role == "user" else "🤖 답변"
                lines.append(f"### {role_label}")
                lines.append(msg.content)
                lines.append("")

            return "\n".join(lines)

        return ""

    def change_allergen(self, allergen: str):
        """알러지 항원 변경"""
        self.allergen = allergen
        # 새 세션 시작
        self.start_session()

    def close(self):
        """리소스 정리"""
        self.qa_engine.close()


def run_interactive_session(allergen: str = "peanut"):
    """
    대화형 세션 실행 (CLI용)

    Args:
        allergen: 알러지 항원
    """
    interface = SymptomQAInterface(allergen=allergen, language="ko")
    session = interface.start_session()

    print("\n" + "=" * 60)
    print(session.messages[0].content)
    print("=" * 60)
    print("\n(종료하려면 'quit' 또는 'exit' 입력)\n")

    while True:
        try:
            user_input = input("질문: ").strip()

            if not user_input:
                continue

            if user_input.lower() in ["quit", "exit", "종료"]:
                print("\n세션을 종료합니다.")
                break

            if user_input.lower() == "export":
                export = interface.export_session(format="markdown")
                print("\n" + export)
                continue

            # 질문 처리
            print("\n검색 중...")
            response = interface.ask(user_input)

            print("\n" + "-" * 60)
            print(response.format_with_citations())
            print("-" * 60)
            print(f"\n신뢰도: {response.confidence:.0%}")
            print(f"인용 논문: {len(response.citations)}개\n")

        except KeyboardInterrupt:
            print("\n\n세션을 종료합니다.")
            break

    interface.close()


if __name__ == "__main__":
    run_interactive_session("peanut")
