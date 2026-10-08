"""Market domain events."""

from dataclasses import dataclass
from typing import Any

from quantlab.domain.events.base import DomainEvent
from quantlab.domain.value_objects.market import OHLCV, Interval, Symbol, Timestamp


@dataclass(frozen=True)
class DataCollected(DomainEvent):
    """Event emitted when raw market data is collected."""

    symbol: Symbol
    interval: Interval
    timestamp: Timestamp
    raw_data: dict[str, Any]


@dataclass(frozen=True)
class DataValidated(DomainEvent):
    """Event emitted when raw data has been successfully validated and cleaned."""

    symbol: Symbol
    interval: Interval
    timestamp: Timestamp
    ohlcv: OHLCV


@dataclass(frozen=True)
class DataStored(DomainEvent):
    """Event emitted when validated data has been persisted to storage."""

    symbol: Symbol
    interval: Interval
    timestamp: Timestamp
