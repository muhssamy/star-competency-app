# star_competency_app/config/settings.py
import os
from functools import lru_cache

from dotenv import load_dotenv
from pydantic_settings import BaseSettings

# Load environment variables from .env file
load_dotenv()


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application settings
    APP_NAME: str = "STAR Competency App"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = os.getenv("DEBUG", "False").lower() in ("true", "1", "t")
    APP_URL: str = os.getenv("APP_URL", "http://localhost:5000")

    # Database settings
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", "postgresql://user:password@db:5432/star_competency"
    )

    # Claude API settings
    CLAUDE_API_KEY: str = os.getenv("CLAUDE_API_KEY", "")
    CLAUDE_MODEL: str = os.getenv("CLAUDE_MODEL", "claude-3-7-sonnet-20250219")
    CLAUDE_MAX_TOKENS: int = int(os.getenv("CLAUDE_MAX_TOKENS", "100000"))

    # Azure SSO settings
    AZURE_CLIENT_ID: str = os.getenv("AZURE_CLIENT_ID", "")
    AZURE_CLIENT_SECRET: str = os.getenv("AZURE_CLIENT_SECRET", "")
    AZURE_TENANT_ID: str = os.getenv("AZURE_TENANT_ID", "")

    # Security settings
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-here")
    SESSION_COOKIE_SECURE: bool = os.getenv(
        "SESSION_COOKIE_SECURE", "True"
    ).lower() in ("true", "1", "t")
    SESSION_COOKIE_HTTPONLY: bool = os.getenv(
        "SESSION_COOKIE_HTTPONLY", "True"
    ).lower() in ("true", "1", "t")
    SESSION_COOKIE_SAMESITE: str = os.getenv("SESSION_COOKIE_SAMESITE", "Lax")

    # File upload settings
    UPLOAD_FOLDER: str = os.getenv("UPLOAD_FOLDER", "/app/data/uploads")
    MAX_CONTENT_LENGTH: int = int(os.getenv("MAX_CONTENT_LENGTH", "16777216"))  # 16MB
    ALLOWED_EXTENSIONS: set = {"png", "jpg", "jpeg", "gif", "pdf"}

    # OpenAI API settings
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_TEXT_MODEL: str = os.getenv("OPENAI_TEXT_MODEL", "gpt-4-turbo-preview")
    OPENAI_IMAGE_MODEL: str = os.getenv("OPENAI_IMAGE_MODEL", "gpt-4-vision-preview")
    OPENAI_MAX_TOKENS: int = int(os.getenv("OPENAI_MAX_TOKENS", "4096"))

    # Security settings
    ENCRYPTION_KEY: str = os.getenv("ENCRYPTION_KEY", "")
    HASH_SALT: str = os.getenv("HASH_SALT", "default-salt-change-me-in-production")
    SECURITY_LOG_LEVEL: str = os.getenv("SECURITY_LOG_LEVEL", "INFO")
    SESSION_LIFETIME: int = int(os.getenv("SESSION_LIFETIME", "1800"))  # 30 minutes

    # Admin
    ADMIN_EMAILS: str = os.getenv("ADMIN_EMAILS", "azzam.ma@nahdi.sa")

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings():
    """Get cached settings to avoid reloading from environment for each request."""
    return Settings()
