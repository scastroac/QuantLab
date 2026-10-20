"""Unit tests for BinanceMarketDataCollector."""

from __future__ import annotations

from datetime import UTC, datetime

import httpx
import pytest

from quantlab.domain.value_objects.market import Interval, Symbol, Timestamp
from quantlab.infrastructure.collectors.binance_collector import BinanceMarketDataCollector


@pytest.mark.asyncio
async def test_binance_collector_success() -> None:
    sample_response = [
        [
            1767225600000,
            "90000.00",
            "91000.00",
            "89500.00",
            "90500.00",
            "120.50",
            1767229199999,
            "10905250.00",
            1500,
            "60.25",
            "5452625.00",
            "0",
        ]
    ]

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.params["symbol"] == "BTCUSDT"
        assert request.url.params["interval"] == "1h"
        return httpx.Response(200, json=sample_response)

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        collector = BinanceMarketDataCollector(client=client)
        symbol = Symbol("BTC/USDT")
        interval = Interval("1h")
        start = Timestamp(datetime(2026, 1, 1, 0, 0, tzinfo=UTC))
        end = Timestamp(datetime(2026, 1, 1, 1, 0, tzinfo=UTC))

        results = [row async for row in collector.collect(symbol, interval, start, end)]

        assert len(results) == 1
        assert results[0]["symbol"] == "BTC/USDT"
        assert results[0]["open"] == "90000.00"
        assert results[0]["close"] == "90500.00"


@pytest.mark.asyncio
async def test_binance_collector_http_error() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(400, json={"code": -1121, "msg": "Invalid symbol."})

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        collector = BinanceMarketDataCollector(client=client)
        symbol = Symbol("INVALID")
        interval = Interval("1h")
        start = Timestamp(datetime(2026, 1, 1, 0, 0, tzinfo=UTC))
        end = Timestamp(datetime(2026, 1, 1, 1, 0, tzinfo=UTC))

        with pytest.raises(httpx.HTTPStatusError):
            _ = [row async for row in collector.collect(symbol, interval, start, end)]
