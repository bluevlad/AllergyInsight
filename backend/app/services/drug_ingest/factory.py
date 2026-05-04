"""Drug ingest 파이프라인 팩토리.

환경변수에서 어댑터 구성을 읽어 DrugIngestPipeline 을 생성한다.
진입점(CLI · admin API · 스케줄러 job) 은 이 함수 하나만 호출하면 된다.

환경변수:
- OPENFDA_API_KEY (선택) — 없어도 openFDA 무료 티어 동작
- MFDS_API_KEY (선택) — 없으면 MFDS 3개 어댑터가 파이프라인에서 제외됨
  (필수가 아닌 이유: 다른 소스만으로도 부분 수집이 가능해야 함)
- DAILYMED_ENABLED (선택, 기본 "1") — DailyMed 어댑터 on/off
- DSLD_ENABLED (선택, 기본 "1") — DSLD 어댑터 on/off
- RXNORM_ENABLED (선택, 기본 "1") — RxNorm 어댑터 on/off

DailyMed / DSLD / RxNorm 은 별도 키가 필요 없고 Public Domain / UMLS
Cat 0 라이선스이므로 기본 활성화된다. 네트워크 제약이 있는 CI 환경에서
플래그로 비활성화할 수 있다.
"""
from __future__ import annotations

import logging
import os

from .pipeline import DrugIngestPipeline
from .sources.base import DrugSourceAdapter
from .sources.dailymed import DailyMedAdapter
from .sources.dsld import DsldAdapter
from .sources.mfds_eyakeunyo import MfdsEyakeunyoAdapter
from .sources.mfds_hfood import MfdsHfoodAdapter
from .sources.mfds_license import MfdsLicenseAdapter
from .sources.openfda import OpenFdaLabelAdapter
from .sources.rxnorm import RxNormAdapter

logger = logging.getLogger(__name__)


def _flag_enabled(name: str, default: bool = True) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() not in ("0", "false", "no", "off", "")


def build_default_pipeline() -> DrugIngestPipeline:
    """환경변수 기반으로 사용 가능한 어댑터만 조합해 파이프라인을 만든다.

    어느 어댑터도 구성할 수 없으면 RuntimeError — 호출자가 기동
    실패를 감지하도록 (silent empty 방지).
    """
    adapters: list[DrugSourceAdapter] = []

    adapters.append(OpenFdaLabelAdapter())
    logger.info("drug_ingest.factory: openFDA adapter ready")

    mfds_key = os.getenv("MFDS_API_KEY")
    if mfds_key:
        adapters.append(MfdsEyakeunyoAdapter(api_key=mfds_key))
        logger.info("drug_ingest.factory: MFDS e약은요 adapter ready")
        adapters.append(MfdsLicenseAdapter(api_key=mfds_key))
        logger.info("drug_ingest.factory: MFDS 제품허가정보 adapter ready")
        adapters.append(MfdsHfoodAdapter(api_key=mfds_key))
        logger.info("drug_ingest.factory: MFDS 건강기능식품 adapter ready")
    else:
        logger.warning(
            "drug_ingest.factory: MFDS_API_KEY not set — 3 MFDS adapters skipped"
        )

    if _flag_enabled("DAILYMED_ENABLED"):
        adapters.append(DailyMedAdapter())
        logger.info("drug_ingest.factory: DailyMed adapter ready")

    if _flag_enabled("DSLD_ENABLED"):
        adapters.append(DsldAdapter())
        logger.info("drug_ingest.factory: DSLD adapter ready")

    if _flag_enabled("RXNORM_ENABLED"):
        adapters.append(RxNormAdapter())
        logger.info("drug_ingest.factory: RxNorm adapter ready")

    if not adapters:
        raise RuntimeError(
            "drug_ingest: no adapters could be constructed — check env vars"
        )

    return DrugIngestPipeline(adapters)
