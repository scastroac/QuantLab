"""Automated guardrails for the hexagonal dependency rule (ADR-0001)."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

SOURCE_ROOT = Path(__file__).resolve().parents[3] / "src"
PACKAGE_ROOT = SOURCE_ROOT / "quantlab"

_OUTER_LAYERS = ("quantlab.infrastructure", "quantlab.interfaces")
_TECHNOLOGIES = (
    "alembic",
    "asyncpg",
    "catboost",
    "fastapi",
    "lightgbm",
    "psycopg",
    "pyarrow",
    "redis",
    "sqlalchemy",
    "torch",
    "xgboost",
    "yaml",
)

# Layer directory under src/quantlab -> import prefixes that layer must never use.
FORBIDDEN_IMPORTS: dict[str, tuple[str, ...]] = {
    "domain": ("quantlab.application", *_OUTER_LAYERS, *_TECHNOLOGIES),
    "application": (*_OUTER_LAYERS, *_TECHNOLOGIES),
    "core": ("quantlab.domain", "quantlab.application", *_OUTER_LAYERS),
    "infrastructure": ("quantlab.interfaces",),
}


def imported_modules(source: str, module: str, *, is_package: bool) -> set[str]:
    """Return every absolute module name a source file may import.

    Relative imports are resolved against ``module``. For ``from a import b`` both ``a`` and
    ``a.b`` are reported, so ``from quantlab import infrastructure`` cannot hide a dependency.

    Args:
        source: Python source code to analyze.
        module: Dotted name of the module that owns the source.
        is_package: Whether the source is a package ``__init__.py``.

    Returns:
        The set of dotted module names referenced by import statements.
    """
    package = module if is_package else module.rpartition(".")[0]
    imported: set[str] = set()
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            imported.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            base = ""
            if node.level:
                anchor = package.split(".")
                base = ".".join(anchor[: len(anchor) - node.level + 1])
            origin = ".".join(part for part in (base, node.module) if part)
            imported.add(origin)
            imported.update(f"{origin}.{alias.name}" for alias in node.names)
    return imported


def find_forbidden_imports(
    source: str, module: str, *, is_package: bool, forbidden: tuple[str, ...]
) -> list[str]:
    """Return the imported names that match any forbidden module prefix."""
    return sorted(
        name
        for name in imported_modules(source, module, is_package=is_package)
        if any(name == prefix or name.startswith(f"{prefix}.") for prefix in forbidden)
    )


def _module_name(path: Path) -> tuple[str, bool]:
    """Return the dotted module name of a source file and whether it is a package."""
    parts = path.relative_to(SOURCE_ROOT).with_suffix("").parts
    if parts[-1] == "__init__":
        return ".".join(parts[:-1]), True
    return ".".join(parts), False


@pytest.mark.parametrize("layer", sorted(FORBIDDEN_IMPORTS))
def test_layer_respects_the_dependency_rule(layer: str) -> None:
    """No module of a layer may import what the architecture forbids for it."""
    files = sorted((PACKAGE_ROOT / layer).rglob("*.py"))
    assert files, f"No sources found for layer {layer!r}; the guardrail would pass vacuously"

    offenders: list[str] = []
    for path in files:
        module, is_package = _module_name(path)
        found = find_forbidden_imports(
            path.read_text(encoding="utf-8"),
            module,
            is_package=is_package,
            forbidden=FORBIDDEN_IMPORTS[layer],
        )
        offenders.extend(f"{module} imports {name}" for name in found)

    assert not offenders, "Dependency rule violated:\n" + "\n".join(offenders)


@pytest.mark.parametrize(
    "source",
    [
        pytest.param("import quantlab.infrastructure.plugins", id="plain-import"),
        pytest.param(
            "from quantlab.infrastructure.messaging import LocalEventBus", id="from-import"
        ),
        pytest.param("from quantlab import interfaces", id="package-attribute"),
        pytest.param("from ...infrastructure import plugins", id="relative-import"),
        pytest.param(
            "if TYPE_CHECKING:\n    from quantlab.interfaces.cli import composition",
            id="type-checking-import",
        ),
    ],
)
def test_detector_flags_forbidden_imports(source: str) -> None:
    """The checker itself must catch every import style, or the guardrail is decorative."""
    found = find_forbidden_imports(
        source,
        "quantlab.application.use_cases.sample",
        is_package=False,
        forbidden=_OUTER_LAYERS,
    )

    assert found


def test_detector_allows_inward_dependencies() -> None:
    """Application code may depend on domain code."""
    found = find_forbidden_imports(
        "from quantlab.domain.events import DomainEvent",
        "quantlab.application.ports.event_bus",
        is_package=False,
        forbidden=FORBIDDEN_IMPORTS["application"],
    )

    assert found == []
