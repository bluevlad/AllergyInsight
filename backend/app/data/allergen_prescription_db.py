"""알러젠 처방 지식베이스

SGTi-Allergy Screen PLUS 검사 대상 알러젠에 대한
처방 권고 정보를 포함합니다.

식품 알러지: 9종
흡입성 알러지: 7종
총 16종 지원
"""
from typing import Optional

# ============================================================================
# 식품 알러지 (Food Allergens) - 9종
# ============================================================================

FOOD_ALLERGENS = {
    # -------------------------------------------------------------------------
    # 1. 땅콩 (Peanut)
    # -------------------------------------------------------------------------
    "peanut": {
        "name_kr": "땅콩",
        "name_en": "Peanut",
        "category": "food",
        "description": "땅콩은 가장 흔한 식품 알러젠 중 하나로, 심각한 알러지 반응을 일으킬 수 있습니다.",

        # 직접 회피해야 할 식품
        "avoid_foods": [
            "땅콩",
            "땅콩버터",
            "땅콩오일 (정제되지 않은 것)",
            "땅콩가루",
            "땅콩소스",
            "땅콩크림",
            "볶은 땅콩",
            "땅콩 스낵",
        ],

        # 숨겨진 알러젠이 포함될 수 있는 식품
        "hidden_sources": [
            "초콜릿 및 사탕류",
            "쿠키, 케이크, 베이커리 제품",
            "아이스크림",
            "시리얼 및 그래놀라",
            "에너지바, 프로틴바",
            "아시아 소스 (사테이 소스, 파다이 소스)",
            "샐러드 드레싱",
            "마가린 일부 제품",
            "빵 및 빵가루",
            "칠리 소스",
            "태국/베트남/중국 요리",
            "아프리카 요리",
            "인도 요리 (일부)",
        ],

        # 대체 식품
        "substitutes": [
            {
                "original": "땅콩버터",
                "alternatives": ["해바라기씨 버터", "타히니 (참깨 버터)", "아몬드 버터 (견과류 알러지 없는 경우)"],
                "notes": "견과류 교차반응 확인 필요"
            },
            {
                "original": "땅콩오일",
                "alternatives": ["카놀라유", "올리브유", "해바라기유", "포도씨유"],
                "notes": "정제된 땅콩오일은 일부 환자에게 안전할 수 있으나 주의 필요"
            },
            {
                "original": "땅콩 스낵",
                "alternatives": ["해바라기씨", "호박씨", "팝콘", "쌀과자"],
                "notes": ""
            },
        ],

        # 외식 시 주의
        "restaurant_cautions": [
            "중식당 (볶음요리에 땅콩오일 또는 땅콩 사용 빈번)",
            "태국 음식점 (파타이, 사테이 등)",
            "베트남 음식점",
            "아프리카 음식점",
            "인도 음식점",
            "디저트/베이커리 카페",
            "아이스크림 가게 (교차 오염 주의)",
        ],

        # 라벨 확인 키워드 (한글)
        "label_keywords_kr": [
            "땅콩",
            "낙화생",
            "피넛",
            "아라키스",
        ],

        # 라벨 확인 키워드 (영문)
        "label_keywords_en": [
            "peanut",
            "peanuts",
            "groundnut",
            "groundnuts",
            "arachis oil",
            "arachis hypogaea",
            "monkey nuts",
            "earth nuts",
            "beer nuts",
            "mixed nuts",
        ],

        # 등급별 예상 증상
        "symptoms_by_grade": {
            "1-2": {
                "symptoms": [
                    {"name": "경미한 가려움", "name_en": "mild itching", "probability": "60-70%", "onset": "수분~1시간"},
                    {"name": "입술/입안 따끔거림", "name_en": "oral tingling", "probability": "50-60%", "onset": "수분 이내"},
                ],
                "severity": "mild",
            },
            "3-4": {
                "symptoms": [
                    {"name": "두드러기", "name_en": "urticaria/hives", "probability": "70-80%", "onset": "30분~2시간"},
                    {"name": "혈관부종 (입술/눈꺼풀 부종)", "name_en": "angioedema", "probability": "40-50%", "onset": "30분~2시간"},
                    {"name": "복통", "name_en": "abdominal pain", "probability": "30-40%", "onset": "1~3시간"},
                    {"name": "구토", "name_en": "vomiting", "probability": "20-30%", "onset": "1~3시간"},
                ],
                "severity": "moderate",
            },
            "5-6": {
                "symptoms": [
                    {"name": "전신 두드러기", "name_en": "generalized urticaria", "probability": "80-90%", "onset": "수분~1시간"},
                    {"name": "호흡곤란", "name_en": "dyspnea", "probability": "40-60%", "onset": "수분~30분"},
                    {"name": "천명음 (쌕쌕거림)", "name_en": "wheezing", "probability": "30-50%", "onset": "수분~30분"},
                    {"name": "혈압저하", "name_en": "hypotension", "probability": "20-30%", "onset": "수분~30분"},
                    {"name": "아나필락시스", "name_en": "anaphylaxis", "probability": "10-25%", "onset": "수분~30분"},
                ],
                "severity": "severe",
            },
        },

        # 교차반응 정보
        "cross_reactivity": [
            {
                "allergen": "tree_nuts",
                "allergen_kr": "견과류",
                "probability": "25-40%",
                "common_protein": "저장 단백질 (Vicilins, Legumins)",
                "related_foods": ["호두", "아몬드", "캐슈넛", "피스타치오", "브라질넛"],
            },
            {
                "allergen": "soy",
                "allergen_kr": "대두",
                "probability": "5-10%",
                "common_protein": "콩과 식물 단백질",
                "related_foods": ["두부", "된장", "간장", "콩나물"],
            },
            {
                "allergen": "lupin",
                "allergen_kr": "루핀콩",
                "probability": "50-60%",
                "common_protein": "Conglutin",
                "related_foods": ["루핀 가루 함유 빵/파스타"],
            },
        ],
    },

    # -------------------------------------------------------------------------
    # 2. 우유 (Milk)
    # -------------------------------------------------------------------------
    "milk": {
        "name_kr": "우유",
        "name_en": "Milk",
        "category": "food",
        "description": "우유 알러지는 영유아에서 가장 흔한 식품 알러지이며, 카제인과 유청 단백질에 대한 반응입니다.",

        "avoid_foods": [
            "우유 (일반, 저지방, 무지방)",
            "치즈 (모든 종류)",
            "버터",
            "요거트",
            "크림",
            "아이스크림",
            "분유",
            "연유",
            "유청 (whey)",
            "카제인 (casein)",
        ],

        "hidden_sources": [
            "빵 및 베이커리 제품",
            "케이크, 쿠키, 비스킷",
            "초콜릿",
            "크림 소스, 그레이비",
            "수프 (크림 베이스)",
            "감자 튀김 (일부 버터 사용)",
            "소시지, 핫도그",
            "샐러드 드레싱",
            "마가린 일부",
            "캐러멜",
            "누가",
            "단백질 쉐이크/보충제",
            "일부 의약품 코팅",
        ],

        "substitutes": [
            {
                "original": "우유",
                "alternatives": ["두유", "귀리 우유", "쌀 우유", "아몬드 우유", "코코넛 우유"],
                "notes": "대두 또는 견과류 알러지 여부 확인 필요"
            },
            {
                "original": "치즈",
                "alternatives": ["비건 치즈 (캐슈넛 기반 등)", "영양효모"],
                "notes": "견과류 기반 대체품은 견과류 알러지 확인"
            },
            {
                "original": "버터",
                "alternatives": ["식물성 마가린 (유제품 미함유)", "코코넛 오일", "올리브유"],
                "notes": "마가린 성분표 확인 필수"
            },
            {
                "original": "요거트",
                "alternatives": ["두유 요거트", "코코넛 요거트"],
                "notes": ""
            },
            {
                "original": "아이스크림",
                "alternatives": ["소르베", "코코넛 아이스크림", "두유 아이스크림"],
                "notes": ""
            },
        ],

        "restaurant_cautions": [
            "양식당 (크림 소스 다수 사용)",
            "이탈리안 레스토랑 (치즈, 크림 파스타)",
            "베이커리/카페",
            "피자 가게",
            "패스트푸드점 (치즈버거, 아이스크림)",
            "인도 요리 (기 버터, 파니르 치즈)",
        ],

        "label_keywords_kr": [
            "우유",
            "유제품",
            "버터",
            "치즈",
            "크림",
            "유청",
            "카제인",
            "락토스",
            "유단백",
        ],

        "label_keywords_en": [
            "milk",
            "butter",
            "cheese",
            "cream",
            "whey",
            "casein",
            "caseinate",
            "lactose",
            "lactalbumin",
            "lactoglobulin",
            "ghee",
            "curds",
            "dairy",
            "milk protein",
        ],

        "symptoms_by_grade": {
            "1-2": {
                "symptoms": [
                    {"name": "피부 발진", "name_en": "skin rash", "probability": "50-60%", "onset": "1~3시간"},
                    {"name": "경미한 복부 불편감", "name_en": "mild abdominal discomfort", "probability": "40-50%", "onset": "1~3시간"},
                ],
                "severity": "mild",
            },
            "3-4": {
                "symptoms": [
                    {"name": "두드러기", "name_en": "urticaria", "probability": "60-70%", "onset": "30분~2시간"},
                    {"name": "구토", "name_en": "vomiting", "probability": "40-50%", "onset": "30분~2시간"},
                    {"name": "설사", "name_en": "diarrhea", "probability": "30-40%", "onset": "2~6시간"},
                    {"name": "복통", "name_en": "abdominal pain", "probability": "50-60%", "onset": "1~3시간"},
                ],
                "severity": "moderate",
            },
            "5-6": {
                "symptoms": [
                    {"name": "전신 두드러기", "name_en": "generalized urticaria", "probability": "70-80%", "onset": "수분~1시간"},
                    {"name": "호흡곤란", "name_en": "dyspnea", "probability": "30-40%", "onset": "수분~30분"},
                    {"name": "아나필락시스", "name_en": "anaphylaxis", "probability": "5-15%", "onset": "수분~30분"},
                ],
                "severity": "severe",
            },
        },

        "cross_reactivity": [
            {
                "allergen": "goat_milk",
                "allergen_kr": "염소유",
                "probability": "90%+",
                "common_protein": "카제인",
                "related_foods": ["염소유", "염소 치즈", "페타 치즈"],
            },
            {
                "allergen": "sheep_milk",
                "allergen_kr": "양유",
                "probability": "90%+",
                "common_protein": "카제인",
                "related_foods": ["양유", "로크포르 치즈", "페코리노 치즈"],
            },
            {
                "allergen": "beef",
                "allergen_kr": "소고기",
                "probability": "10-20%",
                "common_protein": "소 혈청 알부민",
                "related_foods": ["소고기"],
            },
        ],
    },

    # -------------------------------------------------------------------------
    # 3. 계란 (Egg)
    # -------------------------------------------------------------------------
    "egg": {
        "name_kr": "계란",
        "name_en": "Egg",
        "category": "food",
        "description": "계란 알러지는 흰자(알부민)와 노른자 단백질에 대한 반응으로, 아이들에게 매우 흔합니다.",

        "avoid_foods": [
            "계란 (삶은, 프라이, 스크램블 등 모든 형태)",
            "계란 흰자",
            "계란 노른자",
            "마요네즈",
            "머랭",
            "에그노그",
            "계란 국수/파스타",
            "계란찜",
            "오믈렛",
        ],

        "hidden_sources": [
            "빵 및 베이커리 제품",
            "케이크, 머핀, 쿠키",
            "파스타 (일부)",
            "튀김 옷 (배터)",
            "미트볼/미트로프",
            "마시멜로",
            "누가",
            "프레첼",
            "와플, 팬케이크",
            "아이스크림 (일부)",
            "샐러드 드레싱",
            "타르타르 소스",
            "일부 백신 (인플루엔자 등)",
        ],

        "substitutes": [
            {
                "original": "계란 (베이킹용)",
                "alternatives": ["아마씨 계란 (아마씨 1T + 물 3T)", "치아씨드 계란", "바나나 1/4개", "사과소스 1/4컵", "두부 (으깬 것)"],
                "notes": "용도에 따라 대체품 선택"
            },
            {
                "original": "마요네즈",
                "alternatives": ["비건 마요네즈", "아보카도", "후무스"],
                "notes": "성분표에서 계란 미함유 확인"
            },
            {
                "original": "계란 국수",
                "alternatives": ["쌀국수", "메밀국수 (계란 미함유)", "글루텐프리 파스타"],
                "notes": ""
            },
        ],

        "restaurant_cautions": [
            "베이커리/카페 (대부분 제품에 계란 함유)",
            "양식당 (오믈렛, 소스류)",
            "일식당 (계란말이, 돈부리)",
            "중식당 (계란 볶음밥)",
            "패스트푸드점",
            "브런치 전문점",
        ],

        "label_keywords_kr": [
            "계란",
            "달걀",
            "난백",
            "난황",
            "알부민",
            "마요네즈",
        ],

        "label_keywords_en": [
            "egg",
            "eggs",
            "albumin",
            "globulin",
            "lysozyme",
            "mayonnaise",
            "meringue",
            "ovalbumin",
            "ovomucin",
            "ovomucoid",
            "ovovitellin",
            "livetin",
            "vitellin",
            "egg lecithin",
        ],

        "symptoms_by_grade": {
            "1-2": {
                "symptoms": [
                    {"name": "피부 발진", "name_en": "skin rash", "probability": "50-60%", "onset": "30분~2시간"},
                    {"name": "입 주변 발적", "name_en": "perioral redness", "probability": "40-50%", "onset": "수분~30분"},
                ],
                "severity": "mild",
            },
            "3-4": {
                "symptoms": [
                    {"name": "두드러기", "name_en": "urticaria", "probability": "60-70%", "onset": "30분~2시간"},
                    {"name": "아토피 피부염 악화", "name_en": "atopic dermatitis flare", "probability": "40-50%", "onset": "수시간"},
                    {"name": "구토", "name_en": "vomiting", "probability": "30-40%", "onset": "1~3시간"},
                    {"name": "복통", "name_en": "abdominal pain", "probability": "30-40%", "onset": "1~3시간"},
                ],
                "severity": "moderate",
            },
            "5-6": {
                "symptoms": [
                    {"name": "전신 두드러기", "name_en": "generalized urticaria", "probability": "70-80%", "onset": "수분~1시간"},
                    {"name": "호흡곤란", "name_en": "dyspnea", "probability": "20-30%", "onset": "수분~30분"},
                    {"name": "아나필락시스", "name_en": "anaphylaxis", "probability": "5-10%", "onset": "수분~30분"},
                ],
                "severity": "severe",
            },
        },

        "cross_reactivity": [
            {
                "allergen": "chicken",
                "allergen_kr": "닭고기",
                "probability": "5-10%",
                "common_protein": "알파-리베틴",
                "related_foods": ["닭고기"],
            },
            {
                "allergen": "other_bird_eggs",
                "allergen_kr": "다른 조류 알",
                "probability": "50-70%",
                "common_protein": "오보알부민, 오보뮤코이드",
                "related_foods": ["오리알", "메추리알", "거위알"],
            },
        ],
    },

    # -------------------------------------------------------------------------
    # 4. 밀 (Wheat)
    # -------------------------------------------------------------------------
    "wheat": {
        "name_kr": "밀",
        "name_en": "Wheat",
        "category": "food",
        "description": "밀 알러지는 밀 단백질(글리아딘, 글루테닌 등)에 대한 면역 반응입니다. 셀리악병과는 다릅니다.",

        "avoid_foods": [
            "밀가루",
            "빵",
            "파스타/국수",
            "시리얼 (밀 함유)",
            "쿠키, 케이크",
            "밀 배아",
            "밀기울",
            "세몰리나",
            "듀럼밀",
            "스펠트밀",
            "불가",
            "쿠스쿠스",
        ],

        "hidden_sources": [
            "간장 (일부 밀 함유)",
            "맥주",
            "튀김 옷/빵가루",
            "소시지/가공육",
            "수프 (농후제로 밀가루 사용)",
            "그레이비 소스",
            "아이스크림 콘",
            "리코리스 (감초 사탕)",
            "일부 의약품/비타민",
            "플레이도우 (play-dough)",
        ],

        "substitutes": [
            {
                "original": "밀가루",
                "alternatives": ["쌀가루", "감자 전분", "타피오카 전분", "아몬드 가루", "코코넛 가루", "옥수수 전분"],
                "notes": "견과류 알러지 있으면 아몬드 가루 제외"
            },
            {
                "original": "빵",
                "alternatives": ["쌀빵", "글루텐프리 빵", "옥수수 또띠아"],
                "notes": "글루텐프리 표시 확인"
            },
            {
                "original": "파스타",
                "alternatives": ["쌀국수", "메밀국수 (100% 메밀)", "옥수수 파스타", "퀴노아 파스타"],
                "notes": "메밀국수는 밀가루 혼합 제품 주의"
            },
            {
                "original": "간장",
                "alternatives": ["타마리 (밀 미함유 간장)", "코코넛 아미노스"],
                "notes": "일반 간장은 밀 함유"
            },
        ],

        "restaurant_cautions": [
            "베이커리/카페",
            "이탈리안 (파스타, 피자)",
            "중식당 (면류, 만두, 튀김)",
            "일식당 (우동, 라멘, 튀김)",
            "패스트푸드 (햄버거 번, 튀김)",
            "한식당 (칼국수, 수제비, 부침개)",
        ],

        "label_keywords_kr": [
            "밀",
            "밀가루",
            "소맥분",
            "글루텐",
            "세몰리나",
        ],

        "label_keywords_en": [
            "wheat",
            "flour",
            "bread",
            "breadcrumbs",
            "bulgur",
            "couscous",
            "durum",
            "einkorn",
            "emmer",
            "farina",
            "kamut",
            "semolina",
            "spelt",
            "triticale",
            "gluten",
            "seitan",
        ],

        "symptoms_by_grade": {
            "1-2": {
                "symptoms": [
                    {"name": "피부 가려움", "name_en": "skin itching", "probability": "50-60%", "onset": "30분~2시간"},
                    {"name": "경미한 복부 불편감", "name_en": "mild GI discomfort", "probability": "30-40%", "onset": "1~3시간"},
                ],
                "severity": "mild",
            },
            "3-4": {
                "symptoms": [
                    {"name": "두드러기", "name_en": "urticaria", "probability": "50-60%", "onset": "30분~2시간"},
                    {"name": "복통", "name_en": "abdominal pain", "probability": "40-50%", "onset": "1~3시간"},
                    {"name": "구토", "name_en": "vomiting", "probability": "20-30%", "onset": "1~3시간"},
                    {"name": "비염 증상", "name_en": "rhinitis", "probability": "20-30%", "onset": "30분~1시간"},
                ],
                "severity": "moderate",
            },
            "5-6": {
                "symptoms": [
                    {"name": "전신 두드러기", "name_en": "generalized urticaria", "probability": "60-70%", "onset": "수분~1시간"},
                    {"name": "호흡곤란", "name_en": "dyspnea", "probability": "20-30%", "onset": "수분~30분"},
                    {"name": "운동유발 아나필락시스", "name_en": "exercise-induced anaphylaxis", "probability": "10-20%", "onset": "운동 중/후"},
                ],
                "severity": "severe",
            },
        },

        "cross_reactivity": [
            {
                "allergen": "barley",
                "allergen_kr": "보리",
                "probability": "20-25%",
                "common_protein": "프롤라민",
                "related_foods": ["보리", "보리차", "맥주"],
            },
            {
                "allergen": "rye",
                "allergen_kr": "호밀",
                "probability": "20-25%",
                "common_protein": "프롤라민",
                "related_foods": ["호밀빵"],
            },
            {
                "allergen": "grass_pollen",
                "allergen_kr": "잔디 꽃가루",
                "probability": "10-20%",
                "common_protein": "프로필린",
                "related_foods": [],
            },
        ],
    },

    # -------------------------------------------------------------------------
    # 5. 대두 (Soy)
    # -------------------------------------------------------------------------
    "soy": {
        "name_kr": "대두",
        "name_en": "Soy",
        "category": "food",
        "description": "대두(콩) 알러지는 콩 단백질에 대한 반응으로, 다양한 가공식품에 숨겨져 있어 주의가 필요합니다.",

        "avoid_foods": [
            "대두/콩",
            "두부",
            "두유",
            "된장",
            "고추장 (일부)",
            "간장",
            "콩나물",
            "에다마메",
            "미소",
            "템페",
            "대두유 (정제되지 않은 것)",
            "콩가루",
            "유부",
        ],

        "hidden_sources": [
            "가공식품 (대두 단백 첨가)",
            "소시지/햄",
            "빵 및 베이커리",
            "참치캔 (대두유 사용)",
            "마가린",
            "초콜릿",
            "아이스크림",
            "이유식",
            "단백질 보충제",
            "채식 대체육",
            "아시아 소스류",
        ],

        "substitutes": [
            {
                "original": "두유",
                "alternatives": ["귀리 우유", "쌀 우유", "아몬드 우유", "코코넛 우유"],
                "notes": "견과류 알러지 확인"
            },
            {
                "original": "두부",
                "alternatives": ["닭고기", "생선", "계란 (알러지 없는 경우)"],
                "notes": ""
            },
            {
                "original": "간장",
                "alternatives": ["코코넛 아미노스", "소금 + 식초 믹스"],
                "notes": ""
            },
            {
                "original": "대두유",
                "alternatives": ["카놀라유", "올리브유", "해바라기유"],
                "notes": "고도 정제된 대두유는 일부 환자에게 안전할 수 있음"
            },
        ],

        "restaurant_cautions": [
            "한식당 (된장, 간장, 두부 사용 빈번)",
            "일식당 (간장, 된장국, 에다마메)",
            "중식당 (두부 요리, 간장)",
            "채식/비건 식당 (대두 기반 대체육)",
            "아시아 퓨전 레스토랑",
        ],

        "label_keywords_kr": [
            "대두",
            "콩",
            "두부",
            "간장",
            "된장",
            "콩기름",
            "대두유",
            "식물성 단백",
        ],

        "label_keywords_en": [
            "soy",
            "soya",
            "soybean",
            "soy protein",
            "soy lecithin",
            "tofu",
            "miso",
            "tempeh",
            "edamame",
            "textured vegetable protein",
            "TVP",
            "hydrolyzed soy protein",
        ],

        "symptoms_by_grade": {
            "1-2": {
                "symptoms": [
                    {"name": "경미한 복부 불편감", "name_en": "mild GI discomfort", "probability": "40-50%", "onset": "1~3시간"},
                    {"name": "피부 가려움", "name_en": "skin itching", "probability": "30-40%", "onset": "30분~2시간"},
                ],
                "severity": "mild",
            },
            "3-4": {
                "symptoms": [
                    {"name": "두드러기", "name_en": "urticaria", "probability": "50-60%", "onset": "30분~2시간"},
                    {"name": "복통", "name_en": "abdominal pain", "probability": "40-50%", "onset": "1~3시간"},
                    {"name": "구토", "name_en": "vomiting", "probability": "20-30%", "onset": "1~3시간"},
                    {"name": "아토피 피부염 악화", "name_en": "atopic dermatitis flare", "probability": "30-40%", "onset": "수시간"},
                ],
                "severity": "moderate",
            },
            "5-6": {
                "symptoms": [
                    {"name": "전신 두드러기", "name_en": "generalized urticaria", "probability": "60-70%", "onset": "수분~1시간"},
                    {"name": "호흡곤란", "name_en": "dyspnea", "probability": "15-25%", "onset": "수분~30분"},
                    {"name": "아나필락시스", "name_en": "anaphylaxis", "probability": "5-10%", "onset": "수분~30분"},
                ],
                "severity": "severe",
            },
        },

        "cross_reactivity": [
            {
                "allergen": "peanut",
                "allergen_kr": "땅콩",
                "probability": "5-15%",
                "common_protein": "콩과 식물 단백질",
                "related_foods": ["땅콩"],
            },
            {
                "allergen": "other_legumes",
                "allergen_kr": "기타 콩류",
                "probability": "5-10%",
                "common_protein": "저장 단백질",
                "related_foods": ["렌틸콩", "병아리콩", "완두콩"],
            },
            {
                "allergen": "birch_pollen",
                "allergen_kr": "자작나무 꽃가루",
                "probability": "10-15%",
                "common_protein": "Gly m 4 (PR-10)",
                "related_foods": [],
            },
        ],
    },

    # -------------------------------------------------------------------------
    # 6. 생선 (Fish)
    # -------------------------------------------------------------------------
    "fish": {
        "name_kr": "생선",
        "name_en": "Fish",
        "category": "food",
        "description": "생선 알러지는 주로 파르브알부민 단백질에 대한 반응으로, 특정 어종 또는 모든 생선에 반응할 수 있습니다.",

        "avoid_foods": [
            "모든 종류의 생선",
            "참치",
            "연어",
            "고등어",
            "삼치",
            "광어",
            "도미",
            "대구",
            "명태",
            "청어",
            "멸치",
            "정어리",
            "어묵",
            "피쉬 소스",
            "생선 젓갈",
        ],

        "hidden_sources": [
            "시저 샐러드 드레싱 (멸치)",
            "우스터 소스",
            "김치 (젓갈 함유)",
            "젓갈류",
            "일부 아시아 소스",
            "수프/육수 (생선 베이스)",
            "오메가-3 보충제 (어유)",
            "일부 화장품/의약품",
            "비료 (생선 기반)",
        ],

        "substitutes": [
            {
                "original": "생선",
                "alternatives": ["닭고기", "소고기", "돼지고기", "두부 (대두 알러지 없는 경우)"],
                "notes": ""
            },
            {
                "original": "오메가-3 (어유)",
                "alternatives": ["아마씨유", "치아씨드", "호두 (견과류 알러지 없는 경우)", "해조류 기반 오메가-3"],
                "notes": ""
            },
            {
                "original": "피쉬 소스",
                "alternatives": ["간장", "코코넛 아미노스", "버섯 소스"],
                "notes": ""
            },
        ],

        "restaurant_cautions": [
            "일식당 (회, 초밥, 다시 육수)",
            "한식당 (젓갈, 김치, 생선 반찬)",
            "태국/베트남 음식점 (피쉬 소스)",
            "해산물 전문점",
            "중식당 (생선 요리)",
        ],

        "label_keywords_kr": [
            "생선",
            "어류",
            "멸치",
            "참치",
            "연어",
            "피쉬",
            "젓갈",
            "액젓",
            "어묵",
        ],

        "label_keywords_en": [
            "fish",
            "anchovy",
            "tuna",
            "salmon",
            "cod",
            "mackerel",
            "sardine",
            "fish sauce",
            "fish oil",
            "omega-3",
            "surimi",
            "imitation crab",
        ],

        "symptoms_by_grade": {
            "1-2": {
                "symptoms": [
                    {"name": "입 주변 가려움", "name_en": "oral itching", "probability": "50-60%", "onset": "수분~30분"},
                    {"name": "두드러기", "name_en": "urticaria", "probability": "40-50%", "onset": "30분~2시간"},
                ],
                "severity": "mild",
            },
            "3-4": {
                "symptoms": [
                    {"name": "전신 두드러기", "name_en": "generalized urticaria", "probability": "60-70%", "onset": "30분~2시간"},
                    {"name": "혈관부종", "name_en": "angioedema", "probability": "30-40%", "onset": "30분~2시간"},
                    {"name": "구토", "name_en": "vomiting", "probability": "30-40%", "onset": "1~3시간"},
                    {"name": "복통", "name_en": "abdominal pain", "probability": "30-40%", "onset": "1~3시간"},
                ],
                "severity": "moderate",
            },
            "5-6": {
                "symptoms": [
                    {"name": "심한 전신 두드러기", "name_en": "severe generalized urticaria", "probability": "70-80%", "onset": "수분~1시간"},
                    {"name": "호흡곤란", "name_en": "dyspnea", "probability": "30-40%", "onset": "수분~30분"},
                    {"name": "아나필락시스", "name_en": "anaphylaxis", "probability": "10-20%", "onset": "수분~30분"},
                ],
                "severity": "severe",
            },
        },

        "cross_reactivity": [
            {
                "allergen": "other_fish",
                "allergen_kr": "다른 생선류",
                "probability": "50-70%",
                "common_protein": "파르브알부민",
                "related_foods": ["대부분의 다른 생선"],
            },
            {
                "allergen": "shellfish",
                "allergen_kr": "갑각류",
                "probability": "5-10%",
                "common_protein": "",
                "related_foods": ["새우", "게", "랍스터"],
            },
        ],
    },

    # -------------------------------------------------------------------------
    # 7. 갑각류 (Shellfish)
    # -------------------------------------------------------------------------
    "shellfish": {
        "name_kr": "갑각류",
        "name_en": "Shellfish",
        "category": "food",
        "description": "갑각류 알러지는 새우, 게, 랍스터 등의 트로포미오신 단백질에 대한 반응으로, 성인에서 가장 흔한 식품 알러지 중 하나입니다.",

        "avoid_foods": [
            "새우",
            "게",
            "랍스터",
            "가재",
            "크릴새우",
            "바닷가재",
            "킹크랩",
            "대게",
            "꽃게",
        ],

        "hidden_sources": [
            "해산물 수프/찌개",
            "해산물 스톡/육수",
            "새우젓",
            "굴소스 (일부)",
            "XO 소스",
            "파에야",
            "짬뽕",
            "해물 볶음밥",
            "칵테일 새우",
            "일부 아시아 스낵",
            "글루코사민 보충제 (새우 껍질 유래)",
        ],

        "substitutes": [
            {
                "original": "새우/게",
                "alternatives": ["생선 (생선 알러지 없는 경우)", "두부", "닭고기", "버섯"],
                "notes": "생선 교차반응 확인 필요"
            },
            {
                "original": "새우젓",
                "alternatives": ["소금", "멸치젓 (생선 알러지 없는 경우)"],
                "notes": ""
            },
            {
                "original": "굴소스",
                "alternatives": ["버섯 굴소스 (채식용)", "간장 + 설탕 믹스"],
                "notes": ""
            },
        ],

        "restaurant_cautions": [
            "해산물 전문점",
            "일식당 (초밥, 새우튀김)",
            "중식당 (해물요리, 짬뽕)",
            "태국/베트남 음식점",
            "한식당 (해물찌개, 젓갈)",
            "스페인 요리점 (파에야)",
        ],

        "label_keywords_kr": [
            "새우",
            "게",
            "갑각류",
            "크랩",
            "쉬림프",
            "랍스터",
            "가재",
        ],

        "label_keywords_en": [
            "shrimp",
            "prawn",
            "crab",
            "lobster",
            "crayfish",
            "crawfish",
            "shellfish",
            "crustacean",
            "krill",
            "scampi",
        ],

        "symptoms_by_grade": {
            "1-2": {
                "symptoms": [
                    {"name": "입 주변 가려움", "name_en": "oral itching", "probability": "50-60%", "onset": "수분~30분"},
                    {"name": "피부 가려움", "name_en": "skin itching", "probability": "40-50%", "onset": "30분~2시간"},
                ],
                "severity": "mild",
            },
            "3-4": {
                "symptoms": [
                    {"name": "두드러기", "name_en": "urticaria", "probability": "60-70%", "onset": "30분~2시간"},
                    {"name": "혈관부종", "name_en": "angioedema", "probability": "30-40%", "onset": "30분~2시간"},
                    {"name": "구토", "name_en": "vomiting", "probability": "30-40%", "onset": "1~3시간"},
                    {"name": "복통", "name_en": "abdominal pain", "probability": "30-40%", "onset": "1~3시간"},
                ],
                "severity": "moderate",
            },
            "5-6": {
                "symptoms": [
                    {"name": "심한 전신 두드러기", "name_en": "severe generalized urticaria", "probability": "70-80%", "onset": "수분~1시간"},
                    {"name": "호흡곤란", "name_en": "dyspnea", "probability": "30-40%", "onset": "수분~30분"},
                    {"name": "아나필락시스", "name_en": "anaphylaxis", "probability": "15-25%", "onset": "수분~30분"},
                ],
                "severity": "severe",
            },
        },

        "cross_reactivity": [
            {
                "allergen": "mollusks",
                "allergen_kr": "연체류",
                "probability": "30-50%",
                "common_protein": "트로포미오신",
                "related_foods": ["조개", "굴", "홍합", "오징어", "문어"],
            },
            {
                "allergen": "dust_mite",
                "allergen_kr": "집먼지진드기",
                "probability": "60-80%",
                "common_protein": "트로포미오신",
                "related_foods": [],
            },
            {
                "allergen": "cockroach",
                "allergen_kr": "바퀴벌레",
                "probability": "40-60%",
                "common_protein": "트로포미오신",
                "related_foods": [],
            },
        ],
    },

    # -------------------------------------------------------------------------
    # 8. 견과류 (Tree Nuts)
    # -------------------------------------------------------------------------
    "tree_nuts": {
        "name_kr": "견과류",
        "name_en": "Tree Nuts",
        "category": "food",
        "description": "견과류 알러지는 호두, 아몬드, 캐슈넛 등 나무 열매에 대한 반응으로, 땅콩 알러지와 별개입니다.",

        "avoid_foods": [
            "호두",
            "아몬드",
            "캐슈넛",
            "피스타치오",
            "마카다미아",
            "브라질넛",
            "헤이즐넛",
            "피칸",
            "잣",
            "밤",
            "견과류 오일",
            "견과류 버터",
        ],

        "hidden_sources": [
            "초콜릿",
            "쿠키, 케이크, 베이커리",
            "시리얼/그래놀라",
            "에너지바",
            "아이스크림",
            "페스토 소스 (잣)",
            "마지팬 (아몬드)",
            "누가",
            "프랄린",
            "일부 샐러드",
            "아시아 요리 (캐슈넛)",
            "화장품 (아몬드 오일 등)",
        ],

        "substitutes": [
            {
                "original": "견과류 버터",
                "alternatives": ["해바라기씨 버터", "타히니", "호박씨 버터"],
                "notes": ""
            },
            {
                "original": "아몬드 가루",
                "alternatives": ["코코넛 가루", "해바라기씨 가루", "쌀가루"],
                "notes": ""
            },
            {
                "original": "페스토 (잣)",
                "alternatives": ["잣 없는 페스토", "해바라기씨 페스토"],
                "notes": ""
            },
            {
                "original": "견과류 스낵",
                "alternatives": ["해바라기씨", "호박씨", "팝콘", "볶은 병아리콩"],
                "notes": ""
            },
        ],

        "restaurant_cautions": [
            "베이커리/카페",
            "아이스크림 가게",
            "아시아 레스토랑 (캐슈넛 볶음)",
            "이탈리안 (페스토, 아몬드)",
            "인도 요리 (캐슈넛, 아몬드)",
            "디저트 전문점",
        ],

        "label_keywords_kr": [
            "견과류",
            "호두",
            "아몬드",
            "캐슈넛",
            "피스타치오",
            "마카다미아",
            "헤이즐넛",
            "잣",
            "밤",
        ],

        "label_keywords_en": [
            "tree nut",
            "nut",
            "walnut",
            "almond",
            "cashew",
            "pistachio",
            "macadamia",
            "brazil nut",
            "hazelnut",
            "filbert",
            "pecan",
            "pine nut",
            "chestnut",
            "praline",
            "marzipan",
            "nougat",
        ],

        "symptoms_by_grade": {
            "1-2": {
                "symptoms": [
                    {"name": "입 주변 가려움", "name_en": "oral itching", "probability": "50-60%", "onset": "수분~30분"},
                    {"name": "경미한 두드러기", "name_en": "mild urticaria", "probability": "40-50%", "onset": "30분~2시간"},
                ],
                "severity": "mild",
            },
            "3-4": {
                "symptoms": [
                    {"name": "두드러기", "name_en": "urticaria", "probability": "60-70%", "onset": "30분~2시간"},
                    {"name": "혈관부종", "name_en": "angioedema", "probability": "30-40%", "onset": "30분~2시간"},
                    {"name": "복통", "name_en": "abdominal pain", "probability": "30-40%", "onset": "1~3시간"},
                    {"name": "구토", "name_en": "vomiting", "probability": "20-30%", "onset": "1~3시간"},
                ],
                "severity": "moderate",
            },
            "5-6": {
                "symptoms": [
                    {"name": "심한 전신 두드러기", "name_en": "severe generalized urticaria", "probability": "70-80%", "onset": "수분~1시간"},
                    {"name": "호흡곤란", "name_en": "dyspnea", "probability": "30-40%", "onset": "수분~30분"},
                    {"name": "아나필락시스", "name_en": "anaphylaxis", "probability": "15-25%", "onset": "수분~30분"},
                ],
                "severity": "severe",
            },
        },

        "cross_reactivity": [
            {
                "allergen": "peanut",
                "allergen_kr": "땅콩",
                "probability": "25-40%",
                "common_protein": "저장 단백질",
                "related_foods": ["땅콩"],
            },
            {
                "allergen": "other_tree_nuts",
                "allergen_kr": "다른 견과류",
                "probability": "30-50%",
                "common_protein": "다양한 저장 단백질",
                "related_foods": ["개별 견과류 간 교차반응 흔함"],
            },
            {
                "allergen": "birch_pollen",
                "allergen_kr": "자작나무 꽃가루",
                "probability": "20-40%",
                "common_protein": "PR-10 단백질",
                "related_foods": ["헤이즐넛 특히 관련"],
            },
        ],
    },

    # -------------------------------------------------------------------------
    # 9. 참깨 (Sesame)
    # -------------------------------------------------------------------------
    "sesame": {
        "name_kr": "참깨",
        "name_en": "Sesame",
        "category": "food",
        "description": "참깨 알러지는 최근 증가 추세에 있으며, 많은 국가에서 주요 알러젠으로 지정되었습니다.",

        "avoid_foods": [
            "참깨",
            "깨소금",
            "참기름",
            "타히니 (참깨 버터)",
            "후무스 (타히니 함유)",
            "할바",
            "참깨빵 (햄버거 번)",
            "참깨과자",
        ],

        "hidden_sources": [
            "아시아 요리 전반",
            "중동 요리 (후무스, 팔라펠)",
            "베이글, 빵 토핑",
            "샐러드 드레싱",
            "스시 (참깨 토핑)",
            "쿠키, 크래커",
            "에너지바",
            "일부 화장품",
            "마사지 오일",
        ],

        "substitutes": [
            {
                "original": "참기름",
                "alternatives": ["들기름 (들깨 알러지 없는 경우)", "포도씨유", "카놀라유"],
                "notes": ""
            },
            {
                "original": "타히니",
                "alternatives": ["해바라기씨 버터", "캐슈넛 버터 (견과류 알러지 없는 경우)"],
                "notes": ""
            },
            {
                "original": "깨소금",
                "alternatives": ["소금", "들깨가루 (들깨 알러지 없는 경우)"],
                "notes": ""
            },
        ],

        "restaurant_cautions": [
            "한식당 (비빔밥, 나물, 참기름 사용)",
            "일식당 (참깨 드레싱, 토핑)",
            "중동 음식점 (후무스, 팔라펠)",
            "중식당",
            "패스트푸드 (참깨빵 햄버거)",
            "베이글 전문점",
        ],

        "label_keywords_kr": [
            "참깨",
            "깨",
            "참기름",
            "세서미",
            "타히니",
        ],

        "label_keywords_en": [
            "sesame",
            "sesame seed",
            "sesame oil",
            "tahini",
            "tahina",
            "halvah",
            "hummus",
            "benne seed",
            "gingelly oil",
            "til",
            "sesamum indicum",
        ],

        "symptoms_by_grade": {
            "1-2": {
                "symptoms": [
                    {"name": "입 주변 가려움", "name_en": "oral itching", "probability": "50-60%", "onset": "수분~30분"},
                    {"name": "경미한 피부 발진", "name_en": "mild skin rash", "probability": "40-50%", "onset": "30분~2시간"},
                ],
                "severity": "mild",
            },
            "3-4": {
                "symptoms": [
                    {"name": "두드러기", "name_en": "urticaria", "probability": "60-70%", "onset": "30분~2시간"},
                    {"name": "혈관부종", "name_en": "angioedema", "probability": "30-40%", "onset": "30분~2시간"},
                    {"name": "복통", "name_en": "abdominal pain", "probability": "30-40%", "onset": "1~3시간"},
                ],
                "severity": "moderate",
            },
            "5-6": {
                "symptoms": [
                    {"name": "심한 전신 두드러기", "name_en": "severe generalized urticaria", "probability": "70-80%", "onset": "수분~1시간"},
                    {"name": "호흡곤란", "name_en": "dyspnea", "probability": "25-35%", "onset": "수분~30분"},
                    {"name": "아나필락시스", "name_en": "anaphylaxis", "probability": "10-20%", "onset": "수분~30분"},
                ],
                "severity": "severe",
            },
        },

        "cross_reactivity": [
            {
                "allergen": "tree_nuts",
                "allergen_kr": "견과류",
                "probability": "10-20%",
                "common_protein": "저장 단백질",
                "related_foods": ["호두", "캐슈넛"],
            },
            {
                "allergen": "poppy_seed",
                "allergen_kr": "양귀비씨",
                "probability": "30-40%",
                "common_protein": "올레오신",
                "related_foods": ["양귀비씨 베이글/머핀"],
            },
            {
                "allergen": "kiwi",
                "allergen_kr": "키위",
                "probability": "10-20%",
                "common_protein": "2S 알부민",
                "related_foods": ["키위"],
            },
        ],
    },
}


# ============================================================================
# 흡입성 알러지 (Inhalant Allergens) - 7종
# ============================================================================

INHALANT_ALLERGENS = {
    # -------------------------------------------------------------------------
    # 1. 집먼지진드기 (House Dust Mite)
    # -------------------------------------------------------------------------
    "dust_mite": {
        "name_kr": "집먼지진드기",
        "name_en": "House Dust Mite",
        "category": "inhalant",
        "description": "집먼지진드기는 실내 알러지의 가장 흔한 원인으로, 침구류, 카펫, 천 소재에서 번식합니다.",

        # 회피해야 할 환경/물질
        "avoid_exposure": [
            "오래된 침구류",
            "카펫",
            "천 소파",
            "봉제 인형",
            "두꺼운 커튼",
            "먼지가 많은 환경",
        ],

        # 관리 권고사항
        "management_tips": [
            "침구류를 주 1회 60°C 이상 물로 세탁",
            "진드기 방지 침구 커버 사용",
            "카펫 대신 나무/타일 바닥 권장",
            "실내 습도 50% 이하 유지",
            "HEPA 필터 공기청정기 사용",
            "정기적인 진공청소 (HEPA 필터 청소기)",
            "봉제 인형은 -18°C 냉동 후 세탁",
            "침실에서 반려동물 배제",
        ],

        "symptoms_by_grade": {
            "1-2": {
                "symptoms": [
                    {"name": "간헐적 코막힘", "name_en": "intermittent nasal congestion", "probability": "60-70%", "onset": "노출 후 수분~수시간"},
                    {"name": "재채기", "name_en": "sneezing", "probability": "50-60%", "onset": "노출 즉시~수분"},
                ],
                "severity": "mild",
            },
            "3-4": {
                "symptoms": [
                    {"name": "지속적 비염", "name_en": "persistent rhinitis", "probability": "70-80%", "onset": "만성"},
                    {"name": "눈 가려움/충혈", "name_en": "itchy/red eyes", "probability": "50-60%", "onset": "노출 시"},
                    {"name": "기침", "name_en": "cough", "probability": "40-50%", "onset": "노출 후"},
                    {"name": "아토피 피부염 악화", "name_en": "atopic dermatitis flare", "probability": "30-40%", "onset": "지속 노출 시"},
                ],
                "severity": "moderate",
            },
            "5-6": {
                "symptoms": [
                    {"name": "천식 증상", "name_en": "asthma symptoms", "probability": "50-70%", "onset": "노출 시"},
                    {"name": "심한 비염", "name_en": "severe rhinitis", "probability": "70-80%", "onset": "만성"},
                    {"name": "수면장애", "name_en": "sleep disturbance", "probability": "40-50%", "onset": "만성"},
                ],
                "severity": "severe",
            },
        },

        "cross_reactivity": [
            {
                "allergen": "shellfish",
                "allergen_kr": "갑각류",
                "probability": "60-80%",
                "common_protein": "트로포미오신",
                "related_foods": ["새우", "게", "랍스터"],
            },
            {
                "allergen": "cockroach",
                "allergen_kr": "바퀴벌레",
                "probability": "70-80%",
                "common_protein": "트로포미오신",
                "related_foods": [],
            },
            {
                "allergen": "storage_mite",
                "allergen_kr": "저장진드기",
                "probability": "80-90%",
                "common_protein": "유사 단백질",
                "related_foods": [],
            },
        ],

        # 식품 관련 주의 (교차반응)
        "food_cautions": [
            "갑각류 (새우, 게) - 교차반응 가능성 높음",
            "연체류 (오징어, 조개) - 교차반응 가능성",
        ],
    },

    # -------------------------------------------------------------------------
    # 2. 꽃가루 (Pollen)
    # -------------------------------------------------------------------------
    "pollen": {
        "name_kr": "꽃가루",
        "name_en": "Pollen",
        "category": "inhalant",
        "description": "꽃가루 알러지(화분증)는 계절성 알러지로, 나무, 잔디, 잡초의 꽃가루에 반응합니다.",

        "avoid_exposure": [
            "꽃가루 농도가 높은 날 외출",
            "바람이 많이 부는 날 외출",
            "이른 아침 (꽃가루 농도 최고)",
            "잔디 깎기",
            "정원 작업",
        ],

        "management_tips": [
            "꽃가루 예보 확인 후 외출",
            "외출 시 마스크 및 선글라스 착용",
            "외출 후 샤워 및 옷 세탁",
            "창문 닫고 에어컨 사용",
            "HEPA 필터 공기청정기 사용",
            "차량 에어컨 필터 정기 교체",
            "빨래 실내 건조",
            "반려동물 외출 후 닦아주기",
        ],

        "symptoms_by_grade": {
            "1-2": {
                "symptoms": [
                    {"name": "재채기", "name_en": "sneezing", "probability": "70-80%", "onset": "노출 즉시"},
                    {"name": "맑은 콧물", "name_en": "runny nose", "probability": "60-70%", "onset": "노출 즉시"},
                ],
                "severity": "mild",
            },
            "3-4": {
                "symptoms": [
                    {"name": "심한 비염", "name_en": "severe rhinitis", "probability": "70-80%", "onset": "계절 시"},
                    {"name": "눈 가려움/충혈", "name_en": "itchy/red eyes", "probability": "60-70%", "onset": "노출 시"},
                    {"name": "코막힘", "name_en": "nasal congestion", "probability": "60-70%", "onset": "지속"},
                    {"name": "기침", "name_en": "cough", "probability": "30-40%", "onset": "노출 시"},
                ],
                "severity": "moderate",
            },
            "5-6": {
                "symptoms": [
                    {"name": "천식 증상", "name_en": "asthma symptoms", "probability": "40-60%", "onset": "노출 시"},
                    {"name": "심한 결막염", "name_en": "severe conjunctivitis", "probability": "50-60%", "onset": "계절 시"},
                    {"name": "부비동염", "name_en": "sinusitis", "probability": "30-40%", "onset": "만성"},
                ],
                "severity": "severe",
            },
        },

        "cross_reactivity": [
            {
                "allergen": "oral_allergy_syndrome",
                "allergen_kr": "구강 알러지 증후군",
                "probability": "40-60%",
                "common_protein": "PR-10 단백질, 프로필린",
                "related_foods": ["사과", "복숭아", "체리", "셀러리", "당근"],
            },
        ],

        "food_cautions": [
            "자작나무 꽃가루: 사과, 배, 체리, 복숭아, 살구, 자두, 키위, 당근, 셀러리, 헤이즐넛, 아몬드",
            "잔디 꽃가루: 토마토, 감자, 멜론, 오렌지",
            "돼지풀 꽃가루: 멜론, 바나나, 수박, 오이, 호박",
        ],
    },

    # -------------------------------------------------------------------------
    # 3. 곰팡이 (Mold)
    # -------------------------------------------------------------------------
    "mold": {
        "name_kr": "곰팡이",
        "name_en": "Mold",
        "category": "inhalant",
        "description": "곰팡이 알러지는 실내외 곰팡이 포자에 대한 반응으로, 습한 환경에서 악화됩니다.",

        "avoid_exposure": [
            "습기가 많은 장소",
            "오래된 건물",
            "욕실, 지하실",
            "낙엽 더미",
            "퇴비",
            "썩은 나무",
        ],

        "management_tips": [
            "실내 습도 50% 이하 유지",
            "제습기 사용",
            "욕실 환기팬 사용",
            "물기 즉시 제거",
            "곰팡이 발생 시 즉시 제거 (락스 희석액)",
            "화분 흙 표면 관리",
            "에어컨/제습기 필터 정기 청소",
            "낙엽 작업 시 마스크 착용",
        ],

        "symptoms_by_grade": {
            "1-2": {
                "symptoms": [
                    {"name": "재채기", "name_en": "sneezing", "probability": "50-60%", "onset": "노출 시"},
                    {"name": "콧물", "name_en": "runny nose", "probability": "50-60%", "onset": "노출 시"},
                ],
                "severity": "mild",
            },
            "3-4": {
                "symptoms": [
                    {"name": "비염", "name_en": "rhinitis", "probability": "60-70%", "onset": "노출 시"},
                    {"name": "눈 가려움", "name_en": "itchy eyes", "probability": "40-50%", "onset": "노출 시"},
                    {"name": "기침", "name_en": "cough", "probability": "40-50%", "onset": "노출 시"},
                    {"name": "피부 가려움", "name_en": "skin itching", "probability": "30-40%", "onset": "노출 시"},
                ],
                "severity": "moderate",
            },
            "5-6": {
                "symptoms": [
                    {"name": "천식 증상", "name_en": "asthma symptoms", "probability": "50-70%", "onset": "노출 시"},
                    {"name": "심한 비염", "name_en": "severe rhinitis", "probability": "60-70%", "onset": "지속"},
                    {"name": "알러지성 기관지폐 아스페르길루스증", "name_en": "ABPA", "probability": "5-10%", "onset": "만성"},
                ],
                "severity": "severe",
            },
        },

        "cross_reactivity": [
            {
                "allergen": "penicillin",
                "allergen_kr": "페니실린",
                "probability": "낮음",
                "common_protein": "곰팡이 유래",
                "related_foods": [],
            },
        ],

        "food_cautions": [
            "발효식품 주의 가능: 치즈, 식초, 간장, 된장, 맥주, 와인",
            "버섯류 주의 가능",
        ],
    },

    # -------------------------------------------------------------------------
    # 4. 반려동물 (Pet Dander) - 고양이
    # -------------------------------------------------------------------------
    "cat": {
        "name_kr": "고양이",
        "name_en": "Cat",
        "category": "inhalant",
        "description": "고양이 알러지는 주로 Fel d 1 단백질(피지선, 타액)에 대한 반응입니다.",

        "avoid_exposure": [
            "고양이 직접 접촉",
            "고양이가 있는 집 방문",
            "고양이 털이 묻은 옷/물건",
        ],

        "management_tips": [
            "고양이를 침실에 들이지 않기",
            "HEPA 필터 공기청정기 사용",
            "정기적인 청소 및 진공청소",
            "고양이 주 2회 목욕 (가능한 경우)",
            "카펫 제거",
            "손 자주 씻기",
            "옷에 묻은 털 제거",
        ],

        "symptoms_by_grade": {
            "1-2": {
                "symptoms": [
                    {"name": "재채기", "name_en": "sneezing", "probability": "60-70%", "onset": "노출 즉시"},
                    {"name": "콧물", "name_en": "runny nose", "probability": "50-60%", "onset": "노출 즉시"},
                ],
                "severity": "mild",
            },
            "3-4": {
                "symptoms": [
                    {"name": "심한 비염", "name_en": "severe rhinitis", "probability": "70-80%", "onset": "노출 시"},
                    {"name": "눈 가려움/충혈", "name_en": "itchy/red eyes", "probability": "60-70%", "onset": "노출 시"},
                    {"name": "피부 발진/가려움", "name_en": "skin rash/itching", "probability": "40-50%", "onset": "접촉 시"},
                    {"name": "기침", "name_en": "cough", "probability": "40-50%", "onset": "노출 시"},
                ],
                "severity": "moderate",
            },
            "5-6": {
                "symptoms": [
                    {"name": "천식 발작", "name_en": "asthma attack", "probability": "50-70%", "onset": "노출 시"},
                    {"name": "심한 호흡곤란", "name_en": "severe dyspnea", "probability": "30-40%", "onset": "노출 시"},
                ],
                "severity": "severe",
            },
        },

        "cross_reactivity": [
            {
                "allergen": "other_cats",
                "allergen_kr": "다른 고양이",
                "probability": "100%",
                "common_protein": "Fel d 1",
                "related_foods": [],
            },
            {
                "allergen": "pork",
                "allergen_kr": "돼지고기",
                "probability": "희귀",
                "common_protein": "혈청 알부민 (고양이-돼지 증후군)",
                "related_foods": ["돼지고기"],
            },
        ],

        "food_cautions": [
            "고양이-돼지 증후군: 매우 드물게 돼지고기 알러지 동반 가능",
        ],
    },

    # -------------------------------------------------------------------------
    # 5. 반려동물 (Pet Dander) - 개
    # -------------------------------------------------------------------------
    "dog": {
        "name_kr": "개",
        "name_en": "Dog",
        "category": "inhalant",
        "description": "개 알러지는 Can f 1 등의 단백질(피부, 타액, 소변)에 대한 반응입니다.",

        "avoid_exposure": [
            "개 직접 접촉",
            "개가 있는 집 방문",
            "개 털이 묻은 옷/물건",
        ],

        "management_tips": [
            "개를 침실에 들이지 않기",
            "HEPA 필터 공기청정기 사용",
            "정기적인 청소 및 진공청소",
            "개 주 1-2회 목욕",
            "카펫 제거",
            "손 자주 씻기",
        ],

        "symptoms_by_grade": {
            "1-2": {
                "symptoms": [
                    {"name": "재채기", "name_en": "sneezing", "probability": "60-70%", "onset": "노출 즉시"},
                    {"name": "콧물", "name_en": "runny nose", "probability": "50-60%", "onset": "노출 즉시"},
                ],
                "severity": "mild",
            },
            "3-4": {
                "symptoms": [
                    {"name": "심한 비염", "name_en": "severe rhinitis", "probability": "60-70%", "onset": "노출 시"},
                    {"name": "눈 가려움/충혈", "name_en": "itchy/red eyes", "probability": "50-60%", "onset": "노출 시"},
                    {"name": "피부 발진", "name_en": "skin rash", "probability": "30-40%", "onset": "접촉 시"},
                    {"name": "기침", "name_en": "cough", "probability": "30-40%", "onset": "노출 시"},
                ],
                "severity": "moderate",
            },
            "5-6": {
                "symptoms": [
                    {"name": "천식 증상", "name_en": "asthma symptoms", "probability": "40-60%", "onset": "노출 시"},
                    {"name": "심한 호흡곤란", "name_en": "severe dyspnea", "probability": "20-30%", "onset": "노출 시"},
                ],
                "severity": "severe",
            },
        },

        "cross_reactivity": [
            {
                "allergen": "other_dogs",
                "allergen_kr": "다른 개",
                "probability": "높음",
                "common_protein": "Can f 1",
                "related_foods": [],
            },
            {
                "allergen": "cat",
                "allergen_kr": "고양이",
                "probability": "10-20%",
                "common_protein": "혈청 알부민",
                "related_foods": [],
            },
        ],

        "food_cautions": [],
    },

    # -------------------------------------------------------------------------
    # 6. 바퀴벌레 (Cockroach)
    # -------------------------------------------------------------------------
    "cockroach": {
        "name_kr": "바퀴벌레",
        "name_en": "Cockroach",
        "category": "inhalant",
        "description": "바퀴벌레 알러지는 바퀴벌레 배설물, 타액, 사체에 대한 반응으로, 도시 환경에서 중요한 알러젠입니다.",

        "avoid_exposure": [
            "바퀴벌레 서식 환경",
            "음식물 방치",
            "습한 환경",
        ],

        "management_tips": [
            "음식물 밀폐 보관",
            "쓰레기통 밀봉",
            "싱크대, 욕실 물기 제거",
            "틈새 밀봉 (배관 주변 등)",
            "정기적 해충 방제",
            "식사 후 즉시 설거지",
            "반려동물 사료 밀폐 보관",
        ],

        "symptoms_by_grade": {
            "1-2": {
                "symptoms": [
                    {"name": "재채기", "name_en": "sneezing", "probability": "50-60%", "onset": "노출 시"},
                    {"name": "콧물", "name_en": "runny nose", "probability": "50-60%", "onset": "노출 시"},
                ],
                "severity": "mild",
            },
            "3-4": {
                "symptoms": [
                    {"name": "비염", "name_en": "rhinitis", "probability": "60-70%", "onset": "만성"},
                    {"name": "눈 가려움", "name_en": "itchy eyes", "probability": "40-50%", "onset": "노출 시"},
                    {"name": "기침", "name_en": "cough", "probability": "40-50%", "onset": "노출 시"},
                    {"name": "피부 발진", "name_en": "skin rash", "probability": "30-40%", "onset": "노출 시"},
                ],
                "severity": "moderate",
            },
            "5-6": {
                "symptoms": [
                    {"name": "천식 증상", "name_en": "asthma symptoms", "probability": "50-70%", "onset": "노출 시"},
                    {"name": "심한 천식 악화", "name_en": "severe asthma exacerbation", "probability": "30-40%", "onset": "만성 노출"},
                ],
                "severity": "severe",
            },
        },

        "cross_reactivity": [
            {
                "allergen": "shellfish",
                "allergen_kr": "갑각류",
                "probability": "40-60%",
                "common_protein": "트로포미오신",
                "related_foods": ["새우", "게", "랍스터"],
            },
            {
                "allergen": "dust_mite",
                "allergen_kr": "집먼지진드기",
                "probability": "70-80%",
                "common_protein": "트로포미오신",
                "related_foods": [],
            },
        ],

        "food_cautions": [
            "갑각류 (새우, 게) - 교차반응 가능성",
        ],
    },

    # -------------------------------------------------------------------------
    # 7. 반려동물 비듬 (Pet Dander) - 일반
    # -------------------------------------------------------------------------
    "pet_dander": {
        "name_kr": "반려동물 비듬",
        "name_en": "Pet Dander",
        "category": "inhalant",
        "description": "반려동물 비듬 알러지는 동물의 피부 각질, 타액, 소변에 포함된 단백질에 대한 반응입니다.",

        "avoid_exposure": [
            "반려동물 직접 접촉",
            "반려동물이 있는 집 방문",
            "동물 털이 묻은 옷/물건",
        ],

        "management_tips": [
            "반려동물을 침실에 들이지 않기",
            "HEPA 필터 공기청정기 사용",
            "정기적인 청소 및 진공청소",
            "반려동물 정기 목욕",
            "카펫 제거",
            "손 자주 씻기",
            "알러지 완화 견종/묘종 고려 (저자극성)",
        ],

        "symptoms_by_grade": {
            "1-2": {
                "symptoms": [
                    {"name": "재채기", "name_en": "sneezing", "probability": "60-70%", "onset": "노출 즉시"},
                    {"name": "콧물", "name_en": "runny nose", "probability": "50-60%", "onset": "노출 즉시"},
                ],
                "severity": "mild",
            },
            "3-4": {
                "symptoms": [
                    {"name": "심한 비염", "name_en": "severe rhinitis", "probability": "60-70%", "onset": "노출 시"},
                    {"name": "눈 가려움/충혈", "name_en": "itchy/red eyes", "probability": "50-60%", "onset": "노출 시"},
                    {"name": "피부 발진", "name_en": "skin rash", "probability": "30-40%", "onset": "접촉 시"},
                    {"name": "기침", "name_en": "cough", "probability": "30-40%", "onset": "노출 시"},
                ],
                "severity": "moderate",
            },
            "5-6": {
                "symptoms": [
                    {"name": "천식 증상", "name_en": "asthma symptoms", "probability": "40-60%", "onset": "노출 시"},
                    {"name": "심한 호흡곤란", "name_en": "severe dyspnea", "probability": "20-30%", "onset": "노출 시"},
                ],
                "severity": "severe",
            },
        },

        "cross_reactivity": [
            {
                "allergen": "multiple_animals",
                "allergen_kr": "다양한 동물",
                "probability": "다양",
                "common_protein": "혈청 알부민, 리포칼린",
                "related_foods": [],
            },
        ],

        "food_cautions": [],
    },
}


# ============================================================================
# 교차반응 종합 맵
# ============================================================================

CROSS_REACTIVITY_MAP = {
    # 땅콩 관련
    ("peanut", "tree_nuts"): {"probability": "25-40%", "protein": "저장 단백질"},
    ("peanut", "soy"): {"probability": "5-10%", "protein": "콩과 식물 단백질"},
    ("peanut", "lupin"): {"probability": "50-60%", "protein": "Conglutin"},

    # 우유 관련
    ("milk", "goat_milk"): {"probability": "90%+", "protein": "카제인"},
    ("milk", "sheep_milk"): {"probability": "90%+", "protein": "카제인"},
    ("milk", "beef"): {"probability": "10-20%", "protein": "소 혈청 알부민"},

    # 계란 관련
    ("egg", "chicken"): {"probability": "5-10%", "protein": "알파-리베틴"},
    ("egg", "other_bird_eggs"): {"probability": "50-70%", "protein": "오보알부민"},

    # 갑각류/진드기 관련
    ("shellfish", "dust_mite"): {"probability": "60-80%", "protein": "트로포미오신"},
    ("shellfish", "cockroach"): {"probability": "40-60%", "protein": "트로포미오신"},
    ("dust_mite", "cockroach"): {"probability": "70-80%", "protein": "트로포미오신"},

    # 꽃가루-식품 관련 (구강 알러지 증후군)
    ("pollen", "apple"): {"probability": "40-60%", "protein": "PR-10 (Bet v 1 상동체)"},
    ("pollen", "peach"): {"probability": "40-60%", "protein": "PR-10, LTP"},
    ("pollen", "celery"): {"probability": "30-50%", "protein": "PR-10, 프로필린"},
}


# ============================================================================
# 응급 대처 가이드라인
# ============================================================================

EMERGENCY_GUIDELINES = {
    "anaphylaxis": {
        "condition": "아나필락시스",
        "condition_en": "Anaphylaxis",
        "description": "전신 알러지 반응으로 생명을 위협할 수 있는 응급 상황",
        "symptoms": [
            "호흡곤란, 천명음",
            "입술/혀/목 부종",
            "심한 두드러기 (전신)",
            "어지러움, 의식저하",
            "혈압 급격한 저하",
            "빠른 맥박",
            "심한 복통, 구토",
        ],
        "immediate_actions": [
            "1. 에피네프린 자가주사기 (에피펜) 즉시 투여 - 허벅지 바깥쪽",
            "2. 119 응급 전화",
            "3. 환자를 눕히고 다리를 올림 (호흡곤란 시 앉은 자세)",
            "4. 숨을 쉴 수 있으면 경구 항히스타민제 복용",
            "5. 5-15분 후 증상 지속 시 에피네프린 2차 투여",
            "6. 구급대 도착까지 환자 상태 모니터링",
        ],
        "medication_info": "에피네프린 자가주사기 (에피펜, 젝스트): 0.3mg (성인), 0.15mg (소아). 허벅지 바깥쪽 근육에 수직으로 10초간 유지",
        "when_to_call_119": "아나필락시스 의심 증상 발생 즉시 119 호출. 에피네프린 투여 후에도 반드시 응급실 이송 필요 (이상반응 관찰)",
    },

    "mild_reaction": {
        "condition": "경미한 알러지 반응",
        "condition_en": "Mild Allergic Reaction",
        "description": "국소적인 알러지 증상으로 생명에 지장이 없는 상태",
        "symptoms": [
            "국소 가려움, 발진",
            "입 주변 따끔거림",
            "경미한 두드러기 (일부 부위)",
            "재채기, 콧물",
            "눈 가려움",
        ],
        "immediate_actions": [
            "1. 알러젠 노출 중단",
            "2. 경구 항히스타민제 복용 (세티리진, 로라타딘 등)",
            "3. 증상 모니터링",
            "4. 증상 악화 시 병원 방문",
        ],
        "medication_info": "항히스타민제: 세티리진(지르텍) 10mg, 로라타딘(클라리틴) 10mg. 1일 1회 복용",
        "when_to_call_119": "증상이 전신으로 퍼지거나, 호흡곤란, 어지러움 발생 시",
    },

    "moderate_reaction": {
        "condition": "중등도 알러지 반응",
        "condition_en": "Moderate Allergic Reaction",
        "description": "전신 증상이 나타나지만 생명 위협은 아직 없는 상태",
        "symptoms": [
            "전신 두드러기",
            "얼굴/입술 부종",
            "복통, 구토",
            "지속적인 기침",
        ],
        "immediate_actions": [
            "1. 알러젠 노출 중단",
            "2. 경구 항히스타민제 복용",
            "3. 에피네프린 자가주사기 준비",
            "4. 증상 악화 여부 주의 깊게 관찰",
            "5. 병원 방문 권장",
        ],
        "medication_info": "항히스타민제 복용 + 에피네프린 자가주사기 대기. 증상 악화 시 즉시 에피네프린 투여",
        "when_to_call_119": "호흡곤란, 의식저하, 증상 급격한 악화 시",
    },
}


# ============================================================================
# 유틸리티 함수
# ============================================================================

def get_allergen_info(allergen_code: str) -> Optional[dict]:
    """
    알러젠 코드로 처방 정보 조회

    Args:
        allergen_code: 알러젠 코드 (예: "peanut", "dust_mite")

    Returns:
        알러젠 정보 딕셔너리 또는 None
    """
    if allergen_code in FOOD_ALLERGENS:
        return FOOD_ALLERGENS[allergen_code]
    elif allergen_code in INHALANT_ALLERGENS:
        return INHALANT_ALLERGENS[allergen_code]
    return None


def get_cross_reactivities(allergen_code: str) -> list[dict]:
    """
    특정 알러젠의 교차반응 정보 조회

    Args:
        allergen_code: 알러젠 코드

    Returns:
        교차반응 정보 리스트
    """
    allergen_info = get_allergen_info(allergen_code)
    if allergen_info and "cross_reactivity" in allergen_info:
        return allergen_info["cross_reactivity"]
    return []


def get_all_allergens() -> dict:
    """
    모든 알러젠 정보 조회

    Returns:
        {"food": {...}, "inhalant": {...}} 형태의 딕셔너리
    """
    return {
        "food": FOOD_ALLERGENS,
        "inhalant": INHALANT_ALLERGENS,
    }


def get_allergen_list() -> list[dict]:
    """
    알러젠 목록 조회 (UI용)

    Returns:
        [{"code": "peanut", "name_kr": "땅콩", "category": "food"}, ...]
    """
    result = []

    for code, info in FOOD_ALLERGENS.items():
        result.append({
            "code": code,
            "name_kr": info["name_kr"],
            "name_en": info["name_en"],
            "category": "food",
        })

    for code, info in INHALANT_ALLERGENS.items():
        result.append({
            "code": code,
            "name_kr": info["name_kr"],
            "name_en": info["name_en"],
            "category": "inhalant",
        })

    return result


# 전체 알러젠 데이터베이스
ALLERGEN_PRESCRIPTION_DB = {
    **FOOD_ALLERGENS,
    **INHALANT_ALLERGENS,
}
