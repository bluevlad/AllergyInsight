"""Seed test diagnosis data for development/testing"""
from datetime import datetime, date
from dataclasses import asdict
from sqlalchemy.orm import Session
import bcrypt

from .connection import SessionLocal
from .models import User, DiagnosisKit, UserDiagnosis
from ..services.prescription_engine import PrescriptionEngine


def serialize_prescription(prescription):
    """Serialize prescription dataclass to dict, handling datetime objects"""
    def convert_value(obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, date):
            return obj.isoformat()
        elif hasattr(obj, '__dataclass_fields__'):
            return {k: convert_value(v) for k, v in asdict(obj).items()}
        elif isinstance(obj, list):
            return [convert_value(item) for item in obj]
        elif isinstance(obj, dict):
            return {k: convert_value(v) for k, v in obj.items()}
        elif hasattr(obj, 'value'):  # Enum
            return obj.value
        return obj

    return convert_value(prescription)


def hash_pin(pin: str) -> str:
    """Hash PIN using bcrypt"""
    return bcrypt.hashpw(pin.encode(), bcrypt.gensalt()).decode()


# Test diagnosis kit data
TEST_DIAGNOSIS_KIT = {
    "serial_number": "SGT-2024-TEST1-0001",
    "pin": "123456",
    "results": {
        # Food allergens (9 items)
        "peanut": 4,      # 땅콩 - 양성 (높음)
        "milk": 3,        # 우유 - 양성 (중등도)
        "egg": 2,         # 계란 - 양성 (경미)
        "wheat": 0,       # 밀 - 음성
        "soy": 1,         # 대두 - 양성 (약양성)
        "fish": 0,        # 생선 - 음성
        "shrimp": 5,      # 새우 - 양성 (매우 높음)
        "crab": 4,        # 게 - 양성 (높음)
        "buckwheat": 0,   # 메밀 - 음성
        # Inhalant allergens (7 items)
        "dust_mite": 3,   # 집먼지진드기 - 양성 (중등도)
        "cat": 0,         # 고양이 - 음성
        "dog": 1,         # 개 - 양성 (약양성)
        "cockroach": 0,   # 바퀴벌레 - 음성
        "mugwort": 2,     # 쑥 - 양성 (경미)
        "ragweed": 0,     # 돼지풀 - 음성
        "mold": 0,        # 곰팡이 - 음성
    },
    "diagnosis_date": date(2024, 12, 15),
}


def seed_diagnosis_data(db: Session = None):
    """Seed test diagnosis data for 김철수"""
    if db is None:
        db = SessionLocal()
        close_db = True
    else:
        close_db = False

    try:
        # Find 김철수 user
        user = db.query(User).filter(User.phone == "010-9999-8888").first()
        if not user:
            print("Error: 김철수 user not found. Run seed_users first.")
            return

        print(f"Found user: {user.name} (ID: {user.id})")

        # Check if test kit already exists
        existing_kit = db.query(DiagnosisKit).filter(
            DiagnosisKit.serial_number == TEST_DIAGNOSIS_KIT["serial_number"]
        ).first()

        if existing_kit:
            print(f"Test kit already exists: {existing_kit.serial_number}")
            kit = existing_kit
        else:
            # Create diagnosis kit
            kit = DiagnosisKit(
                serial_number=TEST_DIAGNOSIS_KIT["serial_number"],
                pin_hash=hash_pin(TEST_DIAGNOSIS_KIT["pin"]),
                results=TEST_DIAGNOSIS_KIT["results"],
                diagnosis_date=TEST_DIAGNOSIS_KIT["diagnosis_date"],
                is_registered=True,
                registered_user_id=user.id,
                registered_at=datetime.utcnow(),
                created_at=datetime.utcnow(),
            )
            db.add(kit)
            db.flush()
            print(f"Created diagnosis kit: {kit.serial_number}")

        # Check if diagnosis already exists for this user and kit
        existing_diagnosis = db.query(UserDiagnosis).filter(
            UserDiagnosis.user_id == user.id,
            UserDiagnosis.kit_id == kit.id
        ).first()

        if existing_diagnosis:
            print(f"Diagnosis already exists for {user.name}")
            diagnosis = existing_diagnosis
        else:
            # Generate prescription using prescription engine
            engine = PrescriptionEngine()
            diagnosis_list = [
                {"allergen": code, "grade": grade}
                for code, grade in TEST_DIAGNOSIS_KIT["results"].items()
            ]
            prescription = engine.generate_prescription(
                diagnosis_list,
                diagnosis_date=datetime.combine(
                    TEST_DIAGNOSIS_KIT["diagnosis_date"],
                    datetime.min.time()
                )
            )

            # Create user diagnosis
            diagnosis = UserDiagnosis(
                user_id=user.id,
                kit_id=kit.id,
                results=TEST_DIAGNOSIS_KIT["results"],
                diagnosis_date=TEST_DIAGNOSIS_KIT["diagnosis_date"],
                prescription=serialize_prescription(prescription),
                created_at=datetime.utcnow(),
            )
            db.add(diagnosis)
            print(f"Created user diagnosis for {user.name}")

        db.commit()

        # Print summary
        print("\n" + "="*50)
        print("Diagnosis Data Summary")
        print("="*50)
        print(f"User: {user.name} ({user.phone})")
        print(f"Kit: {kit.serial_number}")
        print(f"Date: {TEST_DIAGNOSIS_KIT['diagnosis_date']}")
        print("\nPositive Allergens:")

        positive_allergens = [
            (code, grade) for code, grade in TEST_DIAGNOSIS_KIT["results"].items()
            if grade > 0
        ]
        for code, grade in sorted(positive_allergens, key=lambda x: -x[1]):
            print(f"  - {code}: Grade {grade}")

        print("\n" + "="*50)
        print("Test Complete!")
        print(f"Login as: {user.phone} / PIN: 715302")
        print("Access URL: http://localhost:4040/app")
        print("="*50)

    except Exception as e:
        db.rollback()
        print(f"Error seeding diagnosis: {e}")
        import traceback
        traceback.print_exc()
        raise

    finally:
        if close_db:
            db.close()


if __name__ == "__main__":
    seed_diagnosis_data()
