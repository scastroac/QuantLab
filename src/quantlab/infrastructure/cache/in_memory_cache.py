"""In-memory market data cache adapter."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta

from quantlab.application.ports.cache import MarketDataCache
from quantlab.domain.entities.market import Candle
from quantlab.domain.value_objects.market import Interval, Symbol, Timestamp


class InMemoryMarketDataCache(MarketDataCache):
    """Thread-safe in-memory cache for candles with optional TTL."""

    def __init__(self) -> None:
        self._cache: dict[tuple[str, str, datetime], tuple[Candle, datetime | None]] = {}
        self._lock = asyncio.Lock()

    async def get_candle(
        self, symbol: Symbol, interval: Interval, timestamp: Timestamp
    ) -> Candle | None:
        """Retrieve a candle if present and not expired."""
        key = (symbol.name, interval.name, timestamp.value)
        async with self._lock:
            entry = self._cache.get(key)
            if entry is None:
                return None

            candle, expires_at = entry
            if expires_at is not None and datetime.now(UTC) > expires_at:
                del self._cache[key]
                return None

            return candle

    async def set_candle(self, candle: Candle, ttl_seconds: int | None = None) -> None:
        """Store a candle in cache with optional TTL in seconds."""
        key = (candle.symbol.name, candle.interval.name, candle.timestamp.value)
        expires_at = datetime.now(UTC) + timedelta(seconds=ttl_seconds) if ttl_seconds else None
        async with self._lock:
            self._cache[key] = (candle, expires_at)

    async def clear(self) -> None:
        """Purge all entries from the cache."""
        async with self._lock:
            self._cache.clear()
