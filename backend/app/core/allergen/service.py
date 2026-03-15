"""알러젠 마스터 데이터 서비스 (DB 기반)

allergen_master 테이블을 통한 CRUD 및 조회 기능을 제공합니다.
"""
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from datetime import datetime

from ...database.allergen_models import AllergenMaster
from ...data.allergen_master import AllergenCategory, AllergenType


def get_by_code(db: Session, code: str) -> Optional[AllergenMaster]:
    """코드로 알러젠 조회"""
    return db.query(AllergenMaster).filter(
        AllergenMaster.code == code.lower(),
        AllergenMaster.is_active == True,
    ).first()


def list_allergens(
    db: Session,
    category: Optional[str] = None,
    allergen_type: Optional[str] = None,
    search: Optional[str] = None,
    is_active: bool = True,
    limit: int = 200,
    offset: int = 0,
) -> tuple[List[AllergenMaster], int]:
    """알러젠 목록 조회 (필터, 검색, 페이징)"""
    query = db.query(AllergenMaster)

    if is_active is not None:
        query = query.filter(AllergenMaster.is_active == is_active)

    if category:
        query = query.filter(AllergenMaster.category == category)

    if allergen_type:
        query = query.filter(AllergenMaster.type == allergen_type)

    if search:
        search_pattern = f"%{search}%"
        query = query.filter(or_(
            AllergenMaster.code.ilike(search_pattern),
            AllergenMaster.name_kr.ilike(search_pattern),
            AllergenMaster.name_en.ilike(search_pattern),
        ))

    total = query.count()
    items = query.order_by(
        AllergenMaster.sort_order, AllergenMaster.code
    ).offset(offset).limit(limit).all()

    return items, total


def search_allergens(db: Session, query_str: str) -> List[AllergenMaster]:
    """알러젠 검색 (한글명/영문명/코드)"""
    search_pattern = f"%{query_str}%"
    return db.query(AllergenMaster).filter(
        AllergenMaster.is_active == True,
        or_(
            AllergenMaster.code.ilike(search_pattern),
            AllergenMaster.name_kr.ilike(search_pattern),
            AllergenMaster.name_en.ilike(search_pattern),
        ),
    ).order_by(AllergenMaster.sort_order, AllergenMaster.code).all()


def get_all_codes(db: Session) -> List[str]:
    """전체 알러젠 코드 목록"""
    rows = db.query(AllergenMaster.code).filter(
        AllergenMaster.is_active == True,
    ).order_by(AllergenMaster.sort_order, AllergenMaster.code).all()
    return [r[0] for r in rows]


def get_count(db: Session) -> int:
    """전체 알러젠 수"""
    return db.query(func.count(AllergenMaster.id)).filter(
        AllergenMaster.is_active == True,
    ).scalar() or 0


def get_summary(db: Session) -> dict:
    """알러젠 요약 통계 (카테고리별/타입별 분포)"""
    # 카테고리별
    cat_rows = db.query(
        AllergenMaster.category, func.count(AllergenMaster.id)
    ).filter(
        AllergenMaster.is_active == True,
    ).group_by(AllergenMaster.category).all()

    # 타입별
    type_rows = db.query(
        AllergenMaster.type, func.count(AllergenMaster.id)
    ).filter(
        AllergenMaster.is_active == True,
    ).group_by(AllergenMaster.type).all()

    total = db.query(func.count(AllergenMaster.id)).filter(
        AllergenMaster.is_active == True,
    ).scalar() or 0

    return {
        "total": total,
        "by_category": {cat: count for cat, count in cat_rows},
        "by_type": {typ: count for typ, count in type_rows},
    }


# ============================================================================
# Admin CRUD
# ============================================================================

def create_allergen(db: Session, data: dict) -> AllergenMaster:
    """알러젠 추가"""
    allergen = AllergenMaster(
        code=data["code"].lower(),
        name_kr=data["name_kr"],
        name_en=data["name_en"],
        category=data["category"],
        type=data["type"],
        description=data.get("description"),
        note=data.get("note"),
        is_active=True,
        sort_order=data.get("sort_order", 0),
    )
    db.add(allergen)
    db.commit()
    db.refresh(allergen)
    return allergen


def update_allergen(db: Session, code: str, data: dict) -> Optional[AllergenMaster]:
    """알러젠 수정"""
    allergen = db.query(AllergenMaster).filter(
        AllergenMaster.code == code.lower(),
    ).first()

    if not allergen:
        return None

    for field in ("name_kr", "name_en", "category", "type", "description", "note", "sort_order"):
        if field in data and data[field] is not None:
            setattr(allergen, field, data[field])

    allergen.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(allergen)
    return allergen


def delete_allergen(db: Session, code: str) -> bool:
    """알러젠 소프트 삭제 (is_active = False)"""
    allergen = db.query(AllergenMaster).filter(
        AllergenMaster.code == code.lower(),
    ).first()

    if not allergen:
        return False

    allergen.is_active = False
    allergen.updated_at = datetime.utcnow()
    db.commit()
    return True


def restore_allergen(db: Session, code: str) -> bool:
    """삭제된 알러젠 복원"""
    allergen = db.query(AllergenMaster).filter(
        AllergenMaster.code == code.lower(),
    ).first()

    if not allergen:
        return False

    allergen.is_active = True
    allergen.updated_at = datetime.utcnow()
    db.commit()
    return True
