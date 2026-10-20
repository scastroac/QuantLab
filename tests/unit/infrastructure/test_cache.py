"""Unit tests for InMemoryMarketDataCache."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

import pytest

from quantlab.domain.entities.market import Candle
from quantlab.domain.value_objects.market import OHLCV, Interval, Symbol, Timestamp
from quantlab.infrastructure.cache.in_memory_cache import InMemoryMarketDataCache


def make_candle() -> Candle:
    return Candle(
        symbol=Symbol("BTCUSD"),
        interval=Interval("1m"),
        timestamp=Timestamp(datetime(2026, 1, 1, 0, 0, tzinfo=UTC)),
        ohlcv=OHLCV(
            open=Decimal("100.0"),
            high=Decimal("105.0"),
            low=Decimal("95.0"),
            close=Decimal("102.0"),
            volume=Decimal("100.0"),
        ),
    )


@pytest.mark.asyncio
async def test_cache_set_and_get() -> None:
    cache = InMemoryMarketDataCache()
    candle = make_candle()

    assert await cache.get_candle(candle.symbol, candle.interval, candle.timestamp) is None

    await cache.set_candle(candle)
    cached = await cache.get_candle(candle.symbol, candle.interval, candle.timestamp)

    assert cached is not None
    assert cached.symbol == candle.symbol
    assert cached.ohlcv.close == Decimal("102.0")


@pytest.mark.asyncio
async def test_cache_expiration() -> None:
    cache = InMemoryMarketDataCache()
    candle = make_candle()

    # Expire in 0 seconds (immediate expiration)
    await cache.set_candle(candle, ttl_seconds=-1)
    cached = await cache.get_candle(candle.symbol, candle.interval, candle.timestamp)
    assert cached is None


@pytest.mark.asyncio
async def test_cache_clear() -> None:
    cache = InMemoryMarketDataCache()
    candle = make_candle()

    await cache.set_candle(candle)
    await cache.clear()

    assert await cache.get_candle(candle.symbol, candle.interval, candle.timestamp) is None
