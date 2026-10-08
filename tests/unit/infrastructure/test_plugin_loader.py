"""Tests for filesystem plugin discovery and isolation."""

from __future__ import annotations

import logging
from collections.abc import Iterable
from pathlib import Path

import pytest

from quantlab.infrastructure.plugins.loader import PluginLoader, PluginLoadError


def _create_plugin(
    directory: Path,
    *,
    name: str = "example-plugin",
    metadata_name: str | None = None,
    dependencies: Iterable[str] = (),
) -> None:
    """Create a minimal technical plugin fixture without a business capability."""
    directory.mkdir()
    dependency_list = tuple(dependencies)
    (directory / "plugin.yaml").write_text(
        "\n".join(
            [
                f"name: {name}",
                "version: 1.0.0",
                "type: utility",
                "description: Test-only technical plugin",
                f"dependencies: {list(dependency_list)!r}",
                "entrypoint: entrypoint.py:create_plugin",
            ]
        ),
        encoding="utf-8",
    )
    (directory / "entrypoint.py").write_text(
        "\n".join(
            [
                "from quantlab.core.plugins import PluginMetadata",
                "",
                "class TestPlugin:",
                "    @property",
                "    def metadata(self) -> PluginMetadata:",
                (
                    "        return PluginMetadata(name='"
                    f"{metadata_name or name}', version='1.0.0', plugin_type='utility', "
                    "description='Test-only technical plugin', "
                    f"dependencies={dependency_list!r})"
                ),
                "",
                "def create_plugin() -> TestPlugin:",
                "    return TestPlugin()",
            ]
        ),
        encoding="utf-8",
    )


def test_loader_discovers_and_loads_a_manifest_backed_plugin(tmp_path: Path) -> None:
    """Manifest metadata is validated against the dynamic plugin instance."""
    _create_plugin(tmp_path / "example")
    loader = PluginLoader(root_directory=tmp_path, logger=logging.getLogger("tests.plugins"))

    discovered = loader.discover()
    loaded = loader.load_all()

    assert discovered[0].manifest.metadata.identifier == "utility:example-plugin"
    assert loaded[0].identifier == "utility:example-plugin"


def test_loader_rejects_metadata_mismatch(tmp_path: Path) -> None:
    """A plugin cannot impersonate the identity declared in its manifest."""
    _create_plugin(tmp_path / "example", metadata_name="different-name")
    loader = PluginLoader(root_directory=tmp_path, logger=logging.getLogger("tests.plugins"))

    with pytest.raises(PluginLoadError, match="metadata mismatch"):
        loader.load_all()


def test_loader_returns_empty_for_missing_directory(tmp_path: Path) -> None:
    """An absent plugin folder is a valid empty registry during bootstrap."""
    loader = PluginLoader(
        root_directory=tmp_path / "does-not-exist",
        logger=logging.getLogger("tests.plugins"),
    )

    assert loader.discover() == ()


def test_loader_resolves_dependencies_before_dependents(tmp_path: Path) -> None:
    """The loader returns a stable topological order for plugin initialization."""
    _create_plugin(tmp_path / "dependent", name="dependent", dependencies=("utility:foundation",))
    _create_plugin(tmp_path / "foundation", name="foundation")
    loader = PluginLoader(root_directory=tmp_path, logger=logging.getLogger("tests.plugins"))

    discovered = loader.discover()
    loaded = loader.load_all()

    assert [plugin.manifest.metadata.identifier for plugin in discovered] == [
        "utility:foundation",
        "utility:dependent",
    ]
    assert [plugin.identifier for plugin in loaded] == [
        "utility:foundation",
        "utility:dependent",
    ]


def test_loader_rejects_missing_plugin_dependency(tmp_path: Path) -> None:
    """A manifest cannot depend on a plugin absent from its configured registry."""
    _create_plugin(tmp_path / "dependent", dependencies=("utility:missing",))
    loader = PluginLoader(root_directory=tmp_path, logger=logging.getLogger("tests.plugins"))

    with pytest.raises(PluginLoadError, match=r"Missing plugin dependencies.*utility:missing"):
        loader.discover()


def test_loader_rejects_cyclic_plugin_dependencies(tmp_path: Path) -> None:
    """Cycles fail during discovery before executing arbitrary plugin code."""
    _create_plugin(tmp_path / "first", name="first", dependencies=("utility:second",))
    _create_plugin(tmp_path / "second", name="second", dependencies=("utility:first",))
    loader = PluginLoader(root_directory=tmp_path, logger=logging.getLogger("tests.plugins"))

    with pytest.raises(PluginLoadError, match="Cyclic plugin dependencies"):
        loader.discover()


def test_loader_rejects_invalid_dependency_identifier(tmp_path: Path) -> None:
    """Dependency declarations must be fully qualified, not ambiguous plugin names."""
    _create_plugin(tmp_path / "example", dependencies=("foundation",))
    loader = PluginLoader(root_directory=tmp_path, logger=logging.getLogger("tests.plugins"))

    with pytest.raises(PluginLoadError, match="Dependencies must use 'type:name'"):
        loader.discover()


def test_loader_rejects_duplicate_plugin_identifiers(tmp_path: Path) -> None:
    """Two folders cannot claim the same registry identity."""
    _create_plugin(tmp_path / "first", name="same")
    _create_plugin(tmp_path / "second", name="same")
    loader = PluginLoader(root_directory=tmp_path, logger=logging.getLogger("tests.plugins"))

    with pytest.raises(PluginLoadError, match="Duplicate plugin identifier"):
        loader.discover()


def test_loader_rejects_entrypoint_path_escaping_plugin_directory(tmp_path: Path) -> None:
    """An entrypoint cannot reference a Python file owned by a neighboring plugin."""
    plugin_directory = tmp_path / "example"
    _create_plugin(plugin_directory)
    (plugin_directory / "plugin.yaml").write_text(
        "\n".join(
            [
                "name: example-plugin",
                "version: 1.0.0",
                "type: utility",
                "entrypoint: ../outside.py:create_plugin",
            ]
        ),
        encoding="utf-8",
    )
    loader = PluginLoader(root_directory=tmp_path, logger=logging.getLogger("tests.plugins"))

    with pytest.raises(PluginLoadError, match="escapes plugin directory"):
        loader.load_all()
