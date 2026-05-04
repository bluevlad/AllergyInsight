"""Strategic Intel 시드 데이터

- Tech Taxonomy v1 (12개 기술 카테고리)
- Company-Tech Fit Matrix v1 (4사 × 12 = 48 셀)

대상 회사 (단독 회사 기준 — 그룹 시너지 제외):
  - sugentech    : 수젠텍 (자사, KOSDAQ 253840)
  - greencross   : 녹십자엠에스 (KOSDAQ 142280)
  - bodytech     : 바디텍메드 (KOSDAQ 206640)
  - madx         : Macro Array Diagnostics (비상장, fit matrix만)
"""
from datetime import date
from sqlalchemy.orm import Session

from .strategic_intel_models import TechCategory, CompanyTechFit


# ---------------------------------------------------------------------------
# Tech Taxonomy v1 (12개)
# ---------------------------------------------------------------------------

TECH_CATEGORIES_V1 = [
    {
        "id": "multiplex_microarray",
        "name_kr": "멀티플렉스 마이크로어레이",
        "name_en": "Multiplex Microarray",
        "description": "다수 알러젠을 동시에 검사하는 마이크로어레이 / 라인블롯 / 매크로어레이 기반 검사. ALEX2, ImmunoCAP ISAC, EUROLINE, MARIA 등.",
        "keywords_en": [
            "microarray IgE", "multiplex allergy", "ImmunoCAP ISAC",
            "ALEX2", "MARIA", "EUROLINE", "macroarray allergy",
        ],
        "keywords_kr": ["마이크로어레이", "멀티플렉스 알러지", "동시 다중 검사"],
        "sort_order": 1,
    },
    {
        "id": "crd",
        "name_kr": "분자 단위 진단 (CRD)",
        "name_en": "Component-Resolved Diagnostics",
        "description": "재조합 알러젠을 사용해 분자 단위에서 IgE 반응을 진단. ImmunoCAP CRD가 골드스탠다드.",
        "keywords_en": [
            "component-resolved diagnostics", "CRD", "recombinant allergen",
            "molecular allergy", "molecular allergology",
        ],
        "keywords_kr": ["분자 알러지 진단", "컴포넌트 진단", "재조합 알러젠"],
        "sort_order": 2,
    },
    {
        "id": "singleplex_quant_ige",
        "name_kr": "단일정량 IgE",
        "name_en": "Singleplex Quantitative IgE",
        "description": "단일 항원에 대한 정량 IgE 측정. 형광/효소면역분석. ImmunoCAP, IMMULITE 등.",
        "keywords_en": [
            "singleplex IgE", "fluorescent enzyme immunoassay", "FEIA",
            "ImmunoCAP", "IMMULITE", "specific IgE",
        ],
        "keywords_kr": ["정량 IgE", "단일항원 IgE", "특이 IgE"],
        "sort_order": 3,
    },
    {
        "id": "poc_lateral_flow",
        "name_kr": "POC / 신속진단",
        "name_en": "Point-of-Care / Lateral Flow",
        "description": "현장형 신속 알러지 검사. 측면유동(lateral flow) 면역분석 기반. 수젠텍·바디텍메드 핵심 영역.",
        "keywords_en": [
            "point-of-care allergy", "lateral flow IgE", "rapid allergy test",
            "POC allergy", "rapid IgE", "immunochromatography allergy",
        ],
        "keywords_kr": ["현장진단", "신속 알러지 검사", "면역크로마토그래피"],
        "sort_order": 4,
    },
    {
        "id": "mast_immunoblot",
        "name_kr": "MAST / 면역블롯",
        "name_en": "MAST / Immunoblot",
        "description": "다중 알러젠 동시 검사 (한국 표준 검사 중 하나). 화학발광 면역블롯. 수젠텍 강세.",
        "keywords_en": [
            "MAST chemiluminescent", "immunoblot allergy", "line blot IgE",
            "MAST allergy", "panel IgE blot",
        ],
        "keywords_kr": ["MAST 검사", "면역블롯", "다중 알러젠 검사"],
        "sort_order": 5,
    },
    {
        "id": "bat",
        "name_kr": "호염기구 활성화 시험",
        "name_en": "Basophil Activation Test",
        "description": "환자 호염기구의 알러젠 노출 후 활성 마커(CD63, CD203c) 측정. 차세대 기능검사.",
        "keywords_en": [
            "basophil activation test", "BAT", "CD63 basophil",
            "CD203c", "flow cytometry allergy",
        ],
        "keywords_kr": ["호염기구 활성화", "BAT 검사", "기능적 알러지 검사"],
        "sort_order": 6,
    },
    {
        "id": "mediator_release",
        "name_kr": "매개체 방출 시험",
        "name_en": "Mediator Release Test",
        "description": "히스타민·류코트리엔 등 매개체 방출량 측정. BAT 보완·대체 기술.",
        "keywords_en": [
            "mediator release test", "MRT", "histamine release",
            "leukotriene release", "ELISpot allergy",
        ],
        "keywords_kr": ["매개체 방출", "히스타민 방출 시험"],
        "sort_order": 7,
    },
    {
        "id": "microfluidics_loc",
        "name_kr": "미세유체 / Lab-on-Chip",
        "name_en": "Microfluidics / Lab-on-Chip",
        "description": "미세유체 / 칩 기반 통합 진단 플랫폼. 차세대 폼팩터.",
        "keywords_en": [
            "microfluidic allergy", "lab-on-chip IgE", "organ-on-chip allergy",
            "microfluidics IgE",
        ],
        "keywords_kr": ["미세유체", "랩온칩"],
        "sort_order": 8,
    },
    {
        "id": "biosensor_nano",
        "name_kr": "바이오센서 / 나노",
        "name_en": "Biosensor / Nanoparticle",
        "description": "나노입자·전기화학·SPR 기반 IgE 검출 바이오센서. R&D 단계.",
        "keywords_en": [
            "biosensor IgE", "nanoparticle allergy", "electrochemical IgE",
            "SPR allergy", "graphene biosensor allergy",
        ],
        "keywords_kr": ["바이오센서", "나노입자 진단"],
        "sort_order": 9,
    },
    {
        "id": "genomics_omics",
        "name_kr": "유전자/오믹스 패널",
        "name_en": "Genomics / Omics Panel",
        "description": "NGS 알러지 패널 키트, 유전체 기반 정밀 진단 시약. 키트화된 IVD 영역만 포함 (R&D 영역 제외).",
        "keywords_en": [
            "NGS allergy panel", "allergy genomics kit", "molecular allergy panel",
            "allergen sequencing kit", "genomic IVD allergy",
        ],
        "keywords_kr": ["알러지 유전자 패널", "NGS 알러지", "정밀 알러지 진단 키트"],
        "sort_order": 10,
    },
]


# ---------------------------------------------------------------------------
# Company-Tech Fit Matrix v1 (단독 회사 기준)
# ---------------------------------------------------------------------------
# 점수 가이드:
#   0.0 무관 / 0.3 미보유(잠재) / 0.6 보유·확장 가능 / 0.9+ 핵심 영역

FIT_MATRIX_V1 = {
    # 수젠텍 — MAST/면역블롯 + POC 핵심
    "sugentech": {
        "multiplex_microarray": (0.40, "면역블롯과 인접 영역, 일부 보유"),
        "crd": (0.30, "단일 컴포넌트 검사 직접 보유 안 함"),
        "singleplex_quant_ige": (0.50, "정량 IgE 라인 일부 보유"),
        "poc_lateral_flow": (0.85, "신속진단 핵심 사업 영역"),
        "mast_immunoblot": (0.95, "MAST 검사 — 회사 정체성 핵심 제품"),
        "bat": (0.40, "차세대 기능검사 — 미보유 / 잠재 기회"),
        "mediator_release": (0.30, "미보유"),
        "microfluidics_loc": (0.50, "신속진단 폼팩터와 인접"),
        "biosensor_nano": (0.40, "R&D 후보 — 미상용화"),
        "genomics_omics": (0.30, "NGS 패널 키트 직접 보유 X"),
    },
    # 녹십자엠에스 — 진단시약 (단일정량) 중심
    "greencross": {
        "multiplex_microarray": (0.30, "직접 보유 X"),
        "crd": (0.40, "분자 진단 R&D 잠재"),
        "singleplex_quant_ige": (0.70, "진단시약 사업부 — 정량 IgE 라인"),
        "poc_lateral_flow": (0.60, "신속진단 라인 보유"),
        "mast_immunoblot": (0.50, "다중 검사 인접"),
        "bat": (0.30, "미보유"),
        "mediator_release": (0.30, "미보유"),
        "microfluidics_loc": (0.30, "미보유"),
        "biosensor_nano": (0.30, "미보유"),
        "genomics_omics": (0.30, "단독 회사로 직접 보유 X (그룹 시너지 미반영)"),
    },
    # 바디텍메드 — POC/신속진단 + 형광면역분석 강자
    "bodytech": {
        "multiplex_microarray": (0.30, "마이크로어레이 직접 보유 X"),
        "crd": (0.30, "분자 단위 보유 X"),
        "singleplex_quant_ige": (0.40, "정량 라인 일부"),
        "poc_lateral_flow": (0.95, "POC/신속 IVD 핵심 사업 — 회사 정체성"),
        "mast_immunoblot": (0.40, "다중 검사 인접 영역"),
        "bat": (0.30, "미보유"),
        "mediator_release": (0.30, "미보유"),
        "microfluidics_loc": (0.60, "POC 폼팩터 자연 연장"),
        "biosensor_nano": (0.50, "R&D 후보"),
        "genomics_omics": (0.30, "보유 X"),
    },
    # MADx — 멀티플렉스 마이크로어레이 + CRD 절대강자 (비상장, 검증 제외)
    "madx": {
        "multiplex_microarray": (0.95, "ALEX2 — 회사 핵심 제품"),
        "crd": (0.85, "분자 단위 알러젠 진단 핵심"),
        "singleplex_quant_ige": (0.40, "보조"),
        "poc_lateral_flow": (0.00, "POC 영역 무관"),
        "mast_immunoblot": (0.20, "유사 영역 일부"),
        "bat": (0.40, "미보유 / 잠재"),
        "mediator_release": (0.30, "미보유"),
        "microfluidics_loc": (0.50, "마이크로어레이 인접"),
        "biosensor_nano": (0.30, "R&D 잠재"),
        "genomics_omics": (0.60, "분자 진단 자연 연계"),
    },
}


# ---------------------------------------------------------------------------
# Seed 함수
# ---------------------------------------------------------------------------

V1_EFFECTIVE_FROM = date(2025, 12, 1)  # 백필 시작점과 동일


def seed_tech_categories(db: Session) -> int:
    """12개 기술 카테고리 시드 (idempotent — id 충돌 시 업데이트)"""
    inserted = 0
    for spec in TECH_CATEGORIES_V1:
        existing = db.query(TechCategory).filter(TechCategory.id == spec["id"]).first()
        if existing:
            existing.name_kr = spec["name_kr"]
            existing.name_en = spec["name_en"]
            existing.description = spec["description"]
            existing.keywords_en = spec["keywords_en"]
            existing.keywords_kr = spec["keywords_kr"]
            existing.sort_order = spec["sort_order"]
            existing.is_active = True
        else:
            db.add(TechCategory(**spec, is_active=True))
            inserted += 1
    db.commit()
    return inserted


def seed_company_tech_fits(db: Session, version: str = "v1") -> int:
    """4사 × 12 카테고리 적합도 매트릭스 시드 (effective_from = 2025-12-01)

    동일 (company_code, tech_category_id, effective_from) 이미 존재하면 점수만 갱신.
    """
    inserted = 0
    for company_code, scores in FIT_MATRIX_V1.items():
        for tech_id, (score, rationale) in scores.items():
            existing = (
                db.query(CompanyTechFit)
                .filter(
                    CompanyTechFit.company_code == company_code,
                    CompanyTechFit.tech_category_id == tech_id,
                    CompanyTechFit.effective_from == V1_EFFECTIVE_FROM,
                )
                .first()
            )
            if existing:
                existing.fit_score = score
                existing.rationale = rationale
                existing.version = version
            else:
                db.add(
                    CompanyTechFit(
                        company_code=company_code,
                        tech_category_id=tech_id,
                        fit_score=score,
                        rationale=rationale,
                        version=version,
                        effective_from=V1_EFFECTIVE_FROM,
                    )
                )
                inserted += 1
    db.commit()
    return inserted


def seed_all(db: Session) -> dict:
    """Tech taxonomy + Fit matrix v1 일괄 시드"""
    n_tech = seed_tech_categories(db)
    n_fit = seed_company_tech_fits(db, version="v1")
    return {"tech_categories_inserted": n_tech, "fit_cells_inserted": n_fit}
