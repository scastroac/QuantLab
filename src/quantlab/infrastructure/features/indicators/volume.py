"""Volume feature indicator calculators."""

from __future__ import annotations

from collections.abc import Sequence
from decimal import Decimal

from quantlab.application.ports.feature import FeatureCalculator
from quantlab.domain.entities.market import Candle
from quantlab.domain.value_objects.feature import FeatureFamily, FeatureName, FeatureSeries, FeatureValue


class VolumeWeightedAveragePrice(FeatureCalculator):
    """Computes Volume Weighted Average Price (VWAP)."""

    def __init__(self) -> None:
        self._name = FeatureName("volume:vwap")

    @property
    def name(self) -> FeatureName:
        return self._name

    @property
    def family(self) -> FeatureFamily:
        return FeatureFamily.VOLUME

    @property
    def version(self) -> str:
        return "1.0.0"

    def calculate(self, candles: Sequence[Candle]) -> FeatureSeries:
        if not candles:
            return FeatureSeries(name=self.name, family=self.family, values=())

        values: list[FeatureValue] = []
        cumulative_tp_vol = Decimal(0)
        cumulative_vol = Decimal(0)

        for c in candles:
            typical_price = (c.ohlcv.high + c.ohlcv.low + c.ohlcv.close) / Decimal(3)
            cumulative_tp_vol += typical_price * c.ohlcv.volume
            cumulative_vol += c.ohlcv.volume

            if cumulative_vol == Decimal(0):
                vwap = typical_price
            else:
                vwap = cumulative_tp_vol / cumulative_vol

            values.append(
                FeatureValue(timestamp=c.timestamp, value=round(vwap, 4))
            )

        return FeatureSeries(name=self.name, family=self.family, values=tuple(values))
