"""CSV file based market data collector adapter."""

from __future__ import annotations

import csv
from collections.abc import AsyncIterator
from datetime import UTC, datetime
from pathlib import Path

from quantlab.application.ports.market import MarketDataCollector
from quantlab.domain.value_objects.market import Interval, Symbol, Timestamp


class CsvMarketDataCollector(MarketDataCollector):
    """Adapter to collect market data from a CSV file."""

    def __init__(self, file_path: Path) -> None:
        self.file_path = file_path

    async def collect(
        self, symbol: Symbol, interval: Interval, start: Timestamp, end: Timestamp
    ) -> AsyncIterator[dict[str, str | float | int]]:
        """Yield rows from the CSV file that match the symbol, interval, and time range."""
        if not self.file_path.exists():
            raise FileNotFoundError(f"CSV file not found: {self.file_path}")

        with self.file_path.open(mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get("symbol") != symbol.name or row.get("interval") != interval.name:
                    continue

                ts_str = row.get("timestamp")
                if ts_str is not None:
                    try:
                        row_dt = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                        if row_dt.tzinfo is None:
                            row_dt = row_dt.replace(tzinfo=UTC)
                        if not (start.value <= row_dt <= end.value):
                            continue
                    except ValueError:
                        continue

                yield dict(row)
