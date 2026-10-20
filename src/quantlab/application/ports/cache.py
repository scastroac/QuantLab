"""Market data cache port."""

from __future__ import annotations

from abc import ABC, abstractmethod

from quantlab.domain.entities.market import Candle
from quantlab.domain.value_objects.market import Interval, Symbol, Timestamp


class MarketDataCache(ABC):
    """Port for temporary caching of candle data."""

    @abstractmethod
    async def get_candle(
        self, symbol: Symbol, interval: Interval, timestamp: Timestamp
    ) -> Candle | None:
        """Retrieve a cached candle if present and not expired."""
        pass

    @abstractmethod
    async def set_candle(self, candle: Candle, ttl_seconds: int | None = None) -> None:
        """Cache a candle with an optional time-to-live in seconds."""
        pass

    @abstractmethod
    async def clear(self) -> None:
        """Clear all cached entries."""
        pass
