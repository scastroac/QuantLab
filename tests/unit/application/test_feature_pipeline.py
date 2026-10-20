"""Unit tests for FeaturePipeline application service."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
import logging
from pathlib import Path

import pytest

from quantlab.application.services.feature_pipeline import FeaturePipeline
from quantlab.domain.entities.market import Candle
from quantlab.domain.events.feature import FeaturesCalculated
from quantlab.domain.value_objects.market import OHLCV, Interval, Symbol, Timestamp
from quantlab.infrastructure.features.indicators.trend import SimpleMovingAverage
from quantlab.infrastructure.features.registry import InMemoryFeatureRegistry
from quantlab.infrastructure.messaging.local_event_bus import LocalEventBus
from quantlab.infrastructure.storage.parquet_feature_store import ParquetFeatureStore


def make_candle(idx: int, price: str = "100.0") -> Candle:
    dt = datetime(2026, 1, 1, tzinfo=UTC) + timedelta(minutes=idx)
    p = Decimal(price)
    return Candle(
        symbol=Symbol("BTCUSD"),
        interval=Interval("1m"),
        timestamp=Timestamp(dt),
        ohlcv=OHLCV(open=p, high=p + Decimal(2), low=p - Decimal(2), close=p, volume=Decimal(10)),
    )


@pytest.mark.asyncio
async def test_feature_pipeline_computes_and_dispatches(tmp_path: Path) -> None:
    registry = InMemoryFeatureRegistry()
    registry.register(SimpleMovingAverage(period=2))

    store = ParquetFeatureStore(base_dir=tmp_path)
    event_bus = LocalEventBus(logger=logging.getLogger("test"))

    emitted_events: list[FeaturesCalculated] = []

    async def on_features(event: FeaturesCalculated) -> None:
        emitted_events.append(event)

    event_bus.subscribe(FeaturesCalculated, on_features)

    pipeline = FeaturePipeline(registry=registry, store=store, event_bus=event_bus)

    candles = [make_candle(0, "10.0"), make_candle(1, "20.0"), make_candle(2, "30.0")]
    feature_set = await pipeline.compute_features(candles)

    assert len(feature_set) == 1
    assert "trend:sma_2" in feature_set.feature_names
    assert len(emitted_events) == 1
    assert emitted_events[0].feature_names == ("trend:sma_2",)

    # Verify persisted in store
    loaded = await store.load(candles[0].symbol, candles[0].interval)
    assert loaded is not None
    assert "trend:sma_2" in loaded.feature_names


@pytest.mark.asyncio
async def test_feature_pipeline_empty_candles() -> None:
    registry = InMemoryFeatureRegistry()
    pipeline = FeaturePipeline(registry=registry)

    with pytest.raises(ValueError, match="cannot be empty"):
        await pipeline.compute_features([])


@pytest.mark.asyncio
async def test_feature_pipeline_missing_feature() -> None:
    registry = InMemoryFeatureRegistry()
    pipeline = FeaturePipeline(registry=registry)
    candles = [make_candle(0)]

    with pytest.raises(KeyError, match="is not registered"):
        await pipeline.compute_features(candles, feature_names=["nonexistent:feat"])
