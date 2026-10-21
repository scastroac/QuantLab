"""Unit tests for InMemoryFeatureRegistry."""

from __future__ import annotations

from quantlab.domain.value_objects.feature import FeatureFamily
from quantlab.infrastructure.features.indicators.momentum import RelativeStrengthIndex
from quantlab.infrastructure.features.indicators.trend import SimpleMovingAverage
from quantlab.infrastructure.features.registry import InMemoryFeatureRegistry


def test_registry_register_and_get() -> None:
    registry = InMemoryFeatureRegistry()
    sma = SimpleMovingAverage(period=20)
    rsi = RelativeStrengthIndex(period=14)

    registry.register(sma)
    registry.register(rsi)

    assert registry.get("trend:sma_20") is sma
    assert registry.get("momentum:rsi_14") is rsi
    assert registry.get("nonexistent") is None


def test_registry_filter_by_family() -> None:
    registry = InMemoryFeatureRegistry()
    sma = SimpleMovingAverage(period=20)
    rsi = RelativeStrengthIndex(period=14)

    registry.register(sma)
    registry.register(rsi)

    assert len(registry.list_all()) == 2
    trend_features = registry.list_all(FeatureFamily.TREND)
    assert len(trend_features) == 1
    assert trend_features[0] is sma
