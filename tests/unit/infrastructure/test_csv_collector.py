"""Unit tests for CsvMarketDataCollector."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest

from quantlab.domain.value_objects.market import Interval, Symbol, Timestamp
from quantlab.infrastructure.collectors.csv_collector import CsvMarketDataCollector


@pytest.mark.asyncio
async def test_csv_collector_collects_matching_rows(tmp_path: Path) -> None:
    csv_file = tmp_path / "market_data.csv"
    csv_file.write_text(
        "symbol,interval,timestamp,open,high,low,close,volume\n"
        "BTC/USDT,1h,2026-01-01T00:00:00Z,100,105,95,102,1000\n"
        "BTC/USDT,1h,2026-01-01T01:00:00Z,102,108,100,106,1200\n"
        "ETH/USDT,1h,2026-01-01T00:00:00Z,2000,2050,1950,2020,500\n"
        "BTC/USDT,1d,2026-01-01T00:00:00Z,100,110,90,105,5000\n"
        "BTC/USDT,1h,2026-01-02T00:00:00Z,106,110,104,108,800\n",
        encoding="utf-8",
    )

    collector = CsvMarketDataCollector(csv_file)
    symbol = Symbol("BTC/USDT")
    interval = Interval("1h")
    start = Timestamp(datetime(2026, 1, 1, 0, 0, 0, tzinfo=UTC))
    end = Timestamp(datetime(2026, 1, 1, 12, 0, 0, tzinfo=UTC))

    collected = [row async for row in collector.collect(symbol, interval, start, end)]

    assert len(collected) == 2
    assert collected[0]["timestamp"] == "2026-01-01T00:00:00Z"
    assert collected[1]["timestamp"] == "2026-01-01T01:00:00Z"


@pytest.mark.asyncio
async def test_csv_collector_raises_on_missing_file(tmp_path: Path) -> None:
    missing_file = tmp_path / "nonexistent.csv"
    collector = CsvMarketDataCollector(missing_file)
    symbol = Symbol("BTCUSD")
    interval = Interval("1h")
    start = Timestamp(datetime(2026, 1, 1, tzinfo=UTC))
    end = Timestamp(datetime(2026, 1, 2, tzinfo=UTC))

    with pytest.raises(FileNotFoundError, match="CSV file not found"):
        _ = [row async for row in collector.collect(symbol, interval, start, end)]


@pytest.mark.asyncio
async def test_csv_collector_ignores_malformed_timestamp(tmp_path: Path) -> None:
    csv_file = tmp_path / "market_data.csv"
    csv_file.write_text(
        "symbol,interval,timestamp,open,high,low,close,volume\n"
        "BTCUSD,1h,not-a-valid-date,100,105,95,102,1000\n",
        encoding="utf-8",
    )
    collector = CsvMarketDataCollector(csv_file)
    symbol = Symbol("BTCUSD")
    interval = Interval("1h")
    start = Timestamp(datetime(2026, 1, 1, tzinfo=UTC))
    end = Timestamp(datetime(2026, 1, 2, tzinfo=UTC))

    collected = [row async for row in collector.collect(symbol, interval, start, end)]
    assert collected == []
