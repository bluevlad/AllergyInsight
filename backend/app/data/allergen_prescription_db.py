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
    # 9. 게 (Crab) - 갑각류 세분화
    # -------------------------------------------------------------------------
    "crab": {
        "name_kr": "게",
        "name_en": "Crab",
        "category": "food",
        "description": "게 알러지는 갑각류 알러지의 일종으로, 트로포미오신 단백질에 대한 반응입니다. 새우 알러지와 높은 교차반응을 보입니다.",

        "avoid_foods": [
            "모든 종류의 게 (킹크랩, 대게, 꽃게, 털게 등)",
            "게살",
            "게장",
            "게맛살 (이미테이션 크랩)",
            "게 통조림",
        ],

        "hidden_sources": [
            "해물 수프/찌개/탕",
            "해물 볶음밥",
            "크랩 케이크",
            "캘리포니아 롤 (게맛살)",
            "해산물 소스",
            "XO 소스",
            "굴소스 일부",
        ],

        "substitutes": [
            {
                "original": "게살",
                "alternatives": ["버섯", "두부", "콩고기"],
                "notes": "대두 알러지 확인"
            },
            {
                "original": "게맛살",
                "alternatives": ["어묵 (생선 알러지 없는 경우)", "두부"],
                "notes": "게맛살은 주로 생선으로 만들지만 일부 제품은 게 추출물 함유"
            },
        ],

        "restaurant_cautions": [
            "해산물 전문점",
            "일식당 (초밥, 게요리)",
            "중식당 (게살 볶음, 해물요리)",
            "한식당 (게장, 해물탕)",
            "뷔페 (해산물 코너)",
        ],

        "label_keywords_kr": [
            "게",
            "크랩",
            "게살",
            "게맛살",
            "갑각류",
        ],

        "label_keywords_en": [
            "crab",
            "crabmeat",
            "imitation crab",
            "surimi",
            "crustacean",
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
                "allergen": "shrimp",
                "allergen_kr": "새우",
                "probability": "75-85%",
                "common_protein": "트로포미오신",
                "related_foods": ["새우"],
            },
            {
                "allergen": "lobster",
                "allergen_kr": "랍스터",
                "probability": "70-80%",
                "common_protein": "트로포미오신",
                "related_foods": ["랍스터", "바닷가재"],
            },
            {
                "allergen": "dust_mite",
                "allergen_kr": "집먼지진드기",
                "probability": "60-80%",
                "common_protein": "트로포미오신",
                "related_foods": [],
            },
        ],
    },

    # -------------------------------------------------------------------------
    # 10. 참치 (Tuna)
    # -------------------------------------------------------------------------
    "tuna": {
        "name_kr": "참치",
        "name_en": "Tuna",
        "category": "food",
        "description": "참치 알러지는 파르브알부민 단백질에 대한 반응으로, 다른 생선과 교차반응할 수 있습니다.",

        "avoid_foods": [
            "참치 (생, 캔, 냉동)",
            "참치회",
            "참치 초밥",
            "참치 샐러드",
            "참치 샌드위치",
            "참치 통조림",
            "참치 스테이크",
        ],

        "hidden_sources": [
            "피자 토핑",
            "샐러드 토핑",
            "김밥",
            "카레 (참치 카레)",
            "일부 소스류",
            "오메가-3 보충제 (어유)",
        ],

        "substitutes": [
            {
                "original": "참치 캔",
                "alternatives": ["닭가슴살 캔", "병아리콩", "연두부"],
                "notes": ""
            },
            {
                "original": "참치회",
                "alternatives": ["육회 (소고기 알러지 없는 경우)", "채소 샐러드"],
                "notes": ""
            },
        ],

        "restaurant_cautions": [
            "일식당 (초밥, 회)",
            "샌드위치/샐러드 전문점",
            "한식당 (참치김밥, 참치찌개)",
            "양식당 (참치 스테이크)",
        ],

        "label_keywords_kr": [
            "참치",
            "참다랑어",
            "다랑어",
            "튜나",
        ],

        "label_keywords_en": [
            "tuna",
            "tunny",
            "ahi",
            "albacore",
            "bluefin",
            "yellowfin",
            "skipjack",
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
                "allergen_kr": "다른 생선",
                "probability": "50-70%",
                "common_protein": "파르브알부민",
                "related_foods": ["연어", "고등어", "대구"],
            },
        ],
    },

    # -------------------------------------------------------------------------
    # 11. 연어 (Salmon)
    # -------------------------------------------------------------------------
    "salmon": {
        "name_kr": "연어",
        "name_en": "Salmon",
        "category": "food",
        "description": "연어 알러지는 생선 알러지의 일종으로, 연어 특이 단백질에 반응합니다. 일부 환자는 연어에만 반응할 수 있습니다.",

        "avoid_foods": [
            "연어 (생, 훈제, 구이, 캔)",
            "연어회/사시미",
            "연어 초밥",
            "훈제 연어 (스모크 살몬)",
            "연어알 (이쿠라)",
            "연어 통조림",
        ],

        "hidden_sources": [
            "초밥류",
            "샐러드 토핑",
            "베이글 토핑 (훈제연어)",
            "오메가-3 보충제",
            "일부 펫푸드",
        ],

        "substitutes": [
            {
                "original": "연어",
                "alternatives": ["닭고기", "두부", "포토벨로 버섯"],
                "notes": ""
            },
            {
                "original": "오메가-3 (연어유)",
                "alternatives": ["아마씨유", "치아씨드", "해조류 기반 오메가-3"],
                "notes": ""
            },
        ],

        "restaurant_cautions": [
            "일식당",
            "브런치 전문점 (훈제연어 베이글)",
            "해산물 전문점",
            "스시 롤 전문점",
        ],

        "label_keywords_kr": [
            "연어",
            "사몬",
            "훈제연어",
            "이쿠라",
        ],

        "label_keywords_en": [
            "salmon",
            "smoked salmon",
            "lox",
            "nova",
            "ikura",
            "salmon roe",
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
                    {"name": "복통", "name_en": "abdominal pain", "probability": "30-40%", "onset": "1~3시간"},
                    {"name": "구토", "name_en": "vomiting", "probability": "30-40%", "onset": "1~3시간"},
                ],
                "severity": "moderate",
            },
            "5-6": {
                "symptoms": [
                    {"name": "심한 전신 두드러기", "name_en": "severe generalized urticaria", "probability": "70-80%", "onset": "수분~1시간"},
                    {"name": "호흡곤란", "name_en": "dyspnea", "probability": "25-35%", "onset": "수분~30분"},
                    {"name": "아나필락시스", "name_en": "anaphylaxis", "probability": "10-15%", "onset": "수분~30분"},
                ],
                "severity": "severe",
            },
        },

        "cross_reactivity": [
            {
                "allergen": "other_fish",
                "allergen_kr": "다른 생선",
                "probability": "50-70%",
                "common_protein": "파르브알부민",
                "related_foods": ["참치", "고등어", "송어"],
            },
        ],
    },

    # -------------------------------------------------------------------------
    # 12. 사과 (Apple) - 구강알러지증후군
    # -------------------------------------------------------------------------
    "apple": {
        "name_kr": "사과",
        "name_en": "Apple",
        "category": "food",
        "description": "사과 알러지는 주로 자작나무 꽃가루 알러지와 연관된 구강알러지증후군(OAS)으로 나타납니다. Mal d 1 단백질이 원인입니다.",

        "avoid_foods": [
            "생 사과",
            "사과 주스 (비가열)",
            "사과 슬라이스",
            "사과 샐러드",
        ],

        "hidden_sources": [
            "과일 샐러드",
            "스무디",
            "베이비푸드",
            "일부 주스 믹스",
            "사이다/애플 사이더",
        ],

        "substitutes": [
            {
                "original": "생 사과",
                "alternatives": ["익힌 사과 (애플파이, 조림)", "배", "포도"],
                "notes": "가열하면 Mal d 1 단백질이 파괴되어 안전할 수 있음"
            },
            {
                "original": "사과 주스",
                "alternatives": ["포도 주스", "오렌지 주스 (감귤 알러지 없는 경우)"],
                "notes": ""
            },
        ],

        "restaurant_cautions": [
            "샐러드 바",
            "스무디/주스 전문점",
            "디저트 카페",
        ],

        "label_keywords_kr": [
            "사과",
            "애플",
        ],

        "label_keywords_en": [
            "apple",
            "apple juice",
            "apple cider",
        ],

        "symptoms_by_grade": {
            "1-2": {
                "symptoms": [
                    {"name": "입/입술 가려움", "name_en": "oral/lip itching", "probability": "80-90%", "onset": "수분 이내"},
                    {"name": "입안 따끔거림", "name_en": "oral tingling", "probability": "70-80%", "onset": "수분 이내"},
                ],
                "severity": "mild",
            },
            "3-4": {
                "symptoms": [
                    {"name": "입술/혀 부종", "name_en": "lip/tongue swelling", "probability": "40-50%", "onset": "수분~30분"},
                    {"name": "목 가려움", "name_en": "throat itching", "probability": "30-40%", "onset": "수분~30분"},
                    {"name": "두드러기", "name_en": "urticaria", "probability": "20-30%", "onset": "30분~2시간"},
                ],
                "severity": "moderate",
            },
            "5-6": {
                "symptoms": [
                    {"name": "심한 혈관부종", "name_en": "severe angioedema", "probability": "30-40%", "onset": "수분~30분"},
                    {"name": "호흡곤란", "name_en": "dyspnea", "probability": "10-20%", "onset": "수분~30분"},
                    {"name": "아나필락시스", "name_en": "anaphylaxis", "probability": "드물음", "onset": "수분~30분"},
                ],
                "severity": "severe",
            },
        },

        "cross_reactivity": [
            {
                "allergen": "birch_pollen",
                "allergen_kr": "자작나무 꽃가루",
                "probability": "50-70%",
                "common_protein": "Bet v 1 (PR-10)",
                "related_foods": [],
            },
            {
                "allergen": "related_fruits",
                "allergen_kr": "관련 과일",
                "probability": "40-60%",
                "common_protein": "PR-10 단백질",
                "related_foods": ["배", "복숭아", "체리", "자두", "살구"],
            },
            {
                "allergen": "hazelnut",
                "allergen_kr": "헤이즐넛",
                "probability": "30-50%",
                "common_protein": "PR-10 단백질",
                "related_foods": ["헤이즐넛"],
            },
        ],

        "special_notes": "가열 조리 시 PR-10 단백질이 파괴되어 대부분 안전하게 섭취 가능. 단, LTP 알러지인 경우 가열 후에도 반응 가능.",
    },

    # -------------------------------------------------------------------------
    # 13. 복숭아 (Peach) - LTP 증후군
    # -------------------------------------------------------------------------
    "peach": {
        "name_kr": "복숭아",
        "name_en": "Peach",
        "category": "food",
        "description": "복숭아 알러지는 LTP(지질전이단백질) 또는 PR-10 단백질에 의해 발생합니다. LTP 알러지는 가열 후에도 반응하며 아나필락시스 위험이 있습니다.",

        "avoid_foods": [
            "복숭아 (생, 통조림)",
            "복숭아 주스",
            "복숭아 잼",
            "말린 복숭아",
            "복숭아 아이스티",
        ],

        "hidden_sources": [
            "과일 샐러드",
            "스무디",
            "요거트",
            "베이비푸드",
            "화장품 (복숭아 추출물)",
            "아이스크림",
            "케이크/파이",
        ],

        "substitutes": [
            {
                "original": "복숭아",
                "alternatives": ["망고 (교차반응 확인)", "포도", "멜론"],
                "notes": "LTP 알러지인 경우 장미과 과일 전체 주의"
            },
        ],

        "restaurant_cautions": [
            "디저트 카페",
            "아이스크림 가게",
            "스무디/주스 전문점",
            "한식당 (과일 후식)",
        ],

        "label_keywords_kr": [
            "복숭아",
            "피치",
            "황도",
            "백도",
        ],

        "label_keywords_en": [
            "peach",
            "nectarine",
            "peach extract",
        ],

        "symptoms_by_grade": {
            "1-2": {
                "symptoms": [
                    {"name": "입/입술 가려움", "name_en": "oral/lip itching", "probability": "70-80%", "onset": "수분 이내"},
                    {"name": "입안 따끔거림", "name_en": "oral tingling", "probability": "60-70%", "onset": "수분 이내"},
                ],
                "severity": "mild",
            },
            "3-4": {
                "symptoms": [
                    {"name": "입술/혀 부종", "name_en": "lip/tongue swelling", "probability": "40-50%", "onset": "수분~30분"},
                    {"name": "두드러기", "name_en": "urticaria", "probability": "40-50%", "onset": "30분~2시간"},
                    {"name": "복통", "name_en": "abdominal pain", "probability": "30-40%", "onset": "1~3시간"},
                ],
                "severity": "moderate",
            },
            "5-6": {
                "symptoms": [
                    {"name": "전신 두드러기", "name_en": "generalized urticaria", "probability": "60-70%", "onset": "수분~1시간"},
                    {"name": "호흡곤란", "name_en": "dyspnea", "probability": "30-40%", "onset": "수분~30분"},
                    {"name": "아나필락시스", "name_en": "anaphylaxis", "probability": "15-25%", "onset": "수분~30분"},
                ],
                "severity": "severe",
            },
        },

        "cross_reactivity": [
            {
                "allergen": "rosaceae_fruits",
                "allergen_kr": "장미과 과일",
                "probability": "50-70%",
                "common_protein": "LTP (Pru p 3)",
                "related_foods": ["사과", "배", "체리", "자두", "살구", "아몬드"],
            },
            {
                "allergen": "nuts",
                "allergen_kr": "견과류",
                "probability": "30-50%",
                "common_protein": "LTP",
                "related_foods": ["호두", "헤이즐넛"],
            },
            {
                "allergen": "mugwort_pollen",
                "allergen_kr": "쑥 꽃가루",
                "probability": "40-60%",
                "common_protein": "LTP",
                "related_foods": [],
            },
        ],

        "special_notes": "LTP 알러지는 가열 후에도 반응하며, 과일 껍질에 LTP 농도가 높습니다. 심한 전신 반응 및 아나필락시스 위험이 있어 에피펜 휴대 권장.",
    },

    # -------------------------------------------------------------------------
    # 14. 키위 (Kiwi) - 라텍스-과일 증후군
    # -------------------------------------------------------------------------
    "kiwi": {
        "name_kr": "키위",
        "name_en": "Kiwi",
        "category": "food",
        "description": "키위 알러지는 라텍스 알러지와 높은 교차반응을 보이며(라텍스-과일 증후군), Act d 1 등의 단백질에 반응합니다.",

        "avoid_foods": [
            "키위 (그린, 골드)",
            "키위 주스",
            "키위 스무디",
            "키위 요거트",
            "말린 키위",
        ],

        "hidden_sources": [
            "과일 샐러드",
            "스무디",
            "요거트",
            "아이스크림",
            "과일 타르트",
            "일부 화장품",
        ],

        "substitutes": [
            {
                "original": "키위",
                "alternatives": ["딸기", "블루베리", "포도"],
                "notes": "라텍스 알러지 동반 시 바나나, 아보카도도 주의"
            },
        ],

        "restaurant_cautions": [
            "스무디/주스 전문점",
            "디저트 카페",
            "아이스크림 가게",
            "뷔페 (과일 코너)",
        ],

        "label_keywords_kr": [
            "키위",
            "참다래",
            "양다래",
        ],

        "label_keywords_en": [
            "kiwi",
            "kiwifruit",
            "chinese gooseberry",
        ],

        "symptoms_by_grade": {
            "1-2": {
                "symptoms": [
                    {"name": "입/입술 가려움", "name_en": "oral/lip itching", "probability": "70-80%", "onset": "수분 이내"},
                    {"name": "입안 따끔거림", "name_en": "oral tingling", "probability": "60-70%", "onset": "수분 이내"},
                ],
                "severity": "mild",
            },
            "3-4": {
                "symptoms": [
                    {"name": "입술/혀 부종", "name_en": "lip/tongue swelling", "probability": "40-50%", "onset": "수분~30분"},
                    {"name": "두드러기", "name_en": "urticaria", "probability": "40-50%", "onset": "30분~2시간"},
                    {"name": "구토", "name_en": "vomiting", "probability": "30-40%", "onset": "1~3시간"},
                ],
                "severity": "moderate",
            },
            "5-6": {
                "symptoms": [
                    {"name": "전신 두드러기", "name_en": "generalized urticaria", "probability": "60-70%", "onset": "수분~1시간"},
                    {"name": "호흡곤란", "name_en": "dyspnea", "probability": "30-40%", "onset": "수분~30분"},
                    {"name": "아나필락시스", "name_en": "anaphylaxis", "probability": "10-20%", "onset": "수분~30분"},
                ],
                "severity": "severe",
            },
        },

        "cross_reactivity": [
            {
                "allergen": "latex",
                "allergen_kr": "라텍스",
                "probability": "40-60%",
                "common_protein": "키티나제, 클래스 I 키티나제",
                "related_foods": [],
            },
            {
                "allergen": "banana",
                "allergen_kr": "바나나",
                "probability": "40-50%",
                "common_protein": "키티나제",
                "related_foods": ["바나나"],
            },
            {
                "allergen": "avocado",
                "allergen_kr": "아보카도",
                "probability": "30-40%",
                "common_protein": "키티나제",
                "related_foods": ["아보카도"],
            },
            {
                "allergen": "birch_pollen",
                "allergen_kr": "자작나무 꽃가루",
                "probability": "20-40%",
                "common_protein": "PR-10",
                "related_foods": [],
            },
        ],

        "special_notes": "라텍스 알러지가 있는 환자는 키위 섭취 전 의사와 상담 필요. 라텍스-과일 증후군에서 키위는 가장 흔한 원인 과일 중 하나.",
    },

    # -------------------------------------------------------------------------
    # 15. 메밀 (Buckwheat) - 한국에서 중요한 아나필락시스 원인
    # -------------------------------------------------------------------------
    "buckwheat": {
        "name_kr": "메밀",
        "name_en": "Buckwheat",
        "category": "food",
        "description": "메밀 알러지는 심각한 아나필락시스를 유발할 수 있으며, 한국과 일본에서 특히 중요한 식품 알러젠입니다.",

        "avoid_foods": [
            "메밀국수 (냉면, 소바)",
            "메밀가루",
            "메밀묵",
            "메밀전병",
            "메밀베개 (메밀 껍질)",
        ],

        "hidden_sources": [
            "냉면 (메밀 함유)",
            "일부 전 종류",
            "혼합 곡물 제품",
            "글루텐프리 제품 (메밀 함유 가능)",
            "일부 시리얼",
            "메밀 베개/쿠션",
            "유기농 제품 일부",
        ],

        "substitutes": [
            {
                "original": "메밀국수",
                "alternatives": ["쌀국수", "우동", "밀면"],
                "notes": "밀 알러지 있으면 쌀국수 선택"
            },
            {
                "original": "메밀가루",
                "alternatives": ["쌀가루", "옥수수 전분", "감자 전분"],
                "notes": ""
            },
        ],

        "restaurant_cautions": [
            "냉면 전문점",
            "일식당 (소바)",
            "전 전문점",
            "한식당 (메밀전병, 막국수)",
            "비빔밥 전문점 (메밀면 동반)",
        ],

        "label_keywords_kr": [
            "메밀",
            "모밀",
            "교맥",
        ],

        "label_keywords_en": [
            "buckwheat",
            "soba",
            "kasha",
            "fagopyrum",
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
                    {"name": "혈관부종", "name_en": "angioedema", "probability": "40-50%", "onset": "30분~2시간"},
                    {"name": "구토", "name_en": "vomiting", "probability": "40-50%", "onset": "1~3시간"},
                    {"name": "호흡곤란", "name_en": "dyspnea", "probability": "30-40%", "onset": "수분~30분"},
                ],
                "severity": "moderate",
            },
            "5-6": {
                "symptoms": [
                    {"name": "심한 전신 두드러기", "name_en": "severe generalized urticaria", "probability": "70-80%", "onset": "수분~1시간"},
                    {"name": "심한 호흡곤란", "name_en": "severe dyspnea", "probability": "40-60%", "onset": "수분~30분"},
                    {"name": "아나필락시스", "name_en": "anaphylaxis", "probability": "30-50%", "onset": "수분~30분"},
                ],
                "severity": "severe",
            },
        },

        "cross_reactivity": [
            {
                "allergen": "rice",
                "allergen_kr": "쌀",
                "probability": "낮음",
                "common_protein": "",
                "related_foods": ["쌀"],
            },
        ],

        "special_notes": "메밀은 밀과 다른 식물이며, 밀 알러지와는 관련이 없습니다. 그러나 메밀 알러지는 아나필락시스 위험이 높아 에피펜 휴대 필수. 메밀 베개 사용 시에도 흡입으로 반응 가능.",
    },

    # -------------------------------------------------------------------------
    # 16. 닭고기 (Chicken)
    # -------------------------------------------------------------------------
    "chicken": {
        "name_kr": "닭고기",
        "name_en": "Chicken",
        "category": "food",
        "description": "닭고기 알러지는 드물지만, 계란 알러지와 연관될 수 있습니다 (Bird-Egg Syndrome).",

        "avoid_foods": [
            "닭고기 (모든 조리 형태)",
            "치킨",
            "닭가슴살",
            "닭 육수/치킨 스톡",
            "닭고기 소시지",
        ],

        "hidden_sources": [
            "수프/육수 (치킨 스톡)",
            "라면 스프",
            "즉석식품",
            "일부 소시지",
            "만두 속",
            "닭고기 향신료",
        ],

        "substitutes": [
            {
                "original": "닭고기",
                "alternatives": ["돼지고기", "소고기", "두부", "생선"],
                "notes": "각 대체 식품 알러지 여부 확인"
            },
            {
                "original": "닭 육수",
                "alternatives": ["채소 육수", "소고기 육수", "버섯 육수"],
                "notes": ""
            },
        ],

        "restaurant_cautions": [
            "치킨 전문점",
            "한식당 (삼계탕, 닭볶음탕)",
            "패스트푸드",
            "중식당 (깐풍기)",
            "일식당 (야키토리)",
        ],

        "label_keywords_kr": [
            "닭고기",
            "치킨",
            "닭",
            "계육",
        ],

        "label_keywords_en": [
            "chicken",
            "poultry",
            "chicken broth",
            "chicken stock",
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
                    {"name": "구토", "name_en": "vomiting", "probability": "30-40%", "onset": "1~3시간"},
                ],
                "severity": "moderate",
            },
            "5-6": {
                "symptoms": [
                    {"name": "전신 두드러기", "name_en": "generalized urticaria", "probability": "60-70%", "onset": "수분~1시간"},
                    {"name": "호흡곤란", "name_en": "dyspnea", "probability": "20-30%", "onset": "수분~30분"},
                    {"name": "아나필락시스", "name_en": "anaphylaxis", "probability": "드물음", "onset": "수분~30분"},
                ],
                "severity": "severe",
            },
        },

        "cross_reactivity": [
            {
                "allergen": "egg",
                "allergen_kr": "계란",
                "probability": "5-10%",
                "common_protein": "알파-리베틴",
                "related_foods": ["계란"],
            },
            {
                "allergen": "turkey",
                "allergen_kr": "칠면조",
                "probability": "50-70%",
                "common_protein": "유사 근육 단백질",
                "related_foods": ["칠면조 고기"],
            },
            {
                "allergen": "other_poultry",
                "allergen_kr": "다른 가금류",
                "probability": "30-50%",
                "common_protein": "유사 단백질",
                "related_foods": ["오리고기", "거위고기"],
            },
        ],
    },

    # -------------------------------------------------------------------------
    # 17. 돼지고기 (Pork) - 알파갈 증후군
    # -------------------------------------------------------------------------
    "pork": {
        "name_kr": "돼지고기",
        "name_en": "Pork",
        "category": "food",
        "description": "돼지고기 알러지는 진드기 물림과 연관된 알파갈 증후군이나 고양이 알러지와 연관된 고양이-돼지 증후군으로 발생할 수 있습니다.",

        "avoid_foods": [
            "돼지고기 (모든 부위)",
            "삼겹살",
            "베이컨",
            "햄",
            "소시지",
            "돼지 내장 (곱창, 막창)",
            "라드 (돼지기름)",
        ],

        "hidden_sources": [
            "가공육 제품",
            "소시지, 핫도그",
            "베이컨 조각 (샐러드, 피자 토핑)",
            "일부 육수",
            "젤라틴 (돼지 유래)",
            "일부 의약품 캡슐",
            "붓/브러시 (돼지털)",
        ],

        "substitutes": [
            {
                "original": "돼지고기",
                "alternatives": ["소고기", "닭고기", "칠면조", "두부"],
                "notes": "알파갈 증후군인 경우 소고기도 주의"
            },
            {
                "original": "베이컨",
                "alternatives": ["터키 베이컨", "채식 베이컨"],
                "notes": ""
            },
            {
                "original": "젤라틴",
                "alternatives": ["한천(아가)", "펙틴"],
                "notes": ""
            },
        ],

        "restaurant_cautions": [
            "한식당 (삼겹살, 돼지국밥)",
            "일식당 (돈카츠, 규동)",
            "중식당 (탕수육, 돼지고기 요리)",
            "패스트푸드 (베이컨 버거)",
            "뷔페",
        ],

        "label_keywords_kr": [
            "돼지고기",
            "돈육",
            "삼겹살",
            "베이컨",
            "햄",
            "라드",
        ],

        "label_keywords_en": [
            "pork",
            "bacon",
            "ham",
            "lard",
            "porcine",
            "swine",
            "pig",
        ],

        "symptoms_by_grade": {
            "1-2": {
                "symptoms": [
                    {"name": "피부 가려움", "name_en": "skin itching", "probability": "50-60%", "onset": "2~6시간 (알파갈)"},
                    {"name": "두드러기", "name_en": "urticaria", "probability": "40-50%", "onset": "2~6시간"},
                ],
                "severity": "mild",
            },
            "3-4": {
                "symptoms": [
                    {"name": "전신 두드러기", "name_en": "generalized urticaria", "probability": "60-70%", "onset": "2~6시간"},
                    {"name": "복통", "name_en": "abdominal pain", "probability": "50-60%", "onset": "3~6시간"},
                    {"name": "구토", "name_en": "vomiting", "probability": "40-50%", "onset": "3~6시간"},
                ],
                "severity": "moderate",
            },
            "5-6": {
                "symptoms": [
                    {"name": "심한 전신 두드러기", "name_en": "severe generalized urticaria", "probability": "70-80%", "onset": "2~6시간"},
                    {"name": "호흡곤란", "name_en": "dyspnea", "probability": "30-40%", "onset": "2~6시간"},
                    {"name": "아나필락시스", "name_en": "anaphylaxis", "probability": "20-30%", "onset": "2~6시간"},
                ],
                "severity": "severe",
            },
        },

        "cross_reactivity": [
            {
                "allergen": "cat",
                "allergen_kr": "고양이",
                "probability": "20-40%",
                "common_protein": "혈청 알부민 (고양이-돼지 증후군)",
                "related_foods": [],
            },
            {
                "allergen": "beef",
                "allergen_kr": "소고기",
                "probability": "높음 (알파갈)",
                "common_protein": "알파갈",
                "related_foods": ["소고기", "양고기"],
            },
            {
                "allergen": "lamb",
                "allergen_kr": "양고기",
                "probability": "높음 (알파갈)",
                "common_protein": "알파갈",
                "related_foods": ["양고기"],
            },
        ],

        "special_notes": "알파갈 증후군은 진드기 물림 후 발생하며, 증상이 섭취 후 3-6시간 지연되어 나타나는 특징이 있습니다. 고양이 알러지가 있는 경우 돼지고기에도 반응할 수 있습니다.",
    },

    # -------------------------------------------------------------------------
    # 18. 소고기 (Beef)
    # -------------------------------------------------------------------------
    "beef": {
        "name_kr": "소고기",
        "name_en": "Beef",
        "category": "food",
        "description": "소고기 알러지는 우유 알러지와 연관될 수 있으며(소 혈청 알부민), 알파갈 증후군의 주요 유발 식품입니다.",

        "avoid_foods": [
            "소고기 (모든 부위)",
            "소 내장 (곱창, 천엽 등)",
            "소 육수",
            "소고기 젤라틴",
        ],

        "hidden_sources": [
            "육수 (소고기 베이스)",
            "라면 스프",
            "즉석식품",
            "그레이비 소스",
            "미트볼 (소고기 함유)",
            "일부 젤라틴 제품",
        ],

        "substitutes": [
            {
                "original": "소고기",
                "alternatives": ["닭고기", "칠면조", "생선", "두부"],
                "notes": "알파갈 증후군인 경우 돼지고기, 양고기도 주의"
            },
            {
                "original": "소 육수",
                "alternatives": ["채소 육수", "닭 육수", "버섯 육수"],
                "notes": ""
            },
        ],

        "restaurant_cautions": [
            "스테이크 전문점",
            "한식당 (불고기, 갈비, 설렁탕)",
            "일식당 (규동, 샤브샤브)",
            "버거 전문점",
            "이탈리안 (미트소스)",
        ],

        "label_keywords_kr": [
            "소고기",
            "우육",
            "쇠고기",
            "한우",
        ],

        "label_keywords_en": [
            "beef",
            "bovine",
            "veal",
            "beef broth",
            "beef stock",
        ],

        "symptoms_by_grade": {
            "1-2": {
                "symptoms": [
                    {"name": "피부 가려움", "name_en": "skin itching", "probability": "50-60%", "onset": "2~6시간 (알파갈)"},
                    {"name": "두드러기", "name_en": "urticaria", "probability": "40-50%", "onset": "2~6시간"},
                ],
                "severity": "mild",
            },
            "3-4": {
                "symptoms": [
                    {"name": "전신 두드러기", "name_en": "generalized urticaria", "probability": "60-70%", "onset": "2~6시간"},
                    {"name": "복통", "name_en": "abdominal pain", "probability": "50-60%", "onset": "3~6시간"},
                    {"name": "구토", "name_en": "vomiting", "probability": "40-50%", "onset": "3~6시간"},
                ],
                "severity": "moderate",
            },
            "5-6": {
                "symptoms": [
                    {"name": "심한 전신 두드러기", "name_en": "severe generalized urticaria", "probability": "70-80%", "onset": "2~6시간"},
                    {"name": "호흡곤란", "name_en": "dyspnea", "probability": "30-40%", "onset": "2~6시간"},
                    {"name": "아나필락시스", "name_en": "anaphylaxis", "probability": "20-30%", "onset": "2~6시간"},
                ],
                "severity": "severe",
            },
        },

        "cross_reactivity": [
            {
                "allergen": "milk",
                "allergen_kr": "우유",
                "probability": "10-20%",
                "common_protein": "소 혈청 알부민 (BSA)",
                "related_foods": ["우유", "유제품"],
            },
            {
                "allergen": "pork",
                "allergen_kr": "돼지고기",
                "probability": "높음 (알파갈)",
                "common_protein": "알파갈",
                "related_foods": ["돼지고기"],
            },
            {
                "allergen": "lamb",
                "allergen_kr": "양고기",
                "probability": "높음 (알파갈)",
                "common_protein": "알파갈",
                "related_foods": ["양고기"],
            },
        ],

        "special_notes": "알파갈 증후군은 진드기 물림 후 발생하는 적색육 알러지로, 소고기, 돼지고기, 양고기에 모두 반응합니다. 우유 알러지와 소고기 알러지는 소 혈청 알부민을 통해 연관될 수 있습니다.",
    },

    # -------------------------------------------------------------------------
    # 19. 호두 (Walnut)
    # -------------------------------------------------------------------------
    "walnut": {
        "name_kr": "호두",
        "name_en": "Walnut",
        "category": "food",
        "description": "호두 알러지는 견과류 알러지 중 가장 흔한 유형 중 하나로, 심각한 알러지 반응을 유발할 수 있습니다.",

        "avoid_foods": [
            "호두",
            "호두 오일",
            "호두 버터",
            "호두 과자/빵",
        ],

        "hidden_sources": [
            "베이커리 제품 (쿠키, 브라우니, 케이크)",
            "시리얼/그래놀라",
            "에너지바",
            "아이스크림",
            "초콜릿",
            "샐러드 토핑",
            "페스토 (일부)",
            "중국/한국 요리 (호두 요리)",
        ],

        "substitutes": [
            {
                "original": "호두",
                "alternatives": ["해바라기씨", "호박씨", "볶은 병아리콩"],
                "notes": "다른 견과류 교차반응 확인 필요"
            },
            {
                "original": "호두 오일",
                "alternatives": ["올리브유", "해바라기유", "포도씨유"],
                "notes": ""
            },
        ],

        "restaurant_cautions": [
            "베이커리/카페",
            "아이스크림 가게",
            "중식당 (호두 새우, 호두 요리)",
            "한식당 (호두 강정)",
            "디저트 전문점",
        ],

        "label_keywords_kr": [
            "호두",
            "월넛",
        ],

        "label_keywords_en": [
            "walnut",
            "walnuts",
            "walnut oil",
            "juglans",
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
                    {"name": "혈관부종", "name_en": "angioedema", "probability": "40-50%", "onset": "30분~2시간"},
                    {"name": "복통", "name_en": "abdominal pain", "probability": "30-40%", "onset": "1~3시간"},
                    {"name": "구토", "name_en": "vomiting", "probability": "25-35%", "onset": "1~3시간"},
                ],
                "severity": "moderate",
            },
            "5-6": {
                "symptoms": [
                    {"name": "심한 전신 두드러기", "name_en": "severe generalized urticaria", "probability": "70-80%", "onset": "수분~1시간"},
                    {"name": "호흡곤란", "name_en": "dyspnea", "probability": "35-45%", "onset": "수분~30분"},
                    {"name": "아나필락시스", "name_en": "anaphylaxis", "probability": "20-30%", "onset": "수분~30분"},
                ],
                "severity": "severe",
            },
        },

        "cross_reactivity": [
            {
                "allergen": "pecan",
                "allergen_kr": "피칸",
                "probability": "90%+",
                "common_protein": "저장 단백질 (2S 알부민)",
                "related_foods": ["피칸"],
            },
            {
                "allergen": "other_tree_nuts",
                "allergen_kr": "다른 견과류",
                "probability": "30-50%",
                "common_protein": "저장 단백질",
                "related_foods": ["캐슈넛", "피스타치오", "헤이즐넛", "아몬드"],
            },
            {
                "allergen": "peanut",
                "allergen_kr": "땅콩",
                "probability": "25-40%",
                "common_protein": "저장 단백질",
                "related_foods": ["땅콩"],
            },
        ],
    },

    # -------------------------------------------------------------------------
    # 20. 헤이즐넛 (Hazelnut) - 자작나무 꽃가루 교차반응
    # -------------------------------------------------------------------------
    "hazelnut": {
        "name_kr": "헤이즐넛",
        "name_en": "Hazelnut",
        "category": "food",
        "description": "헤이즐넛 알러지는 자작나무 꽃가루와 높은 교차반응을 보이며, 초콜릿 제품에 흔히 포함되어 있어 주의가 필요합니다.",

        "avoid_foods": [
            "헤이즐넛",
            "헤이즐넛 오일",
            "헤이즐넛 버터",
            "누텔라 (헤이즐넛 스프레드)",
            "프랄린",
            "잔두야",
        ],

        "hidden_sources": [
            "초콜릿 제품 (누텔라, 페레로로쉐 등)",
            "커피 시럽/향료",
            "베이커리 제품",
            "아이스크림",
            "리큐어 (프랑젤리코)",
            "시리얼/그래놀라",
            "에너지바",
            "화장품 (헤이즐넛 오일)",
        ],

        "substitutes": [
            {
                "original": "헤이즐넛 스프레드",
                "alternatives": ["해바라기씨 버터 초콜릿 스프레드", "카카오 스프레드"],
                "notes": ""
            },
            {
                "original": "헤이즐넛",
                "alternatives": ["해바라기씨", "호박씨"],
                "notes": "다른 견과류 교차반응 확인"
            },
        ],

        "restaurant_cautions": [
            "카페 (헤이즐넛 시럽)",
            "초콜릿 전문점",
            "베이커리",
            "아이스크림 가게",
            "이탈리안 디저트 (잔두야, 젤라또)",
        ],

        "label_keywords_kr": [
            "헤이즐넛",
            "개암",
            "필버트",
            "누텔라",
            "잔두야",
        ],

        "label_keywords_en": [
            "hazelnut",
            "hazelnuts",
            "filbert",
            "cobnut",
            "nutella",
            "praline",
            "gianduja",
        ],

        "symptoms_by_grade": {
            "1-2": {
                "symptoms": [
                    {"name": "입/입술 가려움", "name_en": "oral/lip itching", "probability": "70-80%", "onset": "수분 이내"},
                    {"name": "입안 따끔거림", "name_en": "oral tingling", "probability": "60-70%", "onset": "수분 이내"},
                ],
                "severity": "mild",
            },
            "3-4": {
                "symptoms": [
                    {"name": "입술/혀 부종", "name_en": "lip/tongue swelling", "probability": "40-50%", "onset": "수분~30분"},
                    {"name": "두드러기", "name_en": "urticaria", "probability": "40-50%", "onset": "30분~2시간"},
                    {"name": "복통", "name_en": "abdominal pain", "probability": "30-40%", "onset": "1~3시간"},
                ],
                "severity": "moderate",
            },
            "5-6": {
                "symptoms": [
                    {"name": "전신 두드러기", "name_en": "generalized urticaria", "probability": "60-70%", "onset": "수분~1시간"},
                    {"name": "호흡곤란", "name_en": "dyspnea", "probability": "30-40%", "onset": "수분~30분"},
                    {"name": "아나필락시스", "name_en": "anaphylaxis", "probability": "15-25%", "onset": "수분~30분"},
                ],
                "severity": "severe",
            },
        },

        "cross_reactivity": [
            {
                "allergen": "birch_pollen",
                "allergen_kr": "자작나무 꽃가루",
                "probability": "70-80%",
                "common_protein": "Cor a 1 (PR-10)",
                "related_foods": [],
            },
            {
                "allergen": "other_tree_nuts",
                "allergen_kr": "다른 견과류",
                "probability": "30-50%",
                "common_protein": "저장 단백질",
                "related_foods": ["호두", "캐슈넛", "아몬드"],
            },
            {
                "allergen": "apple",
                "allergen_kr": "사과",
                "probability": "40-60%",
                "common_protein": "PR-10 단백질",
                "related_foods": ["사과", "배", "체리"],
            },
        ],

        "special_notes": "자작나무 꽃가루 알러지가 있는 환자의 약 70-80%가 헤이즐넛에 교차반응을 보입니다. 로스팅하면 PR-10 단백질이 파괴되어 일부 환자에게 안전할 수 있습니다.",
    },

    # -------------------------------------------------------------------------
    # 21. 참깨 (Sesame)
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

    # -------------------------------------------------------------------------
    # 8. 유럽집먼지진드기 (Dermatophagoides pteronyssinus)
    # -------------------------------------------------------------------------
    "d_pteronyssinus": {
        "name_kr": "유럽집먼지진드기",
        "name_en": "European House Dust Mite",
        "category": "inhalant",
        "description": "유럽집먼지진드기(D. pteronyssinus)는 전 세계적으로 가장 흔한 실내 알러젠으로, Der p 1, Der p 2 등의 알러젠을 생산합니다.",

        "avoid_exposure": [
            "오래된 침구류",
            "카펫, 러그",
            "천 소파",
            "봉제 인형",
            "두꺼운 커튼",
            "먼지가 많은 환경",
            "습한 환경 (습도 70% 이상)",
        ],

        "management_tips": [
            "침구류를 주 1회 60°C 이상 물로 세탁",
            "진드기 방지 침구 커버 (매트리스, 베개, 이불) 사용",
            "카펫 제거, 나무/타일 바닥 권장",
            "실내 습도 50% 이하 유지",
            "HEPA 필터 공기청정기 사용",
            "HEPA 필터 진공청소기로 주 2회 청소",
            "봉제 인형은 -18°C에서 24시간 냉동 후 세탁",
            "침실에서 반려동물 배제",
            "침대 밑 물건 정리 (먼지 축적 방지)",
        ],

        "symptoms_by_grade": {
            "1-2": {
                "symptoms": [
                    {"name": "간헐적 코막힘", "name_en": "intermittent nasal congestion", "probability": "60-70%", "onset": "노출 후 수분~수시간"},
                    {"name": "재채기", "name_en": "sneezing", "probability": "50-60%", "onset": "노출 즉시~수분"},
                    {"name": "맑은 콧물", "name_en": "clear rhinorrhea", "probability": "50-60%", "onset": "노출 후"},
                ],
                "severity": "mild",
            },
            "3-4": {
                "symptoms": [
                    {"name": "지속적 비염", "name_en": "persistent rhinitis", "probability": "70-80%", "onset": "만성"},
                    {"name": "눈 가려움/충혈", "name_en": "itchy/red eyes", "probability": "50-60%", "onset": "노출 시"},
                    {"name": "기침", "name_en": "cough", "probability": "40-50%", "onset": "노출 후"},
                    {"name": "아토피 피부염 악화", "name_en": "atopic dermatitis flare", "probability": "40-50%", "onset": "지속 노출 시"},
                ],
                "severity": "moderate",
            },
            "5-6": {
                "symptoms": [
                    {"name": "천식 증상/악화", "name_en": "asthma symptoms/exacerbation", "probability": "60-80%", "onset": "노출 시"},
                    {"name": "심한 비염", "name_en": "severe rhinitis", "probability": "70-80%", "onset": "만성"},
                    {"name": "수면장애", "name_en": "sleep disturbance", "probability": "50-60%", "onset": "만성"},
                ],
                "severity": "severe",
            },
        },

        "cross_reactivity": [
            {
                "allergen": "d_farinae",
                "allergen_kr": "미국집먼지진드기",
                "probability": "80-90%",
                "common_protein": "Der p/f 1, 2",
                "related_foods": [],
            },
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
        ],

        "food_cautions": [
            "갑각류 (새우, 게) - 트로포미오신 교차반응 가능",
            "연체류 (오징어, 조개) - 교차반응 가능성",
            "달팽이 - 일부 교차반응 보고",
        ],
    },

    # -------------------------------------------------------------------------
    # 9. 미국집먼지진드기 (Dermatophagoides farinae)
    # -------------------------------------------------------------------------
    "d_farinae": {
        "name_kr": "미국집먼지진드기",
        "name_en": "American House Dust Mite",
        "category": "inhalant",
        "description": "미국집먼지진드기(D. farinae)는 유럽집먼지진드기와 함께 가장 흔한 실내 알러젠입니다. 더 건조한 환경에서도 생존합니다.",

        "avoid_exposure": [
            "오래된 침구류",
            "카펫",
            "천 소파",
            "봉제 인형",
            "두꺼운 커튼",
            "먼지가 많은 환경",
        ],

        "management_tips": [
            "침구류를 주 1회 60°C 이상 물로 세탁",
            "진드기 방지 침구 커버 사용",
            "카펫 대신 나무/타일 바닥 권장",
            "실내 습도 50% 이하 유지",
            "HEPA 필터 공기청정기 사용",
            "HEPA 필터 진공청소기로 주 2회 청소",
            "봉제 인형 냉동 후 세탁",
        ],

        "symptoms_by_grade": {
            "1-2": {
                "symptoms": [
                    {"name": "간헐적 코막힘", "name_en": "intermittent nasal congestion", "probability": "60-70%", "onset": "노출 후"},
                    {"name": "재채기", "name_en": "sneezing", "probability": "50-60%", "onset": "노출 즉시"},
                ],
                "severity": "mild",
            },
            "3-4": {
                "symptoms": [
                    {"name": "지속적 비염", "name_en": "persistent rhinitis", "probability": "70-80%", "onset": "만성"},
                    {"name": "눈 가려움/충혈", "name_en": "itchy/red eyes", "probability": "50-60%", "onset": "노출 시"},
                    {"name": "기침", "name_en": "cough", "probability": "40-50%", "onset": "노출 후"},
                    {"name": "아토피 피부염 악화", "name_en": "atopic dermatitis flare", "probability": "40-50%", "onset": "지속 노출 시"},
                ],
                "severity": "moderate",
            },
            "5-6": {
                "symptoms": [
                    {"name": "천식 증상", "name_en": "asthma symptoms", "probability": "60-80%", "onset": "노출 시"},
                    {"name": "심한 비염", "name_en": "severe rhinitis", "probability": "70-80%", "onset": "만성"},
                    {"name": "수면장애", "name_en": "sleep disturbance", "probability": "50-60%", "onset": "만성"},
                ],
                "severity": "severe",
            },
        },

        "cross_reactivity": [
            {
                "allergen": "d_pteronyssinus",
                "allergen_kr": "유럽집먼지진드기",
                "probability": "80-90%",
                "common_protein": "Der f/p 1, 2",
                "related_foods": [],
            },
            {
                "allergen": "shellfish",
                "allergen_kr": "갑각류",
                "probability": "60-80%",
                "common_protein": "트로포미오신",
                "related_foods": ["새우", "게"],
            },
        ],

        "food_cautions": [
            "갑각류 - 트로포미오신 교차반응",
        ],
    },

    # -------------------------------------------------------------------------
    # 10. 삼나무 (Japanese Cedar)
    # -------------------------------------------------------------------------
    "japanese_cedar": {
        "name_kr": "삼나무",
        "name_en": "Japanese Cedar",
        "category": "inhalant",
        "description": "삼나무 꽃가루 알러지는 일본과 한국에서 봄철 화분증의 주요 원인입니다. Cry j 1, Cry j 2 단백질에 반응합니다.",

        "avoid_exposure": [
            "꽃가루 시즌 외출 (2-4월)",
            "바람 많은 날",
            "산림 지역",
            "아침 시간대 (꽃가루 농도 최고)",
        ],

        "management_tips": [
            "꽃가루 예보 확인 후 외출",
            "외출 시 마스크 (KF94 이상) 및 선글라스 착용",
            "외출 후 샤워 및 옷 세탁",
            "창문 닫고 에어컨 사용",
            "HEPA 필터 공기청정기 사용",
            "차량 에어컨 필터 정기 교체",
            "빨래 실내 건조",
            "비강 세척 (생리식염수)",
        ],

        "symptoms_by_grade": {
            "1-2": {
                "symptoms": [
                    {"name": "재채기", "name_en": "sneezing", "probability": "70-80%", "onset": "노출 즉시"},
                    {"name": "맑은 콧물", "name_en": "clear rhinorrhea", "probability": "60-70%", "onset": "노출 즉시"},
                ],
                "severity": "mild",
            },
            "3-4": {
                "symptoms": [
                    {"name": "심한 비염", "name_en": "severe rhinitis", "probability": "70-80%", "onset": "시즌 중"},
                    {"name": "눈 가려움/충혈/눈물", "name_en": "itchy/red/watery eyes", "probability": "60-70%", "onset": "노출 시"},
                    {"name": "코막힘", "name_en": "nasal congestion", "probability": "60-70%", "onset": "지속"},
                    {"name": "목 가려움", "name_en": "throat itching", "probability": "30-40%", "onset": "노출 시"},
                ],
                "severity": "moderate",
            },
            "5-6": {
                "symptoms": [
                    {"name": "천식 증상", "name_en": "asthma symptoms", "probability": "40-60%", "onset": "시즌 중"},
                    {"name": "심한 결막염", "name_en": "severe conjunctivitis", "probability": "50-60%", "onset": "시즌 중"},
                    {"name": "두통/피로", "name_en": "headache/fatigue", "probability": "40-50%", "onset": "시즌 중"},
                ],
                "severity": "severe",
            },
        },

        "cross_reactivity": [
            {
                "allergen": "cypress",
                "allergen_kr": "측백나무",
                "probability": "70-80%",
                "common_protein": "유사 꽃가루 단백질",
                "related_foods": [],
            },
            {
                "allergen": "tomato",
                "allergen_kr": "토마토",
                "probability": "10-20%",
                "common_protein": "Cry j 1 유사체",
                "related_foods": ["토마토"],
            },
        ],

        "food_cautions": [
            "토마토 - 일부 교차반응 보고 (구강알러지증후군)",
        ],
    },

    # -------------------------------------------------------------------------
    # 11. 자작나무 (Birch)
    # -------------------------------------------------------------------------
    "birch": {
        "name_kr": "자작나무",
        "name_en": "Birch",
        "category": "inhalant",
        "description": "자작나무 꽃가루 알러지는 봄철 화분증의 주요 원인이며, 많은 과일/채소와 교차반응(구강알러지증후군)을 일으킵니다.",

        "avoid_exposure": [
            "꽃가루 시즌 외출 (3-5월)",
            "자작나무 숲/공원",
            "바람 많은 날",
            "이른 아침",
        ],

        "management_tips": [
            "꽃가루 예보 확인",
            "외출 시 마스크 및 선글라스 착용",
            "외출 후 샤워 및 옷 세탁",
            "창문 닫고 에어컨 사용",
            "HEPA 필터 공기청정기",
            "비강 세척",
            "교차반응 식품 주의",
        ],

        "symptoms_by_grade": {
            "1-2": {
                "symptoms": [
                    {"name": "재채기", "name_en": "sneezing", "probability": "70-80%", "onset": "노출 즉시"},
                    {"name": "맑은 콧물", "name_en": "clear rhinorrhea", "probability": "60-70%", "onset": "노출 즉시"},
                ],
                "severity": "mild",
            },
            "3-4": {
                "symptoms": [
                    {"name": "심한 비염", "name_en": "severe rhinitis", "probability": "70-80%", "onset": "시즌 중"},
                    {"name": "눈 가려움/충혈", "name_en": "itchy/red eyes", "probability": "60-70%", "onset": "노출 시"},
                    {"name": "코막힘", "name_en": "nasal congestion", "probability": "60-70%", "onset": "지속"},
                    {"name": "구강알러지증후군", "name_en": "oral allergy syndrome", "probability": "50-70%", "onset": "관련 식품 섭취 시"},
                ],
                "severity": "moderate",
            },
            "5-6": {
                "symptoms": [
                    {"name": "천식 증상", "name_en": "asthma symptoms", "probability": "40-60%", "onset": "시즌 중"},
                    {"name": "심한 결막염", "name_en": "severe conjunctivitis", "probability": "50-60%", "onset": "시즌 중"},
                ],
                "severity": "severe",
            },
        },

        "cross_reactivity": [
            {
                "allergen": "apple",
                "allergen_kr": "사과",
                "probability": "50-70%",
                "common_protein": "Bet v 1 (PR-10)",
                "related_foods": ["사과"],
            },
            {
                "allergen": "stone_fruits",
                "allergen_kr": "핵과류",
                "probability": "40-60%",
                "common_protein": "PR-10",
                "related_foods": ["복숭아", "체리", "자두", "살구"],
            },
            {
                "allergen": "hazelnut",
                "allergen_kr": "헤이즐넛",
                "probability": "70-80%",
                "common_protein": "Cor a 1 (PR-10)",
                "related_foods": ["헤이즐넛"],
            },
            {
                "allergen": "carrot_celery",
                "allergen_kr": "당근/셀러리",
                "probability": "30-50%",
                "common_protein": "PR-10",
                "related_foods": ["당근", "셀러리"],
            },
            {
                "allergen": "soy",
                "allergen_kr": "대두",
                "probability": "10-15%",
                "common_protein": "Gly m 4 (PR-10)",
                "related_foods": ["대두"],
            },
        ],

        "food_cautions": [
            "장미과 과일 (사과, 배, 복숭아, 체리, 자두, 살구) - OAS 흔함",
            "헤이즐넛 - 높은 교차반응",
            "당근, 셀러리 - 교차반응 가능",
            "대두 - 일부 교차반응",
            "아몬드 - 교차반응 가능",
            "키위, 감자 - 일부 보고",
        ],
    },

    # -------------------------------------------------------------------------
    # 12. 알터나리아 (Alternaria alternata)
    # -------------------------------------------------------------------------
    "alternaria": {
        "name_kr": "알터나리아",
        "name_en": "Alternaria",
        "category": "inhalant",
        "description": "알터나리아는 야외 곰팡이로, 천식 악화의 중요한 원인입니다. 특히 어린이 천식과 강한 연관성이 있습니다.",

        "avoid_exposure": [
            "낙엽 더미",
            "퇴비",
            "썩은 나무/식물",
            "농업 환경",
            "곡물 저장소",
            "비 온 후 야외 활동",
        ],

        "management_tips": [
            "실내 습도 50% 이하 유지",
            "제습기 사용",
            "야외 활동 후 샤워 및 옷 세탁",
            "정원 작업 시 마스크 착용",
            "낙엽 정리 피하기 (다른 사람에게 요청)",
            "HEPA 필터 공기청정기",
            "욕실/주방 환기",
            "식물 화분 흙 관리",
        ],

        "symptoms_by_grade": {
            "1-2": {
                "symptoms": [
                    {"name": "재채기", "name_en": "sneezing", "probability": "50-60%", "onset": "노출 시"},
                    {"name": "콧물", "name_en": "rhinorrhea", "probability": "50-60%", "onset": "노출 시"},
                ],
                "severity": "mild",
            },
            "3-4": {
                "symptoms": [
                    {"name": "비염", "name_en": "rhinitis", "probability": "60-70%", "onset": "노출 시"},
                    {"name": "눈 가려움", "name_en": "itchy eyes", "probability": "40-50%", "onset": "노출 시"},
                    {"name": "기침", "name_en": "cough", "probability": "50-60%", "onset": "노출 시"},
                ],
                "severity": "moderate",
            },
            "5-6": {
                "symptoms": [
                    {"name": "천식 악화", "name_en": "asthma exacerbation", "probability": "60-80%", "onset": "노출 시"},
                    {"name": "심한 천명음", "name_en": "severe wheezing", "probability": "50-60%", "onset": "노출 시"},
                    {"name": "호흡곤란", "name_en": "dyspnea", "probability": "40-50%", "onset": "노출 시"},
                ],
                "severity": "severe",
            },
        },

        "cross_reactivity": [
            {
                "allergen": "other_molds",
                "allergen_kr": "다른 곰팡이",
                "probability": "다양",
                "common_protein": "엔올라제 등",
                "related_foods": [],
            },
        ],

        "food_cautions": [
            "곰팡이 발효 식품 주의 가능 (치즈, 와인 등)",
        ],

        "special_notes": "알터나리아 감작은 천식 발작 및 호흡기 응급상황의 중요한 위험인자입니다. 천식 환자는 특히 주의가 필요합니다.",
    },

    # -------------------------------------------------------------------------
    # 13. 아스페르길루스 (Aspergillus fumigatus)
    # -------------------------------------------------------------------------
    "aspergillus": {
        "name_kr": "아스페르길루스",
        "name_en": "Aspergillus",
        "category": "inhalant",
        "description": "아스페르길루스는 ABPA(알러지성 기관지폐 아스페르길루스증)를 유발할 수 있는 곰팡이입니다. 천식 환자에서 특히 중요합니다.",

        "avoid_exposure": [
            "습기 많은 환경",
            "오래된 건물",
            "에어컨 필터",
            "썩은 식물/퇴비",
            "건설 현장 먼지",
            "실내 화분 흙",
        ],

        "management_tips": [
            "실내 습도 50% 이하 유지",
            "제습기 사용",
            "욕실/주방 환기 철저",
            "에어컨 필터 정기 청소/교체",
            "곰팡이 발생 시 즉시 제거",
            "화분 흙 표면 관리",
            "HEPA 필터 공기청정기",
        ],

        "symptoms_by_grade": {
            "1-2": {
                "symptoms": [
                    {"name": "기침", "name_en": "cough", "probability": "50-60%", "onset": "노출 시"},
                    {"name": "콧물", "name_en": "rhinorrhea", "probability": "40-50%", "onset": "노출 시"},
                ],
                "severity": "mild",
            },
            "3-4": {
                "symptoms": [
                    {"name": "비염", "name_en": "rhinitis", "probability": "50-60%", "onset": "노출 시"},
                    {"name": "기침", "name_en": "cough", "probability": "60-70%", "onset": "노출 시"},
                    {"name": "천명음", "name_en": "wheezing", "probability": "40-50%", "onset": "노출 시"},
                ],
                "severity": "moderate",
            },
            "5-6": {
                "symptoms": [
                    {"name": "천식 악화", "name_en": "asthma exacerbation", "probability": "50-70%", "onset": "노출 시"},
                    {"name": "ABPA 증상", "name_en": "ABPA symptoms", "probability": "10-20%", "onset": "만성"},
                    {"name": "호흡곤란", "name_en": "dyspnea", "probability": "40-50%", "onset": "노출 시"},
                ],
                "severity": "severe",
            },
        },

        "cross_reactivity": [
            {
                "allergen": "other_molds",
                "allergen_kr": "다른 곰팡이",
                "probability": "다양",
                "common_protein": "곰팡이 효소",
                "related_foods": [],
            },
        ],

        "food_cautions": [],

        "special_notes": "ABPA(알러지성 기관지폐 아스페르길루스증)는 천식 환자에서 발생할 수 있는 심각한 합병증입니다. 지속적인 천식 악화, 기침, 갈색 객담이 있으면 의료진 상담이 필요합니다.",
    },

    # -------------------------------------------------------------------------
    # 14. 큰조아재비 (Timothy Grass)
    # -------------------------------------------------------------------------
    "timothy_grass": {
        "name_kr": "큰조아재비",
        "name_en": "Timothy Grass",
        "category": "inhalant",
        "description": "큰조아재비는 대표적인 목초 꽃가루 알러젠으로, 여름철 화분증의 주요 원인입니다. Phl p 1, Phl p 5 등의 알러젠을 생산합니다.",

        "avoid_exposure": [
            "꽃가루 시즌 외출 (5-7월)",
            "잔디밭/공원",
            "잔디 깎기",
            "이른 아침 및 저녁 (꽃가루 농도 높음)",
            "바람 많은 날",
        ],

        "management_tips": [
            "꽃가루 예보 확인",
            "외출 시 마스크 및 선글라스 착용",
            "외출 후 샤워 및 옷 세탁",
            "창문 닫고 에어컨 사용",
            "잔디 깎기 회피 (다른 사람에게 요청)",
            "HEPA 필터 공기청정기",
            "빨래 실내 건조",
            "반려동물 외출 후 닦기",
        ],

        "symptoms_by_grade": {
            "1-2": {
                "symptoms": [
                    {"name": "재채기", "name_en": "sneezing", "probability": "70-80%", "onset": "노출 즉시"},
                    {"name": "맑은 콧물", "name_en": "clear rhinorrhea", "probability": "60-70%", "onset": "노출 즉시"},
                ],
                "severity": "mild",
            },
            "3-4": {
                "symptoms": [
                    {"name": "심한 비염", "name_en": "severe rhinitis", "probability": "70-80%", "onset": "시즌 중"},
                    {"name": "눈 가려움/충혈", "name_en": "itchy/red eyes", "probability": "60-70%", "onset": "노출 시"},
                    {"name": "코막힘", "name_en": "nasal congestion", "probability": "60-70%", "onset": "지속"},
                ],
                "severity": "moderate",
            },
            "5-6": {
                "symptoms": [
                    {"name": "천식 증상", "name_en": "asthma symptoms", "probability": "40-60%", "onset": "시즌 중"},
                    {"name": "심한 결막염", "name_en": "severe conjunctivitis", "probability": "50-60%", "onset": "시즌 중"},
                ],
                "severity": "severe",
            },
        },

        "cross_reactivity": [
            {
                "allergen": "other_grasses",
                "allergen_kr": "다른 목초",
                "probability": "80-90%",
                "common_protein": "그룹 1, 5 알러젠",
                "related_foods": [],
            },
            {
                "allergen": "wheat",
                "allergen_kr": "밀",
                "probability": "10-20%",
                "common_protein": "프로필린",
                "related_foods": ["밀"],
            },
            {
                "allergen": "melon_fruits",
                "allergen_kr": "멜론류 과일",
                "probability": "10-20%",
                "common_protein": "프로필린",
                "related_foods": ["멜론", "수박"],
            },
        ],

        "food_cautions": [
            "멜론, 수박 - 일부 구강알러지증후군 보고",
            "토마토, 감자 - 일부 교차반응 가능",
            "밀 - 드물게 교차반응",
        ],
    },

    # -------------------------------------------------------------------------
    # 15. 쑥 (Mugwort)
    # -------------------------------------------------------------------------
    "mugwort": {
        "name_kr": "쑥",
        "name_en": "Mugwort",
        "category": "inhalant",
        "description": "쑥 꽃가루 알러지는 늦여름~가을(8-10월)에 발생하며, 한국에서 중요한 가을 화분증 원인입니다. 셀러리-쑥-향신료 증후군과 관련됩니다.",

        "avoid_exposure": [
            "꽃가루 시즌 외출 (8-10월)",
            "풀밭, 빈 공터",
            "야생 쑥 서식지",
            "이른 아침",
            "바람 많은 날",
        ],

        "management_tips": [
            "꽃가루 예보 확인",
            "외출 시 마스크 및 선글라스 착용",
            "외출 후 샤워 및 옷 세탁",
            "창문 닫고 에어컨 사용",
            "HEPA 필터 공기청정기",
            "교차반응 식품 주의",
        ],

        "symptoms_by_grade": {
            "1-2": {
                "symptoms": [
                    {"name": "재채기", "name_en": "sneezing", "probability": "70-80%", "onset": "노출 즉시"},
                    {"name": "맑은 콧물", "name_en": "clear rhinorrhea", "probability": "60-70%", "onset": "노출 즉시"},
                ],
                "severity": "mild",
            },
            "3-4": {
                "symptoms": [
                    {"name": "심한 비염", "name_en": "severe rhinitis", "probability": "70-80%", "onset": "시즌 중"},
                    {"name": "눈 가려움/충혈", "name_en": "itchy/red eyes", "probability": "60-70%", "onset": "노출 시"},
                    {"name": "코막힘", "name_en": "nasal congestion", "probability": "60-70%", "onset": "지속"},
                    {"name": "구강알러지증후군", "name_en": "oral allergy syndrome", "probability": "30-50%", "onset": "관련 식품 섭취 시"},
                ],
                "severity": "moderate",
            },
            "5-6": {
                "symptoms": [
                    {"name": "천식 증상", "name_en": "asthma symptoms", "probability": "40-60%", "onset": "시즌 중"},
                    {"name": "심한 결막염", "name_en": "severe conjunctivitis", "probability": "50-60%", "onset": "시즌 중"},
                ],
                "severity": "severe",
            },
        },

        "cross_reactivity": [
            {
                "allergen": "celery",
                "allergen_kr": "셀러리",
                "probability": "40-60%",
                "common_protein": "Art v 1 유사체",
                "related_foods": ["셀러리"],
            },
            {
                "allergen": "carrot",
                "allergen_kr": "당근",
                "probability": "30-50%",
                "common_protein": "LTP, 프로필린",
                "related_foods": ["당근"],
            },
            {
                "allergen": "spices",
                "allergen_kr": "향신료",
                "probability": "20-40%",
                "common_protein": "LTP",
                "related_foods": ["파슬리", "고수", "회향", "아니스", "캐러웨이"],
            },
            {
                "allergen": "peach",
                "allergen_kr": "복숭아",
                "probability": "30-50%",
                "common_protein": "LTP (Pru p 3)",
                "related_foods": ["복숭아"],
            },
            {
                "allergen": "sunflower_seeds",
                "allergen_kr": "해바라기씨",
                "probability": "20-30%",
                "common_protein": "LTP",
                "related_foods": ["해바라기씨"],
            },
        ],

        "food_cautions": [
            "셀러리 - 셀러리-쑥-향신료 증후군",
            "당근 - 교차반응 흔함",
            "향신료 (파슬리, 고수, 회향 등) - 주의 필요",
            "복숭아, 사과 - LTP 교차반응",
            "해바라기씨 - 일부 교차반응",
            "머스타드, 꿀 - 일부 보고",
        ],

        "special_notes": "쑥 알러지는 셀러리-쑥-향신료 증후군(CMS)과 관련됩니다. 이 증후군에서는 셀러리, 당근, 다양한 향신료에 대한 알러지 반응이 동반될 수 있습니다. LTP 알러지인 경우 심각한 전신 반응 가능성이 있어 주의가 필요합니다.",
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
