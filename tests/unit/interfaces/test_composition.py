"""Tests for the explicit infrastructure composition root."""

from __future__ import annotations

from quantlab.__main__ import main
from quantlab.infrastructure.messaging import LocalEventBus
from quantlab.infrastructure.plugins import PluginLoader
from quantlab.interfaces.cli.composition import bootstrap


def test_bootstrap_composes_infrastructure_without_plugin_side_effects() -> None:
    """The composition root owns concrete adapters while exposing their dependencies explicitly."""
    container = bootstrap()

    assert isinstance(container.event_bus, LocalEventBus)
    assert isinstance(container.plugin_loader, PluginLoader)
    assert container.plugin_loader.root_directory == container.settings.plugins.directory


def test_technical_entrypoint_exits_successfully() -> None:
    """The package command validates infrastructure wiring without a business workflow."""
    assert main() == 0
