"""증상 Q&A 예제

땅콩 알러지에 대한 논문 기반 Q&A 시스템 예제입니다.
모든 답변에 출처(Citation)가 포함됩니다.

실행 방법:
    cd C:\GIT\AllergyInsight\backend
    pip install -r requirements.txt
    python example_symptom_qa.py
"""
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from app.services.qa_engine import QAEngine
from app.services.symptom_qa_interface import SymptomQAInterface


def example_1_basic_qa():
    """예제 1: 기본 Q&A"""
    print("\n" + "=" * 60)
    print("예제 1: 땅콩 알러지 기본 Q&A")
    print("=" * 60)

    engine = QAEngine()

    # 질문 목록
    questions = [
        "땅콩 알러지의 주요 증상은 무엇인가요?",
        "땅콩 알러지가 얼마나 위험한가요?",
        "땅콩 알러지가 있으면 다른 음식도 조심해야 하나요?",
    ]

    for question in questions:
        print(f"\n### 질문: {question}")
        print("-" * 50)

        response = engine.ask(question, allergen="peanut")

        # 답변 출력
        print(response.answer[:500])
        if len(response.answer) > 500:
            print("... (이하 생략)")

        # 출처 출력
        print(f"\n📚 출처 ({len(response.citations)}개):")
        for i, citation in enumerate(response.citations[:3], 1):
            print(f"  [{i}] {citation.format_short()}")
            if citation.doi:
                print(f"      DOI: {citation.doi}")

        print(f"\n✅ 신뢰도: {response.confidence:.0%}")

    engine.close()


def example_2_detailed_response():
    """예제 2: 상세 응답 (출처 포함)"""
    print("\n" + "=" * 60)
    print("예제 2: 출처 포함 상세 응답")
    print("=" * 60)

    engine = QAEngine()

    question = "땅콩 알러지의 증상과 위험성에 대해 알려주세요"
    print(f"\n질문: {question}\n")

    response = engine.ask(question, allergen="peanut", max_citations=5)

    # 전체 포맷팅된 응답 출력
    print(response.format_with_citations())

    # 메타 정보
    print("\n" + "=" * 40)
    print("메타 정보:")
    print(f"  - 관련 증상: {len(response.related_symptoms)}개")
    print(f"  - 교차 반응: {len(response.related_cross_reactivities)}개")
    print(f"  - 인용 논문: {len(response.citations)}개")
    print(f"  - 신뢰도: {response.confidence:.0%}")

    engine.close()


def example_3_citation_verification():
    """예제 3: 출처 검증"""
    print("\n" + "=" * 60)
    print("예제 3: 출처 검증 정보")
    print("=" * 60)

    engine = QAEngine()

    response = engine.ask("땅콩 알러지 증상", allergen="peanut")

    print("\n### 인용된 논문 상세 정보:\n")

    for i, citation in enumerate(response.citations, 1):
        print(f"[{i}] {citation.paper_title}")
        print(f"    저자: {', '.join(citation.authors[:3])}" +
              ("..." if len(citation.authors) > 3 else ""))
        print(f"    연도: {citation.year or 'N/A'}")
        print(f"    저널: {citation.journal or 'N/A'}")

        # 검증 링크
        if citation.doi:
            print(f"    🔗 DOI 링크: https://doi.org/{citation.doi}")
        if citation.pmid:
            print(f"    🔗 PubMed: https://pubmed.ncbi.nlm.nih.gov/{citation.pmid}/")

        # 관련 원문
        if citation.relevant_text:
            print(f"    📝 관련 텍스트:")
            text = citation.relevant_text[:200]
            print(f"       \"{text}...\"")

        print()

    engine.close()


def example_4_interactive_session():
    """예제 4: 대화형 세션"""
    print("\n" + "=" * 60)
    print("예제 4: 대화형 Q&A 세션")
    print("=" * 60)

    interface = SymptomQAInterface(allergen="peanut", language="ko")
    session = interface.start_session()

    # 환영 메시지
    print("\n" + session.messages[0].content)

    # 미리 정의된 질문들로 테스트
    test_questions = ["1", "2", "3"]  # 빠른 질문 번호

    for q in test_questions:
        print(f"\n{'=' * 40}")
        print(f"입력: {q}")

        response = interface.ask(q)

        print(f"\n{response.answer[:400]}...")
        print(f"\n📚 인용: {len(response.citations)}개 논문")

    # 세션 내보내기
    print("\n" + "=" * 40)
    print("세션 기록:")
    history = interface.get_session_history()
    for msg in history:
        role = "Q" if msg["role"] == "user" else "A"
        content = msg["content"][:50] + "..." if len(msg["content"]) > 50 else msg["content"]
        print(f"  [{role}] {content}")

    interface.close()


def example_5_export_report():
    """예제 5: 리포트 내보내기"""
    print("\n" + "=" * 60)
    print("예제 5: Q&A 리포트 내보내기")
    print("=" * 60)

    interface = SymptomQAInterface(allergen="peanut", language="ko")
    interface.start_session()

    # 여러 질문 수행
    questions = [
        "증상은 무엇인가요?",
        "위험한가요?",
    ]

    for q in questions:
        interface.ask(q)

    # 마크다운으로 내보내기
    export = interface.export_session(format="markdown")

    print("\n### 내보낸 리포트 (Markdown):\n")
    print(export[:1500])
    if len(export) > 1500:
        print("\n... (이하 생략)")

    interface.close()


def example_6_different_allergens():
    """예제 6: 다양한 알러지 항원"""
    print("\n" + "=" * 60)
    print("예제 6: 다양한 알러지 항원 Q&A")
    print("=" * 60)

    allergens = ["peanut", "milk", "egg"]

    for allergen in allergens:
        print(f"\n### {allergen.upper()} 알러지")
        print("-" * 40)

        engine = QAEngine()
        response = engine.ask(f"{allergen} 알러지 주요 증상", allergen=allergen)

        # 발견된 증상 수
        print(f"발견된 증상: {len(response.related_symptoms)}개")

        # 주요 증상 나열
        for symptom in response.related_symptoms[:5]:
            print(f"  - {symptom.name_kr} ({symptom.name}): {symptom.severity.value}")

        # 인용 수
        print(f"인용 논문: {len(response.citations)}개")

        engine.close()


def run_demo():
    """전체 데모 실행"""
    print("=" * 60)
    print("AllergyInsight 증상 Q&A 시스템 데모")
    print("=" * 60)

    print("""
이 데모는 땅콩 알러지에 대한 논문 기반 Q&A 시스템을 보여줍니다.

주요 기능:
1. 논문 검색 (PubMed + Semantic Scholar)
2. 증상 정보 추출
3. 질문-답변 생성
4. 출처(Citation) 표시
5. 검증 가능한 링크 제공

실행할 예제를 선택하세요:
1. 기본 Q&A
2. 상세 응답 (출처 포함)
3. 출처 검증 정보
4. 대화형 세션
5. 리포트 내보내기
6. 다양한 알러지 항원
0. 전체 실행
i. 대화형 모드 (직접 질문)
""")

    choice = input("선택 (0-6, i): ").strip().lower() or "0"

    try:
        if choice == "0":
            example_1_basic_qa()
            example_2_detailed_response()
            example_3_citation_verification()
            example_4_interactive_session()
            example_5_export_report()
            example_6_different_allergens()
        elif choice == "1":
            example_1_basic_qa()
        elif choice == "2":
            example_2_detailed_response()
        elif choice == "3":
            example_3_citation_verification()
        elif choice == "4":
            example_4_interactive_session()
        elif choice == "5":
            example_5_export_report()
        elif choice == "6":
            example_6_different_allergens()
        elif choice == "i":
            from app.services.symptom_qa_interface import run_interactive_session
            run_interactive_session("peanut")
            return

        print("\n" + "=" * 60)
        print("데모 완료!")
        print("=" * 60)

    except Exception as e:
        print(f"\n오류 발생: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    run_demo()
