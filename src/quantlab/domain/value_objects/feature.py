"""Feature engineering value objects."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum
import re

from quantlab.domain.value_objects.market import Timestamp

_FEATURE_NAME_RE = re.compile(r"^[a-z0-9_]+:[a-z0-9_\-]+$")


class FeatureFamily(StrEnum):
    """Categorical classification of financial feature families."""

    TREND = "trend"
    MOMENTUM = "momentum"
    VOLATILITY = "volatility"
    VOLUME = "volume"
    STATISTICAL = "statistical"
    CANDLESTICK = "candlestick"
    CUSTOM = "custom"


@dataclass(frozen=True, slots=True)
class FeatureName:
    """Strongly validated identifier for a feature (e.g. 'trend:sma_20')."""

    value: str

    def __post_init__(self) -> None:
        if not self.value or not _FEATURE_NAME_RE.match(self.value):
            raise ValueError(
                f"Invalid feature name: {self.value!r}. "
                "Expected format 'family:name' (e.g. 'trend:sma_20', 'momentum:rsi_14')."
            )


@dataclass(frozen=True, slots=True)
class FeatureValue:
    """Point-in-time scalar calculation of an indicator."""

    timestamp: Timestamp
    value: Decimal


@dataclass(frozen=True, slots=True)
class FeatureSeries:
    """Immutable sequence of calculated feature values over time."""

    name: FeatureName
    family: FeatureFamily
    values: tuple[FeatureValue, ...]

    def __len__(self) -> int:
        return len(self.values)
