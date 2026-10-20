"""Market data export port."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence
from pathlib import Path

from quantlab.domain.entities.market import Candle


class MarketDataExporter(ABC):
    """Port for serializing candle series into analytical data formats (e.g. Parquet, CSV)."""

    @abstractmethod
    def export(self, candles: Sequence[Candle], destination: Path) -> Path:
        """Export candles to a target destination and return the resolved file path."""
        pass
