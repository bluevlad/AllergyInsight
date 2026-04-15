"""학술 전용 알러지 치료 Agent 서비스

Phase 4~6의 핵심 컴포넌트:
- cross_check_service: 5개 축 크로스 체크 (성분/약리군/ACB/금기/투여경로)
- response_validator: Agent 응답 검증기 (PMID 인용 강제, 금지어 필터)
- drug_agent_service: Tool Calling 오케스트레이터

관련 문서:
- services/allergyinsight/plans/academic-drug-agent-plan.md Phase 4~6
- services/allergyinsight/adr/009-tool-calling-academic-agent.md
- services/allergyinsight/adr/010-yaml-route-rules-engine.md
"""
