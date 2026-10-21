"""Feature application ports."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence

from quantlab.domain.entities.feature import FeatureSet
from quantlab.domain.entities.market import Candle
from quantlab.domain.value_objects.feature import FeatureFamily, FeatureName, FeatureSeries
from quantlab.domain.value_objects.market import Interval, Symbol


class FeatureCalculator(ABC):
    """Port for computing a specific quantitative indicator over a candle sequence."""

    @property
    @abstractmethod
    def name(self) -> FeatureName:
        """Return the unique, strongly validated feature identifier."""
        pass

    @property
    @abstractmethod
    def family(self) -> FeatureFamily:
        """Return the category family of this feature."""
        pass

    @property
    @abstractmethod
    def version(self) -> str:
        """Return the implementation version for reproducibility."""
        pass

    @abstractmethod
    def calculate(self, candles: Sequence[Candle]) -> FeatureSeries:
        """Compute the feature series from historical candles."""
        pass


class FeatureRegistry(ABC):
    """Port for discovering, registering, and listing available feature calculators."""

    @abstractmethod
    def register(self, calculator: FeatureCalculator) -> None:
        """Register a feature calculator into the catalog."""
        pass

    @abstractmethod
    def get(self, name: str) -> FeatureCalculator | None:
        """Look up a calculator by its feature name string."""
        pass

    @abstractmethod
    def list_all(self, family: FeatureFamily | None = None) -> list[FeatureCalculator]:
        """List all calculators, optionally filtered by feature family."""
        pass


class FeatureStore(ABC):
    """Port for persisting and retrieving computed feature sets."""

    @abstractmethod
    async def save(self, feature_set: FeatureSet) -> None:
        """Persist a computed feature set."""
        pass

    @abstractmethod
    async def load(
        self,
        symbol: Symbol,
        interval: Interval,
        feature_names: Sequence[str] | None = None,
    ) -> FeatureSet | None:
        """Retrieve a stored feature set for a symbol and interval."""
        pass
