"""Trend feature indicator calculators."""

from __future__ import annotations

from collections.abc import Sequence
from decimal import Decimal

from quantlab.application.ports.feature import FeatureCalculator
from quantlab.domain.entities.market import Candle
from quantlab.domain.value_objects.feature import FeatureFamily, FeatureName, FeatureSeries, FeatureValue


class SimpleMovingAverage(FeatureCalculator):
    """Computes Simple Moving Average (SMA) over closing prices."""

    def __init__(self, period: int = 20) -> None:
        if period <= 0:
            raise ValueError("SMA period must be positive")
        self.period = period
        self._name = FeatureName(f"trend:sma_{period}")

    @property
    def name(self) -> FeatureName:
        return self._name

    @property
    def family(self) -> FeatureFamily:
        return FeatureFamily.TREND

    @property
    def version(self) -> str:
        return "1.0.0"

    def calculate(self, candles: Sequence[Candle]) -> FeatureSeries:
        if len(candles) < self.period:
            return FeatureSeries(name=self.name, family=self.family, values=())

        values: list[FeatureValue] = []
        prices = [c.ohlcv.close for c in candles]

        # Rolling window average
        window_sum = sum(prices[: self.period])
        avg = window_sum / Decimal(self.period)
        values.append(FeatureValue(timestamp=candles[self.period - 1].timestamp, value=avg))

        for i in range(self.period, len(candles)):
            window_sum += prices[i] - prices[i - self.period]
            avg = window_sum / Decimal(self.period)
            values.append(FeatureValue(timestamp=candles[i].timestamp, value=avg))

        return FeatureSeries(name=self.name, family=self.family, values=tuple(values))


class ExponentialMovingAverage(FeatureCalculator):
    """Computes Exponential Moving Average (EMA) over closing prices."""

    def __init__(self, period: int = 20) -> None:
        if period <= 0:
            raise ValueError("EMA period must be positive")
        self.period = period
        self._name = FeatureName(f"trend:ema_{period}")

    @property
    def name(self) -> FeatureName:
        return self._name

    @property
    def family(self) -> FeatureFamily:
        return FeatureFamily.TREND

    @property
    def version(self) -> str:
        return "1.0.0"

    def calculate(self, candles: Sequence[Candle]) -> FeatureSeries:
        if len(candles) < self.period:
            return FeatureSeries(name=self.name, family=self.family, values=())

        multiplier = Decimal(2) / Decimal(self.period + 1)
        values: list[FeatureValue] = []

        # Initialize with SMA of first window
        initial_ema = sum(c.ohlcv.close for c in candles[: self.period]) / Decimal(self.period)
        values.append(FeatureValue(timestamp=candles[self.period - 1].timestamp, value=initial_ema))

        current_ema = initial_ema
        for i in range(self.period, len(candles)):
            close_price = candles[i].ohlcv.close
            current_ema = (close_price * multiplier) + (current_ema * (Decimal(1) - multiplier))
            values.append(FeatureValue(timestamp=candles[i].timestamp, value=current_ema))

        return FeatureSeries(name=self.name, family=self.family, values=tuple(values))
