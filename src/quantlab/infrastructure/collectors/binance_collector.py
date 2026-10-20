"""Binance public REST market data collector adapter."""

from __future__ import annotations

from collections.abc import AsyncIterator
from datetime import UTC, datetime
from typing import Any

import httpx

from quantlab.application.ports.market import MarketDataCollector
from quantlab.domain.value_objects.market import Interval, Symbol, Timestamp

_DEFAULT_BASE_URL = "https://api.binance.com"


class BinanceMarketDataCollector(MarketDataCollector):
    """Fetches public candlestick data from the Binance REST API."""

    def __init__(
        self,
        base_url: str = _DEFAULT_BASE_URL,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self._client = client

    def _normalize_symbol(self, symbol: Symbol) -> str:
        """Strip delimiters to format symbols as expected by Binance (e.g. BTCUSDT)."""
        return symbol.name.replace("/", "").replace("-", "").replace("_", "").upper()

    async def collect(
        self, symbol: Symbol, interval: Interval, start: Timestamp, end: Timestamp
    ) -> AsyncIterator[dict[str, str | float | int]]:
        """Query Binance klines endpoint and yield raw candle records."""
        url = f"{self.base_url}/api/v3/klines"
        params: dict[str, Any] = {
            "symbol": self._normalize_symbol(symbol),
            "interval": interval.name,
            "startTime": int(start.value.timestamp() * 1000),
            "endTime": int(end.value.timestamp() * 1000),
            "limit": 1000,
        }

        should_close = False
        client = self._client
        if client is None:
            client = httpx.AsyncClient()
            should_close = True

        try:
            response = await client.get(url, params=params, timeout=10.0)
            response.raise_for_status()
            data = response.json()

            for kline in data:
                # kline structure:
                # [0: open_time, 1: open, 2: high, 3: low, 4: close, 5: volume, ...]
                open_time_ms = int(kline[0])
                dt = datetime.fromtimestamp(open_time_ms / 1000.0, tz=UTC)

                yield {
                    "symbol": symbol.name,
                    "interval": interval.name,
                    "timestamp": dt.isoformat(),
                    "open": str(kline[1]),
                    "high": str(kline[2]),
                    "low": str(kline[3]),
                    "close": str(kline[4]),
                    "volume": str(kline[5]),
                }
        finally:
            if should_close:
                await client.aclose()
