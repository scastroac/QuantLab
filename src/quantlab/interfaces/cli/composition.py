"""Explicit dependency composition for the current technical entry point."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from logging import Logger

from quantlab.core.config import Settings, get_settings
from quantlab.core.logging import configure_logging
from quantlab.infrastructure.messaging import LocalEventBus
from quantlab.infrastructure.plugins import PluginLoader


@dataclass(frozen=True, slots=True)
class InfrastructureContainer:
    """Dependencies that future inbound adapters receive explicitly."""

    settings: Settings
    logger: Logger
    event_bus: LocalEventBus
    plugin_loader: PluginLoader


def bootstrap() -> InfrastructureContainer:
    """Compose technical adapters without introducing global service locators."""
    settings = get_settings()
    configure_logging(settings.logging)
    logger = logging.getLogger("quantlab")
    return InfrastructureContainer(
        settings=settings,
        logger=logger,
        event_bus=LocalEventBus(logger=logger),
        plugin_loader=PluginLoader(root_directory=settings.plugins.directory, logger=logger),
    )
