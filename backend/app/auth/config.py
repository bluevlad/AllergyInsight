"""Authentication Configuration"""
import os
from pydantic_settings import BaseSettings


class AuthSettings(BaseSettings):
    # Google OAuth
    google_client_id: str = os.getenv("GOOGLE_CLIENT_ID", "")
    google_client_secret: str = os.getenv("GOOGLE_CLIENT_SECRET", "")

    # JWT
    jwt_secret_key: str = os.getenv("JWT_SECRET_KEY", "your-super-secret-key-change-in-production")
    jwt_algorithm: str = os.getenv("JWT_ALGORITHM", "HS256")
    jwt_expire_minutes: int = int(os.getenv("JWT_EXPIRE_MINUTES", "1440"))  # 24 hours

    # URLs
    frontend_url: str = os.getenv("FRONTEND_URL", "http://localhost:4040")
    backend_url: str = os.getenv("BACKEND_URL", "http://localhost:9040")

    class Config:
        env_file = ".env"


auth_settings = AuthSettings()
