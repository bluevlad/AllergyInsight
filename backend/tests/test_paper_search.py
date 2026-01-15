"""논문 검색 서비스 테스트

실행 방법:
    cd C:\GIT\AllergyInsight\backend
    pip install -r requirements.txt
    python -m pytest tests/test_paper_search.py -v

또는 직접 실행:
    python tests/test_paper_search.py
"""
import sys
import os

# 상위 디렉토리를 path에 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.services.pubmed_service import PubMedService
from app.services.semantic_scholar_service import SemanticScholarService
from app.services.paper_search_service import PaperSearchService
from app.models.paper import PaperSource


def test_pubmed_search():
    """PubMed 검색 테스트"""
    print("\n" + "=" * 60)
    print("PubMed 검색 테스트")
    print("=" * 60)

    service = PubMedService()

    # 일반 검색
    result = service.search("peanut allergy cross-reactivity", max_results=5)

    print(f"\n검색어: {result.query}")
    print(f"총 결과 수: {result.total_count}")
    print(f"가져온 논문 수: {len(result.papers)}")
    print(f"검색 시간: {result.search_time_ms:.2f}ms")

    for i, paper in enumerate(result.papers, 1):
        print(f"\n--- 논문 {i} ---")
        print(f"제목: {paper.title[:80]}...")
        print(f"저자: {', '.join(paper.authors[:3])}{'...' if len(paper.authors) > 3 else ''}")
        print(f"연도: {paper.year}")
        print(f"저널: {paper.journal}")
        print(f"PMID: {paper.source_id}")
        print(f"DOI: {paper.doi}")
        if paper.abstract:
            print(f"초록: {paper.abstract[:150]}...")

    return result


def test_pubmed_allergy_search():
    """PubMed 알러지 특화 검색 테스트"""
    print("\n" + "=" * 60)
    print("PubMed 알러지 특화 검색 테스트")
    print("=" * 60)

    service = PubMedService()

    # 알러지 특화 검색
    result = service.search_allergy_papers("milk", include_cross_reactivity=True, max_results=3)

    print(f"\n검색어: {result.query}")
    print(f"총 결과 수: {result.total_count}")

    for paper in result.papers:
        print(f"\n- {paper.title[:70]}...")
        print(f"  키워드: {', '.join(paper.keywords[:5])}")

    return result


def test_semantic_scholar_search():
    """Semantic Scholar 검색 테스트"""
    print("\n" + "=" * 60)
    print("Semantic Scholar 검색 테스트")
    print("=" * 60)

    service = SemanticScholarService()

    # 일반 검색
    result = service.search("food allergy immunotherapy", max_results=5)

    print(f"\n검색어: {result.query}")
    print(f"총 결과 수: {result.total_count}")
    print(f"가져온 논문 수: {len(result.papers)}")
    print(f"검색 시간: {result.search_time_ms:.2f}ms")

    for i, paper in enumerate(result.papers, 1):
        print(f"\n--- 논문 {i} ---")
        print(f"제목: {paper.title[:80]}...")
        print(f"저자: {', '.join(paper.authors[:3])}{'...' if len(paper.authors) > 3 else ''}")
        print(f"연도: {paper.year}")
        print(f"인용 수: {paper.citation_count}")
        print(f"PDF URL: {paper.pdf_url or '없음'}")
        print(f"DOI: {paper.doi}")

    return result


def test_semantic_scholar_open_access():
    """Semantic Scholar 오픈 액세스 검색 테스트"""
    print("\n" + "=" * 60)
    print("Semantic Scholar 오픈 액세스 검색 테스트")
    print("=" * 60)

    service = SemanticScholarService()

    # 오픈 액세스만 검색
    result = service.search(
        "egg allergy",
        max_results=5,
        open_access_only=True,
        fields_of_study=["Medicine"],
    )

    print(f"\n검색어: {result.query} (오픈 액세스만)")
    print(f"가져온 논문 수: {len(result.papers)}")

    pdf_count = sum(1 for p in result.papers if p.pdf_url)
    print(f"PDF 다운로드 가능: {pdf_count}개")

    for paper in result.papers:
        if paper.pdf_url:
            print(f"\n- {paper.title[:60]}...")
            print(f"  PDF: {paper.pdf_url}")

    return result


def test_unified_search():
    """통합 검색 테스트"""
    print("\n" + "=" * 60)
    print("통합 검색 테스트 (PubMed + Semantic Scholar)")
    print("=" * 60)

    service = PaperSearchService()

    result = service.search("shrimp allergy cross-reactivity", max_results_per_source=5)

    print(f"\n검색어: {result.query}")
    print(f"PubMed 결과: {result.pubmed_count}개")
    print(f"Semantic Scholar 결과: {result.semantic_scholar_count}개")
    print(f"중복 제거 후: {result.total_unique}개")
    print(f"PDF 다운로드 가능: {result.downloadable_count}개")
    print(f"검색 시간: {result.search_time_ms:.2f}ms")

    print("\n--- 통합 결과 ---")
    for i, paper in enumerate(result.papers[:5], 1):
        source_name = "PubMed" if paper.source == PaperSource.PUBMED else "S2"
        print(f"\n{i}. [{source_name}] {paper.title[:60]}...")
        print(f"   DOI: {paper.doi or '없음'}")
        print(f"   PDF: {'있음' if paper.pdf_url else '없음'}")

    service.close()
    return result


def test_allergy_unified_search():
    """알러지 특화 통합 검색 테스트"""
    print("\n" + "=" * 60)
    print("알러지 특화 통합 검색 테스트")
    print("=" * 60)

    service = PaperSearchService()

    allergens = ["peanut", "milk", "egg"]

    for allergen in allergens:
        print(f"\n### {allergen.upper()} 알러지 검색 ###")
        result = service.search_allergy(allergen, max_results_per_source=3)

        print(f"총 논문: {result.total_unique}개")
        print(f"PDF 가능: {result.downloadable_count}개")

        # 상위 2개만 출력
        for paper in result.papers[:2]:
            print(f"  - {paper.title[:50]}...")

    service.close()


if __name__ == "__main__":
    print("=" * 60)
    print("AllergyInsight 논문 검색 테스트")
    print("=" * 60)

    try:
        # 1. PubMed 테스트
        test_pubmed_search()
        test_pubmed_allergy_search()

        # 2. Semantic Scholar 테스트
        test_semantic_scholar_search()
        test_semantic_scholar_open_access()

        # 3. 통합 검색 테스트
        test_unified_search()
        test_allergy_unified_search()

        print("\n" + "=" * 60)
        print("모든 테스트 완료!")
        print("=" * 60)

    except Exception as e:
        print(f"\n오류 발생: {e}")
        import traceback
        traceback.print_exc()
