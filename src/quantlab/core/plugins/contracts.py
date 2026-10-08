"""Contracts exposed to all technical plugin implementations."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable


@dataclass(frozen=True, slots=True)
class PluginMetadata:
    """Identity and descriptive data shared by every plugin."""

    name: str
    version: str
    plugin_type: str
    description: str = ""
    dependencies: tuple[str, ...] = ()

    @property
    def identifier(self) -> str:
        """Return the stable registry key for the plugin."""
        return f"{self.plugin_type}:{self.name}"


@runtime_checkable
class Plugin(Protocol):
    """Minimum contract a dynamically loaded plugin must satisfy."""

    @property
    def metadata(self) -> PluginMetadata:
        """Return immutable plugin metadata."""
