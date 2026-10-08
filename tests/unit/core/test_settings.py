"""Tests for typed configuration boundaries."""

from __future__ import annotations

from pathlib import Path

from quantlab.core.config.settings import Environment, Settings


def test_settings_resolve_plugin_directory_from_project_root() -> None:
    """A relative plugin path is stable regardless of the caller's working directory."""
    settings = Settings(plugins={"directory": "custom-plugins"})

    assert settings.plugins.directory.is_absolute()
    assert settings.plugins.directory.name == "custom-plugins"


def test_settings_accept_nested_environment_values() -> None:
    """Pydantic Settings accepts strongly typed nested configuration."""
    settings = Settings(
        environment=Environment.TESTING,
        logging={"level": "warning", "json": True},
        plugins={"directory": Path("plugins")},
    )

    assert settings.environment is Environment.TESTING
    assert settings.logging.level == "warning"
    assert settings.logging.json_logs is True
