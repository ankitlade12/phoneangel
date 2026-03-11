"""Application configuration loaded from environment variables."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """All config is read from .env or environment variables."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # ── DigitalOcean Gradient AI ──────────────────────────────────────
    DO_API_TOKEN: str = ""
    GRADIENT_AGENT_PREP_ID: str = ""       # Call-Prep agent endpoint
    GRADIENT_AGENT_COACH_ID: str = ""      # Live-Coach agent endpoint
    GRADIENT_AGENT_PROXY_ID: str = ""      # Proxy-Caller agent endpoint
    GRADIENT_KB_ID: str = ""               # Knowledge base for phone scripts
    GRADIENT_MODEL: str = "anthropic/claude-sonnet-4-20250514"
    PREP_AGENT_ACCESS_KEY: str = ""        # Access key for Call-Prep agent endpoint
    COACH_AGENT_ACCESS_KEY: str = ""       # Access key for Live-Coach agent endpoint
    PROXY_AGENT_ACCESS_KEY: str = ""       # Access key for Proxy-Caller agent endpoint

    # ── Deepgram (real-time speech-to-text) ───────────────────────────
    DEEPGRAM_API_KEY: str = ""

    # ── Twilio (outbound calls for proxy mode) ────────────────────────
    TWILIO_ACCOUNT_SID: str = ""
    TWILIO_AUTH_TOKEN: str = ""
    TWILIO_PHONE_NUMBER: str = ""

    # ── App ───────────────────────────────────────────────────────────
    APP_NAME: str = "PhoneAngel"
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000
    DATABASE_URL: str = "sqlite+aiosqlite:///./phoneangel.db"
    # In development, allow all origins so the Vite dev server on any port works.
    CORS_ORIGINS: list[str] = ["*"]
    DEBUG: bool = False


settings = Settings()
