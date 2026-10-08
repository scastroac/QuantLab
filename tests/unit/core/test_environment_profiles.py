"""Tests for the development, testing and production configuration profiles."""

from __future__ import annotations

import os
from pathlib import Path

import pytest
from pydantic import ValidationError

from quantlab.core.config.settings import Environment, Settings

PROJECT_ROOT = Path(__file__).resolve().parents[3]
ENVIRONMENTS_DIRECTORY = PROJECT_ROOT / "config" / "environments"
_SENSITIVE_MARKERS = ("SECRET", "PASSWORD", "TOKEN", "API_KEY", "PRIVATE")


@pytest.fixture(autouse=True)
def isolated_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    """Remove ambient QUANTLAB_* variables so only the file under test applies."""
    for name in [key for key in os.environ if key.startswith("QUANTLAB_")]:
        monkeypatch.delenv(name)


def _load_profile(name: str) -> Settings:
    """Load one reference profile without depending on import-time environment selection."""
    return Settings(_env_file=ENVIRONMENTS_DIRECTORY / f"{name}.env")


@pytest.mark.parametrize(
    ("profile", "environment", "level", "json_logs"),
    [
        ("development", Environment.DEVELOPMENT, "DEBUG", False),
        ("testing", Environment.TESTING, "WARNING", False),
        ("production", Environment.PRODUCTION, "INFO", True),
    ],
)
def test_profile_defines_the_expected_settings(
    profile: str, environment: Environment, level: str, json_logs: bool
) -> None:
    """Each reference profile selects its environment, log level and log format."""
    settings = _load_profile(profile)

    assert settings.environment is environment
    assert settings.logging.level == level
    assert settings.logging.json_logs is json_logs
    assert settings.plugins.directory == PROJECT_ROOT / "plugins"


def test_every_environment_has_a_profile_file() -> None:
    """Adding an Environment member without its profile file must fail loudly."""
    for environment in Environment:
        assert (ENVIRONMENTS_DIRECTORY / f"{environment.value}.env").is_file()


def test_process_environment_overrides_the_profile_file() -> None:
    """Environment variables win over file values without discarding the rest of the profile."""
    os.environ["QUANTLAB_LOGGING__LEVEL"] = "ERROR"
    try:
        settings = _load_profile("production")
    finally:
        del os.environ["QUANTLAB_LOGGING__LEVEL"]

    assert settings.logging.level == "ERROR"
    assert settings.logging.json_logs is True


def test_unknown_environment_is_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    """A typo in QUANTLAB_ENVIRONMENT must not silently fall back to another profile."""
    monkeypatch.setenv("QUANTLAB_ENVIRONMENT", "staging")

    with pytest.raises(ValidationError):
        Settings(_env_file=None)


def test_profile_files_contain_no_secret_like_keys() -> None:
    """Versioned profiles may only hold non-secret QUANTLAB_* settings."""
    profiles = sorted(ENVIRONMENTS_DIRECTORY.glob("*.env"))
    assert profiles

    for path in profiles:
        keys = [
            line.partition("=")[0].strip().upper()
            for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.lstrip().startswith("#")
        ]
        assert keys, f"{path.name} defines no settings"
        assert all(key.startswith("QUANTLAB_") for key in keys), path.name
        assert not [key for key in keys if any(m in key for m in _SENSITIVE_MARKERS)], path.name
