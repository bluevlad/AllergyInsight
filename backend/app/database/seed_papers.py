"""Seed sample papers for testing"""
from datetime import datetime
from sqlalchemy.orm import Session
from .connection import SessionLocal
from .models import Paper, PaperAllergenLink


SAMPLE_PAPERS = [
    # 식품 알러지 가이드라인
    {
        "pmid": "35922095",
        "doi": "10.1016/j.jaci.2022.05.010",
        "title": "EAACI guidelines on the diagnosis of IgE-mediated food allergy",
        "title_kr": "EAACI IgE 매개 식품 알러지 진단 가이드라인",
        "authors": "Santos AF, Riggioni C, et al.",
        "journal": "Allergy",
        "year": 2023,
        "abstract": "European Academy guidelines for diagnosis of food allergies including clinical history, skin prick tests, and serum IgE measurements.",
        "url": "https://pubmed.ncbi.nlm.nih.gov/35922095/",
        "paper_type": "guideline",
        "is_verified": True,
        "links": [
            {"allergen_code": "peanut", "link_type": "symptom", "relevance_score": 95},
            {"allergen_code": "milk", "link_type": "symptom", "relevance_score": 95},
            {"allergen_code": "egg", "link_type": "symptom", "relevance_score": 95},
            {"allergen_code": "peanut", "link_type": "dietary", "relevance_score": 90},
        ]
    },
    # 아나필락시스 가이드라인
    {
        "pmid": "32178988",
        "doi": "10.1016/j.jaci.2020.01.025",
        "title": "World Allergy Organization Anaphylaxis Guidance 2020",
        "title_kr": "세계알러지기구 아나필락시스 가이드라인 2020",
        "authors": "Cardona V, Ansotegui IJ, et al.",
        "journal": "World Allergy Organ J",
        "year": 2020,
        "abstract": "Global guidance for recognition, treatment, and prevention of anaphylaxis, including epinephrine administration.",
        "url": "https://pubmed.ncbi.nlm.nih.gov/32178988/",
        "paper_type": "guideline",
        "is_verified": True,
        "links": [
            {"allergen_code": "peanut", "link_type": "emergency", "relevance_score": 100},
            {"allergen_code": "milk", "link_type": "emergency", "relevance_score": 100},
            {"allergen_code": "shellfish", "link_type": "emergency", "relevance_score": 100},
            {"allergen_code": "tree_nuts", "link_type": "emergency", "relevance_score": 100},
        ]
    },
    # 우유 알러지 리뷰
    {
        "pmid": "35103282",
        "doi": "10.3390/nu14030607",
        "title": "Cow's Milk Allergy: From Allergens to New Forms of Diagnosis, Therapy and Prevention",
        "title_kr": "우유 알러지: 알러젠부터 새로운 진단, 치료 및 예방법까지",
        "authors": "Villa C, Costa J, et al.",
        "journal": "Nutrients",
        "year": 2022,
        "abstract": "Comprehensive review of cow's milk allergy including cross-reactivity with other mammalian milks.",
        "url": "https://pubmed.ncbi.nlm.nih.gov/35103282/",
        "paper_type": "review",
        "is_verified": True,
        "links": [
            {"allergen_code": "milk", "link_type": "symptom", "relevance_score": 90},
            {"allergen_code": "milk", "link_type": "cross_reactivity", "relevance_score": 95},
            {"allergen_code": "milk", "link_type": "dietary", "relevance_score": 85},
        ]
    },
    # 땅콩 알러지 교차반응
    {
        "pmid": "31609450",
        "doi": "10.1016/j.jaci.2019.08.043",
        "title": "Cross-reactivity between peanut and tree nuts: Diagnostic implications",
        "title_kr": "땅콩과 견과류의 교차반응: 진단적 의의",
        "authors": "Maloney JM, Rudengren M, et al.",
        "journal": "J Allergy Clin Immunol",
        "year": 2019,
        "abstract": "Analysis of cross-reactivity patterns between peanuts and various tree nuts, with clinical recommendations.",
        "url": "https://pubmed.ncbi.nlm.nih.gov/31609450/",
        "paper_type": "research",
        "is_verified": True,
        "links": [
            {"allergen_code": "peanut", "link_type": "cross_reactivity", "relevance_score": 95},
            {"allergen_code": "tree_nuts", "link_type": "cross_reactivity", "relevance_score": 95},
        ]
    },
    # 식품 대체 가이드
    {
        "pmid": "29618616",
        "doi": "10.1016/j.jand.2017.12.006",
        "title": "Nutritional management of food allergy: Practice guidelines for dietitians",
        "title_kr": "식품 알러지 영양 관리: 영양사를 위한 실무 가이드라인",
        "authors": "Venter C, Groetch M, et al.",
        "journal": "J Acad Nutr Diet",
        "year": 2018,
        "abstract": "Evidence-based guidelines for dietary management and nutritional counseling in food allergy patients.",
        "url": "https://pubmed.ncbi.nlm.nih.gov/29618616/",
        "paper_type": "guideline",
        "is_verified": True,
        "links": [
            {"allergen_code": "milk", "link_type": "dietary", "relevance_score": 95},
            {"allergen_code": "egg", "link_type": "dietary", "relevance_score": 95},
            {"allergen_code": "wheat", "link_type": "dietary", "relevance_score": 90},
            {"allergen_code": "soy", "link_type": "dietary", "relevance_score": 90},
        ]
    },
    # 갑각류 알러지
    {
        "pmid": "30075648",
        "doi": "10.1111/cea.13235",
        "title": "Shellfish allergy: Clinical patterns, diagnosis, and management",
        "title_kr": "갑각류 알러지: 임상 양상, 진단 및 관리",
        "authors": "Ruethers T, Taki AC, et al.",
        "journal": "Clin Exp Allergy",
        "year": 2018,
        "abstract": "Review of shellfish allergy including tropomyosin-mediated reactions and cross-reactivity with other invertebrates.",
        "url": "https://pubmed.ncbi.nlm.nih.gov/30075648/",
        "paper_type": "review",
        "is_verified": True,
        "links": [
            {"allergen_code": "shellfish", "link_type": "symptom", "relevance_score": 95},
            {"allergen_code": "shellfish", "link_type": "cross_reactivity", "relevance_score": 90},
            {"allergen_code": "shellfish", "link_type": "dietary", "relevance_score": 85},
        ]
    },
    # 집먼지진드기 관리
    {
        "pmid": "28802610",
        "doi": "10.1016/j.jaci.2017.06.003",
        "title": "House dust mite control measures for asthma: Systematic review",
        "title_kr": "천식 환자를 위한 집먼지진드기 관리 방법: 체계적 문헌고찰",
        "authors": "Custovic A, Tovey E, et al.",
        "journal": "J Allergy Clin Immunol",
        "year": 2017,
        "abstract": "Meta-analysis of environmental control measures for dust mite allergen reduction.",
        "url": "https://pubmed.ncbi.nlm.nih.gov/28802610/",
        "paper_type": "meta_analysis",
        "is_verified": True,
        "links": [
            {"allergen_code": "dust_mite", "link_type": "management", "relevance_score": 95},
        ]
    },
    # 꽃가루 알러지
    {
        "pmid": "33169618",
        "doi": "10.1111/all.14586",
        "title": "EAACI position paper on management of pollen food syndrome",
        "title_kr": "EAACI 꽃가루-식품 증후군 관리 포지션 페이퍼",
        "authors": "Werfel T, Asero R, et al.",
        "journal": "Allergy",
        "year": 2021,
        "abstract": "Guidelines on oral allergy syndrome and cross-reactivity between pollen and foods.",
        "url": "https://pubmed.ncbi.nlm.nih.gov/33169618/",
        "paper_type": "guideline",
        "is_verified": True,
        "links": [
            {"allergen_code": "pollen", "link_type": "symptom", "relevance_score": 90},
            {"allergen_code": "pollen", "link_type": "cross_reactivity", "relevance_score": 95},
            {"allergen_code": "pollen", "link_type": "management", "relevance_score": 85},
        ]
    },
]


def seed_papers(db: Session = None):
    """Seed sample papers into database"""
    if db is None:
        db = SessionLocal()
        close_db = True
    else:
        close_db = False

    try:
        added = 0
        for paper_data in SAMPLE_PAPERS:
            # Check if paper already exists
            existing = db.query(Paper).filter(
                (Paper.pmid == paper_data.get("pmid")) |
                (Paper.doi == paper_data.get("doi"))
            ).first()

            if existing:
                print(f"Paper already exists: {paper_data['title'][:50]}...")
                continue

            # Create paper
            links_data = paper_data.pop("links", [])
            paper = Paper(**paper_data)
            db.add(paper)
            db.flush()

            # Create links
            for link_data in links_data:
                link = PaperAllergenLink(
                    paper_id=paper.id,
                    **link_data
                )
                db.add(link)

            added += 1
            print(f"Added: {paper_data['title'][:50]}...")

        db.commit()
        print(f"\nSeeded {added} papers successfully!")

    except Exception as e:
        db.rollback()
        print(f"Error seeding papers: {e}")
        raise

    finally:
        if close_db:
            db.close()


if __name__ == "__main__":
    seed_papers()
