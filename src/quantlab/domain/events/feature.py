"""Feature domain events."""

from __future__ import annotations

from dataclasses import dataclass

from quantlab.domain.events.base import DomainEvent
from quantlab.domain.value_objects.feature import FeatureFamily, FeatureName
from quantlab.domain.value_objects.market import Interval, Symbol


@dataclass(frozen=True, kw_only=True, slots=True)
class FeaturesCalculated(DomainEvent):
    """Event emitted when a set of features has been computed."""

    symbol: Symbol
    interval: Interval
    feature_names: tuple[str, ...]
    sample_count: int


@dataclass(frozen=True, kw_only=True, slots=True)
class FeatureRegistered(DomainEvent):
    """Event emitted when a new feature indicator is registered into the catalog."""

    feature_name: FeatureName
    family: FeatureFamily
    version: str
