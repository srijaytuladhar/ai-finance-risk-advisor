"""Configuration settings module using Pydantic Settings."""

import os
from pathlib import Path
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration loaded from environment variables and .env file."""

    model_config = SettingsConfigDict(
        env_file=str(Path(__file__).resolve().parent.parent / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    OPENAI_API_KEY: str = ""
    MODEL_NAME: str = "gpt-4o-mini"
    CHROMA_PATH: str = str(Path(__file__).resolve().parent.parent / "data" / "chroma")
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    CORS_ORIGINS: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
    ]

    @field_validator("OPENAI_API_KEY")
    @classmethod
    def validate_openai_api_key(cls, value: str) -> str:
        """Validate that OPENAI_API_KEY is provided and not empty."""
        cleaned = value.strip()
        if not cleaned or cleaned == "your_openai_api_key_here":
            raise ValueError(
                "\n"
                "====================================================================\n"
                "FATAL CONFIGURATION ERROR: OPENAI_API_KEY is missing or invalid!\n"
                "Please configure your key in backend/.env or set the OPENAI_API_KEY\n"
                "environment variable before starting the application.\n"
                "Example: OPENAI_API_KEY=sk-proj-...\n"
                "===================================================================="
            )
        return cleaned


def get_settings() -> Settings:
    """Instantiate and return the application settings singleton."""
    return Settings()


settings = get_settings()
