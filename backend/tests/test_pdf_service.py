"""PDF 서비스 테스트

실행 방법:
    cd C:\GIT\AllergyInsight\backend
    pip install -r requirements.txt
    python tests/test_pdf_service.py
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.services.pdf_service import PDFService, format_summary_as_text
from app.services.paper_search_service import PaperSearchService


def test_pdf_download_and_extract():
    """PDF 다운로드 및 텍스트 추출 테스트"""
    print("\n" + "=" * 60)
    print("PDF 다운로드 및 텍스트 추출 테스트")
    print("=" * 60)

    # 1. 먼저 오픈 액세스 논문 검색
    search_service = PaperSearchService()
    result = search_service.search(
        "food allergy mechanisms",
        max_results_per_source=10,
    )

    # PDF URL이 있는 논문 찾기
    paper_with_pdf = None
    for paper in result.papers:
        if paper.pdf_url:
            paper_with_pdf = paper
            break

    if not paper_with_pdf:
        print("PDF URL이 있는 논문을 찾지 못했습니다.")
        print("수동으로 PDF 파일을 테스트하세요.")
        return None

    print(f"\n선택된 논문: {paper_with_pdf.title[:60]}...")
    print(f"PDF URL: {paper_with_pdf.pdf_url}")

    # 2. PDF 다운로드 및 처리
    pdf_service = PDFService(download_dir="./downloads/papers")

    pdf_path = pdf_service.download_pdf(paper_with_pdf.pdf_url)
    if not pdf_path:
        print("PDF 다운로드 실패")
        return None

    print(f"다운로드 완료: {pdf_path}")

    # 3. 텍스트 추출
    doc = pdf_service.extract_text(pdf_path)
    if not doc:
        print("텍스트 추출 실패")
        return None

    print(f"\n--- 추출 결과 ---")
    print(f"제목: {doc.title}")
    print(f"총 페이지: {doc.total_pages}")
    print(f"총 문자 수: {doc.total_chars:,}")
    print(f"총 단어 수: {doc.total_words:,}")
    print(f"섹션 수: {len(doc.sections)}")

    print("\n--- 섹션 목록 ---")
    for section in doc.sections:
        content_preview = section.content[:100].replace("\n", " ")
        print(f"  - {section.title}: {content_preview}...")

    search_service.close()
    return doc


def test_keyword_search_in_pdf():
    """PDF 내 키워드 검색 테스트"""
    print("\n" + "=" * 60)
    print("PDF 내 키워드 검색 테스트")
    print("=" * 60)

    # 기존에 다운로드한 PDF가 있다고 가정
    pdf_service = PDFService(download_dir="./downloads/papers")

    # downloads 폴더에서 PDF 파일 찾기
    download_dir = "./downloads/papers"
    pdf_files = []
    if os.path.exists(download_dir):
        pdf_files = [f for f in os.listdir(download_dir) if f.endswith(".pdf")]

    if not pdf_files:
        print("테스트할 PDF 파일이 없습니다.")
        print("먼저 test_pdf_download_and_extract()를 실행하세요.")
        return None

    pdf_path = os.path.join(download_dir, pdf_files[0])
    print(f"테스트 파일: {pdf_path}")

    # 텍스트 추출
    doc = pdf_service.extract_text(pdf_path)
    if not doc:
        print("텍스트 추출 실패")
        return None

    # 키워드 검색
    keywords = ["allergy", "cross-reactivity", "IgE", "immunotherapy"]

    print("\n--- 키워드 검색 결과 ---")
    for keyword in keywords:
        results = doc.search_text(keyword, context_chars=100)
        print(f"\n'{keyword}': {len(results)}건 발견")
        if results:
            # 첫 번째 결과만 출력
            ctx = results[0]["context"].replace("\n", " ")[:150]
            print(f"  예시: ...{ctx}...")

    return doc


def test_create_summary():
    """PDF 요약본 생성 테스트"""
    print("\n" + "=" * 60)
    print("PDF 요약본 생성 테스트")
    print("=" * 60)

    pdf_service = PDFService(download_dir="./downloads/papers")

    # downloads 폴더에서 PDF 파일 찾기
    download_dir = "./downloads/papers"
    pdf_files = []
    if os.path.exists(download_dir):
        pdf_files = [f for f in os.listdir(download_dir) if f.endswith(".pdf")]

    if not pdf_files:
        print("테스트할 PDF 파일이 없습니다.")
        return None

    pdf_path = os.path.join(download_dir, pdf_files[0])
    print(f"테스트 파일: {pdf_path}")

    # 텍스트 추출
    doc = pdf_service.extract_text(pdf_path)
    if not doc:
        print("텍스트 추출 실패")
        return None

    # 요약본 생성
    keywords = ["allergy", "cross-reactivity", "treatment"]
    summary = pdf_service.create_summary(doc, keywords)

    print("\n--- 요약본 ---")
    print(f"제목: {summary.title}")
    print(f"Abstract 길이: {len(summary.abstract)}자")

    if summary.abstract:
        print(f"\nAbstract 미리보기:")
        print(summary.abstract[:300] + "...")

    print(f"\n주요 섹션: {len(summary.key_sections)}개")
    for section in summary.key_sections:
        print(f"  - {section.title}")

    print(f"\n키워드별 관련 문장:")
    for keyword, sentences in summary.keywords_found.items():
        print(f"\n  [{keyword}] - {len(sentences)}개 문장")
        if sentences:
            print(f"    예: {sentences[0][:100]}...")

    # 텍스트로 포맷팅
    print("\n--- 포맷팅된 요약본 ---")
    formatted = format_summary_as_text(summary)
    # 처음 1000자만 출력
    print(formatted[:1000])
    if len(formatted) > 1000:
        print("... (이하 생략)")

    return summary


def test_full_pipeline():
    """전체 파이프라인 테스트 (검색 -> 다운로드 -> 요약)"""
    print("\n" + "=" * 60)
    print("전체 파이프라인 테스트")
    print("=" * 60)

    # 1. 논문 검색
    search_service = PaperSearchService()
    pdf_service = PDFService(download_dir="./downloads/papers")

    allergen = "peanut"
    print(f"\n1. '{allergen}' 알러지 관련 논문 검색...")

    result = search_service.search_allergy(allergen, max_results_per_source=10)
    print(f"   검색 결과: {result.total_unique}개")
    print(f"   PDF 다운로드 가능: {result.downloadable_count}개")

    # 2. PDF 있는 논문 처리
    processed = 0
    for paper in result.papers:
        if not paper.pdf_url:
            continue

        print(f"\n2. 논문 처리: {paper.title[:50]}...")

        # 다운로드
        pdf_path = pdf_service.download_pdf(paper.pdf_url)
        if not pdf_path:
            print("   다운로드 실패, 다음 논문으로...")
            continue

        print(f"   다운로드 완료: {pdf_path}")

        # 텍스트 추출
        doc = pdf_service.extract_text(pdf_path)
        if not doc:
            print("   텍스트 추출 실패")
            continue

        print(f"   텍스트 추출: {doc.total_words:,}단어")

        # 요약본 생성
        keywords = [allergen, "cross-reactivity", "IgE", "treatment"]
        summary = pdf_service.create_summary(doc, keywords)

        print(f"\n3. 요약본 생성 완료")
        print(f"   Abstract: {len(summary.abstract)}자")
        print(f"   주요 섹션: {len(summary.key_sections)}개")
        print(f"   키워드 매칭: {sum(len(v) for v in summary.keywords_found.values())}개 문장")

        processed += 1
        if processed >= 1:  # 1개만 테스트
            break

    search_service.close()

    if processed == 0:
        print("\n처리된 논문이 없습니다.")
    else:
        print(f"\n총 {processed}개 논문 처리 완료!")


if __name__ == "__main__":
    print("=" * 60)
    print("AllergyInsight PDF 서비스 테스트")
    print("=" * 60)

    try:
        # 1. PDF 다운로드 및 추출 테스트
        doc = test_pdf_download_and_extract()

        if doc:
            # 2. 키워드 검색 테스트
            test_keyword_search_in_pdf()

            # 3. 요약본 생성 테스트
            test_create_summary()

        # 4. 전체 파이프라인 테스트
        # test_full_pipeline()  # 시간이 오래 걸릴 수 있음

        print("\n" + "=" * 60)
        print("테스트 완료!")
        print("=" * 60)

    except Exception as e:
        print(f"\n오류 발생: {e}")
        import traceback
        traceback.print_exc()
