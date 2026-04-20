from __future__ import annotations

from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict
from google.adk.models.lite_llm import LiteLlm


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # ── Google / Gemini ──────────────────────────────────────────────────────
    google_api_key: str = ""
    google_model: str = "gemini-2.5-flash"
    google_genai_use_vertexai: bool = False

    # ── LiteLLM ──────────────────────────────────────────────────────────────
    litellm_model: str = ""

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

@lru_cache
def get_model():
    settings = get_settings()

    # If a LiteLLM/Ollama model is provided
    if settings.litellm_model:
        return LiteLlm(model=settings.litellm_model)

    # Otherwise, return the string for the ADK to handle natively
    # (The ADK will treat a string as a Gemini model name by default)
    return settings.google_model

@lru_cache
def is_gemini_model() -> bool:
    """Returns True when using a native Gemini model, False for LiteLLM/Ollama."""
    return not bool(get_settings().litellm_model)