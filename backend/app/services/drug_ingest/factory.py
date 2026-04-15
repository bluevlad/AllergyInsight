"""Drug ingest 파이프라인 팩토리.

환경변수에서 어댑터 구성을 읽어 DrugIngestPipeline 을 생성한다.
진입점(CLI · admin API · 스케줄러 job) 은 이 함수 하나만 호출하면 된다.

환경변수:
- OPENFDA_API_KEY (선택) — 없어도 openFDA 무료 티어 동작
- MFDS_API_KEY (선택) — 없으면 MFDS 어댑터가 파이프라인에서 제외됨
  (필수가 아닌 이유: openFDA 만으로도 부분 수집이 가능해야 함)
"""
from __future__ import annotations

import logging
import os

from .pipeline import DrugIngestPipeline
from .sources.base import DrugSourceAdapter
from .sources.mfds_eyakeunyo import MfdsEyakeunyoAdapter
from .sources.openfda import OpenFdaLabelAdapter

logger = logging.getLogger(__name__)


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
        logger.info("drug_ingest.factory: MFDS adapter ready")
    else:
        logger.warning(
            "drug_ingest.factory: MFDS_API_KEY not set — MFDS adapter skipped"
        )

    if not adapters:
        raise RuntimeError(
            "drug_ingest: no adapters could be constructed — check env vars"
        )

    return DrugIngestPipeline(adapters)
