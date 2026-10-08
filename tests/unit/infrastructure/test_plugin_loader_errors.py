"""Failure-mode tests for the plugin loader."""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from textwrap import dedent

import pytest

from quantlab.infrastructure.plugins.loader import PluginLoader, PluginLoadError

_BASE_MANIFEST = "name: example-plugin\nversion: 1.0.0\ntype: utility\n"

_VALID_ENTRYPOINT = dedent(
    """
    from quantlab.core.plugins import PluginMetadata


    class ExamplePlugin:
        @property
        def metadata(self) -> PluginMetadata:
            return PluginMetadata(
                name="example-plugin", version="1.0.0", plugin_type="utility"
            )


    def create_plugin() -> ExamplePlugin:
        return ExamplePlugin()
    """
)


def _loader_for(
    root: Path,
    *,
    manifest: str = _BASE_MANIFEST,
    entrypoint: str | None = _VALID_ENTRYPOINT,
) -> PluginLoader:
    """Write a single plugin fixture under ``root`` and return a loader pointed at it."""
    directory = root / "example"
    directory.mkdir()
    (directory / "plugin.yaml").write_text(manifest, encoding="utf-8")
    if entrypoint is not None:
        (directory / "entrypoint.py").write_text(entrypoint, encoding="utf-8")
    return PluginLoader(root_directory=root, logger=logging.getLogger("tests.plugins"))


@pytest.mark.parametrize(
    ("manifest", "message"),
    [
        pytest.param("- a\n- b\n", "Manifest must contain a YAML mapping", id="not-a-mapping"),
        pytest.param("name: [unclosed\n", "Invalid plugin manifest", id="malformed-yaml"),
        pytest.param(
            _BASE_MANIFEST + "unexpected: true\n",
            "Extra inputs are not permitted",
            id="unknown-field",
        ),
        pytest.param(
            "name: Bad_Name\nversion: 1.0.0\ntype: utility\n",
            "Invalid plugin manifest",
            id="invalid-name",
        ),
        pytest.param(
            "name: example-plugin\ntype: utility\n",
            "Invalid plugin manifest",
            id="missing-version",
        ),
        pytest.param(
            _BASE_MANIFEST + "dependencies: ['utility:a', 'utility:a']\n",
            "duplicate plugin identifiers",
            id="duplicate-dependencies",
        ),
        pytest.param(
            _BASE_MANIFEST + "dependencies: ['utility:example-plugin']\n",
            "Cyclic plugin dependencies",
            id="self-dependency",
        ),
    ],
)
def test_discovery_rejects_invalid_manifests(tmp_path: Path, manifest: str, message: str) -> None:
    """Manifest problems are reported during discovery, before any plugin code runs."""
    loader = _loader_for(tmp_path, manifest=manifest)

    with pytest.raises(PluginLoadError, match=message):
        loader.discover()


@pytest.mark.parametrize(
    ("manifest", "entrypoint", "message"),
    [
        pytest.param(
            _BASE_MANIFEST + "entrypoint: entrypoint.py\n",
            _VALID_ENTRYPOINT,
            "Entrypoint must use the form",
            id="missing-factory-separator",
        ),
        pytest.param(
            _BASE_MANIFEST + "entrypoint: entrypoint.txt:create_plugin\n",
            _VALID_ENTRYPOINT,
            "Entrypoint must use the form",
            id="non-python-file",
        ),
        pytest.param(_BASE_MANIFEST, None, "Entrypoint does not exist", id="missing-file"),
        pytest.param(_BASE_MANIFEST, "VALUE = 1\n", "is not callable", id="missing-factory"),
        pytest.param(
            _BASE_MANIFEST, "create_plugin = 42\n", "is not callable", id="factory-not-callable"
        ),
        pytest.param(
            _BASE_MANIFEST,
            "def create_plugin() -> object:\n    return object()\n",
            "did not return a Plugin",
            id="not-a-plugin",
        ),
        pytest.param(
            _BASE_MANIFEST,
            "raise RuntimeError('boom')\n",
            "Plugin entrypoint failed",
            id="import-time-error",
        ),
        pytest.param(
            _BASE_MANIFEST,
            _VALID_ENTRYPOINT.replace("1.0.0", "2.0.0"),
            "metadata mismatch",
            id="version-mismatch",
        ),
    ],
)
def test_load_all_rejects_invalid_entrypoints(
    tmp_path: Path, manifest: str, entrypoint: str | None, message: str
) -> None:
    """Every entrypoint failure surfaces as PluginLoadError with an actionable message."""
    loader = _loader_for(tmp_path, manifest=manifest, entrypoint=entrypoint)

    with pytest.raises(PluginLoadError, match=message):
        loader.load_all()


def test_discovery_does_not_execute_entrypoints(tmp_path: Path) -> None:
    """Only load_all() runs plugin code; discover() must stay side-effect free."""
    loader = _loader_for(tmp_path, entrypoint="raise RuntimeError('must not run')\n")

    discovered = loader.discover()

    assert [plugin.manifest.metadata.identifier for plugin in discovered] == [
        "utility:example-plugin"
    ]


def test_failed_entrypoint_does_not_leak_a_module(tmp_path: Path) -> None:
    """A plugin that crashes on import must not stay registered in sys.modules."""
    loader = _loader_for(tmp_path, entrypoint="raise RuntimeError('boom')\n")
    before = {name for name in sys.modules if name.startswith("_quantlab_plugin_")}

    with pytest.raises(PluginLoadError):
        loader.load_all()

    after = {name for name in sys.modules if name.startswith("_quantlab_plugin_")}
    assert after == before
