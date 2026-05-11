"""Core module - 공통 서비스 (인증, 알러젠 데이터, 다도메인 framework).

서비스 이원화를 위한 공통 모듈입니다.
- auth: 인증 및 권한 관리
- allergen: 알러젠 데이터베이스
- feature_flags, pii_masking: 보조 유틸리티
- sources: VerticalInsight Framework Layer 1 (Connector ABC + registry)
- domains: DomainPack 로더 + 린터

**Hotfix (2026-05-11)**: 이전 버전은 ``from .auth import ...`` 와
``from .allergen import ...`` 를 모듈 최상위에서 eager import 했으나, 이는
scheduler 컨테이너처럼 ``JWT_SECRET_KEY`` 환경변수가 없는 서브 컨테이너에서
``KeyError: 'JWT_SECRET_KEY'`` 로 import chain 을 깨뜨림 (Phase 1 framework
이식 후 ``services/__init__.py → paper_search_service → core.sources →
core (__init__)`` 의 chain 으로 노출).

호출자 전체 grep 결과 ``from app.core import X`` 사용처 0건 — 본 re-export 는
dead code 였음. 명시적 submodule import 만 허용하도록 정리:

    from app.core.auth import require_auth      # OK
    from app.core.allergen import get_allergen_info  # OK
    from app.core.sources import registry        # OK
    from app.core import require_auth            # FAIL (의도된 동작)
"""

# 의도적으로 비어 있음 — eager submodule import 금지.
# 새 submodule 추가 시 본 파일에서 re-export 하지 말 것.
