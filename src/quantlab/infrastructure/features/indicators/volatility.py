"""Volatility feature indicator calculators."""

from __future__ import annotations

from collections.abc import Sequence
from decimal import Decimal
import math

from quantlab.application.ports.feature import FeatureCalculator
from quantlab.domain.entities.market import Candle
from quantlab.domain.value_objects.feature import FeatureFamily, FeatureName, FeatureSeries, FeatureValue


class BollingerUpperBand(FeatureCalculator):
    """Computes Bollinger Upper Band: SMA + (num_std * rolling_std)."""

    def __init__(self, period: int = 20, num_std: float = 2.0) -> None:
        if period <= 1:
            raise ValueError("Bollinger period must be > 1")
        self.period = period
        self.num_std = Decimal(str(num_std))
        self._name = FeatureName(f"volatility:bb_upper_{period}")

    @property
    def name(self) -> FeatureName:
        return self._name

    @property
    def family(self) -> FeatureFamily:
        return FeatureFamily.VOLATILITY

    @property
    def version(self) -> str:
        return "1.0.0"

    def calculate(self, candles: Sequence[Candle]) -> FeatureSeries:
        if len(candles) < self.period:
            return FeatureSeries(name=self.name, family=self.family, values=())

        values: list[FeatureValue] = []
        prices = [c.ohlcv.close for c in candles]

        for i in range(self.period - 1, len(candles)):
            window = prices[i - self.period + 1 : i + 1]
            mean = sum(window) / Decimal(self.period)
            variance = sum((p - mean) ** 2 for p in window) / Decimal(self.period)
            std = Decimal(str(math.sqrt(float(variance))))
            upper = mean + (self.num_std * std)
            values.append(
                FeatureValue(timestamp=candles[i].timestamp, value=round(upper, 4))
            )

        return FeatureSeries(name=self.name, family=self.family, values=tuple(values))


class BollingerLowerBand(FeatureCalculator):
    """Computes Bollinger Lower Band: SMA - (num_std * rolling_std)."""

    def __init__(self, period: int = 20, num_std: float = 2.0) -> None:
        if period <= 1:
            raise ValueError("Bollinger period must be > 1")
        self.period = period
        self.num_std = Decimal(str(num_std))
        self._name = FeatureName(f"volatility:bb_lower_{period}")

    @property
    def name(self) -> FeatureName:
        return self._name

    @property
    def family(self) -> FeatureFamily:
        return FeatureFamily.VOLATILITY

    @property
    def version(self) -> str:
        return "1.0.0"

    def calculate(self, candles: Sequence[Candle]) -> FeatureSeries:
        if len(candles) < self.period:
            return FeatureSeries(name=self.name, family=self.family, values=())

        values: list[FeatureValue] = []
        prices = [c.ohlcv.close for c in candles]

        for i in range(self.period - 1, len(candles)):
            window = prices[i - self.period + 1 : i + 1]
            mean = sum(window) / Decimal(self.period)
            variance = sum((p - mean) ** 2 for p in window) / Decimal(self.period)
            std = Decimal(str(math.sqrt(float(variance))))
            lower = mean - (self.num_std * std)
            values.append(
                FeatureValue(timestamp=candles[i].timestamp, value=round(lower, 4))
            )

        return FeatureSeries(name=self.name, family=self.family, values=tuple(values))


class AverageTrueRange(FeatureCalculator):
    """Computes Average True Range (ATR)."""

    def __init__(self, period: int = 14) -> None:
        if period <= 0:
            raise ValueError("ATR period must be positive")
        self.period = period
        self._name = FeatureName(f"volatility:atr_{period}")

    @property
    def name(self) -> FeatureName:
        return self._name

    @property
    def family(self) -> FeatureFamily:
        return FeatureFamily.VOLATILITY

    @property
    def version(self) -> str:
        return "1.0.0"

    def calculate(self, candles: Sequence[Candle]) -> FeatureSeries:
        if len(candles) <= self.period:
            return FeatureSeries(name=self.name, family=self.family, values=())

        tr_values: list[Decimal] = []
        for i in range(1, len(candles)):
            high = candles[i].ohlcv.high
            low = candles[i].ohlcv.low
            prev_close = candles[i - 1].ohlcv.close

            hl = high - low
            hpc = abs(high - prev_close)
            lpc = abs(low - prev_close)

            tr = max(hl, hpc, lpc)
            tr_values.append(tr)

        values: list[FeatureValue] = []
        current_atr = sum(tr_values[: self.period]) / Decimal(self.period)
        values.append(
            FeatureValue(timestamp=candles[self.period].timestamp, value=round(current_atr, 4))
        )

        for i in range(self.period, len(tr_values)):
            current_atr = (
                (current_atr * Decimal(self.period - 1)) + tr_values[i]
            ) / Decimal(self.period)
            values.append(
                FeatureValue(
                    timestamp=candles[i + 1].timestamp,
                    value=round(current_atr, 4),
                )
            )

        return FeatureSeries(name=self.name, family=self.family, values=tuple(values))
