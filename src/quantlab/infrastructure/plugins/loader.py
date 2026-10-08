"""Safe filesystem discovery for technical plugins."""

from __future__ import annotations

import hashlib
import importlib.util
import re
import sys
from dataclasses import dataclass
from logging import Logger
from pathlib import Path
from types import ModuleType

import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator

from quantlab.core.plugins import Plugin, PluginMetadata


class PluginLoadError(RuntimeError):
    """Raised when a filesystem plugin cannot be discovered or instantiated."""


_PLUGIN_IDENTIFIER_PATTERN = re.compile(r"^[a-z][a-z0-9_-]*:[a-z][a-z0-9_-]*$")


class PluginManifest(BaseModel):
    """Validated representation of a plugin.yaml manifest."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    name: str = Field(pattern=r"^[a-z][a-z0-9_-]*$")
    version: str
    plugin_type: str = Field(alias="type", pattern=r"^[a-z][a-z0-9_-]*$")
    entrypoint: str = "entrypoint.py:create_plugin"
    description: str = ""
    dependencies: tuple[str, ...] = ()

    @field_validator("dependencies")
    @classmethod
    def validate_dependencies(cls, dependencies: tuple[str, ...]) -> tuple[str, ...]:
        """Require unique, fully qualified dependency identifiers."""
        invalid_dependencies = sorted(
            dependency
            for dependency in dependencies
            if not _PLUGIN_IDENTIFIER_PATTERN.fullmatch(dependency)
        )
        if invalid_dependencies:
            msg = f"Dependencies must use 'type:name': {', '.join(invalid_dependencies)}"
            raise ValueError(msg)
        if len(dependencies) != len(set(dependencies)):
            msg = "Dependencies must not contain duplicate plugin identifiers"
            raise ValueError(msg)
        return dependencies

    @property
    def metadata(self) -> PluginMetadata:
        """Build the public metadata contract from this manifest."""
        return PluginMetadata(
            name=self.name,
            version=self.version,
            plugin_type=self.plugin_type,
            description=self.description,
            dependencies=self.dependencies,
        )


@dataclass(frozen=True, slots=True)
class DiscoveredPlugin:
    """A manifest paired with the directory that owns it."""

    manifest: PluginManifest
    directory: Path


@dataclass(frozen=True, slots=True)
class LoadedPlugin:
    """A verified plugin instance and immutable discovery data."""

    manifest: PluginManifest
    directory: Path
    instance: Plugin

    @property
    def identifier(self) -> str:
        """Return the registry identity delegated to plugin metadata."""
        return self.manifest.metadata.identifier


@dataclass(slots=True)
class PluginLoader:
    """Discover and instantiate plugins without coupling core code to plugin families."""

    root_directory: Path
    logger: Logger

    def discover(self) -> tuple[DiscoveredPlugin, ...]:
        """Validate every manifest beneath the configured plugin directory."""
        if not self.root_directory.exists():
            self.logger.info(
                "Plugin directory does not exist", extra={"path": str(self.root_directory)}
            )
            return ()

        discovered_by_identifier: dict[str, DiscoveredPlugin] = {}
        for manifest_path in sorted(self.root_directory.rglob("plugin.yaml")):
            discovered_plugin = self._read_manifest(manifest_path)
            identifier = discovered_plugin.manifest.metadata.identifier
            if identifier in discovered_by_identifier:
                msg = f"Duplicate plugin identifier: {identifier}"
                raise PluginLoadError(msg)
            discovered_by_identifier[identifier] = discovered_plugin
        return _order_by_dependencies(discovered_by_identifier)

    def load_all(self) -> tuple[LoadedPlugin, ...]:
        """Instantiate all validated plugins using their isolated entrypoint files."""
        return tuple(self._load_plugin(discovered) for discovered in self.discover())

    def _read_manifest(self, manifest_path: Path) -> DiscoveredPlugin:
        """Parse and validate a single manifest file."""
        try:
            raw_manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
            if not isinstance(raw_manifest, dict):
                msg = "Manifest must contain a YAML mapping"
                raise PluginLoadError(f"{manifest_path}: {msg}")
            manifest = PluginManifest.model_validate(raw_manifest)
        except (OSError, ValidationError, yaml.YAMLError) as error:
            raise PluginLoadError(f"Invalid plugin manifest at {manifest_path}: {error}") from error
        return DiscoveredPlugin(manifest=manifest, directory=manifest_path.parent)

    def _load_plugin(self, discovered: DiscoveredPlugin) -> LoadedPlugin:
        """Load one plugin factory and verify its declared metadata."""
        module_path, factory_name = _parse_entrypoint(discovered.manifest.entrypoint)
        entrypoint_path = (discovered.directory / module_path).resolve()
        _ensure_path_within(entrypoint_path, discovered.directory)
        if not entrypoint_path.is_file():
            msg = f"Entrypoint does not exist: {entrypoint_path}"
            raise PluginLoadError(msg)

        module = _load_module(entrypoint_path)
        factory = getattr(module, factory_name, None)
        if not callable(factory):
            msg = f"Plugin factory '{factory_name}' is not callable in {entrypoint_path}"
            raise PluginLoadError(msg)

        instance = factory()
        if not isinstance(instance, Plugin):
            msg = f"Plugin factory '{factory_name}' did not return a Plugin"
            raise PluginLoadError(msg)
        if instance.metadata != discovered.manifest.metadata:
            msg = (
                f"Plugin metadata mismatch for {discovered.directory}: "
                f"expected {discovered.manifest.metadata.identifier}"
            )
            raise PluginLoadError(msg)

        loaded = LoadedPlugin(
            manifest=discovered.manifest,
            directory=discovered.directory,
            instance=instance,
        )
        self.logger.info("Plugin loaded", extra={"plugin_id": loaded.identifier})
        return loaded


def _parse_entrypoint(value: str) -> tuple[Path, str]:
    """Parse a relative Python-file entrypoint in ``path.py:factory`` form."""
    module_path, separator, factory_name = value.partition(":")
    if separator != ":" or not module_path.endswith(".py") or not factory_name:
        msg = "Entrypoint must use the form 'relative/path.py:factory_name'"
        raise PluginLoadError(msg)
    return Path(module_path), factory_name


def _order_by_dependencies(
    discovered_by_identifier: dict[str, DiscoveredPlugin],
) -> tuple[DiscoveredPlugin, ...]:
    """Return plugins in deterministic dependency order or explain an invalid graph.

    Dependencies reference exact plugin identifiers (``type:name``). They are intentionally local
    to the configured registry: package installation and semantic version resolution are separate
    concerns from plugin discovery.
    """
    missing_dependencies = {
        identifier: sorted(
            set(discovered.manifest.dependencies).difference(discovered_by_identifier)
        )
        for identifier, discovered in discovered_by_identifier.items()
    }
    unresolved = {
        identifier: dependencies
        for identifier, dependencies in missing_dependencies.items()
        if dependencies
    }
    if unresolved:
        details = "; ".join(
            f"{identifier} -> {', '.join(dependencies)}"
            for identifier, dependencies in sorted(unresolved.items())
        )
        msg = f"Missing plugin dependencies: {details}"
        raise PluginLoadError(msg)

    ordered: list[DiscoveredPlugin] = []
    state: dict[str, str] = {}
    traversal: list[str] = []

    def visit(identifier: str) -> None:
        current_state = state.get(identifier)
        if current_state == "resolved":
            return
        if current_state == "visiting":
            cycle_start = traversal.index(identifier)
            cycle = [*traversal[cycle_start:], identifier]
            msg = f"Cyclic plugin dependencies: {' -> '.join(cycle)}"
            raise PluginLoadError(msg)

        state[identifier] = "visiting"
        traversal.append(identifier)
        for dependency in sorted(discovered_by_identifier[identifier].manifest.dependencies):
            visit(dependency)
        traversal.pop()
        state[identifier] = "resolved"
        ordered.append(discovered_by_identifier[identifier])

    for identifier in sorted(discovered_by_identifier):
        visit(identifier)
    return tuple(ordered)


def _ensure_path_within(candidate: Path, parent: Path) -> None:
    """Reject entrypoint paths that escape their plugin directory."""
    try:
        candidate.relative_to(parent.resolve())
    except ValueError as error:
        msg = f"Entrypoint path escapes plugin directory: {candidate}"
        raise PluginLoadError(msg) from error


def _load_module(entrypoint_path: Path) -> ModuleType:
    """Execute an entrypoint under a unique module name."""
    fingerprint = hashlib.sha256(str(entrypoint_path).encode()).hexdigest()[:16]
    module_name = f"_quantlab_plugin_{fingerprint}"
    spec = importlib.util.spec_from_file_location(module_name, entrypoint_path)
    if spec is None or spec.loader is None:
        msg = f"Unable to create module specification for {entrypoint_path}"
        raise PluginLoadError(msg)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    try:
        spec.loader.exec_module(module)
    except Exception as error:
        sys.modules.pop(module_name, None)
        raise PluginLoadError(f"Plugin entrypoint failed: {entrypoint_path}: {error}") from error
    return module
