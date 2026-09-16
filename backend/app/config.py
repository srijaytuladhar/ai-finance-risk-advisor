"""Configuration settings module using Pydantic Settings."""

import os
from pathlib import Path
from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration loaded from environment variables and .env file."""

    model_config = SettingsConfigDict(
        env_file=str(Path(__file__).resolve().parent.parent / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    GEMINI_API_KEY: str = ""
    OPENROUTER_API_KEY: str = ""
    OPENAI_API_KEY: str = ""
    HUGGINGFACE_API_KEY: str = ""
    LLM_PROVIDER: str = "fallback"  # "fallback", "gemini", "openrouter", "openai", "huggingface", "auto"
    MODEL_NAME: str = "gemini-3.5-flash"
    GEMINI_MODEL: str = "gemini-3.5-flash"
    OPENROUTER_MODEL: str = "openai/gpt-4o-mini"
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"
    OPENAI_MODEL: str = "gpt-4o-mini"
    HUGGINGFACE_MODEL: str = "Qwen/Qwen2.5-72B-Instruct"
    CHROMA_PATH: str = str(Path(__file__).resolve().parent.parent / "data" / "chroma")
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    CORS_ORIGINS: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
    ]

    @field_validator("GEMINI_API_KEY", mode="before")
    @classmethod
    def check_gemini_env(cls, value: str) -> str:
        """Fallback to GOOGLE_API_KEY environment variable if GEMINI_API_KEY is not set."""
        if not value:
            return os.environ.get("GOOGLE_API_KEY", "").strip()
        return value.strip()

    @field_validator("HUGGINGFACE_API_KEY", mode="before")
    @classmethod
    def check_hf_env(cls, value: str) -> str:
        """Fallback to HF_TOKEN or HUGGINGFACEHUB_API_TOKEN environment variable."""
        if not value:
            return os.environ.get("HF_TOKEN", os.environ.get("HUGGINGFACEHUB_API_TOKEN", "")).strip()
        return value.strip()

    @model_validator(mode="after")
    def validate_provider_keys(self) -> "Settings":
        """Ensure that at least one supported LLM API key is provided and valid."""
        gemini_key = self.GEMINI_API_KEY.strip() if self.GEMINI_API_KEY else ""
        openrouter_key = self.OPENROUTER_API_KEY.strip() if self.OPENROUTER_API_KEY else ""
        openai_key = self.OPENAI_API_KEY.strip() if self.OPENAI_API_KEY else ""
        hf_key = self.HUGGINGFACE_API_KEY.strip() if self.HUGGINGFACE_API_KEY else ""

        has_gemini = bool(gemini_key and gemini_key != "your_gemini_api_key_here")
        has_openrouter = bool(openrouter_key and openrouter_key != "your_openrouter_api_key_here")
        has_openai = bool(openai_key and openai_key != "your_openai_api_key_here")
        has_hf = bool(hf_key and hf_key != "your_huggingface_api_key_here")

        if not has_gemini and not has_openrouter and not has_openai and not has_hf:
            raise ValueError(
                "\n"
                "====================================================================\n"
                "FATAL CONFIGURATION ERROR: No LLM API key is configured!\n"
                "Please configure GEMINI_API_KEY, OPENROUTER_API_KEY, OPENAI_API_KEY, or HUGGINGFACE_API_KEY in backend/.env\n"
                "===================================================================="
            )

        if has_gemini and not os.environ.get("GOOGLE_API_KEY"):
            os.environ["GOOGLE_API_KEY"] = gemini_key

        return self


def get_settings() -> Settings:
    """Instantiate and return the application settings singleton."""
    return Settings()


settings = get_settings()
