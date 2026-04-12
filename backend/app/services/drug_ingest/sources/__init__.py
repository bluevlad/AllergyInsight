"""소스별 수집 어댑터

각 어댑터는 DrugSourceAdapter ABC를 상속하여 다음을 제공:
- list_updated_since(timestamp): 증분 수집 대상 목록
- fetch_detail(source_id): 개별 제품 상세
- normalize(raw): 원본 → DrugProductCandidate 정규화

현재 구현:
- openfda.py — FDA openFDA drug/label API (CC0, 키 선택)

계획:
- mfds_eyakeunyo.py — 식약처 e약은요 (공공누리 1유형)
- mfds_license.py — 식약처 제품허가정보
- mfds_hfood.py — 식약처 건강기능식품
- dailymed.py — NIH NLM DailyMed SPL
- dsld.py — NIH ODS DSLD
- rxnorm.py — NIH NLM RxNorm
"""
