"""Unit tests for built-in quantitative feature indicators."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from quantlab.domain.entities.market import Candle
from quantlab.domain.value_objects.market import OHLCV, Interval, Symbol, Timestamp
from quantlab.infrastructure.features.indicators.momentum import RelativeStrengthIndex
from quantlab.infrastructure.features.indicators.trend import (
    ExponentialMovingAverage,
    SimpleMovingAverage,
)
from quantlab.infrastructure.features.indicators.volatility import (
    AverageTrueRange,
    BollingerLowerBand,
    BollingerUpperBand,
)
from quantlab.infrastructure.features.indicators.volume import VolumeWeightedAveragePrice


def make_candle(
    idx: int,
    close: str,
    high: str | None = None,
    low: str | None = None,
    volume: str = "100.0",
) -> Candle:
    c = Decimal(close)
    h = Decimal(high) if high is not None else c + Decimal("2.0")
    l = Decimal(low) if low is not None else c - Decimal("2.0")
    v = Decimal(volume)
    dt = datetime(2026, 1, 1, tzinfo=UTC) + timedelta(minutes=idx)
    return Candle(
        symbol=Symbol("BTCUSD"),
        interval=Interval("1m"),
        timestamp=Timestamp(dt),
        ohlcv=OHLCV(open=c, high=h, low=l, close=c, volume=v),
    )


def test_sma_calculation() -> None:
    candles = [
        make_candle(0, "10.0"),
        make_candle(1, "20.0"),
        make_candle(2, "30.0"),
        make_candle(3, "40.0"),
    ]
    sma = SimpleMovingAverage(period=3)
    series = sma.calculate(candles)

    # First window (10 + 20 + 30)/3 = 20.0
    # Second window (20 + 30 + 40)/3 = 30.0
    assert len(series) == 2
    assert series.values[0].value == Decimal("20.0")
    assert series.values[1].value == Decimal("30.0")


def test_sma_insufficient_candles() -> None:
    candles = [make_candle(0, "10.0")]
    sma = SimpleMovingAverage(period=3)
    series = sma.calculate(candles)
    assert len(series) == 0


def test_ema_calculation() -> None:
    candles = [
        make_candle(0, "10.0"),
        make_candle(1, "20.0"),
        make_candle(2, "30.0"),
        make_candle(3, "40.0"),
    ]
    ema = ExponentialMovingAverage(period=3)
    series = ema.calculate(candles)

    assert len(series) == 2
    assert series.values[0].value == Decimal("20.0")  # Initial SMA
    # Multiplier = 2 / (3 + 1) = 0.5
    # EMA_1 = 40.0 * 0.5 + 20.0 * 0.5 = 30.0
    assert series.values[1].value == Decimal("30.0")


def test_rsi_calculation() -> None:
    # Ascending series -> gains only -> RSI = 100
    candles = [make_candle(i, str(10 + i)) for i in range(20)]
    rsi = RelativeStrengthIndex(period=14)
    series = rsi.calculate(candles)

    assert len(series) > 0
    assert series.values[-1].value == Decimal("100.0000")


def test_bollinger_bands_calculation() -> None:
    candles = [make_candle(i, "100.0") for i in range(25)]
    upper = BollingerUpperBand(period=20, num_std=2.0)
    lower = BollingerLowerBand(period=20, num_std=2.0)

    upper_series = upper.calculate(candles)
    lower_series = lower.calculate(candles)

    # Flat line -> standard deviation is 0 -> upper == lower == 100.0
    assert upper_series.values[-1].value == Decimal("100.0000")
    assert lower_series.values[-1].value == Decimal("100.0000")


def test_atr_calculation() -> None:
    candles = [make_candle(i, "100.0", high="105.0", low="95.0") for i in range(20)]
    atr = AverageTrueRange(period=14)
    series = atr.calculate(candles)

    assert len(series) > 0
    # True range = high - low = 105 - 95 = 10.0
    assert series.values[0].value == Decimal("10.0000")


def test_vwap_calculation() -> None:
    candles = [
        make_candle(0, "100.0", high="100.0", low="100.0", volume="10.0"),
        make_candle(1, "200.0", high="200.0", low="200.0", volume="10.0"),
    ]
    vwap = VolumeWeightedAveragePrice()
    series = vwap.calculate(candles)

    assert len(series) == 2
    assert series.values[0].value == Decimal("100.0000")
    # Cumulative TP*V = (100*10) + (200*10) = 3000, Cumulative Vol = 20 -> VWAP = 150.0
    assert series.values[1].value == Decimal("150.0000")
