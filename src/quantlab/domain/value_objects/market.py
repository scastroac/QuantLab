"""Market value objects."""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal


@dataclass(frozen=True)
class Symbol:
    """A financial instrument symbol."""

    name: str

    def __post_init__(self) -> None:
        if not self.name or not self.name.isalnum():
            raise ValueError(f"Invalid symbol name: {self.name!r}")


@dataclass(frozen=True)
class Interval:
    """A timeframe interval (e.g. '1m', '1h', '1d')."""

    name: str

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("Interval cannot be empty")


@dataclass(frozen=True)
class Timestamp:
    """A point in time in UTC."""

    value: datetime

    def __post_init__(self) -> None:
        if self.value.tzinfo is None:
            raise ValueError("Timestamp must be timezone-aware (UTC)")


@dataclass(frozen=True)
class OHLCV:
    """Open, High, Low, Close, Volume data."""

    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: Decimal

    def __post_init__(self) -> None:
        if any(v < 0 for v in (self.open, self.high, self.low, self.close, self.volume)):
            raise ValueError("OHLCV values cannot be negative")
