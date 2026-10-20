"""Parquet market data exporter adapter using PyArrow."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

import pyarrow as pa  # type: ignore[import-untyped]
import pyarrow.parquet as pq  # type: ignore[import-untyped]

from quantlab.application.ports.exporter import MarketDataExporter
from quantlab.domain.entities.market import Candle


class ParquetMarketDataExporter(MarketDataExporter):
    """Exports candle series to Apache Parquet files."""

    def export(self, candles: Sequence[Candle], destination: Path) -> Path:
        """Serialize candle series to Parquet and save to destination.

        Args:
            candles: Candle sequence to serialize.
            destination: Target file path.

        Returns:
            The resolved target file path.
        """
        destination.parent.mkdir(parents=True, exist_ok=True)

        data = {
            "symbol": [c.symbol.name for c in candles],
            "interval": [c.interval.name for c in candles],
            "timestamp": [c.timestamp.value for c in candles],
            "open": [float(c.ohlcv.open) for c in candles],
            "high": [float(c.ohlcv.high) for c in candles],
            "low": [float(c.ohlcv.low) for c in candles],
            "close": [float(c.ohlcv.close) for c in candles],
            "volume": [float(c.ohlcv.volume) for c in candles],
        }

        table = pa.Table.from_pydict(data)
        pq.write_table(table, destination)
        return destination
