from functools import lru_cache
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings read from environment or .env file.

    Note: attribute names are mapped to environment variables by uppercasing
    (e.g. `open_ai_api_key` -> `OPEN_AI_API_KEY`).
    """

    # Existing
    open_ai_api_key: str = ""
    api_key: str = ""

    db_user: str = ""
    db_password: str = ""
    db_host: str = ""
    db_port: str = ""
    db_name: str = ""

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    """Return cached Settings instance."""
    return Settings()


__all__ = ["Settings", "get_settings"]
