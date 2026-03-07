"""스케줄러 단위 테스트

- 알레르겐 로테이션 로직
- SchedulerService 생명주기
- Job 함수 mock 테스트
- Ollama 서비스 mock 테스트
"""
import os
import sys

os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["TESTING"] = "1"

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from collections import Counter
from unittest.mock import patch, MagicMock


# ============================================================================
# 알레르겐 로테이션 테스트
# ============================================================================

class TestAllergenRotation:
    """get_allergens_for_day() 결정적 로테이션 로직 검증"""

    def test_deterministic(self):
        """같은 day_number는 항상 같은 결과"""
        from app.services.scheduler_jobs import get_allergens_for_day

        result1 = get_allergens_for_day(100)
        result2 = get_allergens_for_day(100)
        assert result1 == result2

    def test_returns_list(self):
        """결과가 리스트"""
        from app.services.scheduler_jobs import get_allergens_for_day

        result = get_allergens_for_day(0)
        assert isinstance(result, list)
        assert len(result) > 0

    def test_tier1_every_2_days(self):
        """Tier 1 알레르겐은 매 2일 주기로 등장"""
        from app.services.scheduler_jobs import get_allergens_for_day, ALLERGEN_TIERS

        tier1 = ALLERGEN_TIERS[2]
        # 30일간 시뮬레이션
        counts = Counter()
        for day in range(30):
            allergens = get_allergens_for_day(day)
            for a in allergens:
                if a in tier1:
                    counts[a] += 1

        # Tier 1은 매 2일이므로 30일 중 ~15회 등장
        for allergen in tier1:
            assert counts[allergen] >= 13, f"{allergen}: {counts[allergen]}회 (expected ~15)"
            assert counts[allergen] <= 17

    def test_tier2_every_3_days(self):
        """Tier 2 알레르겐은 매 3일 주기로 등장"""
        from app.services.scheduler_jobs import get_allergens_for_day, ALLERGEN_TIERS

        tier2 = ALLERGEN_TIERS[3]
        counts = Counter()
        for day in range(30):
            allergens = get_allergens_for_day(day)
            for a in allergens:
                if a in tier2:
                    counts[a] += 1

        # Tier 2는 매 3일이므로 30일 중 ~10회 등장
        for allergen in tier2:
            assert counts[allergen] >= 8, f"{allergen}: {counts[allergen]}회 (expected ~10)"
            assert counts[allergen] <= 12

    def test_tier3_every_4_days(self):
        """Tier 3 알레르겐은 매 4일 주기로 등장"""
        from app.services.scheduler_jobs import get_allergens_for_day, ALLERGEN_TIERS

        tier3 = ALLERGEN_TIERS[4]
        counts = Counter()
        for day in range(40):
            allergens = get_allergens_for_day(day)
            for a in allergens:
                if a in tier3:
                    counts[a] += 1

        # Tier 3는 매 4일이므로 40일 중 ~10회 등장
        for allergen in tier3:
            assert counts[allergen] >= 8, f"{allergen}: {counts[allergen]}회 (expected ~10)"
            assert counts[allergen] <= 12

    def test_all_allergens_covered(self):
        """전체 알레르겐이 일정 기간 내에 모두 커버됨"""
        from app.services.scheduler_jobs import get_allergens_for_day, ALLERGEN_TIERS

        all_allergens = set()
        for tier_list in ALLERGEN_TIERS.values():
            all_allergens.update(tier_list)

        covered = set()
        for day in range(12):  # 최대 주기 4일의 3배
            covered.update(get_allergens_for_day(day))

        assert covered == all_allergens, f"미커버: {all_allergens - covered}"

    def test_daily_count_reasonable(self):
        """일평균 ~5종, 최소 2종 이상"""
        from app.services.scheduler_jobs import get_allergens_for_day

        total = 0
        for day in range(30):
            count = len(get_allergens_for_day(day))
            total += count
            assert count >= 2, f"Day {day}: {count}종 (너무 적음)"

        avg = total / 30
        assert 3 <= avg <= 8, f"일평균 {avg:.1f}종 (expected 3~8)"


# ============================================================================
# SchedulerService 생명주기 테스트
# ============================================================================

class TestSchedulerService:
    """SchedulerService 시작/종료/상태 조회"""

    def test_create_and_start(self):
        """서비스 생성 및 시작"""
        from app.services.scheduler_service import SchedulerService

        service = SchedulerService()
        assert not service._scheduler.running

        service.start()
        assert service._scheduler.running

        service.shutdown()
        assert not service._scheduler.running

    def test_get_status(self):
        """상태 조회"""
        from app.services.scheduler_service import SchedulerService

        service = SchedulerService()
        service.start()

        try:
            status = service.get_status()
            assert status["running"] is True
            assert status["job_count"] == 5
            assert "Asia/Seoul" in status["timezone"]
        finally:
            service.shutdown()

    def test_get_jobs(self):
        """Job 목록 조회"""
        from app.services.scheduler_service import SchedulerService

        service = SchedulerService()
        service.start()

        try:
            jobs = service.get_jobs()
            assert len(jobs) == 5

            job_ids = {j["id"] for j in jobs}
            assert job_ids == {
                "daily_paper_search",
                "newsletter_sync",
                "korean_translation",
                "news_pipeline",
                "newsletter_send",
            }

            for job in jobs:
                assert "next_run_time" in job
                assert "paused" in job
        finally:
            service.shutdown()

    def test_pause_and_resume_job(self):
        """Job 일시중지 및 재개"""
        from app.services.scheduler_service import SchedulerService

        service = SchedulerService()
        service.start()

        try:
            assert service.pause_job("daily_paper_search")

            jobs = service.get_jobs()
            paper_job = next(j for j in jobs if j["id"] == "daily_paper_search")
            assert paper_job["paused"] is True

            assert service.resume_job("daily_paper_search")

            jobs = service.get_jobs()
            paper_job = next(j for j in jobs if j["id"] == "daily_paper_search")
            assert paper_job["paused"] is False
        finally:
            service.shutdown()

    def test_pause_nonexistent_job(self):
        """존재하지 않는 Job 일시중지 시도"""
        from app.services.scheduler_service import SchedulerService

        service = SchedulerService()
        service.start()

        try:
            assert service.pause_job("nonexistent_job") is False
        finally:
            service.shutdown()


# ============================================================================
# Job 함수 mock 테스트
# ============================================================================

class TestJobFunctions:
    """Job 함수가 서비스를 올바르게 호출하는지 검증"""

    @patch("app.services.scheduler_jobs.SessionLocal")
    def test_daily_paper_search_calls_service(self, mock_session_local):
        """daily_paper_search가 PaperSearchService.search_allergy()를 호출"""
        from app.services.scheduler_jobs import job_daily_paper_search

        mock_db = MagicMock()
        mock_session_local.return_value = mock_db

        mock_service = MagicMock()
        mock_result = MagicMock()
        mock_result.total_unique = 5
        mock_service.search_allergy.return_value = mock_result

        with patch("app.services.paper_search_service.PaperSearchService", return_value=mock_service):
            job_daily_paper_search("manual")

        assert mock_service.search_allergy.called
        mock_service.close.assert_called_once()
        mock_db.close.assert_called_once()

    @patch("app.services.scheduler_jobs.SessionLocal")
    def test_news_pipeline_calls_service(self, mock_session_local):
        """news_pipeline이 NewsPipelineService.run_collection_pipeline()을 호출"""
        from app.services.scheduler_jobs import job_news_pipeline

        mock_db = MagicMock()
        mock_session_local.return_value = mock_db

        mock_pipeline = MagicMock()
        mock_pipeline.run_collection_pipeline.return_value = {
            "collected": 3,
            "duplicates": 1,
            "analyzed": 2,
        }

        with patch(
            "app.services.news_pipeline_service.NewsPipelineService",
            return_value=mock_pipeline,
        ):
            job_news_pipeline("manual")

        mock_pipeline.run_collection_pipeline.assert_called_once()
        mock_pipeline.close.assert_called_once()
        mock_db.close.assert_called_once()

    @patch("app.services.scheduler_jobs.SessionLocal")
    def test_newsletter_send_calls_service(self, mock_session_local):
        """newsletter_send가 NewsletterService.send_to_subscribers()를 호출"""
        from app.services.scheduler_jobs import job_newsletter_send

        mock_db = MagicMock()
        mock_session_local.return_value = mock_db

        mock_service = MagicMock()
        mock_service.send_to_subscribers.return_value = {
            "message": "발송 완료",
            "sent_count": 5,
            "failed_count": 0,
        }

        with patch(
            "app.services.newsletter_service.NewsletterService",
            return_value=mock_service,
        ):
            job_newsletter_send("manual")

        mock_service.send_to_subscribers.assert_called_once()
        mock_db.close.assert_called_once()


# ============================================================================
# Ollama 서비스 mock 테스트
# ============================================================================

class TestOllamaService:
    """Ollama 번역 서비스 테스트"""

    @patch("app.services.ollama_service.requests.get")
    def test_check_available_success(self, mock_get):
        """Ollama 서버 사용 가능"""
        from app.services.ollama_service import check_ollama_available

        mock_get.return_value = MagicMock(
            status_code=200,
            json=lambda: {"models": [{"name": "gemma2:9b"}]},
        )

        assert check_ollama_available("gemma2:9b") is True

    @patch("app.services.ollama_service.requests.get")
    def test_check_available_no_model(self, mock_get):
        """모델이 설치되지 않은 경우"""
        from app.services.ollama_service import check_ollama_available

        mock_get.return_value = MagicMock(
            status_code=200,
            json=lambda: {"models": [{"name": "llama2:7b"}]},
        )

        assert check_ollama_available("gemma2:9b") is False

    @patch("app.services.ollama_service.requests.get")
    def test_check_available_connection_error(self, mock_get):
        """서버 접근 불가"""
        from app.services.ollama_service import check_ollama_available
        import requests

        mock_get.side_effect = requests.ConnectionError()

        assert check_ollama_available() is False

    @patch("app.services.ollama_service.requests.post")
    def test_translate_success(self, mock_post):
        """번역 성공"""
        from app.services.ollama_service import ollama_translate

        mock_post.return_value = MagicMock(
            status_code=200,
            json=lambda: {"response": "알레르기 면역 치료"},
        )

        result = ollama_translate("Allergy immunotherapy")
        assert result == "알레르기 면역 치료"

    @patch("app.services.ollama_service.requests.post")
    def test_translate_empty_text(self, mock_post):
        """빈 텍스트 번역"""
        from app.services.ollama_service import ollama_translate

        result = ollama_translate("")
        assert result is None
        mock_post.assert_not_called()

    @patch("app.services.ollama_service.requests.post")
    def test_translate_timeout(self, mock_post):
        """타임아웃 시 None 반환"""
        from app.services.ollama_service import ollama_translate
        import requests

        mock_post.side_effect = requests.Timeout()

        result = ollama_translate("Some text")
        assert result is None

    @patch("app.services.ollama_service.requests.post")
    def test_translate_api_error(self, mock_post):
        """API 오류 시 None 반환"""
        from app.services.ollama_service import ollama_translate

        mock_post.return_value = MagicMock(status_code=500)

        result = ollama_translate("Some text")
        assert result is None
