"""알러젠 마스터 데이터 시딩

앱 시작 시 allergen_master.py의 119종 데이터를 DB에 삽입합니다.
멱등성 보장: 이미 존재하는 코드는 건너뜁니다 (관리자 수정 데이터 보호).
"""
import logging
from sqlalchemy.orm import Session

from .connection import SessionLocal
from .allergen_models import AllergenMaster
from ..data.allergen_master import ALLERGEN_MASTER_DB

logger = logging.getLogger(__name__)


# 카테고리별 정렬 순서
CATEGORY_ORDER = {
    "mite": 100, "dust": 200, "animal": 300, "insect": 400,
    "latex": 500, "microorganism": 600, "tree": 700, "grass": 800,
    "weed": 900, "other": 1000, "egg_dairy": 1100, "crustacean": 1200,
    "fish_shellfish": 1300, "vegetable": 1400, "meat": 1500,
    "fruit": 1600, "seed_nut": 1700,
}


def seed_allergens():
    """알러젠 마스터 데이터를 DB에 시딩"""
    db: Session = SessionLocal()
    try:
        existing_count = db.query(AllergenMaster).count()

        if existing_count >= len(ALLERGEN_MASTER_DB):
            logger.info(f"알러젠 시딩 생략: DB에 {existing_count}종 존재 (원본 {len(ALLERGEN_MASTER_DB)}종)")
            return

        # 기존 코드 조회
        existing_codes = {
            row[0] for row in db.query(AllergenMaster.code).all()
        }

        inserted = 0
        for idx, (code, data) in enumerate(ALLERGEN_MASTER_DB.items()):
            if code in existing_codes:
                continue

            category = data.get("category")
            allergen_type = data.get("type")
            cat_value = category.value if hasattr(category, 'value') else str(category)
            type_value = allergen_type.value if hasattr(allergen_type, 'value') else str(allergen_type)

            allergen = AllergenMaster(
                code=code,
                name_kr=data.get("name_kr", ""),
                name_en=data.get("name_en", ""),
                category=cat_value,
                type=type_value,
                description=data.get("description"),
                note=data.get("note"),
                is_active=True,
                sort_order=CATEGORY_ORDER.get(cat_value, 9999) + idx,
            )
            db.add(allergen)
            inserted += 1

        if inserted > 0:
            db.commit()
            logger.info(f"알러젠 시딩 완료: {inserted}종 추가 (총 {existing_count + inserted}종)")
        else:
            logger.info("알러젠 시딩: 추가할 데이터 없음")

    except Exception as e:
        db.rollback()
        logger.error(f"알러젠 시딩 실패: {e}")
        raise
    finally:
        db.close()
