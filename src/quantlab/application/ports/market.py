"""Market application ports."""

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator

from quantlab.domain.value_objects.market import OHLCV, Interval, Symbol, Timestamp


class MarketDataCollector(ABC):
    """Port for collecting market data from external sources."""

    @abstractmethod
    def collect(
        self, symbol: Symbol, interval: Interval, start: Timestamp, end: Timestamp
    ) -> AsyncIterator[dict[str, str | float | int]]:
        """Collect raw market data within the specified time range."""
        pass


class MarketDataValidator(ABC):
    """Port for validating and cleaning raw market data."""

    @abstractmethod
    def validate(self, raw_data: dict[str, str | float | int]) -> OHLCV:
        """Validate raw data and map it to a domain OHLCV object."""
        pass


class MarketDataStorage(ABC):
    """Port for persisting validated market data."""

    @abstractmethod
    async def store(
        self, symbol: Symbol, interval: Interval, timestamp: Timestamp, ohlcv: OHLCV
    ) -> None:
        """Store the validated market data."""
        pass
