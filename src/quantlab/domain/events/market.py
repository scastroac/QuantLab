"""Market domain events."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from quantlab.domain.events.base import DomainEvent
from quantlab.domain.value_objects.market import OHLCV, Interval, Symbol, Timestamp


@dataclass(frozen=True, kw_only=True, slots=True)
class DataCollected(DomainEvent):
    """Event emitted when raw market data is collected."""

    symbol: Symbol
    interval: Interval
    timestamp: Timestamp
    raw_data: dict[str, Any]


@dataclass(frozen=True, kw_only=True, slots=True)
class DataValidated(DomainEvent):
    """Event emitted when raw data has been successfully validated and cleaned."""

    symbol: Symbol
    interval: Interval
    timestamp: Timestamp
    ohlcv: OHLCV


@dataclass(frozen=True, kw_only=True, slots=True)
class DataStored(DomainEvent):
    """Event emitted when validated data has been persisted to storage."""

    symbol: Symbol
    interval: Interval
    timestamp: Timestamp


@dataclass(frozen=True, kw_only=True, slots=True)
class GapDetected(DomainEvent):
    """Event emitted when a gap is detected in market data candles."""

    symbol: Symbol
    interval: Interval
    expected_timestamp: Timestamp
    actual_timestamp: Timestamp
    missing_intervals: int


@dataclass(frozen=True, kw_only=True, slots=True)
class DataCleaned(DomainEvent):
    """Event emitted when a sequence of market data candles is cleaned and normalized."""

    symbol: Symbol
    interval: Interval
    total_input_count: int
    total_output_count: int
    duplicates_removed: int
