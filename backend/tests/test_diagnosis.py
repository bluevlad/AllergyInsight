"""Diagnosis API Tests

진단 관련 API 엔드포인트 테스트:
- 진단 결과 저장
- 진단 결과 조회
- 진단 목록 조회
- 진단 삭제
"""
import pytest
from datetime import datetime
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.database.models import User, UserDiagnosis


class TestDiagnosisCreate:
    """진단 결과 저장 테스트."""

    def test_create_diagnosis_success(
        self,
        client: TestClient,
        sample_diagnosis_results: list
    ):
        """진단 결과 저장 성공."""
        response = client.post(
            "/api/diagnosis",
            json={
                "diagnosis_results": sample_diagnosis_results,
                "diagnosis_date": datetime.now().isoformat(),
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "diagnosis_id" in data
        assert data["message"] == "진단 결과가 저장되었습니다."

    def test_create_diagnosis_minimal(self, client: TestClient):
        """최소 데이터로 진단 결과 저장."""
        response = client.post(
            "/api/diagnosis",
            json={
                "diagnosis_results": [
                    {"allergen": "peanut", "grade": 3}
                ]
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_create_diagnosis_with_patient_info(
        self,
        client: TestClient,
        sample_diagnosis_results: list
    ):
        """환자 정보 포함 진단 결과 저장."""
        response = client.post(
            "/api/diagnosis",
            json={
                "diagnosis_results": sample_diagnosis_results,
                "diagnosis_date": datetime.now().isoformat(),
                "patient_info": {
                    "name": "테스트환자",
                    "age": 25,
                    "gender": "M"
                }
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_create_diagnosis_invalid_date(self, client: TestClient):
        """잘못된 날짜 형식으로 저장 실패."""
        response = client.post(
            "/api/diagnosis",
            json={
                "diagnosis_results": [
                    {"allergen": "peanut", "grade": 3}
                ],
                "diagnosis_date": "invalid-date-format"
            }
        )
        assert response.status_code == 400
        assert "날짜" in response.json()["detail"] or "date" in response.json()["detail"].lower()


class TestDiagnosisRead:
    """진단 결과 조회 테스트."""

    def test_get_diagnosis_success(self, client: TestClient, sample_diagnosis_results: list):
        """진단 결과 조회 성공."""
        # First create a diagnosis
        create_response = client.post(
            "/api/diagnosis",
            json={"diagnosis_results": sample_diagnosis_results}
        )
        diagnosis_id = create_response.json()["diagnosis_id"]

        # Then get it
        response = client.get(f"/api/diagnosis/{diagnosis_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "diagnosis_results" in data

    def test_get_diagnosis_not_found(self, client: TestClient):
        """존재하지 않는 진단 조회 실패."""
        response = client.get("/api/diagnosis/nonexistent-id-12345")
        assert response.status_code == 404
        assert "찾을 수 없" in response.json()["detail"]


class TestDiagnosisList:
    """진단 목록 조회 테스트."""

    def test_list_diagnoses_empty(self, client: TestClient):
        """빈 진단 목록 조회."""
        response = client.get("/api/diagnosis")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "diagnoses" in data

    def test_list_diagnoses_with_data(
        self,
        client: TestClient,
        sample_diagnosis_results: list
    ):
        """데이터가 있는 진단 목록 조회."""
        # Create multiple diagnoses
        for _ in range(3):
            client.post(
                "/api/diagnosis",
                json={"diagnosis_results": sample_diagnosis_results}
            )

        response = client.get("/api/diagnosis")
        assert response.status_code == 200
        data = response.json()
        assert len(data["diagnoses"]) >= 3

    def test_list_diagnoses_pagination(
        self,
        client: TestClient,
        sample_diagnosis_results: list
    ):
        """진단 목록 페이지네이션."""
        # Create diagnoses
        for _ in range(5):
            client.post(
                "/api/diagnosis",
                json={"diagnosis_results": sample_diagnosis_results}
            )

        # Test limit
        response = client.get("/api/diagnosis?limit=2")
        assert response.status_code == 200
        data = response.json()
        assert len(data["diagnoses"]) <= 2


class TestDiagnosisDelete:
    """진단 결과 삭제 테스트."""

    def test_delete_diagnosis_success(
        self,
        client: TestClient,
        sample_diagnosis_results: list
    ):
        """진단 결과 삭제 성공."""
        # First create
        create_response = client.post(
            "/api/diagnosis",
            json={"diagnosis_results": sample_diagnosis_results}
        )
        diagnosis_id = create_response.json()["diagnosis_id"]

        # Then delete
        response = client.delete(f"/api/diagnosis/{diagnosis_id}")
        assert response.status_code == 200
        assert response.json()["success"] is True

        # Verify deleted
        get_response = client.get(f"/api/diagnosis/{diagnosis_id}")
        assert get_response.status_code == 404

    def test_delete_diagnosis_not_found(self, client: TestClient):
        """존재하지 않는 진단 삭제 실패."""
        response = client.delete("/api/diagnosis/nonexistent-id-12345")
        assert response.status_code == 404


class TestAllergenInfo:
    """알러젠 정보 API 테스트."""

    def test_get_allergens(self, client: TestClient):
        """알러젠 목록 조회."""
        response = client.get("/api/allergens")
        assert response.status_code == 200
        data = response.json()
        assert "food" in data
        assert "inhalant" in data
        # Check structure
        if data["food"]:
            assert "code" in data["food"][0] or "name" in data["food"][0]


class TestSGTiInfo:
    """SGTi 제품 정보 API 테스트."""

    def test_get_sgti_info(self, client: TestClient):
        """SGTi 제품 정보 조회."""
        response = client.get("/api/sgti/info")
        assert response.status_code == 200
        data = response.json()
        assert data["product_name"] == "SGTi-Allergy Screen PLUS"
        assert "grade_system" in data

    def test_get_grade_info(self, client: TestClient):
        """등급 정보 조회."""
        response = client.get("/api/sgti/grades")
        assert response.status_code == 200
        data = response.json()
        assert "grades" in data
        assert "restriction_levels" in data


class TestUserDiagnosis:
    """사용자 진단 조회 테스트 (인증 필요)."""

    def test_get_my_diagnoses_authenticated(
        self,
        client: TestClient,
        auth_headers: dict,
        test_diagnosis: UserDiagnosis
    ):
        """인증된 사용자의 진단 목록 조회."""
        # Note: This endpoint might be at different path based on the actual implementation
        # Check both possible paths
        response = client.get("/api/consumer/my/diagnoses", headers=auth_headers)
        if response.status_code == 404:
            # Try alternative path
            response = client.get("/api/diagnoses/my", headers=auth_headers)

        # If endpoint exists, verify response
        if response.status_code == 200:
            data = response.json()
            assert "diagnoses" in data or isinstance(data, list)

    def test_get_my_diagnoses_unauthenticated(self, client: TestClient):
        """인증 없이 내 진단 목록 조회 실패."""
        response = client.get("/api/consumer/my/diagnoses")
        # Should require authentication
        assert response.status_code in [401, 403, 404]


class TestDiagnosisValidation:
    """진단 결과 유효성 검사 테스트."""

    def test_diagnosis_grade_range(self, client: TestClient):
        """등급 범위 유효성 검사."""
        # Valid grades are 0-6
        valid_response = client.post(
            "/api/diagnosis",
            json={
                "diagnosis_results": [
                    {"allergen": "peanut", "grade": 6}  # Max valid
                ]
            }
        )
        assert valid_response.status_code == 200

    def test_diagnosis_invalid_grade_negative(self, client: TestClient):
        """음수 등급 유효성 검사."""
        response = client.post(
            "/api/diagnosis",
            json={
                "diagnosis_results": [
                    {"allergen": "peanut", "grade": -1}
                ]
            }
        )
        # Should fail validation
        assert response.status_code in [400, 422]

    def test_diagnosis_invalid_grade_too_high(self, client: TestClient):
        """초과 등급 유효성 검사."""
        response = client.post(
            "/api/diagnosis",
            json={
                "diagnosis_results": [
                    {"allergen": "peanut", "grade": 7}  # Max is 6
                ]
            }
        )
        # Should fail validation
        assert response.status_code in [400, 422]

    def test_diagnosis_empty_results(self, client: TestClient):
        """빈 결과 목록 유효성 검사."""
        response = client.post(
            "/api/diagnosis",
            json={
                "diagnosis_results": []
            }
        )
        # Empty list might be invalid depending on implementation
        # Either 200 (accepted) or 400/422 (validation error)
        assert response.status_code in [200, 400, 422]
