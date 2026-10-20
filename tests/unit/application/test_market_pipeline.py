"""Tests for the market data pipeline."""

import logging
from collections.abc import AsyncIterator
from datetime import UTC, datetime
from decimal import Decimal

import pytest

from quantlab.application.ports.market import MarketDataCollector, MarketDataStorage
from quantlab.application.services.market_data_pipeline import (
    BasicMarketDataValidator,
    MarketDataPipeline,
)
from quantlab.domain.events.market import DataCollected, DataStored, DataValidated
from quantlab.domain.value_objects.market import OHLCV, Interval, Symbol, Timestamp
from quantlab.infrastructure.messaging.local_event_bus import LocalEventBus


class MockCollector(MarketDataCollector):
    async def collect(
        self, symbol: Symbol, interval: Interval, start: Timestamp, end: Timestamp
    ) -> AsyncIterator[dict[str, str | float | int]]:
        yield {
            "symbol": symbol.name,
            "interval": interval.name,
            "timestamp": "2026-01-01T00:00:00Z",
            "open": 100.0,
            "high": 105.0,
            "low": 95.0,
            "close": 102.0,
            "volume": 1000.0,
        }
        # Malformed record that should be skipped by validator
        yield {
            "symbol": symbol.name,
            "interval": interval.name,
            "timestamp": "2026-01-01T01:00:00Z",
            "open": 100.0,
            "high": 105.0,
            "low": -5.0,  # Negative value invalid for OHLCV
            "close": 102.0,
            "volume": 1000.0,
        }


class MockStorage(MarketDataStorage):
    def __init__(self) -> None:
        self.stored: list[tuple[Symbol, Interval, Timestamp, OHLCV]] = []

    async def store(
        self, symbol: Symbol, interval: Interval, timestamp: Timestamp, ohlcv: OHLCV
    ) -> None:
        self.stored.append((symbol, interval, timestamp, ohlcv))


@pytest.mark.asyncio
async def test_market_data_pipeline() -> None:
    collector = MockCollector()
    validator = BasicMarketDataValidator()
    storage = MockStorage()
    event_bus = LocalEventBus(logging.getLogger("test"))

    collected_events = []
    validated_events = []
    stored_events = []

    async def on_collected(event: DataCollected) -> None:
        collected_events.append(event)

    async def on_validated(event: DataValidated) -> None:
        validated_events.append(event)

    async def on_stored(event: DataStored) -> None:
        stored_events.append(event)

    event_bus.subscribe(DataCollected, on_collected)
    event_bus.subscribe(DataValidated, on_validated)
    event_bus.subscribe(DataStored, on_stored)

    pipeline = MarketDataPipeline(collector, validator, storage, event_bus)

    start = datetime(2026, 1, 1, tzinfo=UTC)
    end = datetime(2026, 1, 2, tzinfo=UTC)

    await pipeline.run_pipeline("BTCUSD", "1h", start, end)

    # We expect 2 collected events (since one is invalid but still collected)
    assert len(collected_events) == 2
    # We expect 1 validated and 1 stored event
    assert len(validated_events) == 1
    assert len(stored_events) == 1
    assert len(storage.stored) == 1

    stored_item = storage.stored[0]
    assert stored_item[0].name == "BTCUSD"
    assert stored_item[1].name == "1h"
    assert stored_item[3].close == Decimal("102.0")
