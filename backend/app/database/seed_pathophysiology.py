"""병태생리(Pathophysiology) 마스터 데이터 시딩

학술 전용 알러지 치료 Agent의 증상 ↔ 약물 매핑 중간 노드.
15개 초기 태그는 ADR-008에서 정의. 본 시드는 마스터 레코드만 생성하며,
symptom_pathophys · pathophys_atc 엣지는 전문의 감수 이후 별도 생성된다.

참조:
- services/allergyinsight/adr/008-pathophysiology-knowledge-graph.md
- services/allergyinsight/dev/pathophys-reviewer-guideline.md
"""
import logging
from sqlalchemy.orm import Session

from .connection import SessionLocal
from .drug_models import Pathophysiology

logger = logging.getLogger(__name__)


# 15개 초기 병태생리 태그 (ADR-008)
# reference_pmids 는 주요 리뷰/가이드라인 PMID (초안)
PATHOPHYSIOLOGY_SEED: list[dict] = [
    {
        "code": "TH2_DOMINANT",
        "name_kr": "Th2 우세 염증",
        "name_en": "Th2-dominant inflammation",
        "description": (
            "IL-4, IL-5, IL-13 사이토카인이 주도하는 알러지성 염증. "
            "아토피 피부염, 알러지성 비염, 호산구성 천식의 기저 기전."
        ),
        "reference_pmids": [32707227, 31277594],
    },
    {
        "code": "IGE_MEDIATED",
        "name_kr": "IgE 매개 반응",
        "name_en": "IgE-mediated hypersensitivity (Type I)",
        "description": (
            "특이 IgE 감작에 의한 즉시형 과민반응. "
            "식품 알러지, 알러젠 특이 비염, 아나필락시스."
        ),
        "reference_pmids": [32707227],
    },
    {
        "code": "MAST_CELL_DEGRANULATION",
        "name_kr": "마스트셀 탈과립",
        "name_en": "Mast cell degranulation",
        "description": (
            "마스트셀에서 히스타민·트립타제·프로스타글란딘 등이 방출되어 "
            "두드러기·혈관부종·아나필락시스 유발."
        ),
        "reference_pmids": [31277594],
    },
    {
        "code": "HISTAMINE_RELEASE",
        "name_kr": "히스타민 과잉 방출",
        "name_en": "Histamine-dominant response",
        "description": (
            "히스타민이 주요 매개체로 작용하는 증상. "
            "가려움·재채기·콧물·H1 수용체 매개 혈관확장."
        ),
        "reference_pmids": [32707227],
    },
    {
        "code": "LEUKOTRIENE_DOMINANT",
        "name_kr": "류코트리엔 우세 염증",
        "name_en": "Leukotriene-dominant inflammation",
        "description": (
            "CysLT(류코트리엔 C4/D4/E4) 과잉. 아스피린 감작 천식, "
            "만성 비염, NSAIDs-ERD(호흡기 악화질환)."
        ),
        "reference_pmids": [30872049],
    },
    {
        "code": "BRONCHOCONSTRICTION",
        "name_kr": "기관지 수축",
        "name_en": "Bronchoconstriction",
        "description": (
            "기관지 평활근 수축에 의한 기류제한. 천식, 운동 유발 기관지수축. "
            "β2 효현제·항콜린제에 가역적으로 반응."
        ),
        "reference_pmids": [38724449],
    },
    {
        "code": "EOSINOPHILIC",
        "name_kr": "호산구성 염증",
        "name_en": "Eosinophilic inflammation",
        "description": (
            "호산구 침윤이 주된 조직 염증 유형. 중증 호산구성 천식, "
            "호산구성 식도염, 호산구성 비용종."
        ),
        "reference_pmids": [31277594, 38724449],
    },
    {
        "code": "NEUTROPHILIC",
        "name_kr": "호중구성 염증",
        "name_en": "Neutrophilic inflammation",
        "description": (
            "호중구 침윤 우세 염증. 비아토피성 천식, 중증 천식 일부, "
            "스테로이드 난치성 경향."
        ),
        "reference_pmids": [31277594],
    },
    {
        "code": "EPITHELIAL_BARRIER_DYSFUNCTION",
        "name_kr": "상피 장벽 기능 이상",
        "name_en": "Epithelial barrier dysfunction",
        "description": (
            "피부·기도·장 상피의 장벽 기능 약화. 필라그린 변이, TSLP 상향 조절 등. "
            "아토피 피부염, 식품 알러지, 천식의 기저."
        ),
        "reference_pmids": [30872049],
    },
    {
        "code": "DELAYED_TYPE_HYPERSENSITIVITY",
        "name_kr": "지연형 과민반응 (Type IV)",
        "name_en": "Delayed-type hypersensitivity",
        "description": (
            "T 세포 매개 지연형 반응. 접촉성 피부염, 약물 유발 발진. "
            "IgE 비매개로 즉시형 치료제에 반응 없음."
        ),
        "reference_pmids": [31277594],
    },
    {
        "code": "OCULAR_ALLERGIC",
        "name_kr": "안구 알러지 반응",
        "name_en": "Ocular allergic reaction",
        "description": (
            "결막 표면의 IgE·비IgE 매개 염증. 계절성·통년성 알러지성 결막염, "
            "봄철 각결막염(VKC), 거대유두결막염(GPC)."
        ),
        "reference_pmids": [32707227],
    },
    {
        "code": "IMMUNE_MODULATION_DEFICIT",
        "name_kr": "면역 조절 결핍",
        "name_en": "Immune modulation deficit",
        "description": (
            "Treg 기능 저하 또는 면역 관용 부족으로 만성화된 알러지. "
            "알러젠 특이 면역치료(SCIT/SLIT) 대상."
        ),
        "reference_pmids": [32707227],
    },
    {
        "code": "ANAPHYLAXIS_SYSTEMIC",
        "name_kr": "전신 아나필락시스",
        "name_en": "Systemic anaphylaxis",
        "description": (
            "다기관 침범 즉시형 반응(순환허탈·호흡부전). "
            "에피네프린 근주가 1차 치료. 마스트셀·바소필 대규모 활성화."
        ),
        "reference_pmids": [31277594],
    },
    {
        "code": "CHRONIC_URTICARIA",
        "name_kr": "만성 두드러기 기전",
        "name_en": "Chronic urticaria mechanism",
        "description": (
            "6주 이상 지속되는 두드러기. 자가면역성(자가 IgE·FcεRI 항체) 기전 "
            "포함. H1 항히스타민 고용량·오말리주맙 적응."
        ),
        "reference_pmids": [29047144],
    },
    {
        "code": "MIXED_INFLAMMATORY",
        "name_kr": "혼합형 염증",
        "name_en": "Mixed inflammatory pattern",
        "description": (
            "Th2 + 호중구 또는 Th2 + Th17 병합형. 중증 난치성 천식·비염에서 관찰. "
            "단일 기전으로 설명 안 되는 증상에 임시 분류."
        ),
        "reference_pmids": [38724449],
    },
]


def seed_pathophysiology() -> int:
    """병태생리 마스터 레코드 시딩 (멱등성 보장).

    Returns:
        새로 삽입된 레코드 수
    """
    db: Session = SessionLocal()
    inserted = 0
    try:
        existing_codes = {
            row[0] for row in db.query(Pathophysiology.code).all()
        }
        for entry in PATHOPHYSIOLOGY_SEED:
            if entry["code"] in existing_codes:
                continue
            row = Pathophysiology(
                code=entry["code"],
                name_kr=entry["name_kr"],
                name_en=entry["name_en"],
                description=entry["description"],
                reference_pmids=entry["reference_pmids"],
            )
            db.add(row)
            inserted += 1
        db.commit()
        logger.info(
            "Pathophysiology seed complete: inserted=%s, existing=%s, total_seed=%s",
            inserted,
            len(existing_codes),
            len(PATHOPHYSIOLOGY_SEED),
        )
        return inserted
    except Exception:
        db.rollback()
        logger.exception("Pathophysiology seed failed")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    count = seed_pathophysiology()
    print(f"Seeded {count} pathophysiology records.")
