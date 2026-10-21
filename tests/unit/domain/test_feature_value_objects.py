"""Unit tests for feature value objects and entities."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

import pytest

from quantlab.domain.entities.feature import FeatureSet
from quantlab.domain.value_objects.feature import (
    FeatureFamily,
    FeatureName,
    FeatureSeries,
    FeatureValue,
)
from quantlab.domain.value_objects.market import Interval, Symbol, Timestamp


def test_feature_name_valid() -> None:
    fn = FeatureName("trend:sma_20")
    assert fn.value == "trend:sma_20"

    fn2 = FeatureName("momentum:rsi_14")
    assert fn2.value == "momentum:rsi_14"


@pytest.mark.parametrize(
    "invalid_name",
    ["", "sma_20", "trend:", ":sma_20", "trend:sma 20", "trend:sma@20"],
)
def test_feature_name_invalid(invalid_name: str) -> None:
    with pytest.raises(ValueError, match="Invalid feature name"):
        FeatureName(invalid_name)


def test_feature_family_values() -> None:
    assert FeatureFamily.TREND == "trend"
    assert FeatureFamily.MOMENTUM == "momentum"
    assert FeatureFamily.VOLATILITY == "volatility"
    assert FeatureFamily.VOLUME == "volume"
    assert FeatureFamily.STATISTICAL == "statistical"


def test_feature_set_operations() -> None:
    symbol = Symbol("BTC/USDT")
    interval = Interval("1h")
    ts = Timestamp(datetime(2026, 1, 1, 0, 0, tzinfo=UTC))

    series = FeatureSeries(
        name=FeatureName("trend:sma_20"),
        family=FeatureFamily.TREND,
        values=(FeatureValue(timestamp=ts, value=Decimal("100.5")),),
    )

    feature_set = FeatureSet(
        symbol=symbol,
        interval=interval,
        features={"trend:sma_20": series},
    )

    assert len(feature_set) == 1
    assert feature_set.feature_names == ("trend:sma_20",)
    assert feature_set.get_feature("trend:sma_20") == series
    assert feature_set.get_feature("nonexistent") is None
