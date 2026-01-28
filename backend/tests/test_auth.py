"""Authentication API Tests

인증 관련 API 엔드포인트 테스트:
- 간편 로그인/회원가입
- 현재 사용자 조회
- 키트 등록
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.database.models import User, DiagnosisKit


class TestHealthCheck:
    """Health check endpoint tests."""

    def test_health_check(self, client: TestClient):
        """GET /api/health returns healthy status."""
        response = client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data

    def test_root_endpoint(self, client: TestClient):
        """GET / returns API info."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "AllergyInsight API"
        assert "version" in data


class TestSimpleLogin:
    """Simple login (name + phone + PIN) tests."""

    def test_login_success(self, client: TestClient, test_user: User):
        """로그인 성공 테스트."""
        response = client.post(
            "/api/auth/simple/login",
            json={
                "name": test_user.name,
                "phone": test_user.phone,
                "access_pin": "123456",
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["user"]["name"] == test_user.name

    def test_login_wrong_pin(self, client: TestClient, test_user: User):
        """잘못된 PIN으로 로그인 실패."""
        response = client.post(
            "/api/auth/simple/login",
            json={
                "name": test_user.name,
                "phone": test_user.phone,
                "access_pin": "000000",  # Wrong PIN
            }
        )
        assert response.status_code == 401
        assert "Invalid access PIN" in response.json()["detail"]

    def test_login_user_not_found(self, client: TestClient):
        """존재하지 않는 사용자 로그인 실패."""
        response = client.post(
            "/api/auth/simple/login",
            json={
                "name": "존재하지않는유저",
                "phone": "010-0000-0000",
                "access_pin": "123456",
            }
        )
        assert response.status_code == 404
        assert "User not found" in response.json()["detail"]


class TestSimpleRegister:
    """Simple registration (name + phone + kit) tests."""

    def test_register_success(self, client: TestClient, test_kit: DiagnosisKit, test_db: Session):
        """회원가입 성공 테스트."""
        response = client.post(
            "/api/auth/simple/register",
            json={
                "name": "새로운유저",
                "phone": "010-5555-5555",
                "serial_number": test_kit.serial_number,
                "pin": "1234",
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "access_pin" in data
        assert data["user"]["name"] == "새로운유저"
        assert len(data["access_pin"]) == 6  # 6자리 PIN

    def test_register_kit_not_found(self, client: TestClient):
        """존재하지 않는 키트로 회원가입 실패."""
        response = client.post(
            "/api/auth/simple/register",
            json={
                "name": "새로운유저",
                "phone": "010-5555-5555",
                "serial_number": "NONEXISTENT-KIT",
                "pin": "1234",
            }
        )
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_register_wrong_pin(self, client: TestClient, test_kit: DiagnosisKit):
        """잘못된 키트 PIN으로 회원가입 실패."""
        response = client.post(
            "/api/auth/simple/register",
            json={
                "name": "새로운유저",
                "phone": "010-5555-5555",
                "serial_number": test_kit.serial_number,
                "pin": "9999",  # Wrong PIN
            }
        )
        assert response.status_code == 401
        assert "Invalid PIN" in response.json()["detail"]

    def test_register_already_registered_kit(self, client: TestClient, registered_kit: DiagnosisKit):
        """이미 등록된 키트로 회원가입 실패."""
        response = client.post(
            "/api/auth/simple/register",
            json={
                "name": "새로운유저",
                "phone": "010-5555-5555",
                "serial_number": registered_kit.serial_number,
                "pin": "5678",
            }
        )
        assert response.status_code == 400
        assert "already registered" in response.json()["detail"].lower()


class TestCurrentUser:
    """Current user endpoint tests."""

    def test_get_me_authenticated(self, client: TestClient, auth_headers: dict, test_user: User):
        """인증된 사용자 정보 조회."""
        response = client.get("/api/auth/me", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_user.id
        assert data["name"] == test_user.name

    def test_get_me_unauthenticated(self, client: TestClient):
        """인증 없이 사용자 정보 조회 실패."""
        response = client.get("/api/auth/me")
        assert response.status_code in [401, 403]

    def test_get_me_invalid_token(self, client: TestClient):
        """잘못된 토큰으로 사용자 정보 조회 실패."""
        headers = {"Authorization": "Bearer invalid_token_here"}
        response = client.get("/api/auth/me", headers=headers)
        assert response.status_code in [401, 403]


class TestKitRegistration:
    """Kit registration for logged-in users."""

    def test_register_kit_authenticated(
        self,
        client: TestClient,
        auth_headers: dict,
        test_kit: DiagnosisKit,
        test_db: Session
    ):
        """로그인 사용자의 키트 등록 성공."""
        response = client.post(
            "/api/auth/register-kit",
            json={
                "serial_number": test_kit.serial_number,
                "pin": "1234",
            },
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["kit_serial"] == test_kit.serial_number
        assert "results" in data

    def test_register_kit_unauthenticated(self, client: TestClient, test_kit: DiagnosisKit):
        """인증 없이 키트 등록 실패."""
        response = client.post(
            "/api/auth/register-kit",
            json={
                "serial_number": test_kit.serial_number,
                "pin": "1234",
            }
        )
        assert response.status_code in [401, 403]

    def test_register_kit_wrong_pin(
        self,
        client: TestClient,
        auth_headers: dict,
        test_kit: DiagnosisKit
    ):
        """잘못된 PIN으로 키트 등록 실패."""
        response = client.post(
            "/api/auth/register-kit",
            json={
                "serial_number": test_kit.serial_number,
                "pin": "9999",
            },
            headers=auth_headers
        )
        assert response.status_code == 401


class TestLogout:
    """Logout endpoint tests."""

    def test_logout_success(self, client: TestClient, auth_headers: dict):
        """로그아웃 성공."""
        response = client.post("/api/auth/logout", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "success" in data["message"].lower() or "logged out" in data["message"].lower()

    def test_logout_unauthenticated(self, client: TestClient):
        """인증 없이 로그아웃 실패."""
        response = client.post("/api/auth/logout")
        assert response.status_code in [401, 403]


class TestPinAttempts:
    """PIN attempt limit tests."""

    def test_pin_attempts_incremented_on_failure(
        self,
        client: TestClient,
        test_kit: DiagnosisKit,
        test_db: Session
    ):
        """잘못된 PIN 입력 시 시도 횟수 증가."""
        initial_attempts = test_kit.pin_attempts

        response = client.post(
            "/api/auth/simple/register",
            json={
                "name": "새로운유저",
                "phone": "010-5555-5555",
                "serial_number": test_kit.serial_number,
                "pin": "0000",  # Wrong PIN
            }
        )
        assert response.status_code == 401

        # Refresh from DB
        test_db.refresh(test_kit)
        assert test_kit.pin_attempts == initial_attempts + 1
