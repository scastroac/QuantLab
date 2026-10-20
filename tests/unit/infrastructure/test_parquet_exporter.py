"""Unit tests for ParquetMarketDataExporter."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

import pyarrow.parquet as pq

from quantlab.domain.entities.market import Candle
from quantlab.domain.value_objects.market import OHLCV, Interval, Symbol, Timestamp
from quantlab.infrastructure.storage.parquet_exporter import ParquetMarketDataExporter


def test_parquet_exporter_exports_candles(tmp_path: Path) -> None:
    exporter = ParquetMarketDataExporter()
    candles = [
        Candle(
            symbol=Symbol("BTC/USDT"),
            interval=Interval("1h"),
            timestamp=Timestamp(datetime(2026, 1, 1, 0, 0, tzinfo=UTC)),
            ohlcv=OHLCV(
                open=Decimal("100.0"),
                high=Decimal("105.0"),
                low=Decimal("95.0"),
                close=Decimal("102.0"),
                volume=Decimal("1000.0"),
            ),
        ),
        Candle(
            symbol=Symbol("BTC/USDT"),
            interval=Interval("1h"),
            timestamp=Timestamp(datetime(2026, 1, 1, 1, 0, tzinfo=UTC)),
            ohlcv=OHLCV(
                open=Decimal("102.0"),
                high=Decimal("108.0"),
                low=Decimal("101.0"),
                close=Decimal("107.0"),
                volume=Decimal("1200.0"),
            ),
        ),
    ]

    target_file = tmp_path / "subfolder" / "candles.parquet"
    result_path = exporter.export(candles, target_file)

    assert result_path == target_file
    assert target_file.exists()

    table = pq.read_table(target_file)
    assert table.num_rows == 2
    assert "symbol" in table.column_names
    assert "close" in table.column_names
    assert table["close"].to_pylist() == [102.0, 107.0]
    assert table["symbol"].to_pylist() == ["BTC/USDT", "BTC/USDT"]
