"""Application settings using Pydantic Settings."""

from pathlib import Path
from typing import Optional

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Application
    app_name: str = "Project Analyzer API"
    app_version: str = "1.0.0"
    debug: bool = False

    # File paths - computed first
    base_dir: Path = Path(__file__).resolve().parent.parent.parent
    data_dir: Path = base_dir / "data"

    # Database
    # NOTE: set this to None by default so Pydantic looks for a DATABASE_URL env var first
    # Make sure that you have a .env file in the root of `backend` and do something like DATABASE_URL=ConnectionString
    database_url: Optional[str] = None

    database_echo: bool = False
    rules_dir: Path = base_dir / "src" / "core" / "rules"
    temp_dir: Path = base_dir / "temp"
    outputs_dir: Path = base_dir / "outputs"

    # Analysis settings
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    max_upload_size: int = 100 * 1024 * 1024  # 100MB
    allowed_extensions: list[str] = [".zip"]

    # GitHub settings
    github_token: Optional[str] = None
    github_clone_timeout: int = 300  # 5 minutes

    # AI settings
    openai_api_key: Optional[str] = None
    ai_resume_generation: bool = True  # Enable/disable AI resume generation
    ai_model: str = "gpt-4o-mini"  # Default AI model
    ai_temperature: float = 0.7
    ai_max_tokens: int = 500

    # API settings
    api_prefix: str = "/api"
    cors_origins: list[str] = ["*"]

    # VALIDATOR: This is the logic that switches databases automatically.
    # It runs AFTER loading environment variables.
    @model_validator(mode="after")
    def set_default_database_url(self):
        # If no DATABASE_URL env var was found, fall back to local SQLite just in case
        if not self.database_url:
            db_path = self.data_dir / "workmine.db"
            self.database_url = f"sqlite:///{db_path}"
        return self


# Global settings instance
settings = Settings()
