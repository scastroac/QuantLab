"""Feature domain entities."""

from __future__ import annotations

from dataclasses import dataclass, field

from quantlab.domain.value_objects.feature import FeatureSeries
from quantlab.domain.value_objects.market import Interval, Symbol


@dataclass(frozen=True, slots=True)
class FeatureSet:
    """An aggregate of aligned features for a symbol and interval."""

    symbol: Symbol
    interval: Interval
    features: dict[str, FeatureSeries] = field(default_factory=dict)

    def get_feature(self, name: str) -> FeatureSeries | None:
        """Retrieve a specific feature series by its string identifier."""
        return self.features.get(name)

    @property
    def feature_names(self) -> tuple[str, ...]:
        """Return the tuple of all registered feature names."""
        return tuple(self.features.keys())

    def __len__(self) -> int:
        return len(self.features)
