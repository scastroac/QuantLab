"""Market value objects."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal

_SYMBOL_PATTERN = re.compile(r"^[A-Za-z0-9]+([/_\-.:][A-Za-z0-9]+)*$")
_INTERVAL_PATTERN = re.compile(r"^[1-9]\d*[smhdwMy]$")


@dataclass(frozen=True, slots=True)
class Symbol:
    """A financial instrument symbol (e.g. 'BTC/USDT', 'AAPL', 'EUR_USD')."""

    name: str

    def __post_init__(self) -> None:
        if not self.name or not _SYMBOL_PATTERN.match(self.name):
            raise ValueError(f"Invalid financial symbol: {self.name!r}")


@dataclass(frozen=True, slots=True)
class Interval:
    """A quantitative timeframe interval (e.g. '1m', '5m', '1h', '1d', '1w')."""

    name: str

    def __post_init__(self) -> None:
        if not self.name or not _INTERVAL_PATTERN.match(self.name):
            raise ValueError(
                f"Invalid timeframe interval: {self.name!r}. "
                "Expected format matching quantitative timeframes (e.g. '1m', '1h', '1d')."
            )


@dataclass(frozen=True, slots=True)
class Timestamp:
    """A point in time strictly in UTC."""

    value: datetime

    def __post_init__(self) -> None:
        if self.value.tzinfo is None or self.value.utcoffset() != timedelta(0):
            raise ValueError("Timestamp must be timezone-aware and strictly in UTC")


@dataclass(frozen=True, slots=True)
class OHLCV:
    """Validated Open, High, Low, Close, Volume candle data."""

    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: Decimal

    def __post_init__(self) -> None:
        if any(v <= 0 for v in (self.open, self.high, self.low, self.close)):
            raise ValueError("OHLCV price components (open, high, low, close) must be positive")
        if self.volume < 0:
            raise ValueError("OHLCV volume cannot be negative")
        if self.high < self.low:
            raise ValueError(
                f"High price ({self.high}) cannot be lower than low price ({self.low})"
            )
        if self.high < self.open or self.high < self.close:
            raise ValueError(
                f"High price ({self.high}) must be >= open ({self.open}) and close ({self.close})"
            )
        if self.low > self.open or self.low > self.close:
            raise ValueError(
                f"Low price ({self.low}) must be <= open ({self.open}) and close ({self.close})"
            )
