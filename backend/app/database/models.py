"""Database Models"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Date, ForeignKey, JSON, Index
from sqlalchemy.orm import relationship
from .connection import Base


class User(Base):
    """User model - supports both Google OAuth and simple registration"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)

    # Common fields
    name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, nullable=True)

    # Auth type: 'google' or 'simple'
    auth_type = Column(String(20), nullable=False)

    # Google OAuth fields
    google_id = Column(String(255), unique=True, nullable=True)
    profile_image = Column(String(500), nullable=True)

    # Simple registration fields
    phone = Column(String(20), nullable=True)  # Hashed
    birth_date = Column(Date, nullable=True)
    access_pin_hash = Column(String(255), nullable=True)  # For simple login

    # Role: 'user' or 'admin'
    role = Column(String(20), default="user")

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)

    # Relationships
    diagnoses = relationship("UserDiagnosis", back_populates="user")
    registered_kits = relationship("DiagnosisKit", back_populates="registered_user", foreign_keys="[DiagnosisKit.registered_user_id]")

    # Indexes
    __table_args__ = (
        Index('idx_users_google_id', 'google_id'),
        Index('idx_users_name_birth', 'name', 'birth_date'),
    )


class DiagnosisKit(Base):
    """Diagnosis Kit - S-Blot 3 PLUS results"""
    __tablename__ = "diagnosis_kits"

    id = Column(Integer, primary_key=True, index=True)

    # Serial number: SGT-2024-XXXXX-XXXX
    serial_number = Column(String(30), unique=True, nullable=False, index=True)

    # PIN for verification (hashed)
    pin_hash = Column(String(255), nullable=False)
    pin_attempts = Column(Integer, default=0)

    # S-Blot 3 PLUS results (JSON)
    # Format: {"peanut": 3, "milk": 2, "egg": 0, ...}
    results = Column(JSON, nullable=False)
    diagnosis_date = Column(Date, nullable=False)

    # Registration status
    is_registered = Column(Boolean, default=False)
    registered_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    registered_at = Column(DateTime, nullable=True)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)

    # Relationships
    registered_user = relationship("User", back_populates="registered_kits", foreign_keys=[registered_user_id])
    user_diagnoses = relationship("UserDiagnosis", back_populates="kit")


class UserDiagnosis(Base):
    """User Diagnosis History"""
    __tablename__ = "user_diagnoses"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    kit_id = Column(Integer, ForeignKey("diagnosis_kits.id"), nullable=True)

    # Copy of results (preserved even if kit data changes)
    results = Column(JSON, nullable=False)
    diagnosis_date = Column(Date, nullable=False)

    # Cached prescription
    prescription = Column(JSON, nullable=True)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="diagnoses")
    kit = relationship("DiagnosisKit", back_populates="user_diagnoses")

    # Indexes
    __table_args__ = (
        Index('idx_user_diagnoses_user', 'user_id'),
    )
