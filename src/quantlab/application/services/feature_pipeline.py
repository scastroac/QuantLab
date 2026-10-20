"""Feature engineering pipeline service."""

from __future__ import annotations

from collections.abc import Sequence
import logging

from quantlab.application.ports.event_bus import EventBus
from quantlab.application.ports.feature import FeatureRegistry, FeatureStore
from quantlab.domain.entities.feature import FeatureSet
from quantlab.domain.entities.market import Candle
from quantlab.domain.events.feature import FeaturesCalculated
from quantlab.domain.value_objects.feature import FeatureSeries
from quantlab.domain.value_objects.market import Interval, Symbol

logger = logging.getLogger(__name__)


class FeaturePipeline:
    """Orchestrates indicator calculation, event dispatching, and feature persistence."""

    def __init__(
        self,
        registry: FeatureRegistry,
        store: FeatureStore | None = None,
        event_bus: EventBus | None = None,
    ) -> None:
        self.registry = registry
        self.store = store
        self.event_bus = event_bus

    async def compute_features(
        self,
        candles: Sequence[Candle],
        feature_names: Sequence[str] | None = None,
    ) -> FeatureSet:
        """Calculate requested or all registered features for a sequence of candles."""
        if not candles:
            raise ValueError("Candle sequence cannot be empty")

        symbol: Symbol = candles[0].symbol
        interval: Interval = candles[0].interval

        # Collect target calculators
        if feature_names is not None:
            calculators = []
            for name in feature_names:
                calc = self.registry.get(name)
                if calc is None:
                    raise KeyError(f"Feature calculator {name!r} is not registered")
                calculators.append(calc)
        else:
            calculators = self.registry.list_all()

        features: dict[str, FeatureSeries] = {}
        for calc in calculators:
            series = calc.calculate(candles)
            features[calc.name.value] = series

        feature_set = FeatureSet(symbol=symbol, interval=interval, features=features)

        if self.store is not None:
            await self.store.save(feature_set)

        if self.event_bus is not None:
            await self.event_bus.publish(
                FeaturesCalculated(
                    symbol=symbol,
                    interval=interval,
                    feature_names=feature_set.feature_names,
                    sample_count=len(candles),
                )
            )

        return feature_set
