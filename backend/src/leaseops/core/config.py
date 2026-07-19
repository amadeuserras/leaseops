from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

_BACKEND_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=_BACKEND_ROOT / ".env")
    cors_origins: list[str]
    database_url: str
    test_database_url: str
    jwt_secret: str
    anthropic_api_key: str
    openai_api_key: str
    leaseclear_base_url: str


settings = Settings()  # pyright: ignore[reportCallIssue]
