from enum import Enum

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppMode(str, Enum):
    PRIVATE = "private"
    PUBLIC = "public"
    MULTI_TENANT = "multi_tenant"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Application
    APP_NAME: str = "PulseRoute"
    APP_ENV: str = "production"
    APP_MODE: AppMode = AppMode.PRIVATE
    DEBUG: bool = False
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    SECRET_KEY: str = Field(default="pulseroute-super-secure-change-in-production-secret-key-32b")
    PRIMARY_DOMAIN: str = "localhost:8000"
    ROOT_ADMIN_KEY: str = "pr_admin_root_master_key_default"

    # Database & Cache
    DATABASE_URL: str = "sqlite+aiosqlite:///./pulseroute.db"
    REDIS_URL: str | None = "redis://127.0.0.1:6379/0"
    CACHE_DEFAULT_TTL: int = 86400  # 24 hours
    NEGATIVE_CACHE_TTL: int = 60    # 60s for non-existent slugs

    # Rate Limiting
    RATE_LIMIT_PUBLIC_CREATE: int = 5    # Max 5 links per minute per IP in public mode
    RATE_LIMIT_REDIRECT_BURST: int = 100 # Max 100 clicks per minute per IP

    # Security & Custom Domains
    ALLOW_PUBLIC_REGISTRATION: bool = False
    ENFORCE_SAFE_BROWSING: bool = True
    CUSTOM_DOMAIN_CNAME_TARGET: str = "cname.pulseroute.io"
    CADDY_INTERNAL_ASK_SECRET: str | None = None

    # Redirect Behavior
    DEFAULT_REDIRECT_STATUS: int = 307  # 307 Temporary to prevent client hard-caching analytics
    ENABLE_BOT_FILTERING: bool = True


settings = Settings()
