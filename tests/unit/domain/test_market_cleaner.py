"""Unit tests for MarketDataCleaner domain service."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from quantlab.domain.entities.market import Candle
from quantlab.domain.services.market_cleaner import MarketDataCleaner, interval_to_timedelta
from quantlab.domain.value_objects.market import OHLCV, Interval, Symbol, Timestamp


def make_candle(dt: datetime, close_price: str = "100.0") -> Candle:
    """Helper to construct a valid test candle."""
    price = Decimal(close_price)
    return Candle(
        symbol=Symbol("BTC/USDT"),
        interval=Interval("1m"),
        timestamp=Timestamp(dt),
        ohlcv=OHLCV(
            open=price,
            high=price + Decimal("5.0"),
            low=price - Decimal("5.0"),
            close=price,
            volume=Decimal("10.0"),
        ),
    )


def test_interval_to_timedelta_valid() -> None:
    assert interval_to_timedelta(Interval("10s")) == timedelta(seconds=10)
    assert interval_to_timedelta(Interval("1m")) == timedelta(minutes=1)
    assert interval_to_timedelta(Interval("2h")) == timedelta(hours=2)
    assert interval_to_timedelta(Interval("1d")) == timedelta(days=1)
    assert interval_to_timedelta(Interval("2w")) == timedelta(weeks=2)


def test_interval_to_timedelta_unsupported() -> None:
    with pytest.raises(ValueError, match="cannot be converted to a fixed timedelta"):
        interval_to_timedelta(Interval("1M"))


def test_cleaner_empty_sequence() -> None:
    cleaner = MarketDataCleaner()
    candles, gaps = cleaner.clean([])
    assert candles == []
    assert gaps == []


def test_cleaner_rejects_mixed_symbols() -> None:
    cleaner = MarketDataCleaner()
    c1 = make_candle(datetime(2026, 1, 1, 0, 0, tzinfo=UTC))
    c2 = Candle(
        symbol=Symbol("ETH/USDT"),
        interval=Interval("1m"),
        timestamp=Timestamp(datetime(2026, 1, 1, 0, 1, tzinfo=UTC)),
        ohlcv=c1.ohlcv,
    )
    with pytest.raises(ValueError, match="share the same symbol"):
        cleaner.clean([c1, c2])


def test_cleaner_sorts_and_deduplicates() -> None:
    cleaner = MarketDataCleaner()
    t0 = datetime(2026, 1, 1, 0, 0, tzinfo=UTC)
    t1 = datetime(2026, 1, 1, 0, 1, tzinfo=UTC)

    c_first = make_candle(t0, close_price="100.0")
    c_duplicate = make_candle(t0, close_price="105.0")  # Updated tick
    c_second = make_candle(t1, close_price="110.0")

    # Pass in unsorted order with a duplicate
    cleaned, gaps = cleaner.clean([c_second, c_first, c_duplicate])

    assert len(cleaned) == 2
    assert cleaned[0].timestamp.value == t0
    assert cleaned[0].ohlcv.close == Decimal("105.0")  # Kept latest duplicate
    assert cleaned[1].timestamp.value == t1
    assert gaps == []


def test_cleaner_detects_missing_gaps() -> None:
    cleaner = MarketDataCleaner()
    t0 = datetime(2026, 1, 1, 0, 0, tzinfo=UTC)
    t1 = datetime(2026, 1, 1, 0, 1, tzinfo=UTC)
    # Gap from 00:01 to 00:05 (missing 00:02, 00:03, 00:04 = 3 missing candles)
    t4 = datetime(2026, 1, 1, 0, 5, tzinfo=UTC)

    c0 = make_candle(t0)
    c1 = make_candle(t1)
    c4 = make_candle(t4)

    cleaned, gaps = cleaner.clean([c0, c1, c4])

    assert len(cleaned) == 3
    assert len(gaps) == 1
    assert gaps[0].missing_intervals == 3
    assert gaps[0].expected_timestamp.value == datetime(2026, 1, 1, 0, 2, tzinfo=UTC)
    assert gaps[0].actual_timestamp.value == t4
