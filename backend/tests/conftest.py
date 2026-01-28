"""Pytest Configuration and Fixtures

이 파일은 모든 테스트에서 공유되는 fixtures를 정의합니다.

IMPORTANT: Environment variables must be set before any app imports.
"""
import os
import sys

# FIRST: Set environment variable to use SQLite before any imports
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["TESTING"] = "1"

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from typing import Generator
from datetime import datetime
from unittest.mock import MagicMock

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from fastapi.testclient import TestClient

from app.database.connection import Base, get_db
from app.database.models import User, DiagnosisKit, UserDiagnosis
from app.api.main import app
from app.auth.jwt_handler import create_access_token


# ============================================================================
# Database Fixtures
# ============================================================================

@pytest.fixture(scope="function")
def test_db() -> Generator[Session, None, None]:
    """Create a fresh test database for each test function.

    Uses SQLite in-memory database for fast tests.
    """
    # Create in-memory SQLite database
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    # Create all tables
    Base.metadata.create_all(bind=engine)

    # Create session
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestingSessionLocal()

    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(test_db: Session) -> Generator[TestClient, None, None]:
    """Create a test client with test database override.

    This fixture overrides the database dependency to use the test database.
    """
    def override_get_db():
        try:
            yield test_db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


# ============================================================================
# User Fixtures
# ============================================================================

@pytest.fixture
def test_user(test_db: Session) -> User:
    """Create a test user.

    Returns:
        User: A test user with 'simple' auth type.
    """
    import bcrypt

    user = User(
        name="테스트유저",
        phone="010-1234-5678",
        auth_type="simple",
        access_pin_hash=bcrypt.hashpw("123456".encode(), bcrypt.gensalt()).decode(),
        role="user",
        created_at=datetime.utcnow(),
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user


@pytest.fixture
def admin_user(test_db: Session) -> User:
    """Create a test admin user.

    Returns:
        User: A test user with admin role.
    """
    import bcrypt

    user = User(
        name="관리자",
        phone="010-9999-9999",
        auth_type="simple",
        access_pin_hash=bcrypt.hashpw("654321".encode(), bcrypt.gensalt()).decode(),
        role="admin",
        created_at=datetime.utcnow(),
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user


@pytest.fixture
def doctor_user(test_db: Session) -> User:
    """Create a test doctor user.

    Returns:
        User: A test user with doctor role.
    """
    import bcrypt

    user = User(
        name="의사",
        phone="010-8888-8888",
        auth_type="simple",
        access_pin_hash=bcrypt.hashpw("111111".encode(), bcrypt.gensalt()).decode(),
        role="doctor",
        created_at=datetime.utcnow(),
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user


# ============================================================================
# Auth Token Fixtures
# ============================================================================

@pytest.fixture
def user_token(test_user: User) -> str:
    """Create a JWT token for the test user.

    Returns:
        str: JWT access token.
    """
    return create_access_token(
        data={"sub": str(test_user.id), "auth_type": "simple"}
    )


@pytest.fixture
def admin_token(admin_user: User) -> str:
    """Create a JWT token for the admin user.

    Returns:
        str: JWT access token.
    """
    return create_access_token(
        data={"sub": str(admin_user.id), "auth_type": "simple"}
    )


@pytest.fixture
def doctor_token(doctor_user: User) -> str:
    """Create a JWT token for the doctor user.

    Returns:
        str: JWT access token.
    """
    return create_access_token(
        data={"sub": str(doctor_user.id), "auth_type": "simple"}
    )


@pytest.fixture
def auth_headers(user_token: str) -> dict:
    """Create authorization headers with user token.

    Returns:
        dict: Headers dictionary with Authorization header.
    """
    return {"Authorization": f"Bearer {user_token}"}


@pytest.fixture
def admin_headers(admin_token: str) -> dict:
    """Create authorization headers with admin token.

    Returns:
        dict: Headers dictionary with Authorization header.
    """
    return {"Authorization": f"Bearer {admin_token}"}


# ============================================================================
# Diagnosis Kit Fixtures
# ============================================================================

@pytest.fixture
def test_kit(test_db: Session) -> DiagnosisKit:
    """Create a test diagnosis kit.

    Returns:
        DiagnosisKit: An unregistered test kit.
    """
    import bcrypt

    kit = DiagnosisKit(
        serial_number="TEST-KIT-001",
        pin_hash=bcrypt.hashpw("1234".encode(), bcrypt.gensalt()).decode(),
        results={
            "peanut": 4,
            "milk": 2,
            "egg": 1,
            "wheat": 0,
            "shrimp": 3,
        },
        diagnosis_date=datetime.utcnow(),
        is_registered=False,
        pin_attempts=0,
    )
    test_db.add(kit)
    test_db.commit()
    test_db.refresh(kit)
    return kit


@pytest.fixture
def registered_kit(test_db: Session, test_user: User) -> DiagnosisKit:
    """Create a registered diagnosis kit.

    Returns:
        DiagnosisKit: A kit registered to the test user.
    """
    import bcrypt

    kit = DiagnosisKit(
        serial_number="TEST-KIT-002",
        pin_hash=bcrypt.hashpw("5678".encode(), bcrypt.gensalt()).decode(),
        results={
            "peanut": 5,
            "milk": 3,
            "egg": 2,
            "wheat": 1,
            "shrimp": 4,
        },
        diagnosis_date=datetime.utcnow(),
        is_registered=True,
        registered_user_id=test_user.id,
        registered_at=datetime.utcnow(),
        pin_attempts=0,
    )
    test_db.add(kit)
    test_db.commit()
    test_db.refresh(kit)
    return kit


# ============================================================================
# Diagnosis Fixtures
# ============================================================================

@pytest.fixture
def test_diagnosis(test_db: Session, test_user: User, registered_kit: DiagnosisKit) -> UserDiagnosis:
    """Create a test diagnosis record.

    Returns:
        UserDiagnosis: A diagnosis record linked to the test user.
    """
    diagnosis = UserDiagnosis(
        user_id=test_user.id,
        kit_id=registered_kit.id,
        results=registered_kit.results,
        diagnosis_date=registered_kit.diagnosis_date,
        created_at=datetime.utcnow(),
    )
    test_db.add(diagnosis)
    test_db.commit()
    test_db.refresh(diagnosis)
    return diagnosis


# ============================================================================
# Sample Data Fixtures
# ============================================================================

@pytest.fixture
def sample_diagnosis_results() -> list:
    """Sample diagnosis results for testing.

    Returns:
        list: List of diagnosis result items.
    """
    return [
        {"allergen": "peanut", "grade": 4},
        {"allergen": "milk", "grade": 2},
        {"allergen": "egg", "grade": 1},
        {"allergen": "wheat", "grade": 0},
        {"allergen": "shrimp", "grade": 3},
        {"allergen": "crab", "grade": 3},
        {"allergen": "soy", "grade": 1},
    ]


@pytest.fixture
def high_risk_diagnosis_results() -> list:
    """High-risk diagnosis results for testing severe cases.

    Returns:
        list: List of diagnosis result items with high grades.
    """
    return [
        {"allergen": "peanut", "grade": 6},
        {"allergen": "shrimp", "grade": 5},
        {"allergen": "crab", "grade": 5},
        {"allergen": "milk", "grade": 4},
    ]


# ============================================================================
# Mock Fixtures
# ============================================================================

@pytest.fixture
def mock_paper_search_service():
    """Mock PaperSearchService for testing without external API calls."""
    mock_service = MagicMock()
    mock_service.search_allergy.return_value = MagicMock(
        query="test allergy",
        total_unique=10,
        pubmed_count=5,
        semantic_scholar_count=5,
        downloadable_count=3,
        search_time_ms=100.0,
        papers=[],
    )
    return mock_service
