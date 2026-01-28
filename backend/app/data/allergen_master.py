"""알러젠 마스터 데이터베이스

SGTi-Allergy Screen PLUS 진단키트 기준 120종 알러젠 정보

Panel Information: 120 Types of Allergens
- 진드기/집먼지: 6종
- 동물/비듬/상피: 9종
- 벌독/곤충: 3종
- 라텍스: 1종
- 미생물: 6종
- 나무: 18종
- 목초: 8종
- 잡초: 14종
- 기타: 2종
- 알/가금류/유제품: 4종
- 갑각류: 3종
- 어패류: 11종
- 채소: 11종
- 육류: 4종
- 과일: 9종
- 씨/견과류: 21종
"""
from typing import Optional, List, Dict
from enum import Enum


class AllergenCategory(str, Enum):
    """알러젠 대분류"""
    MITE = "mite"                    # 진드기
    DUST = "dust"                    # 집먼지
    ANIMAL = "animal"               # 동물/비듬/상피
    INSECT = "insect"               # 벌독/곤충
    LATEX = "latex"                 # 라텍스
    MICROORGANISM = "microorganism" # 미생물
    TREE = "tree"                   # 나무
    GRASS = "grass"                 # 목초
    WEED = "weed"                   # 잡초
    OTHER = "other"                 # 기타
    EGG_DAIRY = "egg_dairy"         # 알/유제품
    CRUSTACEAN = "crustacean"       # 갑각류
    FISH_SHELLFISH = "fish_shellfish"  # 어패류
    VEGETABLE = "vegetable"         # 채소
    MEAT = "meat"                   # 육류
    FRUIT = "fruit"                 # 과일
    SEED_NUT = "seed_nut"           # 씨/견과류


class AllergenType(str, Enum):
    """알러젠 유형"""
    FOOD = "food"           # 식품
    INHALANT = "inhalant"   # 흡입성
    CONTACT = "contact"     # 접촉성
    VENOM = "venom"         # 독소


# ============================================================================
# 진드기 (Mites) - 5종
# ============================================================================
MITE_ALLERGENS = {
    "d1": {
        "code": "d1",
        "name_kr": "집먼지진드기(Dp)",
        "name_en": "D. pteronyssinus",
        "category": AllergenCategory.MITE,
        "type": AllergenType.INHALANT,
        "description": "유럽형 집먼지진드기, 실내 알러지의 주요 원인",
    },
    "d2": {
        "code": "d2",
        "name_kr": "집먼지진드기(Df)",
        "name_en": "D. farinae",
        "category": AllergenCategory.MITE,
        "type": AllergenType.INHALANT,
        "description": "미국형 집먼지진드기",
    },
    "d70": {
        "code": "d70",
        "name_kr": "수중다리가루진드기",
        "name_en": "Acarus siro",
        "category": AllergenCategory.MITE,
        "type": AllergenType.INHALANT,
        "description": "저장 식품에서 발견되는 진드기",
    },
    "d72": {
        "code": "d72",
        "name_kr": "저장진드기(Tp)",
        "name_en": "Tyrophagus putrescentiae",
        "category": AllergenCategory.MITE,
        "type": AllergenType.INHALANT,
        "description": "저장 진드기, 곰팡이가 핀 식품에서 번식",
    },
}


# ============================================================================
# 집먼지 (House Dust) - 1종
# ============================================================================
DUST_ALLERGENS = {
    "h1": {
        "code": "h1",
        "name_kr": "집먼지",
        "name_en": "House Dust",
        "category": AllergenCategory.DUST,
        "type": AllergenType.INHALANT,
        "description": "집먼지 혼합물 (진드기, 곰팡이, 동물 비듬 등 포함)",
    },
}


# ============================================================================
# 동물/비듬/상피 (Animals) - 9종
# ============================================================================
ANIMAL_ALLERGENS = {
    "e1": {
        "code": "e1",
        "name_kr": "고양이",
        "name_en": "Cat dander",
        "category": AllergenCategory.ANIMAL,
        "type": AllergenType.INHALANT,
        "description": "고양이 비듬/상피, Fel d 1 단백질",
    },
    "e5": {
        "code": "e5",
        "name_kr": "개",
        "name_en": "Dog dander",
        "category": AllergenCategory.ANIMAL,
        "type": AllergenType.INHALANT,
        "description": "개 비듬/상피, Can f 1 단백질",
    },
    "e3": {
        "code": "e3",
        "name_kr": "말",
        "name_en": "Horse dander",
        "category": AllergenCategory.ANIMAL,
        "type": AllergenType.INHALANT,
        "description": "말 비듬/상피",
    },
    "e6": {
        "code": "e6",
        "name_kr": "기니피그",
        "name_en": "Guinea pig epithelium",
        "category": AllergenCategory.ANIMAL,
        "type": AllergenType.INHALANT,
        "description": "기니피그 상피",
    },
    "e71": {
        "code": "e71",
        "name_kr": "생쥐",
        "name_en": "Mouse epithelium",
        "category": AllergenCategory.ANIMAL,
        "type": AllergenType.INHALANT,
        "description": "생쥐 상피, 실험실 종사자 주의",
        "note": "특수 항원",
    },
    "e73": {
        "code": "e73",
        "name_kr": "쥐",
        "name_en": "Rat epithelium",
        "category": AllergenCategory.ANIMAL,
        "type": AllergenType.INHALANT,
        "description": "쥐 상피",
        "note": "특수 항원",
    },
    "e81": {
        "code": "e81",
        "name_kr": "양",
        "name_en": "Sheep epithelium",
        "category": AllergenCategory.ANIMAL,
        "type": AllergenType.INHALANT,
        "description": "양 상피/양모",
    },
    "e82": {
        "code": "e82",
        "name_kr": "토끼",
        "name_en": "Rabbit epithelium",
        "category": AllergenCategory.ANIMAL,
        "type": AllergenType.INHALANT,
        "description": "토끼 상피",
    },
    "e84": {
        "code": "e84",
        "name_kr": "햄스터",
        "name_en": "Hamster epithelium",
        "category": AllergenCategory.ANIMAL,
        "type": AllergenType.INHALANT,
        "description": "햄스터 상피",
    },
}


# ============================================================================
# 벌독/곤충 (Insects) - 3종
# ============================================================================
INSECT_ALLERGENS = {
    "i1": {
        "code": "i1",
        "name_kr": "꿀벌",
        "name_en": "Honey bee venom",
        "category": AllergenCategory.INSECT,
        "type": AllergenType.VENOM,
        "description": "꿀벌 독, 아나필락시스 위험",
    },
    "i3": {
        "code": "i3",
        "name_kr": "말벌",
        "name_en": "Wasp venom",
        "category": AllergenCategory.INSECT,
        "type": AllergenType.VENOM,
        "description": "말벌 독, 심각한 알러지 반응 가능",
    },
    "i6": {
        "code": "i6",
        "name_kr": "바퀴벌레",
        "name_en": "Cockroach",
        "category": AllergenCategory.INSECT,
        "type": AllergenType.INHALANT,
        "description": "바퀴벌레 배설물/사체, 도시 환경 주요 알러젠",
    },
}


# ============================================================================
# 라텍스 (Latex) - 1종
# ============================================================================
LATEX_ALLERGENS = {
    "k82": {
        "code": "k82",
        "name_kr": "라텍스",
        "name_en": "Latex",
        "category": AllergenCategory.LATEX,
        "type": AllergenType.CONTACT,
        "description": "천연고무 라텍스, 의료 종사자 주의",
    },
}


# ============================================================================
# 미생물 (Microorganisms) - 6종
# ============================================================================
MICROORGANISM_ALLERGENS = {
    "m1": {
        "code": "m1",
        "name_kr": "페니실리움",
        "name_en": "Penicillium notatum",
        "category": AllergenCategory.MICROORGANISM,
        "type": AllergenType.INHALANT,
        "description": "푸른곰팡이, 실내/실외 흔한 곰팡이",
    },
    "m2": {
        "code": "m2",
        "name_kr": "클라도스포리움",
        "name_en": "Cladosporium herbarum",
        "category": AllergenCategory.MICROORGANISM,
        "type": AllergenType.INHALANT,
        "description": "검은곰팡이, 가장 흔한 실외 곰팡이",
    },
    "m3": {
        "code": "m3",
        "name_kr": "아스퍼질러스",
        "name_en": "Aspergillus fumigatus",
        "category": AllergenCategory.MICROORGANISM,
        "type": AllergenType.INHALANT,
        "description": "누룩곰팡이, ABPA 원인",
    },
    "m5": {
        "code": "m5",
        "name_kr": "칸디다",
        "name_en": "Candida albicans",
        "category": AllergenCategory.MICROORGANISM,
        "type": AllergenType.INHALANT,
        "description": "효모균",
    },
    "m6": {
        "code": "m6",
        "name_kr": "알터나리아",
        "name_en": "Alternaria alternata",
        "category": AllergenCategory.MICROORGANISM,
        "type": AllergenType.INHALANT,
        "description": "알터나리아 곰팡이, 천식 유발 주요 원인",
    },
    "m11": {
        "code": "m11",
        "name_kr": "리조푸스",
        "name_en": "Rhizopus nigricans",
        "category": AllergenCategory.MICROORGANISM,
        "type": AllergenType.INHALANT,
        "description": "거미줄곰팡이, 빵곰팡이",
    },
}


# ============================================================================
# 나무 (Trees) - 18종
# ============================================================================
TREE_ALLERGENS = {
    "t2": {
        "code": "t2",
        "name_kr": "오리나무",
        "name_en": "Alder",
        "category": AllergenCategory.TREE,
        "type": AllergenType.INHALANT,
        "description": "오리나무 꽃가루, 봄철 알러지",
    },
    "t3": {
        "code": "t3",
        "name_kr": "자작나무",
        "name_en": "Birch",
        "category": AllergenCategory.TREE,
        "type": AllergenType.INHALANT,
        "description": "자작나무 꽃가루, 구강알러지증후군 관련",
    },
    "t4": {
        "code": "t4",
        "name_kr": "개암나무",
        "name_en": "Hazel",
        "category": AllergenCategory.TREE,
        "type": AllergenType.INHALANT,
        "description": "개암나무 꽃가루",
    },
    "t7": {
        "code": "t7",
        "name_kr": "참나무",
        "name_en": "Oak",
        "category": AllergenCategory.TREE,
        "type": AllergenType.INHALANT,
        "description": "참나무 꽃가루",
    },
    "t8": {
        "code": "t8",
        "name_kr": "느릅나무",
        "name_en": "Elm",
        "category": AllergenCategory.TREE,
        "type": AllergenType.INHALANT,
        "description": "느릅나무 꽃가루",
    },
    "t9": {
        "code": "t9",
        "name_kr": "올리브나무",
        "name_en": "Olive",
        "category": AllergenCategory.TREE,
        "type": AllergenType.INHALANT,
        "description": "올리브나무 꽃가루",
        "note": "특수 항원",
    },
    "t11": {
        "code": "t11",
        "name_kr": "플라타너스",
        "name_en": "Plane tree/Sycamore",
        "category": AllergenCategory.TREE,
        "type": AllergenType.INHALANT,
        "description": "플라타너스(양버즘나무) 꽃가루",
    },
    "t12": {
        "code": "t12",
        "name_kr": "버드나무",
        "name_en": "Willow",
        "category": AllergenCategory.TREE,
        "type": AllergenType.INHALANT,
        "description": "버드나무 꽃가루",
    },
    "t14": {
        "code": "t14",
        "name_kr": "미루나무",
        "name_en": "Cottonwood/Poplar",
        "category": AllergenCategory.TREE,
        "type": AllergenType.INHALANT,
        "description": "미루나무/포플러 꽃가루",
    },
    "t15": {
        "code": "t15",
        "name_kr": "물푸레나무",
        "name_en": "Ash",
        "category": AllergenCategory.TREE,
        "type": AllergenType.INHALANT,
        "description": "물푸레나무 꽃가루",
    },
    "t16": {
        "code": "t16",
        "name_kr": "소나무",
        "name_en": "Pine",
        "category": AllergenCategory.TREE,
        "type": AllergenType.INHALANT,
        "description": "소나무 꽃가루",
    },
    "t17": {
        "code": "t17",
        "name_kr": "삼나무",
        "name_en": "Japanese cedar",
        "category": AllergenCategory.TREE,
        "type": AllergenType.INHALANT,
        "description": "삼나무 꽃가루, 일본에서 주요 알러젠",
    },
    "t19": {
        "code": "t19",
        "name_kr": "아카시아",
        "name_en": "Acacia",
        "category": AllergenCategory.TREE,
        "type": AllergenType.INHALANT,
        "description": "아카시아 꽃가루",
    },
    "t222": {
        "code": "t222",
        "name_kr": "편백나무",
        "name_en": "Japanese cypress",
        "category": AllergenCategory.TREE,
        "type": AllergenType.INHALANT,
        "description": "편백나무 꽃가루",
        "note": "특수 항원",
    },
}


# ============================================================================
# 목초 (Grasses) - 8종
# ============================================================================
GRASS_ALLERGENS = {
    "g1": {
        "code": "g1",
        "name_kr": "향기풀",
        "name_en": "Sweet vernal grass",
        "category": AllergenCategory.GRASS,
        "type": AllergenType.INHALANT,
        "description": "향기풀 꽃가루",
    },
    "g2": {
        "code": "g2",
        "name_kr": "우산잔디",
        "name_en": "Bermuda grass",
        "category": AllergenCategory.GRASS,
        "type": AllergenType.INHALANT,
        "description": "버뮤다그래스 꽃가루",
    },
    "g3": {
        "code": "g3",
        "name_kr": "오리새",
        "name_en": "Orchard grass",
        "category": AllergenCategory.GRASS,
        "type": AllergenType.INHALANT,
        "description": "오리새 꽃가루",
    },
    "g6": {
        "code": "g6",
        "name_kr": "큰조아재비",
        "name_en": "Timothy grass",
        "category": AllergenCategory.GRASS,
        "type": AllergenType.INHALANT,
        "description": "큰조아재비 꽃가루, 대표적 화본과 알러젠",
    },
    "g7": {
        "code": "g7",
        "name_kr": "갈대",
        "name_en": "Reed",
        "category": AllergenCategory.GRASS,
        "type": AllergenType.INHALANT,
        "description": "갈대 꽃가루",
    },
    "g9": {
        "code": "g9",
        "name_kr": "외겨이삭",
        "name_en": "Redtop/Bentgrass",
        "category": AllergenCategory.GRASS,
        "type": AllergenType.INHALANT,
        "description": "외겨이삭 꽃가루",
    },
    "g12": {
        "code": "g12",
        "name_kr": "호밀",
        "name_en": "Cultivated rye",
        "category": AllergenCategory.GRASS,
        "type": AllergenType.INHALANT,
        "description": "호밀 꽃가루",
    },
}


# ============================================================================
# 잡초 (Weeds) - 14종
# ============================================================================
WEED_ALLERGENS = {
    "w1": {
        "code": "w1",
        "name_kr": "돼지풀(Common)",
        "name_en": "Common ragweed",
        "category": AllergenCategory.WEED,
        "type": AllergenType.INHALANT,
        "description": "돼지풀 꽃가루, 가을철 주요 알러젠",
    },
    "w4": {
        "code": "w4",
        "name_kr": "돼지풀(Short)",
        "name_en": "Short ragweed",
        "category": AllergenCategory.WEED,
        "type": AllergenType.INHALANT,
        "description": "단풍잎돼지풀 꽃가루",
        "note": "특수 항원",
    },
    "w6": {
        "code": "w6",
        "name_kr": "쑥",
        "name_en": "Mugwort",
        "category": AllergenCategory.WEED,
        "type": AllergenType.INHALANT,
        "description": "쑥 꽃가루, 한국에서 가장 흔한 잡초 알러젠",
    },
    "w7": {
        "code": "w7",
        "name_kr": "불란서국화",
        "name_en": "Marguerite/Ox-eye daisy",
        "category": AllergenCategory.WEED,
        "type": AllergenType.INHALANT,
        "description": "불란서국화 꽃가루",
    },
    "w8": {
        "code": "w8",
        "name_kr": "민들레",
        "name_en": "Dandelion",
        "category": AllergenCategory.WEED,
        "type": AllergenType.INHALANT,
        "description": "민들레 꽃가루",
    },
    "w9": {
        "code": "w9",
        "name_kr": "창질경이",
        "name_en": "Plantain",
        "category": AllergenCategory.WEED,
        "type": AllergenType.INHALANT,
        "description": "창질경이 꽃가루",
    },
    "w10": {
        "code": "w10",
        "name_kr": "명아주",
        "name_en": "Lamb's quarters/Goosefoot",
        "category": AllergenCategory.WEED,
        "type": AllergenType.INHALANT,
        "description": "명아주 꽃가루",
    },
    "w11": {
        "code": "w11",
        "name_kr": "명아주과풀",
        "name_en": "Russian thistle/Saltwort",
        "category": AllergenCategory.WEED,
        "type": AllergenType.INHALANT,
        "description": "명아주과 잡초 꽃가루",
    },
    "w12": {
        "code": "w12",
        "name_kr": "미역취국화",
        "name_en": "Goldenrod",
        "category": AllergenCategory.WEED,
        "type": AllergenType.INHALANT,
        "description": "미역취 꽃가루",
    },
    "w13": {
        "code": "w13",
        "name_kr": "도꼬마리",
        "name_en": "Cocklebur",
        "category": AllergenCategory.WEED,
        "type": AllergenType.INHALANT,
        "description": "도꼬마리 꽃가루",
    },
    "w14": {
        "code": "w14",
        "name_kr": "털비름",
        "name_en": "Pigweed/Amaranth",
        "category": AllergenCategory.WEED,
        "type": AllergenType.INHALANT,
        "description": "털비름 꽃가루",
    },
    "w22": {
        "code": "w22",
        "name_kr": "환삼덩굴",
        "name_en": "Japanese hop",
        "category": AllergenCategory.WEED,
        "type": AllergenType.INHALANT,
        "description": "환삼덩굴 꽃가루, 한국에서 돼지풀 다음으로 흔함",
    },
}


# ============================================================================
# 기타 (Others) - 2종
# ============================================================================
OTHER_ALLERGENS = {
    "o214": {
        "code": "o214",
        "name_kr": "CCD",
        "name_en": "Cross-reactive Carbohydrate Determinants",
        "category": AllergenCategory.OTHER,
        "type": AllergenType.OTHER if hasattr(AllergenType, 'OTHER') else AllergenType.INHALANT,
        "description": "교차반응 탄수화물 결정기, 위양성 원인",
    },
    "f45": {
        "code": "f45",
        "name_kr": "효모",
        "name_en": "Baker's yeast",
        "category": AllergenCategory.OTHER,
        "type": AllergenType.FOOD,
        "description": "제빵용 효모",
    },
}


# ============================================================================
# 알/가금류/유제품 (Egg/Dairy) - 4종
# ============================================================================
EGG_DAIRY_ALLERGENS = {
    "f75": {
        "code": "f75",
        "name_kr": "계란노른자",
        "name_en": "Egg yolk",
        "category": AllergenCategory.EGG_DAIRY,
        "type": AllergenType.FOOD,
        "description": "계란 노른자, 리베틴 단백질",
    },
    "f1": {
        "code": "f1",
        "name_kr": "계란흰자",
        "name_en": "Egg white",
        "category": AllergenCategory.EGG_DAIRY,
        "type": AllergenType.FOOD,
        "description": "계란 흰자, 오보알부민/오보뮤코이드 단백질",
    },
    "f2": {
        "code": "f2",
        "name_kr": "우유",
        "name_en": "Cow's milk",
        "category": AllergenCategory.EGG_DAIRY,
        "type": AllergenType.FOOD,
        "description": "우유, 카제인/유청 단백질",
    },
    "f81": {
        "code": "f81",
        "name_kr": "체다치즈",
        "name_en": "Cheddar cheese",
        "category": AllergenCategory.EGG_DAIRY,
        "type": AllergenType.FOOD,
        "description": "체다치즈, 우유 알러지 관련",
    },
}


# ============================================================================
# 갑각류 (Crustaceans) - 3종
# ============================================================================
CRUSTACEAN_ALLERGENS = {
    "f23": {
        "code": "f23",
        "name_kr": "게",
        "name_en": "Crab",
        "category": AllergenCategory.CRUSTACEAN,
        "type": AllergenType.FOOD,
        "description": "게, 트로포미오신 단백질",
    },
    "f24": {
        "code": "f24",
        "name_kr": "새우",
        "name_en": "Shrimp",
        "category": AllergenCategory.CRUSTACEAN,
        "type": AllergenType.FOOD,
        "description": "새우, 트로포미오신 단백질",
    },
    "f80": {
        "code": "f80",
        "name_kr": "랍스터",
        "name_en": "Lobster",
        "category": AllergenCategory.CRUSTACEAN,
        "type": AllergenType.FOOD,
        "description": "랍스터/바닷가재",
        "note": "특수 항원",
    },
}


# ============================================================================
# 어패류 (Fish/Shellfish) - 11종
# ============================================================================
FISH_SHELLFISH_ALLERGENS = {
    "f3": {
        "code": "f3",
        "name_kr": "대구",
        "name_en": "Codfish",
        "category": AllergenCategory.FISH_SHELLFISH,
        "type": AllergenType.FOOD,
        "description": "대구, 파르브알부민 단백질",
    },
    "f37": {
        "code": "f37",
        "name_kr": "홍합",
        "name_en": "Blue mussel",
        "category": AllergenCategory.FISH_SHELLFISH,
        "type": AllergenType.FOOD,
        "description": "홍합",
    },
    "f40": {
        "code": "f40",
        "name_kr": "참치",
        "name_en": "Tuna",
        "category": AllergenCategory.FISH_SHELLFISH,
        "type": AllergenType.FOOD,
        "description": "참치",
    },
    "f41": {
        "code": "f41",
        "name_kr": "연어",
        "name_en": "Salmon",
        "category": AllergenCategory.FISH_SHELLFISH,
        "type": AllergenType.FOOD,
        "description": "연어",
    },
    "f50": {
        "code": "f50",
        "name_kr": "고등어",
        "name_en": "Mackerel",
        "category": AllergenCategory.FISH_SHELLFISH,
        "type": AllergenType.FOOD,
        "description": "고등어",
    },
    "f207": {
        "code": "f207",
        "name_kr": "조개",
        "name_en": "Clam",
        "category": AllergenCategory.FISH_SHELLFISH,
        "type": AllergenType.FOOD,
        "description": "조개류",
    },
    "f258": {
        "code": "f258",
        "name_kr": "오징어",
        "name_en": "Squid",
        "category": AllergenCategory.FISH_SHELLFISH,
        "type": AllergenType.FOOD,
        "description": "오징어",
    },
    "f254": {
        "code": "f254",
        "name_kr": "가자미",
        "name_en": "Plaice/Flounder",
        "category": AllergenCategory.FISH_SHELLFISH,
        "type": AllergenType.FOOD,
        "description": "가자미/광어",
        "note": "특수 항원",
    },
    "f290": {
        "code": "f290",
        "name_kr": "굴",
        "name_en": "Oyster",
        "category": AllergenCategory.FISH_SHELLFISH,
        "type": AllergenType.FOOD,
        "description": "굴",
        "note": "특수 항원",
    },
    "f313": {
        "code": "f313",
        "name_kr": "멸치",
        "name_en": "Anchovy",
        "category": AllergenCategory.FISH_SHELLFISH,
        "type": AllergenType.FOOD,
        "description": "멸치",
    },
    "f338": {
        "code": "f338",
        "name_kr": "가리비",
        "name_en": "Scallop",
        "category": AllergenCategory.FISH_SHELLFISH,
        "type": AllergenType.FOOD,
        "description": "가리비",
    },
}


# ============================================================================
# 채소 (Vegetables) - 11종
# ============================================================================
VEGETABLE_ALLERGENS = {
    "f25": {
        "code": "f25",
        "name_kr": "토마토",
        "name_en": "Tomato",
        "category": AllergenCategory.VEGETABLE,
        "type": AllergenType.FOOD,
        "description": "토마토, 잔디 꽃가루 교차반응",
    },
    "f31": {
        "code": "f31",
        "name_kr": "당근",
        "name_en": "Carrot",
        "category": AllergenCategory.VEGETABLE,
        "type": AllergenType.FOOD,
        "description": "당근, 자작나무 꽃가루 교차반응",
    },
    "f35": {
        "code": "f35",
        "name_kr": "감자",
        "name_en": "Potato",
        "category": AllergenCategory.VEGETABLE,
        "type": AllergenType.FOOD,
        "description": "감자",
    },
    "f47": {
        "code": "f47",
        "name_kr": "마늘",
        "name_en": "Garlic",
        "category": AllergenCategory.VEGETABLE,
        "type": AllergenType.FOOD,
        "description": "마늘",
    },
    "f48": {
        "code": "f48",
        "name_kr": "양파",
        "name_en": "Onion",
        "category": AllergenCategory.VEGETABLE,
        "type": AllergenType.FOOD,
        "description": "양파",
    },
    "f85": {
        "code": "f85",
        "name_kr": "셀러리",
        "name_en": "Celery",
        "category": AllergenCategory.VEGETABLE,
        "type": AllergenType.FOOD,
        "description": "셀러리, 자작나무 꽃가루 교차반응",
    },
    "f244": {
        "code": "f244",
        "name_kr": "오이",
        "name_en": "Cucumber",
        "category": AllergenCategory.VEGETABLE,
        "type": AllergenType.FOOD,
        "description": "오이",
    },
    "f212": {
        "code": "f212",
        "name_kr": "버섯",
        "name_en": "Mushroom",
        "category": AllergenCategory.VEGETABLE,
        "type": AllergenType.FOOD,
        "description": "버섯",
    },
    "f262": {
        "code": "f262",
        "name_kr": "가지",
        "name_en": "Eggplant",
        "category": AllergenCategory.VEGETABLE,
        "type": AllergenType.FOOD,
        "description": "가지",
        "note": "특수 항원",
    },
    "f225": {
        "code": "f225",
        "name_kr": "호박",
        "name_en": "Pumpkin",
        "category": AllergenCategory.VEGETABLE,
        "type": AllergenType.FOOD,
        "description": "호박",
        "note": "특수 항원",
    },
}


# ============================================================================
# 육류 (Meat) - 4종
# ============================================================================
MEAT_ALLERGENS = {
    "f26": {
        "code": "f26",
        "name_kr": "돼지고기",
        "name_en": "Pork",
        "category": AllergenCategory.MEAT,
        "type": AllergenType.FOOD,
        "description": "돼지고기, 고양이-돼지 증후군 관련",
    },
    "f27": {
        "code": "f27",
        "name_kr": "소고기",
        "name_en": "Beef",
        "category": AllergenCategory.MEAT,
        "type": AllergenType.FOOD,
        "description": "소고기, 우유 알러지 교차반응 가능",
    },
    "f83": {
        "code": "f83",
        "name_kr": "닭고기",
        "name_en": "Chicken",
        "category": AllergenCategory.MEAT,
        "type": AllergenType.FOOD,
        "description": "닭고기, 계란 알러지 교차반응 가능",
    },
    "f88": {
        "code": "f88",
        "name_kr": "양고기",
        "name_en": "Mutton/Lamb",
        "category": AllergenCategory.MEAT,
        "type": AllergenType.FOOD,
        "description": "양고기",
        "note": "특수 항원",
    },
}


# ============================================================================
# 과일 (Fruits) - 9종
# ============================================================================
FRUIT_ALLERGENS = {
    "f33": {
        "code": "f33",
        "name_kr": "오렌지",
        "name_en": "Orange",
        "category": AllergenCategory.FRUIT,
        "type": AllergenType.FOOD,
        "description": "오렌지",
    },
    "f36": {
        "code": "f36",
        "name_kr": "코코넛",
        "name_en": "Coconut",
        "category": AllergenCategory.FRUIT,
        "type": AllergenType.FOOD,
        "description": "코코넛",
    },
    "f44": {
        "code": "f44",
        "name_kr": "딸기",
        "name_en": "Strawberry",
        "category": AllergenCategory.FRUIT,
        "type": AllergenType.FOOD,
        "description": "딸기",
        "note": "특수 항원",
    },
    "f49": {
        "code": "f49",
        "name_kr": "사과",
        "name_en": "Apple",
        "category": AllergenCategory.FRUIT,
        "type": AllergenType.FOOD,
        "description": "사과, 자작나무 꽃가루 교차반응",
    },
    "f84": {
        "code": "f84",
        "name_kr": "키위",
        "name_en": "Kiwi",
        "category": AllergenCategory.FRUIT,
        "type": AllergenType.FOOD,
        "description": "키위, 라텍스 교차반응",
    },
    "f91": {
        "code": "f91",
        "name_kr": "망고",
        "name_en": "Mango",
        "category": AllergenCategory.FRUIT,
        "type": AllergenType.FOOD,
        "description": "망고",
    },
    "f92": {
        "code": "f92",
        "name_kr": "바나나",
        "name_en": "Banana",
        "category": AllergenCategory.FRUIT,
        "type": AllergenType.FOOD,
        "description": "바나나, 라텍스 교차반응",
    },
    "f93": {
        "code": "f93",
        "name_kr": "카카오",
        "name_en": "Cacao/Chocolate",
        "category": AllergenCategory.FRUIT,
        "type": AllergenType.FOOD,
        "description": "카카오/초콜릿",
    },
    "f95": {
        "code": "f95",
        "name_kr": "복숭아",
        "name_en": "Peach",
        "category": AllergenCategory.FRUIT,
        "type": AllergenType.FOOD,
        "description": "복숭아, 자작나무 꽃가루 교차반응, LTP 단백질",
    },
}


# ============================================================================
# 씨/견과류 (Seeds/Nuts) - 21종
# ============================================================================
SEED_NUT_ALLERGENS = {
    "f4": {
        "code": "f4",
        "name_kr": "밀가루",
        "name_en": "Wheat",
        "category": AllergenCategory.SEED_NUT,
        "type": AllergenType.FOOD,
        "description": "밀, 글루텐 관련 (셀리악병과 별개)",
    },
    "f9": {
        "code": "f9",
        "name_kr": "쌀",
        "name_en": "Rice",
        "category": AllergenCategory.SEED_NUT,
        "type": AllergenType.FOOD,
        "description": "쌀",
    },
    "f8": {
        "code": "f8",
        "name_kr": "옥수수",
        "name_en": "Corn/Maize",
        "category": AllergenCategory.SEED_NUT,
        "type": AllergenType.FOOD,
        "description": "옥수수",
    },
    "f6": {
        "code": "f6",
        "name_kr": "보리",
        "name_en": "Barley",
        "category": AllergenCategory.SEED_NUT,
        "type": AllergenType.FOOD,
        "description": "보리, 밀 교차반응",
    },
    "f11": {
        "code": "f11",
        "name_kr": "메밀",
        "name_en": "Buckwheat",
        "category": AllergenCategory.SEED_NUT,
        "type": AllergenType.FOOD,
        "description": "메밀, 심각한 알러지 반응 가능",
    },
    "f10": {
        "code": "f10",
        "name_kr": "참깨",
        "name_en": "Sesame seed",
        "category": AllergenCategory.SEED_NUT,
        "type": AllergenType.FOOD,
        "description": "참깨, 주요 식품 알러젠",
    },
    "f13": {
        "code": "f13",
        "name_kr": "땅콩",
        "name_en": "Peanut",
        "category": AllergenCategory.SEED_NUT,
        "type": AllergenType.FOOD,
        "description": "땅콩, 콩과 식물, 아나필락시스 위험",
    },
    "f14": {
        "code": "f14",
        "name_kr": "콩",
        "name_en": "Soybean",
        "category": AllergenCategory.SEED_NUT,
        "type": AllergenType.FOOD,
        "description": "대두/콩",
    },
    "f15": {
        "code": "f15",
        "name_kr": "흰강낭콩",
        "name_en": "White bean",
        "category": AllergenCategory.SEED_NUT,
        "type": AllergenType.FOOD,
        "description": "흰강낭콩",
    },
    "f17": {
        "code": "f17",
        "name_kr": "헤이즐넛",
        "name_en": "Hazelnut",
        "category": AllergenCategory.SEED_NUT,
        "type": AllergenType.FOOD,
        "description": "헤이즐넛, 자작나무 꽃가루 교차반응",
    },
    "f18": {
        "code": "f18",
        "name_kr": "브라질넛",
        "name_en": "Brazil nut",
        "category": AllergenCategory.SEED_NUT,
        "type": AllergenType.FOOD,
        "description": "브라질넛",
    },
    "f20": {
        "code": "f20",
        "name_kr": "아몬드",
        "name_en": "Almond",
        "category": AllergenCategory.SEED_NUT,
        "type": AllergenType.FOOD,
        "description": "아몬드",
        "note": "특수 항원",
    },
    "f202": {
        "code": "f202",
        "name_kr": "캐슈넛",
        "name_en": "Cashew nut",
        "category": AllergenCategory.SEED_NUT,
        "type": AllergenType.FOOD,
        "description": "캐슈넛, 피스타치오 교차반응",
    },
    "f203": {
        "code": "f203",
        "name_kr": "피스타치오",
        "name_en": "Pistachio",
        "category": AllergenCategory.SEED_NUT,
        "type": AllergenType.FOOD,
        "description": "피스타치오, 캐슈넛 교차반응",
        "note": "특수 항원",
    },
    "f253": {
        "code": "f253",
        "name_kr": "잣",
        "name_en": "Pine nut",
        "category": AllergenCategory.SEED_NUT,
        "type": AllergenType.FOOD,
        "description": "잣",
        "note": "특수 항원",
    },
    "f256": {
        "code": "f256",
        "name_kr": "호두",
        "name_en": "Walnut",
        "category": AllergenCategory.SEED_NUT,
        "type": AllergenType.FOOD,
        "description": "호두",
    },
    "f299": {
        "code": "f299",
        "name_kr": "밤",
        "name_en": "Chestnut",
        "category": AllergenCategory.SEED_NUT,
        "type": AllergenType.FOOD,
        "description": "밤, 라텍스 교차반응",
    },
    "f345": {
        "code": "f345",
        "name_kr": "마카다미아넛",
        "name_en": "Macadamia nut",
        "category": AllergenCategory.SEED_NUT,
        "type": AllergenType.FOOD,
        "description": "마카다미아",
    },
    "k84": {
        "code": "k84",
        "name_kr": "해바라기씨",
        "name_en": "Sunflower seed",
        "category": AllergenCategory.SEED_NUT,
        "type": AllergenType.FOOD,
        "description": "해바라기씨",
        "note": "특수 항원",
    },
}


# ============================================================================
# 전체 알러젠 마스터 데이터베이스
# ============================================================================
ALLERGEN_MASTER_DB: Dict[str, dict] = {
    **MITE_ALLERGENS,
    **DUST_ALLERGENS,
    **ANIMAL_ALLERGENS,
    **INSECT_ALLERGENS,
    **LATEX_ALLERGENS,
    **MICROORGANISM_ALLERGENS,
    **TREE_ALLERGENS,
    **GRASS_ALLERGENS,
    **WEED_ALLERGENS,
    **OTHER_ALLERGENS,
    **EGG_DAIRY_ALLERGENS,
    **CRUSTACEAN_ALLERGENS,
    **FISH_SHELLFISH_ALLERGENS,
    **VEGETABLE_ALLERGENS,
    **MEAT_ALLERGENS,
    **FRUIT_ALLERGENS,
    **SEED_NUT_ALLERGENS,
}


# ============================================================================
# 유틸리티 함수
# ============================================================================

def get_allergen_by_code(code: str) -> Optional[dict]:
    """코드로 알러젠 정보 조회"""
    return ALLERGEN_MASTER_DB.get(code.lower())


def get_allergens_by_category(category: AllergenCategory) -> List[dict]:
    """카테고리별 알러젠 목록 조회"""
    return [
        allergen for allergen in ALLERGEN_MASTER_DB.values()
        if allergen.get("category") == category
    ]


def get_allergens_by_type(allergen_type: AllergenType) -> List[dict]:
    """타입별 알러젠 목록 조회 (식품/흡입성)"""
    return [
        allergen for allergen in ALLERGEN_MASTER_DB.values()
        if allergen.get("type") == allergen_type
    ]


def get_food_allergens() -> List[dict]:
    """식품 알러젠 목록 조회"""
    return get_allergens_by_type(AllergenType.FOOD)


def get_inhalant_allergens() -> List[dict]:
    """흡입성 알러젠 목록 조회"""
    return get_allergens_by_type(AllergenType.INHALANT)


def get_all_allergen_codes() -> List[str]:
    """전체 알러젠 코드 목록"""
    return list(ALLERGEN_MASTER_DB.keys())


def get_allergen_count() -> int:
    """전체 알러젠 수"""
    return len(ALLERGEN_MASTER_DB)


def search_allergens(query: str) -> List[dict]:
    """알러젠 검색 (한글명/영문명)"""
    query = query.lower()
    results = []
    for allergen in ALLERGEN_MASTER_DB.values():
        if (query in allergen.get("name_kr", "").lower() or
            query in allergen.get("name_en", "").lower() or
            query in allergen.get("code", "").lower()):
            results.append(allergen)
    return results


def get_allergen_summary() -> dict:
    """알러젠 요약 통계"""
    categories = {}
    types = {}

    for allergen in ALLERGEN_MASTER_DB.values():
        cat = allergen.get("category")
        if cat:
            cat_name = cat.value if hasattr(cat, 'value') else str(cat)
            categories[cat_name] = categories.get(cat_name, 0) + 1

        typ = allergen.get("type")
        if typ:
            typ_name = typ.value if hasattr(typ, 'value') else str(typ)
            types[typ_name] = types.get(typ_name, 0) + 1

    return {
        "total": len(ALLERGEN_MASTER_DB),
        "by_category": categories,
        "by_type": types,
    }


# ============================================================================
# 코드-구 시스템 매핑 (allergen_prescription_db.py 연동용)
# ============================================================================
# prescription DB의 영문 키와 master DB의 코드 매핑
LEGACY_CODE_MAPPING = {
    # ========== 식품 알러젠 (21종) ==========
    # 기본 9종
    "peanut": "f13",
    "milk": "f2",
    "egg": "f1",  # 흰자 기준
    "wheat": "f4",
    "soy": "f14",
    "fish": "f3",  # 대구 기준
    "shellfish": "f24",  # 새우 기준
    "tree_nuts": "f256",  # 호두 기준
    "sesame": "f10",

    # Phase 2 추가 (12종)
    "crab": "f23",
    "tuna": "f40",
    "salmon": "f41",
    "apple": "f49",
    "peach": "f95",
    "kiwi": "f84",
    "buckwheat": "f11",
    "chicken": "f83",
    "pork": "f26",
    "beef": "f27",
    "walnut": "f256",
    "hazelnut": "f17",

    # ========== 흡입성 알러젠 (15종) ==========
    # 기본 7종
    "dust_mite": "d1",
    "pollen": "g6",  # 큰조아재비 기준
    "mold": "m6",  # 알터나리아 기준
    "cat": "e1",
    "dog": "e5",
    "cockroach": "i6",
    "pet_dander": "e1",  # 고양이 기준

    # Phase 2 추가 (8종)
    "d_pteronyssinus": "d1",
    "d_farinae": "d2",
    "japanese_cedar": "t17",
    "birch": "t3",
    "alternaria": "m6",
    "aspergillus": "m3",
    "timothy_grass": "g6",
    "mugwort": "w6",
}


def get_prescription_code(master_code: str) -> Optional[str]:
    """master DB 코드에서 prescription DB 키 조회"""
    for legacy, new in LEGACY_CODE_MAPPING.items():
        if new == master_code:
            return legacy
    return None


def get_all_prescription_codes() -> List[str]:
    """prescription DB에서 사용 가능한 모든 키 목록"""
    return list(LEGACY_CODE_MAPPING.keys())


def get_legacy_code(new_code: str) -> Optional[str]:
    """새 코드(master DB)에서 레거시 코드(prescription DB) 조회"""
    for legacy, new in LEGACY_CODE_MAPPING.items():
        if new == new_code:
            return legacy
    return None


def get_new_code(legacy_code: str) -> Optional[str]:
    """레거시 코드(prescription DB)에서 새 코드(master DB) 조회"""
    return LEGACY_CODE_MAPPING.get(legacy_code)
