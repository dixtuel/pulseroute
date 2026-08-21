from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Application
    APP_NAME: str = "PulseRoute"
    APP_ENV: str = "production"
    DEBUG: bool = False
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    SECRET_KEY: str = Field(default="pulseroute-super-secure-change-in-production-secret-key-32b")
    PRIMARY_DOMAIN: str = "localhost:8000"

    # Database & Cache
    DATABASE_URL: str = "sqlite+aiosqlite:///./pulseroute.db"
    REDIS_URL: Optional[str] = "redis://127.0.0.1:6379/0"
    CACHE_DEFAULT_TTL: int = 86400  # 24 hours
    NEGATIVE_CACHE_TTL: int = 60    # 60s for non-existent slugs

    # Custom Domains & TLS
    CUSTOM_DOMAIN_CNAME_TARGET: str = "cname.pulseroute.io"
    CADDY_INTERNAL_ASK_SECRET: Optional[str] = None
    ENFORCE_SAFE_BROWSING: bool = True

    # Monetization & AdSense Control (Platform Admin Policy)
    ALLOW_USER_MONETIZATION: bool = False  # Disabled by default so visitors/users cannot inject custom AdSense
    GLOBAL_ADSENSE_CLIENT_ID: Optional[str] = None  # Fallback publisher ID for platform owner

    # Redirect & Tracking Defaults
    DEFAULT_REDIRECT_STATUS: int = 307  # 307 Temporary Redirect
    ENABLE_BOT_FILTERING: bool = True


settings = Settings()
