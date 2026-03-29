from __future__ import annotations

from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # ── Google / Gemini ──────────────────────────────────────────────────────
    google_api_key: str = ""
    google_genai_use_vertexai: bool = False

    # ── Security ─────────────────────────────────────────────────────────────
    secret_key: str = "change-me-in-production-use-openssl-rand-hex-32"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    # ── Rate limiting ─────────────────────────────────────────────────────────
    rate_limit_requests: int = 10        # max requests
    rate_limit_window_seconds: int = 60  # per window

    # ── Input / output filters ────────────────────────────────────────────────
    max_input_length: int = 1_000
    max_output_length: int = 50_000

    # ── Logging ───────────────────────────────────────────────────────────────
    log_level: str = "INFO"
    log_file: str = "logs/audit.jsonl"

    # ── API ───────────────────────────────────────────────────────────────────
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_workers: int = 1

    # ── Predefined users (username:bcrypt_hash) ───────────────────────────────
    admin_username: str = "admin"
    admin_password_hash: str = ""        # ← bcrypt hash (recommended)
    admin_password_plain: str = ""       # ← plain text (dev only)


@lru_cache
def get_settings() -> Settings:
    return Settings()