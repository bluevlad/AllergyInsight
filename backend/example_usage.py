"""AllergyInsight 사용 예제

이 스크립트는 논문 검색, PDF 다운로드, 요약 생성의
전체 워크플로우를 보여줍니다.

실행 방법:
    cd C:\GIT\AllergyInsight\backend
    pip install -r requirements.txt
    python example_usage.py
"""
from app.services import (
    PubMedService,
    SemanticScholarService,
    PaperSearchService,
    PDFService,
)
from app.services.pdf_service import format_summary_as_text


def example_1_basic_pubmed_search():
    """예제 1: 기본 PubMed 검색"""
    print("\n" + "=" * 60)
    print("예제 1: PubMed에서 알러지 논문 검색")
    print("=" * 60)

    service = PubMedService()

    # 땅콩 알러지 교차 반응 논문 검색
    result = service.search_allergy_papers(
        allergen="peanut",
        include_cross_reactivity=True,
        max_results=5,
    )

    print(f"\n검색 결과: {result.total_count}개 논문 발견")
    print(f"가져온 논문: {len(result.papers)}개")

    for i, paper in enumerate(result.papers, 1):
        print(f"\n[{i}] {paper.title}")
        print(f"    저자: {', '.join(paper.authors[:2])}...")
        print(f"    연도: {paper.year}")
        print(f"    PMID: {paper.source_id}")
        if paper.doi:
            print(f"    DOI: {paper.doi}")


def example_2_semantic_scholar_with_pdf():
    """예제 2: Semantic Scholar에서 PDF 있는 논문 검색"""
    print("\n" + "=" * 60)
    print("예제 2: Semantic Scholar에서 오픈 액세스 논문 검색")
    print("=" * 60)

    service = SemanticScholarService()

    # 우유 알러지 논문 (오픈 액세스만)
    result = service.search_allergy_papers(
        allergen="milk",
        include_cross_reactivity=True,
        max_results=10,
        open_access_only=True,
    )

    print(f"\n검색 결과: {result.total_count}개 논문 발견")

    pdf_papers = [p for p in result.papers if p.pdf_url]
    print(f"PDF 다운로드 가능: {len(pdf_papers)}개")

    for i, paper in enumerate(pdf_papers[:3], 1):
        print(f"\n[{i}] {paper.title[:60]}...")
        print(f"    인용 수: {paper.citation_count}")
        print(f"    PDF: {paper.pdf_url}")


def example_3_unified_search():
    """예제 3: 통합 검색 (PubMed + Semantic Scholar)"""
    print("\n" + "=" * 60)
    print("예제 3: 통합 검색으로 최대한 많은 논문 찾기")
    print("=" * 60)

    service = PaperSearchService()

    # 계란 알러지 통합 검색
    result = service.search_allergy(
        allergen="egg",
        include_cross_reactivity=True,
        max_results_per_source=10,
    )

    print(f"\n통합 검색 결과:")
    print(f"  - PubMed: {result.pubmed_count}개")
    print(f"  - Semantic Scholar: {result.semantic_scholar_count}개")
    print(f"  - 중복 제거 후: {result.total_unique}개")
    print(f"  - PDF 다운로드 가능: {result.downloadable_count}개")
    print(f"  - 검색 시간: {result.search_time_ms:.0f}ms")

    service.close()


def example_4_download_and_summarize():
    """예제 4: PDF 다운로드 및 요약"""
    print("\n" + "=" * 60)
    print("예제 4: 논문 PDF 다운로드 및 요약 생성")
    print("=" * 60)

    # 1. 논문 검색
    search_service = PaperSearchService()
    pdf_service = PDFService(download_dir="./downloads/papers")

    result = search_service.search_allergy("shrimp", max_results_per_source=10)

    # PDF 있는 논문 찾기
    paper = None
    for p in result.papers:
        if p.pdf_url:
            paper = p
            break

    if not paper:
        print("PDF가 있는 논문을 찾지 못했습니다.")
        search_service.close()
        return

    print(f"\n선택된 논문: {paper.title[:60]}...")

    # 2. PDF 다운로드
    print("\nPDF 다운로드 중...")
    pdf_path = pdf_service.download_pdf(paper.pdf_url)

    if not pdf_path:
        print("다운로드 실패")
        search_service.close()
        return

    print(f"저장됨: {pdf_path}")

    # 3. 텍스트 추출
    print("\n텍스트 추출 중...")
    doc = pdf_service.extract_text(pdf_path)

    if not doc:
        print("텍스트 추출 실패")
        search_service.close()
        return

    print(f"추출 완료: {doc.total_words:,}단어, {doc.total_pages}페이지")

    # 4. 요약 생성
    print("\n요약 생성 중...")
    keywords = ["shrimp", "allergy", "cross-reactivity", "tropomyosin"]
    summary = pdf_service.create_summary(doc, keywords)

    # 5. 결과 출력
    print("\n" + "-" * 40)
    print("요약 결과")
    print("-" * 40)

    formatted = format_summary_as_text(summary)
    print(formatted[:2000])
    if len(formatted) > 2000:
        print("\n... (이하 생략)")

    search_service.close()


def example_5_batch_search():
    """예제 5: 여러 알러지 항원 일괄 검색"""
    print("\n" + "=" * 60)
    print("예제 5: 여러 알러지 항원 일괄 검색")
    print("=" * 60)

    service = PaperSearchService()

    # 주요 식품 알러지 항원
    allergens = [
        "peanut",      # 땅콩
        "milk",        # 우유
        "egg",         # 계란
        "wheat",       # 밀
        "soy",         # 대두
        "tree nut",    # 견과류
        "fish",        # 생선
        "shellfish",   # 갑각류
    ]

    print("\n알러지 항원별 논문 검색 결과:\n")
    print(f"{'항원':<12} {'총 논문':<10} {'PDF 가능':<10}")
    print("-" * 35)

    for allergen in allergens:
        result = service.search_allergy(allergen, max_results_per_source=5)
        print(f"{allergen:<12} {result.total_unique:<10} {result.downloadable_count:<10}")

    service.close()


if __name__ == "__main__":
    print("=" * 60)
    print("AllergyInsight 사용 예제")
    print("=" * 60)

    try:
        # 기본 예제
        example_1_basic_pubmed_search()
        example_2_semantic_scholar_with_pdf()
        example_3_unified_search()

        # 일괄 검색
        example_5_batch_search()

        # PDF 다운로드 예제 (시간이 걸릴 수 있음)
        # example_4_download_and_summarize()

        print("\n" + "=" * 60)
        print("모든 예제 완료!")
        print("=" * 60)

    except Exception as e:
        print(f"\n오류 발생: {e}")
        import traceback
        traceback.print_exc()
