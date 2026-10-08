"""CSV file based market data collector adapter."""

import csv
from collections.abc import AsyncIterator
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
        """Yield rows from the CSV file that match the symbol and interval."""
        if not self.file_path.exists():
            raise FileNotFoundError(f"CSV file not found: {self.file_path}")

        # In a real async implementation this would use aiofiles,
        # but for simplicity in Sprint 2a we yield synchronously wrapped in async
        with self.file_path.open(mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Basic mock logic, assuming CSV has 'symbol' and 'interval'
                # and timestamp is within range (ignoring time filtering for now to keep it simple)
                if row.get("symbol") == symbol.name and row.get("interval") == interval.name:
                    yield {k: (float(v) if self._is_float(v) else v) for k, v in row.items()}

    def _is_float(self, value: str) -> bool:
        try:
            float(value)
            return True
        except ValueError:
            return False
