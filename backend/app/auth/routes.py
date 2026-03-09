"""Authentication Routes"""
import secrets
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from authlib.integrations.starlette_client import OAuth
import bcrypt

security_logger = logging.getLogger("security")

from ..database.connection import get_db
from ..database.models import User, DiagnosisKit, UserDiagnosis
from .config import auth_settings
from .jwt_handler import create_access_token
from .dependencies import require_auth
from .schemas import (
    UserResponse, UserWithToken,
    SimpleRegisterRequest, SimpleRegisterResponse, SimpleLoginRequest,
    AdminLoginRequest,
    KitRegisterRequest, UserDiagnosisResponse,
    EmailRegisterRequest, EmailVerifyAndRegisterRequest, EmailLoginRequest,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])

# OAuth setup
oauth = OAuth()
oauth.register(
    name='google',
    client_id=auth_settings.google_client_id,
    client_secret=auth_settings.google_client_secret,
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid email profile'}
)


def hash_pin(pin: str) -> str:
    """Hash PIN using bcrypt"""
    return bcrypt.hashpw(pin.encode(), bcrypt.gensalt()).decode()


def verify_pin(plain_pin: str, hashed_pin: str) -> bool:
    """Verify PIN"""
    return bcrypt.checkpw(plain_pin.encode(), hashed_pin.encode())


def generate_access_pin() -> str:
    """Generate 6-digit access PIN"""
    return ''.join([str(secrets.randbelow(10)) for _ in range(6)])


# ============================================================================
# Google OAuth Routes
# ============================================================================

@router.get("/google/login")
async def google_login(request: Request):
    """Initiate Google OAuth login"""
    redirect_uri = f"{auth_settings.backend_url}/auth/google/callback"
    return await oauth.google.authorize_redirect(request, redirect_uri)


@router.get("/google/callback")
async def google_callback(request: Request, db: Session = Depends(get_db)):
    """Handle Google OAuth callback"""
    try:
        token = await oauth.google.authorize_access_token(request)
        user_info = token.get('userinfo')

        if not user_info:
            raise HTTPException(status_code=400, detail="Failed to get user info from Google")

        google_id = user_info.get('sub')
        email = user_info.get('email')
        name = user_info.get('name', email.split('@')[0] if email else 'User')
        picture = user_info.get('picture')

        # Find or create user
        user = db.query(User).filter(User.google_id == google_id).first()

        if not user:
            # Check if email exists with different auth type
            existing_user = db.query(User).filter(User.email == email).first()
            if existing_user:
                # Link Google account to existing user
                existing_user.google_id = google_id
                existing_user.auth_type = 'google'
                existing_user.profile_image = picture
                user = existing_user
            else:
                # Create new user
                user = User(
                    name=name,
                    email=email,
                    auth_type='google',
                    google_id=google_id,
                    profile_image=picture,
                    role='user'
                )
                db.add(user)

        # Super admin role assignment via SUPER_ADMIN_EMAILS env var
        if auth_settings.is_super_admin(email):
            if user.role != 'super_admin':
                security_logger.info(
                    "Super admin role assigned via Google OAuth: email=%s user_id=%s previous_role=%s",
                    email, user.id, user.role
                )
                user.role = 'super_admin'
        else:
            # If user was super_admin but email removed from SUPER_ADMIN_EMAILS, downgrade
            if user.role == 'super_admin':
                security_logger.warning(
                    "Super admin role revoked (email removed from SUPER_ADMIN_EMAILS): email=%s user_id=%s",
                    email, user.id
                )
                user.role = 'user'

        user.last_login_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(user)

        # Create JWT token
        access_token = create_access_token(
            data={"sub": str(user.id), "auth_type": "google"}
        )

        # Redirect to frontend with token
        frontend_url = auth_settings.frontend_url
        return RedirectResponse(
            url=f"{frontend_url}/auth/callback?token={access_token}"
        )

    except Exception as e:
        print(f"Google OAuth error: {e}")
        frontend_url = auth_settings.frontend_url
        return RedirectResponse(
            url=f"{frontend_url}/login?error=oauth_failed"
        )


# ============================================================================
# Simple Registration/Login Routes
# ============================================================================

@router.post("/simple/register", response_model=SimpleRegisterResponse)
async def simple_register(
    request: SimpleRegisterRequest,
    db: Session = Depends(get_db)
):
    """Register with name + phone/birth_date + kit verification"""
    # Verify kit exists and PIN matches
    kit = db.query(DiagnosisKit).filter(
        DiagnosisKit.serial_number == request.serial_number
    ).first()

    if not kit:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Diagnosis kit not found"
        )

    if kit.is_registered:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This kit is already registered"
        )

    # Check PIN attempts
    if kit.pin_attempts >= 5:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many failed attempts. Please contact support."
        )

    if not verify_pin(request.pin, kit.pin_hash):
        kit.pin_attempts += 1
        db.commit()
        security_logger.warning(
            "PIN verification failed: kit=%s attempts=%d",
            request.serial_number, kit.pin_attempts
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid PIN"
        )

    # Check if user already exists
    existing_user = None
    if request.birth_date:
        existing_user = db.query(User).filter(
            User.name == request.name,
            User.birth_date == request.birth_date
        ).first()
    elif request.phone:
        existing_user = db.query(User).filter(
            User.phone == request.phone
        ).first()

    # Generate access PIN for future logins
    access_pin = generate_access_pin()
    access_pin_hash = hash_pin(access_pin)

    if existing_user:
        user = existing_user
        user.access_pin_hash = access_pin_hash
    else:
        user = User(
            name=request.name,
            auth_type='simple',
            phone=request.phone,
            birth_date=request.birth_date,
            access_pin_hash=access_pin_hash,
            role='user'
        )
        db.add(user)
        db.flush()

    # Register kit to user
    kit.is_registered = True
    kit.registered_user_id = user.id
    kit.registered_at = datetime.now(timezone.utc)
    kit.pin_attempts = 0

    # Create user diagnosis record
    diagnosis = UserDiagnosis(
        user_id=user.id,
        kit_id=kit.id,
        results=kit.results,
        diagnosis_date=kit.diagnosis_date
    )
    db.add(diagnosis)

    user.last_login_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(user)

    # Create JWT token
    access_token = create_access_token(
        data={"sub": str(user.id), "auth_type": "simple"}
    )

    return SimpleRegisterResponse(
        user=UserResponse.model_validate(user),
        access_token=access_token,
        access_pin=access_pin,
        message="Registration successful. Please save your access PIN for future logins."
    )


@router.post("/simple/login", response_model=UserWithToken)
async def simple_login(
    request: SimpleLoginRequest,
    db: Session = Depends(get_db)
):
    """Login with name + birth_date/phone + access PIN"""
    user = None

    if request.birth_date:
        user = db.query(User).filter(
            User.name == request.name,
            User.birth_date == request.birth_date
        ).first()
    elif request.phone:
        user = db.query(User).filter(
            User.phone == request.phone
        ).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    if not user.access_pin_hash:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No access PIN set. Please register first."
        )

    if not verify_pin(request.access_pin, user.access_pin_hash):
        from ..core.pii_masking import mask_name
        security_logger.warning(
            "Login failed: user=%s name=%s",
            user.id, mask_name(request.name)
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid access PIN"
        )

    from ..core.pii_masking import mask_name
    security_logger.info("Login success: user=%s name=%s", user.id, mask_name(request.name))
    user.last_login_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(user)

    access_token = create_access_token(
        data={"sub": str(user.id), "auth_type": "simple"}
    )

    return UserWithToken(
        user=UserResponse.model_validate(user),
        access_token=access_token
    )


# ============================================================================
# Admin Login (name + PIN only)
# ============================================================================

@router.post("/admin/login", response_model=UserWithToken)
async def admin_login(
    request: AdminLoginRequest,
    db: Session = Depends(get_db)
):
    """Login for admin users with name + access PIN only"""
    user = db.query(User).filter(
        User.name == request.name,
        User.role.in_(['super_admin', 'admin'])
    ).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="관리자 계정을 찾을 수 없습니다."
        )

    if not user.access_pin_hash:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="접속 PIN이 설정되지 않았습니다."
        )

    if not verify_pin(request.access_pin, user.access_pin_hash):
        from ..core.pii_masking import mask_name
        security_logger.warning(
            "Admin login failed: user=%s name=%s",
            user.id, mask_name(request.name)
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="접속 PIN이 올바르지 않습니다."
        )

    from ..core.pii_masking import mask_name
    security_logger.info("Admin login success: user=%s name=%s", user.id, mask_name(request.name))
    user.last_login_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(user)

    access_token = create_access_token(
        data={"sub": str(user.id), "auth_type": "simple"}
    )

    return UserWithToken(
        user=UserResponse.model_validate(user),
        access_token=access_token
    )


# ============================================================================
# Email + Password Registration/Login Routes
# ============================================================================

@router.post("/email/send-code")
async def email_send_verification(
    request: EmailRegisterRequest,
    db: Session = Depends(get_db)
):
    """Send email verification code for registration"""
    from ..database.subscriber_models import EmailVerification
    from ..services.email_service import get_email_service
    from ..services.report_generator import NewsReportGenerator
    import random
    import string

    # Check if email already registered
    existing = db.query(User).filter(User.email == request.email).first()
    if existing and existing.password_hash:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="이미 가입된 이메일입니다. 로그인해주세요."
        )

    # Invalidate previous unused codes
    db.query(EmailVerification).filter(
        EmailVerification.email == request.email,
        EmailVerification.is_used == False,
    ).update({"is_used": True})

    # Generate and save verification code
    from datetime import timedelta
    code = "".join(random.choices(string.digits, k=6))
    verification = EmailVerification(
        email=request.email,
        code=code,
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=30),
    )
    db.add(verification)
    db.commit()

    # Send email
    email_service = get_email_service()
    report_generator = NewsReportGenerator()
    html = report_generator.generate_subscription_key_email(
        verification_code=code,
        expires_minutes=30,
    )
    email_service.send(
        to=request.email,
        subject="[AllergyInsight] 회원가입 인증 코드",
        html_body=html,
    )

    return {"message": "인증 코드가 발송되었습니다. 이메일을 확인해주세요."}


@router.post("/email/register", response_model=UserWithToken)
async def email_register(
    request: EmailVerifyAndRegisterRequest,
    db: Session = Depends(get_db)
):
    """Verify code and complete registration with password"""
    from ..database.subscriber_models import EmailVerification

    # Verify code
    verification = db.query(EmailVerification).filter(
        EmailVerification.email == request.email,
        EmailVerification.code == request.code,
        EmailVerification.is_used == False,
    ).first()

    if not verification:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="유효하지 않은 인증 코드입니다."
        )

    if verification.expires_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="인증 코드가 만료되었습니다."
        )

    verification.is_used = True

    # Check existing user (e.g., Google OAuth user adding password)
    user = db.query(User).filter(User.email == request.email).first()
    password_hash = bcrypt.hashpw(request.password.encode(), bcrypt.gensalt()).decode()

    if user:
        user.password_hash = password_hash
        if user.auth_type == 'google':
            user.auth_type = 'google'  # keep google
        else:
            user.auth_type = 'email'
    else:
        user = User(
            name=request.email.split('@')[0],
            email=request.email,
            auth_type='email',
            password_hash=password_hash,
            role='user',
        )
        db.add(user)

    user.last_login_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(user)

    access_token = create_access_token(
        data={"sub": str(user.id), "auth_type": "email"}
    )

    return UserWithToken(
        user=UserResponse.model_validate(user),
        access_token=access_token
    )


@router.post("/email/login", response_model=UserWithToken)
async def email_login(
    request: EmailLoginRequest,
    db: Session = Depends(get_db)
):
    """Login with email + password"""
    user = db.query(User).filter(User.email == request.email).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="이메일 또는 비밀번호가 올바르지 않습니다."
        )

    if not user.password_hash:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="비밀번호가 설정되지 않았습니다. 회원가입을 진행해주세요."
        )

    if not bcrypt.checkpw(request.password.encode(), user.password_hash.encode()):
        security_logger.warning(
            "Email login failed: email=%s user_id=%s",
            request.email, user.id
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="이메일 또는 비밀번호가 올바르지 않습니다."
        )

    security_logger.info("Email login success: user=%s email=%s", user.id, request.email)
    user.last_login_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(user)

    access_token = create_access_token(
        data={"sub": str(user.id), "auth_type": "email"}
    )

    return UserWithToken(
        user=UserResponse.model_validate(user),
        access_token=access_token
    )


# ============================================================================
# Current User Routes
# ============================================================================

@router.get("/me", response_model=UserResponse)
async def get_me(user: User = Depends(require_auth)):
    """Get current user info"""
    return UserResponse.model_validate(user)


@router.post("/logout")
async def logout(user: User = Depends(require_auth)):
    """Logout (client should discard token)"""
    return {"message": "Logged out successfully"}


# ============================================================================
# Kit Registration (for logged-in users)
# ============================================================================

@router.post("/register-kit", response_model=UserDiagnosisResponse)
async def register_kit(
    request: KitRegisterRequest,
    user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Register a diagnosis kit to current user"""
    kit = db.query(DiagnosisKit).filter(
        DiagnosisKit.serial_number == request.serial_number
    ).first()

    if not kit:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Diagnosis kit not found"
        )

    if kit.is_registered:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This kit is already registered"
        )

    if kit.pin_attempts >= 5:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many failed attempts"
        )

    if not verify_pin(request.pin, kit.pin_hash):
        kit.pin_attempts += 1
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid PIN"
        )

    # Register kit
    kit.is_registered = True
    kit.registered_user_id = user.id
    kit.registered_at = datetime.now(timezone.utc)
    kit.pin_attempts = 0

    # Create diagnosis record
    diagnosis = UserDiagnosis(
        user_id=user.id,
        kit_id=kit.id,
        results=kit.results,
        diagnosis_date=kit.diagnosis_date
    )
    db.add(diagnosis)
    db.commit()
    db.refresh(diagnosis)

    return UserDiagnosisResponse(
        id=diagnosis.id,
        results=diagnosis.results,
        diagnosis_date=diagnosis.diagnosis_date,
        prescription=diagnosis.prescription,
        created_at=diagnosis.created_at,
        kit_serial=kit.serial_number
    )
