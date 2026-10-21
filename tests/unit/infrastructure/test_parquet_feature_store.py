"""Unit tests for ParquetFeatureStore."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

import pytest

from quantlab.domain.entities.feature import FeatureSet
from quantlab.domain.value_objects.feature import (
    FeatureFamily,
    FeatureName,
    FeatureSeries,
    FeatureValue,
)
from quantlab.domain.value_objects.market import Interval, Symbol, Timestamp
from quantlab.infrastructure.storage.parquet_feature_store import ParquetFeatureStore


@pytest.mark.asyncio
async def test_parquet_feature_store_save_and_load(tmp_path: Path) -> None:
    store = ParquetFeatureStore(base_dir=tmp_path)
    symbol = Symbol("BTC/USDT")
    interval = Interval("1h")
    t0 = Timestamp(datetime(2026, 1, 1, 0, 0, tzinfo=UTC))
    t1 = Timestamp(datetime(2026, 1, 1, 1, 0, tzinfo=UTC))

    series1 = FeatureSeries(
        name=FeatureName("trend:sma_20"),
        family=FeatureFamily.TREND,
        values=(
            FeatureValue(timestamp=t0, value=Decimal("100.5")),
            FeatureValue(timestamp=t1, value=Decimal("101.5")),
        ),
    )

    feature_set = FeatureSet(
        symbol=symbol,
        interval=interval,
        features={"trend:sma_20": series1},
    )

    await store.save(feature_set)

    loaded = await store.load(symbol, interval)
    assert loaded is not None
    assert loaded.symbol == symbol
    assert loaded.interval == interval
    assert "trend:sma_20" in loaded.feature_names

    f_series = loaded.get_feature("trend:sma_20")
    assert f_series is not None
    assert len(f_series) == 2
    assert f_series.values[0].value == Decimal("100.5")
    assert f_series.values[1].value == Decimal("101.5")


@pytest.mark.asyncio
async def test_parquet_feature_store_load_missing(tmp_path: Path) -> None:
    store = ParquetFeatureStore(base_dir=tmp_path)
    symbol = Symbol("ETHUSD")
    interval = Interval("1d")

    loaded = await store.load(symbol, interval)
    assert loaded is None
