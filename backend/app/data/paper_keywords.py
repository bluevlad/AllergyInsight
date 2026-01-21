"""논문 키워드 사전

논문 Abstract에서 specific_item을 자동 추출하기 위한 키워드 매핑
"""
from typing import Dict, List, Tuple

# 증상 키워드 (영어 → 한국어)
SYMPTOM_KEYWORDS: Dict[str, str] = {
    # 피부 증상
    "urticaria": "두드러기",
    "hives": "두드러기",
    "angioedema": "혈관부종",
    "eczema": "습진",
    "atopic dermatitis": "아토피 피부염",
    "pruritus": "가려움증",
    "itching": "가려움증",
    "rash": "발진",
    "erythema": "홍반",
    "flushing": "홍조",

    # 호흡기 증상
    "anaphylaxis": "아나필락시스",
    "anaphylactic shock": "아나필락시스 쇼크",
    "wheezing": "천명",
    "dyspnea": "호흡곤란",
    "shortness of breath": "호흡곤란",
    "bronchospasm": "기관지경련",
    "laryngeal edema": "후두부종",
    "rhinitis": "비염",
    "rhinorrhea": "콧물",
    "nasal congestion": "코막힘",
    "sneezing": "재채기",
    "cough": "기침",
    "asthma": "천식",

    # 소화기 증상
    "vomiting": "구토",
    "nausea": "메스꺼움",
    "diarrhea": "설사",
    "abdominal pain": "복통",
    "abdominal cramps": "복부경련",
    "oral allergy syndrome": "구강알러지증후군",
    "oral pruritus": "입안 가려움",
    "lip swelling": "입술부종",
    "tongue swelling": "혀부종",

    # 심혈관 증상
    "hypotension": "저혈압",
    "tachycardia": "빈맥",
    "dizziness": "어지러움",
    "syncope": "실신",
    "shock": "쇼크",

    # 눈 증상
    "conjunctivitis": "결막염",
    "eye itching": "눈가려움",
    "watery eyes": "눈물",
    "periorbital edema": "눈주위부종",
}

# 회피 식품 키워드 (영어 → 한국어)
AVOID_FOOD_KEYWORDS: Dict[str, Tuple[str, str]] = {
    # (한국어명, 관련 알러젠 코드)
    # 땅콩 관련
    "peanut butter": ("땅콩버터", "peanut"),
    "peanut oil": ("땅콩오일", "peanut"),
    "peanut flour": ("땅콩가루", "peanut"),
    "ground peanuts": ("땅콩분말", "peanut"),
    "peanut sauce": ("땅콩소스", "peanut"),

    # 우유 관련
    "cow's milk": ("우유", "milk"),
    "milk protein": ("우유단백질", "milk"),
    "casein": ("카제인", "milk"),
    "whey": ("유청", "milk"),
    "lactose": ("유당", "milk"),
    "cheese": ("치즈", "milk"),
    "butter": ("버터", "milk"),
    "cream": ("크림", "milk"),
    "yogurt": ("요거트", "milk"),
    "ice cream": ("아이스크림", "milk"),

    # 계란 관련
    "egg white": ("흰자", "egg"),
    "egg yolk": ("노른자", "egg"),
    "albumin": ("알부민", "egg"),
    "ovalbumin": ("오브알부민", "egg"),
    "ovomucoid": ("오보뮤코이드", "egg"),
    "mayonnaise": ("마요네즈", "egg"),

    # 밀 관련
    "wheat flour": ("밀가루", "wheat"),
    "gluten": ("글루텐", "wheat"),
    "bread": ("빵", "wheat"),
    "pasta": ("파스타", "wheat"),
    "noodles": ("면류", "wheat"),
    "cereals": ("시리얼", "wheat"),

    # 대두 관련
    "soy milk": ("두유", "soy"),
    "soy sauce": ("간장", "soy"),
    "tofu": ("두부", "soy"),
    "soy protein": ("대두단백", "soy"),
    "soybean oil": ("대두유", "soy"),
    "edamame": ("에다마메", "soy"),
    "miso": ("미소", "soy"),

    # 생선 관련
    "fish sauce": ("피시소스", "fish"),
    "fish oil": ("어유", "fish"),
    "anchovy": ("멸치", "fish"),
    "salmon": ("연어", "fish"),
    "tuna": ("참치", "fish"),
    "cod": ("대구", "fish"),

    # 갑각류 관련
    "shrimp": ("새우", "shellfish"),
    "crab": ("게", "shellfish"),
    "lobster": ("랍스터", "shellfish"),
    "crawfish": ("가재", "shellfish"),
    "prawn": ("왕새우", "shellfish"),
    "tropomyosin": ("트로포미오신", "shellfish"),

    # 견과류 관련
    "almond": ("아몬드", "tree_nuts"),
    "walnut": ("호두", "tree_nuts"),
    "cashew": ("캐슈넛", "tree_nuts"),
    "pistachio": ("피스타치오", "tree_nuts"),
    "hazelnut": ("헤이즐넛", "tree_nuts"),
    "macadamia": ("마카다미아", "tree_nuts"),
    "pecan": ("피칸", "tree_nuts"),
    "brazil nut": ("브라질넛", "tree_nuts"),

    # 참깨 관련
    "sesame oil": ("참기름", "sesame"),
    "sesame seeds": ("참깨", "sesame"),
    "tahini": ("타히니", "sesame"),
}

# 대체 식품 키워드 (영어 → 한국어, 관련 알러젠)
SUBSTITUTE_KEYWORDS: Dict[str, Tuple[str, str]] = {
    # 우유 대체
    "oat milk": ("귀리우유", "milk"),
    "almond milk": ("아몬드밀크", "milk"),
    "soy milk": ("두유", "milk"),
    "rice milk": ("쌀우유", "milk"),
    "coconut milk": ("코코넛밀크", "milk"),
    "lactose-free": ("무유당", "milk"),

    # 계란 대체
    "egg substitute": ("계란대체제", "egg"),
    "flax egg": ("아마씨에그", "egg"),
    "chia egg": ("치아시드에그", "egg"),
    "aquafaba": ("아쿠아파바", "egg"),

    # 밀 대체
    "gluten-free": ("글루텐프리", "wheat"),
    "rice flour": ("쌀가루", "wheat"),
    "almond flour": ("아몬드가루", "wheat"),
    "coconut flour": ("코코넛가루", "wheat"),
    "buckwheat": ("메밀", "wheat"),
    "quinoa": ("퀴노아", "wheat"),

    # 땅콩 대체
    "sunflower seed butter": ("해바라기씨버터", "peanut"),
    "sunflower butter": ("해바라기씨버터", "peanut"),
    "soy nut butter": ("콩버터", "peanut"),
    "seed butter": ("씨앗버터", "peanut"),
}

# 교차반응 키워드
CROSS_REACTIVITY_KEYWORDS: Dict[str, Tuple[str, str, str]] = {
    # (출발 알러젠, 도착 알러젠, 한국어 설명)
    "latex-fruit syndrome": ("latex", "fruit", "라텍스-과일 증후군"),
    "oral allergy syndrome": ("pollen", "fruit", "구강알러지증후군"),
    "pollen-food syndrome": ("pollen", "food", "꽃가루-식품 증후군"),
    "birch-apple": ("pollen", "apple", "자작나무-사과"),
    "shellfish-dust mite": ("shellfish", "dust_mite", "갑각류-집먼지진드기"),
    "shrimp-cockroach": ("shellfish", "cockroach", "새우-바퀴벌레"),
}

# 환경 관리 키워드 (흡입성 알러젠)
MANAGEMENT_KEYWORDS: Dict[str, Tuple[str, str]] = {
    # (한국어 관리법, 관련 알러젠)
    "hepa filter": ("헤파필터 사용", "dust_mite"),
    "air purifier": ("공기청정기", "dust_mite"),
    "mattress cover": ("매트리스커버", "dust_mite"),
    "bedding wash": ("침구류 세탁", "dust_mite"),
    "humidity control": ("습도 조절", "dust_mite"),
    "dehumidifier": ("제습기", "mold"),
    "ventilation": ("환기", "mold"),
    "mold removal": ("곰팡이 제거", "mold"),
    "pet-free zone": ("반려동물 출입금지", "pet_dander"),
    "pollen count": ("꽃가루 농도", "pollen"),
    "window closed": ("창문 닫기", "pollen"),
    "epinephrine": ("에피네프린", "general"),
    "epipen": ("에피펜", "general"),
    "antihistamine": ("항히스타민제", "general"),
}

# 논문 타입 키워드
PAPER_TYPE_KEYWORDS: Dict[str, str] = {
    "guideline": "guideline",
    "guidelines": "guideline",
    "position paper": "guideline",
    "consensus": "guideline",
    "recommendation": "guideline",
    "systematic review": "review",
    "literature review": "review",
    "review article": "review",
    "meta-analysis": "meta_analysis",
    "meta analysis": "meta_analysis",
    "pooled analysis": "meta_analysis",
    "randomized controlled trial": "research",
    "clinical trial": "research",
    "cohort study": "research",
    "case-control": "research",
    "observational study": "research",
}


def get_all_symptom_keywords() -> List[str]:
    """모든 증상 키워드 목록 반환"""
    return list(SYMPTOM_KEYWORDS.keys())


def get_all_food_keywords() -> List[str]:
    """모든 음식 키워드 목록 반환"""
    return list(AVOID_FOOD_KEYWORDS.keys()) + list(SUBSTITUTE_KEYWORDS.keys())


def get_keywords_for_allergen(allergen_code: str) -> Dict[str, List[str]]:
    """특정 알러젠과 관련된 모든 키워드 반환"""
    result = {
        "avoid_foods": [],
        "substitutes": [],
    }

    for en_term, (kr_term, code) in AVOID_FOOD_KEYWORDS.items():
        if code == allergen_code:
            result["avoid_foods"].append(en_term)

    for en_term, (kr_term, code) in SUBSTITUTE_KEYWORDS.items():
        if code == allergen_code:
            result["substitutes"].append(en_term)

    return result
