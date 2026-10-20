"""Market domain entities."""

from __future__ import annotations

from dataclasses import dataclass

from quantlab.domain.value_objects.market import OHLCV, Interval, Symbol, Timestamp


@dataclass(frozen=True, slots=True)
class Candle:
    """An immutable financial candlestick entity."""

    symbol: Symbol
    interval: Interval
    timestamp: Timestamp
    ohlcv: OHLCV
