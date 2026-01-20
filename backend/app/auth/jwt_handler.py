"""JWT Token Handler"""
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from .config import auth_settings


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token"""
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=auth_settings.jwt_expire_minutes)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode,
        auth_settings.jwt_secret_key,
        algorithm=auth_settings.jwt_algorithm
    )
    return encoded_jwt


def verify_token(token: str) -> Optional[dict]:
    """Verify JWT token and return payload"""
    try:
        payload = jwt.decode(
            token,
            auth_settings.jwt_secret_key,
            algorithms=[auth_settings.jwt_algorithm]
        )
        return payload
    except JWTError:
        return None


def decode_token(token: str) -> dict:
    """Decode token without verification (for debugging)"""
    try:
        return jwt.decode(
            token,
            auth_settings.jwt_secret_key,
            algorithms=[auth_settings.jwt_algorithm],
            options={"verify_exp": False}
        )
    except JWTError:
        return {}
