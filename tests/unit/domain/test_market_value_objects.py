"""Unit tests for market domain value objects."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal

import pytest

from quantlab.domain.value_objects.market import OHLCV, Interval, Symbol, Timestamp


class TestSymbol:
    """Test validation and behavior of Symbol value object."""

    @pytest.mark.parametrize(
        "valid_symbol",
        [
            "BTCUSD",
            "BTC/USDT",
            "BTC-USD",
            "EUR_USD",
            "BRK.A",
            "ES:F",
            "AAPL",
            "1000PEPE",
        ],
    )
    def test_valid_symbol(self, valid_symbol: str) -> None:
        symbol = Symbol(valid_symbol)
        assert symbol.name == valid_symbol

    @pytest.mark.parametrize(
        "invalid_symbol",
        [
            "",
            "/BTC",
            "BTC/",
            "BTC//USDT",
            "BTC$",
            "BTC USD",
            "@INVALID",
        ],
    )
    def test_invalid_symbol(self, invalid_symbol: str) -> None:
        with pytest.raises(ValueError, match="Invalid financial symbol"):
            Symbol(invalid_symbol)


class TestInterval:
    """Test validation and behavior of Interval value object."""

    @pytest.mark.parametrize(
        "valid_interval",
        [
            "1s",
            "5s",
            "1m",
            "3m",
            "5m",
            "15m",
            "30m",
            "1h",
            "2h",
            "4h",
            "1d",
            "3d",
            "1w",
            "1M",
            "1y",
        ],
    )
    def test_valid_interval(self, valid_interval: str) -> None:
        interval = Interval(valid_interval)
        assert interval.name == valid_interval

    @pytest.mark.parametrize(
        "invalid_interval",
        [
            "",
            "0m",
            "01m",
            "foo",
            "1x",
            "1hour",
            "1day",
            "-1m",
        ],
    )
    def test_invalid_interval(self, invalid_interval: str) -> None:
        with pytest.raises(ValueError, match="Invalid timeframe interval"):
            Interval(invalid_interval)


class TestTimestamp:
    """Test validation and behavior of Timestamp value object."""

    def test_valid_utc_timestamp(self) -> None:
        now = datetime.now(UTC)
        ts = Timestamp(now)
        assert ts.value == now

    def test_rejects_naive_timestamp(self) -> None:
        naive = datetime(2026, 1, 1, 12, 0, 0)
        with pytest.raises(ValueError, match="timezone-aware and strictly in UTC"):
            Timestamp(naive)

    def test_rejects_non_utc_timestamp(self) -> None:
        est = timezone(timedelta(hours=-5))
        non_utc = datetime(2026, 1, 1, 12, 0, 0, tzinfo=est)
        with pytest.raises(ValueError, match="timezone-aware and strictly in UTC"):
            Timestamp(non_utc)


class TestOHLCV:
    """Test validation and invariants of OHLCV value object."""

    def test_valid_ohlcv(self) -> None:
        candle = OHLCV(
            open=Decimal("100.0"),
            high=Decimal("110.0"),
            low=Decimal("95.0"),
            close=Decimal("105.0"),
            volume=Decimal("1500.5"),
        )
        assert candle.open == Decimal("100.0")
        assert candle.high == Decimal("110.0")
        assert candle.low == Decimal("95.0")
        assert candle.close == Decimal("105.0")
        assert candle.volume == Decimal("1500.5")

    def test_valid_flat_ohlcv(self) -> None:
        candle = OHLCV(
            open=Decimal("100.0"),
            high=Decimal("100.0"),
            low=Decimal("100.0"),
            close=Decimal("100.0"),
            volume=Decimal("0.0"),
        )
        assert candle.volume == Decimal("0.0")

    @pytest.mark.parametrize(
        ("open_", "high", "low", "close", "volume", "error_match"),
        [
            (
                Decimal("0.0"),
                Decimal("10.0"),
                Decimal("5.0"),
                Decimal("8.0"),
                Decimal("100.0"),
                "must be positive",
            ),
            (
                Decimal("-10.0"),
                Decimal("10.0"),
                Decimal("5.0"),
                Decimal("8.0"),
                Decimal("100.0"),
                "must be positive",
            ),
            (
                Decimal("10.0"),
                Decimal("10.0"),
                Decimal("5.0"),
                Decimal("8.0"),
                Decimal("-1.0"),
                "volume cannot be negative",
            ),
            (
                Decimal("10.0"),
                Decimal("5.0"),
                Decimal("15.0"),
                Decimal("8.0"),
                Decimal("100.0"),
                "cannot be lower than low price",
            ),
            (
                Decimal("12.0"),
                Decimal("10.0"),
                Decimal("5.0"),
                Decimal("8.0"),
                Decimal("100.0"),
                "must be >= open",
            ),
            (
                Decimal("8.0"),
                Decimal("10.0"),
                Decimal("5.0"),
                Decimal("12.0"),
                Decimal("100.0"),
                "must be >= open",
            ),
            (
                Decimal("4.0"),
                Decimal("10.0"),
                Decimal("5.0"),
                Decimal("8.0"),
                Decimal("100.0"),
                "must be <= open",
            ),
            (
                Decimal("8.0"),
                Decimal("10.0"),
                Decimal("5.0"),
                Decimal("4.0"),
                Decimal("100.0"),
                "must be <= open",
            ),
        ],
    )
    def test_invalid_ohlcv_invariants(
        self,
        open_: Decimal,
        high: Decimal,
        low: Decimal,
        close: Decimal,
        volume: Decimal,
        error_match: str,
    ) -> None:
        with pytest.raises(ValueError, match=error_match):
            OHLCV(open=open_, high=high, low=low, close=close, volume=volume)
