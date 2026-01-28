"""Seed test users for development/testing"""
from datetime import datetime
from sqlalchemy.orm import Session
import bcrypt

from .connection import SessionLocal
from .models import User
from .organization_models import (
    Organization, OrganizationMember, OrganizationStatus,
    HospitalPatient, HospitalPatientStatus
)


def hash_pin(pin: str) -> str:
    """Hash PIN using bcrypt"""
    return bcrypt.hashpw(pin.encode(), bcrypt.gensalt()).decode()


# Test users matching README documentation
TEST_USERS = [
    {
        "name": "김철수",
        "phone": "010-9999-8888",
        "auth_type": "simple",
        "access_pin": "715302",
        "role": "user",
    },
    {
        "name": "관리자",
        "phone": "010-1111-2222",
        "auth_type": "simple",
        "access_pin": "123456",
        "role": "admin",
    },
    # Hospital staff test users (Phase 2)
    {
        "name": "이의사",
        "phone": "010-2222-3333",
        "auth_type": "simple",
        "access_pin": "111111",
        "role": "doctor",
    },
    {
        "name": "박간호",
        "phone": "010-3333-4444",
        "auth_type": "simple",
        "access_pin": "222222",
        "role": "nurse",
    },
    {
        "name": "최검사",
        "phone": "010-4444-5555",
        "auth_type": "simple",
        "access_pin": "333333",
        "role": "lab_tech",
    },
    {
        "name": "정병원장",
        "phone": "010-5555-6666",
        "auth_type": "simple",
        "access_pin": "444444",
        "role": "hospital_admin",
    },
]


def seed_users(db: Session = None):
    """Seed test users into database"""
    if db is None:
        db = SessionLocal()
        close_db = True
    else:
        close_db = False

    try:
        added = 0
        updated = 0
        for user_data in TEST_USERS:
            access_pin = user_data["access_pin"]
            access_pin_hash = hash_pin(access_pin)

            # Check if user already exists by phone
            existing = db.query(User).filter(
                User.phone == user_data["phone"]
            ).first()

            if existing:
                # Update existing user's PIN hash (fix invalid hash issue)
                existing.access_pin_hash = access_pin_hash
                existing.role = user_data["role"]
                updated += 1
                print(f"Updated user: {user_data['name']} ({user_data['phone']})")
                continue

            # Create user
            user = User(
                name=user_data["name"],
                phone=user_data["phone"],
                auth_type=user_data["auth_type"],
                access_pin_hash=access_pin_hash,
                role=user_data["role"],
                is_active=True,
                created_at=datetime.utcnow(),
            )
            db.add(user)
            added += 1
            print(f"Added user: {user_data['name']} ({user_data['role']})")

        db.commit()
        print(f"\nSeeded {added} users, updated {updated} users successfully!")

        # Create test organization and link hospital staff
        seed_organization(db)

    except Exception as e:
        db.rollback()
        print(f"Error seeding users: {e}")
        raise

    finally:
        if close_db:
            db.close()


def seed_organization(db: Session):
    """Seed test organization and link hospital staff"""
    # Check if test organization exists
    test_org = db.query(Organization).filter(
        Organization.business_number == "123-45-67890"
    ).first()

    if not test_org:
        test_org = Organization(
            name="테스트 병원",
            org_type="hospital",
            business_number="123-45-67890",
            license_number="의료-2024-001",
            address="서울시 강남구 테헤란로 123",
            phone="02-1234-5678",
            email="test@hospital.com",
            subscription_plan="professional",
            status=OrganizationStatus.ACTIVE,
        )
        db.add(test_org)
        db.flush()
        print(f"Created test organization: {test_org.name}")
    else:
        print(f"Test organization already exists: {test_org.name}")

    # Link hospital staff to organization
    hospital_roles = ["doctor", "nurse", "lab_tech", "hospital_admin"]
    staff_users = db.query(User).filter(User.role.in_(hospital_roles)).all()

    for staff in staff_users:
        existing_member = db.query(OrganizationMember).filter(
            OrganizationMember.organization_id == test_org.id,
            OrganizationMember.user_id == staff.id
        ).first()

        if not existing_member:
            member = OrganizationMember(
                organization_id=test_org.id,
                user_id=staff.id,
                role=staff.role,
                department="진료과" if staff.role == "doctor" else "일반",
                is_active=True,
            )
            db.add(member)
            print(f"  Linked {staff.name} ({staff.role}) to {test_org.name}")

    db.commit()
    print("Organization seeding completed!")

    # Seed hospital patients
    seed_hospital_patients(db, test_org)


def seed_hospital_patients(db: Session, organization: Organization):
    """Seed hospital patients linking regular users to the hospital"""
    # Find 김철수 (regular patient user)
    patient_user = db.query(User).filter(User.phone == "010-9999-8888").first()
    if not patient_user:
        print("Patient user (김철수) not found, skipping hospital patient seeding")
        return

    # Find 이의사's OrganizationMember record
    doctor_user = db.query(User).filter(User.phone == "010-2222-3333").first()
    if not doctor_user:
        print("Doctor user (이의사) not found, skipping hospital patient seeding")
        return

    doctor_member = db.query(OrganizationMember).filter(
        OrganizationMember.organization_id == organization.id,
        OrganizationMember.user_id == doctor_user.id
    ).first()

    if not doctor_member:
        print("Doctor OrganizationMember not found, skipping hospital patient seeding")
        return

    # Check if HospitalPatient already exists
    existing_hp = db.query(HospitalPatient).filter(
        HospitalPatient.organization_id == organization.id,
        HospitalPatient.patient_user_id == patient_user.id
    ).first()

    if existing_hp:
        # Update assigned_doctor_id if not set or incorrect
        # (assigned_doctor_id should be OrganizationMember.id, not User.id)
        if existing_hp.assigned_doctor_id != doctor_member.id:
            existing_hp.assigned_doctor_id = doctor_member.id
            existing_hp.status = HospitalPatientStatus.ACTIVE
            existing_hp.consent_signed = True
            existing_hp.consent_date = datetime.utcnow()
            db.commit()
            print(f"Updated HospitalPatient: {patient_user.name} -> assigned to {doctor_user.name} (OrganizationMember.id={doctor_member.id})")
        else:
            print(f"HospitalPatient already exists with correct doctor assignment: {patient_user.name}")
        return

    # Create HospitalPatient record
    hp = HospitalPatient(
        organization_id=organization.id,
        patient_user_id=patient_user.id,
        patient_number="P-2024-0001",
        assigned_doctor_id=doctor_member.id,
        consent_signed=True,
        consent_date=datetime.utcnow(),
        status=HospitalPatientStatus.ACTIVE
    )
    db.add(hp)
    db.commit()
    print(f"Created HospitalPatient: {patient_user.name} (assigned to {doctor_user.name})")


if __name__ == "__main__":
    seed_users()
