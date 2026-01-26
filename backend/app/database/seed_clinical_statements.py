"""Seed clinical statements and guideline papers"""
from datetime import datetime
from sqlalchemy.orm import Session

from .connection import SessionLocal
from .models import Paper, PaperAllergenLink
from .clinical_models import ClinicalStatement


# Guideline papers
GUIDELINE_PAPERS = [
    {
        "pmid": "33745789",
        "doi": "10.1111/all.14854",
        "title": "EAACI guidelines: Anaphylaxis (2021 update)",
        "title_kr": "EAACI 가이드라인: 아나필락시스 (2021 업데이트)",
        "authors": "Muraro A, Worm M, Alviani C, et al.",
        "journal": "Allergy",
        "year": 2022,
        "abstract": "Anaphylaxis is a severe, potentially life-threatening systemic hypersensitivity reaction. This guideline update addresses recognition, risk factors, and management of anaphylaxis.",
        "paper_type": "guideline",
        "evidence_level": "A",
        "is_guideline": True,
        "guideline_org": "EAACI",
        "url": "https://pubmed.ncbi.nlm.nih.gov/33745789/",
    },
    {
        "pmid": "32628776",
        "doi": "10.1016/j.jaci.2020.05.035",
        "title": "AAAAI/ACAAI Practice parameter update: Food allergy",
        "title_kr": "AAAAI/ACAAI 진료 지침 업데이트: 식품 알레르기",
        "authors": "Sampson HA, Aceves S, Bock SA, et al.",
        "journal": "J Allergy Clin Immunol",
        "year": 2020,
        "abstract": "This practice parameter provides evidence-based recommendations for the diagnosis and management of food allergy.",
        "paper_type": "guideline",
        "evidence_level": "A",
        "is_guideline": True,
        "guideline_org": "AAAAI",
        "url": "https://pubmed.ncbi.nlm.nih.gov/32628776/",
    },
    {
        "pmid": "33040377",
        "doi": "10.1016/j.waojou.2020.100472",
        "title": "World Allergy Organization Anaphylaxis Guidance 2020",
        "title_kr": "세계알레르기기구 아나필락시스 가이드 2020",
        "authors": "Cardona V, Ansotegui IJ, Ebisawa M, et al.",
        "journal": "World Allergy Organ J",
        "year": 2020,
        "abstract": "This document provides updated guidance on the recognition and management of anaphylaxis worldwide.",
        "paper_type": "guideline",
        "evidence_level": "A",
        "is_guideline": True,
        "guideline_org": "WAO",
        "url": "https://pubmed.ncbi.nlm.nih.gov/33040377/",
    },
    {
        "pmid": "28602936",
        "doi": "10.1016/j.jaci.2017.03.024",
        "title": "Shellfish allergy: Tropomyosin as a major allergen",
        "title_kr": "갑각류 알레르기: 주요 알레르겐으로서의 트로포미오신",
        "authors": "Ruethers T, Taki AC, Johnston EB, et al.",
        "journal": "J Allergy Clin Immunol Pract",
        "year": 2018,
        "abstract": "Tropomyosin is the major allergen in shellfish causing cross-reactivity between crustaceans and mollusks.",
        "paper_type": "review",
        "evidence_level": "B",
        "is_guideline": False,
        "guideline_org": None,
        "url": "https://pubmed.ncbi.nlm.nih.gov/28602936/",
    },
    {
        "pmid": "29198729",
        "doi": "10.1016/j.jaci.2017.09.025",
        "title": "Cross-reactivity among peanut and tree nuts",
        "title_kr": "땅콩과 견과류 간의 교차반응",
        "authors": "Brough HA, Caubet JC, Mazon A, et al.",
        "journal": "J Allergy Clin Immunol",
        "year": 2018,
        "abstract": "Cross-reactivity between peanut and tree nuts is clinically relevant in approximately 30-40% of patients.",
        "paper_type": "review",
        "evidence_level": "B",
        "is_guideline": False,
        "guideline_org": None,
        "url": "https://pubmed.ncbi.nlm.nih.gov/29198729/",
    },
]


# Clinical statements with evidence
CLINICAL_STATEMENTS = [
    # Shrimp/Crustacean statements
    {
        "statement_en": "Tropomyosin is the major pan-allergen responsible for cross-reactivity among crustaceans (shrimp, crab, lobster) and mollusks.",
        "statement_kr": "트로포미오신은 갑각류(새우, 게, 랍스터) 및 연체류 간의 교차반응을 일으키는 주요 pan-allergen이다.",
        "allergen_code": "shrimp",
        "context": "cross_reactivity",
        "evidence_level": "A",
        "recommendation_grade": "1A",
        "paper_pmid": "28602936",
        "source_location": "Abstract",
    },
    {
        "statement_en": "Patients with shrimp allergy should be evaluated for cross-reactivity with other crustaceans and house dust mites.",
        "statement_kr": "새우 알레르기 환자는 다른 갑각류 및 집먼지진드기와의 교차반응 여부를 평가해야 한다.",
        "allergen_code": "shrimp",
        "context": "diagnosis",
        "evidence_level": "B",
        "recommendation_grade": "1B",
        "paper_pmid": "28602936",
        "source_location": "Clinical Recommendations",
    },
    {
        "statement_en": "sIgE to tropomyosin (rPen a 1) ≥0.35 kU/L suggests clinical reactivity to crustaceans.",
        "statement_kr": "트로포미오신(rPen a 1)에 대한 sIgE ≥0.35 kU/L는 갑각류에 대한 임상적 반응성을 시사한다.",
        "allergen_code": "shrimp",
        "context": "diagnosis",
        "evidence_level": "B",
        "recommendation_grade": "2B",
        "paper_pmid": "28602936",
        "source_location": "Results, Table 3",
    },
    {
        "statement_en": "Strict avoidance of all crustaceans is recommended for patients with confirmed shrimp allergy and positive tropomyosin sensitization.",
        "statement_kr": "확진된 새우 알레르기 및 트로포미오신 감작 양성 환자에게는 모든 갑각류의 엄격한 회피가 권장된다.",
        "allergen_code": "shrimp",
        "context": "avoidance",
        "evidence_level": "A",
        "recommendation_grade": "1A",
        "paper_pmid": "32628776",
        "source_location": "Management Guidelines",
    },

    # Peanut statements
    {
        "statement_en": "Peanut allergy shows clinical cross-reactivity with tree nuts in 30-40% of patients, despite being botanically unrelated.",
        "statement_kr": "땅콩 알레르기는 식물학적으로 관련이 없음에도 불구하고 30-40%의 환자에서 견과류와 임상적 교차반응을 보인다.",
        "allergen_code": "peanut",
        "context": "cross_reactivity",
        "evidence_level": "B",
        "recommendation_grade": "1B",
        "paper_pmid": "29198729",
        "source_location": "Abstract",
    },
    {
        "statement_en": "sIgE to Ara h 2 ≥0.35 kU/L has high specificity (>95%) for predicting clinical peanut allergy.",
        "statement_kr": "Ara h 2에 대한 sIgE ≥0.35 kU/L는 임상적 땅콩 알레르기 예측에 높은 특이도(>95%)를 보인다.",
        "allergen_code": "peanut",
        "context": "diagnosis",
        "evidence_level": "A",
        "recommendation_grade": "1A",
        "paper_pmid": "32628776",
        "source_location": "Diagnostic Testing",
    },
    {
        "statement_en": "Patients with peanut allergy should be evaluated for tree nut sensitization and advised on individual tree nut avoidance based on clinical history.",
        "statement_kr": "땅콩 알레르기 환자는 견과류 감작 여부를 평가받고, 임상 병력에 따라 개별 견과류 회피에 대한 조언을 받아야 한다.",
        "allergen_code": "peanut",
        "context": "avoidance",
        "evidence_level": "B",
        "recommendation_grade": "1B",
        "paper_pmid": "29198729",
        "source_location": "Clinical Recommendations",
    },

    # Milk statements
    {
        "statement_en": "Cow's milk allergy (CMA) is the most common food allergy in infancy, with most children outgrowing it by age 5.",
        "statement_kr": "우유 알레르기(CMA)는 영아기에 가장 흔한 식품 알레르기이며, 대부분의 아동은 5세까지 내성을 획득한다.",
        "allergen_code": "milk",
        "context": "pathophysiology",
        "evidence_level": "A",
        "recommendation_grade": "1A",
        "paper_pmid": "32628776",
        "source_location": "Epidemiology",
    },
    {
        "statement_en": "Extensively hydrolyzed formula (eHF) is recommended as first-line for CMA management in non-breastfed infants.",
        "statement_kr": "고도 가수분해 분유(eHF)는 모유 수유가 아닌 영아의 CMA 관리에 일차적으로 권장된다.",
        "allergen_code": "milk",
        "context": "treatment",
        "evidence_level": "A",
        "recommendation_grade": "1A",
        "paper_pmid": "32628776",
        "source_location": "Management",
    },

    # Anaphylaxis statements (general)
    {
        "statement_en": "Epinephrine is the first-line treatment for anaphylaxis and should be administered immediately upon recognition.",
        "statement_kr": "에피네프린은 아나필락시스의 일차 치료제이며 인지 즉시 투여해야 한다.",
        "allergen_code": "general",
        "context": "treatment",
        "evidence_level": "A",
        "recommendation_grade": "1A",
        "paper_pmid": "33745789",
        "source_location": "Treatment Guidelines",
    },
    {
        "statement_en": "Patients at risk of anaphylaxis should be prescribed at least two epinephrine auto-injectors and trained on proper use.",
        "statement_kr": "아나필락시스 위험이 있는 환자에게는 최소 2개의 에피네프린 자가주사기를 처방하고 올바른 사용법을 교육해야 한다.",
        "allergen_code": "general",
        "context": "treatment",
        "evidence_level": "A",
        "recommendation_grade": "1A",
        "paper_pmid": "33745789",
        "source_location": "Long-term Management",
    },
    {
        "statement_en": "Biphasic anaphylaxis occurs in up to 20% of cases; observation for 4-6 hours post-treatment is recommended.",
        "statement_kr": "이상성 아나필락시스는 최대 20%의 경우에서 발생하며, 치료 후 4-6시간 관찰이 권장된다.",
        "allergen_code": "general",
        "context": "treatment",
        "evidence_level": "B",
        "recommendation_grade": "1B",
        "paper_pmid": "33040377",
        "source_location": "Post-Episode Management",
    },

    # Crab statements
    {
        "statement_en": "Cross-reactivity between crab and shrimp is greater than 75% due to shared tropomyosin epitopes.",
        "statement_kr": "게와 새우 간의 교차반응은 공유 트로포미오신 에피토프로 인해 75% 이상이다.",
        "allergen_code": "crab",
        "context": "cross_reactivity",
        "evidence_level": "A",
        "recommendation_grade": "1A",
        "paper_pmid": "28602936",
        "source_location": "Cross-Reactivity Section",
    },

    # Dust mite statements
    {
        "statement_en": "House dust mite tropomyosin shows 80% sequence homology with shrimp tropomyosin, leading to potential cross-sensitization.",
        "statement_kr": "집먼지진드기 트로포미오신은 새우 트로포미오신과 80%의 서열 상동성을 보여 교차감작 가능성이 있다.",
        "allergen_code": "dust_mite",
        "context": "cross_reactivity",
        "evidence_level": "B",
        "recommendation_grade": "2B",
        "paper_pmid": "28602936",
        "source_location": "Discussion",
    },
]


def seed_clinical_data(db: Session = None):
    """Seed clinical statements and guideline papers"""
    if db is None:
        db = SessionLocal()
        close_db = True
    else:
        close_db = False

    try:
        # Create papers
        paper_map = {}  # pmid -> paper object

        for paper_data in GUIDELINE_PAPERS:
            existing = db.query(Paper).filter(Paper.pmid == paper_data["pmid"]).first()
            if existing:
                print(f"Paper already exists: {paper_data['pmid']}")
                paper_map[paper_data["pmid"]] = existing
                # Update guideline fields if not set
                if not existing.evidence_level:
                    existing.evidence_level = paper_data.get("evidence_level")
                    existing.is_guideline = paper_data.get("is_guideline", False)
                    existing.guideline_org = paper_data.get("guideline_org")
                continue

            paper = Paper(
                pmid=paper_data["pmid"],
                doi=paper_data.get("doi"),
                title=paper_data["title"],
                title_kr=paper_data.get("title_kr"),
                authors=paper_data.get("authors"),
                journal=paper_data.get("journal"),
                year=paper_data.get("year"),
                abstract=paper_data.get("abstract"),
                paper_type=paper_data.get("paper_type", "research"),
                evidence_level=paper_data.get("evidence_level"),
                is_guideline=paper_data.get("is_guideline", False),
                guideline_org=paper_data.get("guideline_org"),
                url=paper_data.get("url"),
                is_verified=True,
                created_at=datetime.utcnow(),
            )
            db.add(paper)
            db.flush()
            paper_map[paper_data["pmid"]] = paper
            print(f"Created paper: {paper_data['pmid']} - {paper_data['title'][:50]}...")

        # Create clinical statements
        statements_created = 0
        for stmt_data in CLINICAL_STATEMENTS:
            # Check if statement already exists
            existing = db.query(ClinicalStatement).filter(
                ClinicalStatement.statement_en == stmt_data["statement_en"]
            ).first()
            if existing:
                print(f"Statement already exists: {stmt_data['statement_en'][:50]}...")
                continue

            # Get paper_id from pmid
            paper_id = None
            if stmt_data.get("paper_pmid"):
                paper = paper_map.get(stmt_data["paper_pmid"])
                if paper:
                    paper_id = paper.id

            stmt = ClinicalStatement(
                statement_en=stmt_data["statement_en"],
                statement_kr=stmt_data.get("statement_kr"),
                allergen_code=stmt_data.get("allergen_code"),
                context=stmt_data["context"],
                evidence_level=stmt_data.get("evidence_level"),
                recommendation_grade=stmt_data.get("recommendation_grade"),
                paper_id=paper_id,
                source_location=stmt_data.get("source_location"),
                is_active=True,
                created_at=datetime.utcnow(),
            )
            db.add(stmt)
            statements_created += 1

        db.commit()

        # Print summary
        print("\n" + "=" * 50)
        print("Clinical Data Seed Summary")
        print("=" * 50)
        print(f"Papers created/updated: {len(GUIDELINE_PAPERS)}")
        print(f"Clinical statements created: {statements_created}")
        print("=" * 50)

    except Exception as e:
        db.rollback()
        print(f"Error seeding clinical data: {e}")
        import traceback
        traceback.print_exc()
        raise

    finally:
        if close_db:
            db.close()


if __name__ == "__main__":
    seed_clinical_data()
