"""Application settings using Pydantic Settings."""

from pathlib import Path
from typing import Optional

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

    # Database - use absolute path
    @property
    def database_url(self) -> str:
        db_path = self.data_dir / "workmine.db"
        return f"sqlite:///{db_path}"

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


# Global settings instance
settings = Settings()
