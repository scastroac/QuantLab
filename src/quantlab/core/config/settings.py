"""Typed configuration loaded through Pydantic Settings."""

from __future__ import annotations

import os
from enum import StrEnum
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Environment(StrEnum):
    """Supported runtime environments."""

    DEVELOPMENT = "development"
    TESTING = "testing"
    PRODUCTION = "production"


def _selected_environment() -> str:
    """Return the requested environment before Settings resolves all values."""
    return os.getenv("QUANTLAB_ENVIRONMENT", Environment.DEVELOPMENT.value).lower()


def _project_root() -> Path:
    """Resolve the repository root from the installed source layout."""
    return Path(__file__).resolve().parents[4]


class LoggingSettings(BaseModel):
    """Settings controlling the standard-library logging adapter."""

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    level: str = "INFO"
    json_logs: bool = Field(default=False, alias="json")


class PluginSettings(BaseModel):
    """Settings for the filesystem-backed plugin adapter."""

    model_config = ConfigDict(extra="ignore")

    directory: Path = Path("plugins")


class Settings(BaseSettings):
    """Immutable-at-use configuration for a single application composition."""

    model_config = SettingsConfigDict(
        env_prefix="QUANTLAB_",
        env_nested_delimiter="__",
        env_file=(
            _project_root() / "config" / "environments" / f"{_selected_environment()}.env",
            ".env",
        ),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "quantlab-ai"
    environment: Environment = Environment.DEVELOPMENT
    logging: LoggingSettings = Field(default_factory=LoggingSettings)
    plugins: PluginSettings = Field(default_factory=PluginSettings)

    @model_validator(mode="after")
    def resolve_relative_paths(self) -> Settings:
        """Anchor file paths to the repository rather than the caller directory."""
        if not self.plugins.directory.is_absolute():
            self.plugins.directory = _project_root() / self.plugins.directory
        return self


def get_settings() -> Settings:
    """Create settings for dependency injection at the composition root.

    The function intentionally does not cache or expose mutable module-level state. A caller owns
    the resulting object for its process lifetime.
    """
    return Settings()
