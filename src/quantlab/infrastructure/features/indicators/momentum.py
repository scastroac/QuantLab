"""Momentum feature indicator calculators."""

from __future__ import annotations

from collections.abc import Sequence
from decimal import Decimal

from quantlab.application.ports.feature import FeatureCalculator
from quantlab.domain.entities.market import Candle
from quantlab.domain.value_objects.feature import FeatureFamily, FeatureName, FeatureSeries, FeatureValue


class RelativeStrengthIndex(FeatureCalculator):
    """Computes Relative Strength Index (RSI)."""

    def __init__(self, period: int = 14) -> None:
        if period <= 0:
            raise ValueError("RSI period must be positive")
        self.period = period
        self._name = FeatureName(f"momentum:rsi_{period}")

    @property
    def name(self) -> FeatureName:
        return self._name

    @property
    def family(self) -> FeatureFamily:
        return FeatureFamily.MOMENTUM

    @property
    def version(self) -> str:
        return "1.0.0"

    def calculate(self, candles: Sequence[Candle]) -> FeatureSeries:
        if len(candles) <= self.period:
            return FeatureSeries(name=self.name, family=self.family, values=())

        changes = [
            candles[i].ohlcv.close - candles[i - 1].ohlcv.close
            for i in range(1, len(candles))
        ]

        gains = [max(c, Decimal(0)) for c in changes]
        losses = [max(-c, Decimal(0)) for c in changes]

        # Initial averages
        avg_gain = sum(gains[: self.period]) / Decimal(self.period)
        avg_loss = sum(losses[: self.period]) / Decimal(self.period)

        values: list[FeatureValue] = []

        if avg_loss == Decimal(0):
            rsi = Decimal(100)
        else:
            rs = avg_gain / avg_loss
            rsi = Decimal(100) - (Decimal(100) / (Decimal(1) + rs))

        values.append(FeatureValue(timestamp=candles[self.period].timestamp, value=round(rsi, 4)))

        # Smoothed Wilder calculation for subsequent steps
        for i in range(self.period, len(changes)):
            gain = gains[i]
            loss = losses[i]

            avg_gain = ((avg_gain * Decimal(self.period - 1)) + gain) / Decimal(self.period)
            avg_loss = ((avg_loss * Decimal(self.period - 1)) + loss) / Decimal(self.period)

            if avg_loss == Decimal(0):
                rsi = Decimal(100)
            else:
                rs = avg_gain / avg_loss
                rsi = Decimal(100) - (Decimal(100) / (Decimal(1) + rs))

            values.append(
                FeatureValue(timestamp=candles[i + 1].timestamp, value=round(rsi, 4))
            )

        return FeatureSeries(name=self.name, family=self.family, values=tuple(values))
