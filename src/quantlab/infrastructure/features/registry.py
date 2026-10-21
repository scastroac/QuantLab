"""In-memory feature registry implementation."""

from __future__ import annotations

from quantlab.application.ports.feature import FeatureCalculator, FeatureRegistry
from quantlab.domain.value_objects.feature import FeatureFamily


class InMemoryFeatureRegistry(FeatureRegistry):
    """Catalog of available feature calculators."""

    def __init__(self) -> None:
        self._calculators: dict[str, FeatureCalculator] = {}

    def register(self, calculator: FeatureCalculator) -> None:
        """Register a feature calculator into the catalog."""
        self._calculators[calculator.name.value] = calculator

    def get(self, name: str) -> FeatureCalculator | None:
        """Retrieve a calculator by name string."""
        return self._calculators.get(name)

    def list_all(self, family: FeatureFamily | None = None) -> list[FeatureCalculator]:
        """List all calculators, optionally filtered by family."""
        if family is None:
            return list(self._calculators.values())
        return [c for c in self._calculators.values() if c.family == family]
