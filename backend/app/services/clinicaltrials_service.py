"""ClinicalTrials.gov API 연동 서비스

FDA 등록 임상시험 검색. 알러지 관련 임상시험 수집.
API 키 불필요, rate limit 준수 (0.5s 간격).

API 문서: https://clinicaltrials.gov/data-api/api
"""
import logging
import time
from typing import Optional

import httpx

from ..models.paper import Paper, PaperSearchResult, PaperSource

logger = logging.getLogger(__name__)


class ClinicalTrialsService:
    """ClinicalTrials.gov v2 API 클라이언트"""

    BASE_URL = "https://clinicaltrials.gov/api/v2/studies"
    REQUEST_INTERVAL = 0.5  # 요청 간 최소 대기 시간 (초)

    def __init__(self):
        self._client: Optional[httpx.Client] = None
        self._last_request_time: float = 0.0

    def _get_client(self) -> httpx.Client:
        if self._client is None:
            self._client = httpx.Client(timeout=30.0)
        return self._client

    def _wait_for_rate_limit(self):
        """Rate limit 준수를 위한 대기"""
        elapsed = time.time() - self._last_request_time
        if elapsed < self.REQUEST_INTERVAL:
            time.sleep(self.REQUEST_INTERVAL - elapsed)
        self._last_request_time = time.time()

    def search(
        self,
        query: str,
        max_results: int = 20,
        status_filter: Optional[list[str]] = None,
    ) -> PaperSearchResult:
        """임상시험 검색

        Args:
            query: 검색 쿼리
            max_results: 최대 결과 수
            status_filter: 상태 필터 (예: ["RECRUITING", "COMPLETED"])

        Returns:
            PaperSearchResult
        """
        start_time = time.time()
        client = self._get_client()

        papers = []
        try:
            self._wait_for_rate_limit()

            params = {
                "query.term": query,
                "pageSize": min(max_results, 100),
                "format": "json",
                "fields": (
                    "NCTId,BriefTitle,OfficialTitle,BriefSummary,"
                    "Condition,InterventionName,OverallStatus,Phase,"
                    "EnrollmentCount,LeadSponsorName,CollaboratorName,"
                    "StartDate,CompletionDate,StudyType"
                ),
            }

            if status_filter:
                params["filter.overallStatus"] = ",".join(status_filter)

            resp = client.get(self.BASE_URL, params=params)
            resp.raise_for_status()
            data = resp.json()

            studies = data.get("studies", [])
            for study in studies:
                paper = self._parse_study(study)
                if paper:
                    papers.append(paper)

        except Exception as e:
            logger.error(f"ClinicalTrials.gov 검색 실패: {e}")

        elapsed = (time.time() - start_time) * 1000

        return PaperSearchResult(
            papers=papers,
            total_count=len(papers),
            query=query,
            source=PaperSource.CLINICALTRIALS,
            search_time_ms=round(elapsed, 1),
        )

    def search_allergy(
        self,
        allergen: str,
        max_results: int = 20,
    ) -> PaperSearchResult:
        """알러지 관련 임상시험 검색

        Args:
            allergen: 알러젠 이름 (예: "peanut")
            max_results: 최대 결과 수
        """
        query = f"{allergen} allergy OR {allergen} hypersensitivity"
        return self.search(query, max_results=max_results)

    def search_recruiting(
        self,
        query: str,
        max_results: int = 20,
    ) -> PaperSearchResult:
        """모집 중인 임상시험 검색

        Args:
            query: 검색 쿼리
            max_results: 최대 결과 수
        """
        return self.search(
            query,
            max_results=max_results,
            status_filter=["RECRUITING", "NOT_YET_RECRUITING"],
        )

    def get_study(self, nct_id: str) -> Optional[Paper]:
        """NCT 번호로 임상시험 조회

        Args:
            nct_id: NCT 번호 (예: "NCT12345678")

        Returns:
            Paper 또는 None
        """
        client = self._get_client()
        try:
            self._wait_for_rate_limit()

            resp = client.get(
                f"{self.BASE_URL}/{nct_id}",
                params={"format": "json"},
            )
            resp.raise_for_status()
            data = resp.json()

            return self._parse_study(data)

        except Exception as e:
            logger.warning(f"ClinicalTrials.gov 조회 실패 ({nct_id}): {e}")

        return None

    def _parse_study(self, study: dict) -> Optional[Paper]:
        """API 결과를 Paper 모델로 변환"""
        protocol = study.get("protocolSection", {})
        if not protocol:
            return None

        # 식별 정보
        id_module = protocol.get("identificationModule", {})
        nct_id = id_module.get("nctId", "")
        title = (
            id_module.get("briefTitle")
            or id_module.get("officialTitle", "")
        ).strip()
        if not title:
            return None

        # 요약
        desc_module = protocol.get("descriptionModule", {})
        brief_summary = desc_module.get("briefSummary", "")

        # 상태/단계 정보
        status_module = protocol.get("statusModule", {})
        overall_status = status_module.get("overallStatus", "")
        start_date = status_module.get("startDateStruct", {}).get("date", "")

        design_module = protocol.get("designModule", {})
        phases = design_module.get("phases", [])
        phase_str = ", ".join(phases) if phases else ""
        enrollment_info = design_module.get("enrollmentInfo", {})
        enrollment = enrollment_info.get("count")

        # 질환/중재
        conditions_module = protocol.get("conditionsModule", {})
        conditions = conditions_module.get("conditions", [])

        interventions_module = protocol.get("armsInterventionsModule", {})
        interventions = []
        for intervention in interventions_module.get("interventions", []):
            name = intervention.get("name", "")
            if name:
                interventions.append(name)

        # 스폰서 → 저자 매핑
        sponsor_module = protocol.get("sponsorCollaboratorsModule", {})
        authors = []
        lead_sponsor = sponsor_module.get("leadSponsor", {})
        if lead_sponsor.get("name"):
            authors.append(lead_sponsor["name"])
        for collaborator in sponsor_module.get("collaborators", [])[:9]:
            if collaborator.get("name"):
                authors.append(collaborator["name"])

        # 연도 파싱
        year = None
        if start_date:
            try:
                year = int(start_date.split("-")[0])
            except (ValueError, IndexError):
                pass

        # 초록 구성: 요약 + 메타정보
        abstract_parts = []
        if brief_summary:
            abstract_parts.append(brief_summary)
        if conditions:
            abstract_parts.append(f"Conditions: {', '.join(conditions)}")
        if interventions:
            abstract_parts.append(f"Interventions: {', '.join(interventions)}")
        if overall_status:
            abstract_parts.append(f"Status: {overall_status}")
        if phase_str:
            abstract_parts.append(f"Phase: {phase_str}")
        if enrollment is not None:
            abstract_parts.append(f"Enrollment: {enrollment}")

        abstract = "\n".join(abstract_parts)

        # 키워드: 질환 + 중재
        keywords = conditions[:5] + interventions[:5]

        return Paper(
            title=title,
            abstract=abstract,
            authors=authors,
            source=PaperSource.CLINICALTRIALS,
            source_id=nct_id,
            doi=None,
            year=year,
            journal=f"ClinicalTrials.gov ({phase_str})" if phase_str else "ClinicalTrials.gov",
            citation_count=None,
            pdf_url=f"https://clinicaltrials.gov/study/{nct_id}",
            keywords=keywords,
        )

    def close(self):
        """리소스 정리"""
        if self._client:
            self._client.close()
            self._client = None
