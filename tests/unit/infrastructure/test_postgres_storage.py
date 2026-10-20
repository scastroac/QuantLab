"""Unit tests for PostgresMarketDataStorage."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from quantlab.domain.value_objects.market import OHLCV, Interval, Symbol, Timestamp
from quantlab.infrastructure.storage.postgres_market_storage import PostgresMarketDataStorage


@pytest.mark.asyncio
async def test_postgres_storage_connect_and_store() -> None:
    mock_conn = AsyncMock()
    mock_pool = MagicMock()

    class MockAcquireContext:
        async def __aenter__(self) -> AsyncMock:
            return mock_conn

        async def __aexit__(self, exc_type: object, exc_val: object, exc_tb: object) -> None:
            pass

    mock_pool.acquire.return_value = MockAcquireContext()
    mock_pool.close = AsyncMock()

    with patch("asyncpg.create_pool", new_callable=AsyncMock) as mock_create_pool:
        mock_create_pool.return_value = mock_pool
        storage = PostgresMarketDataStorage(dsn="postgresql://user:pass@localhost:5432/testdb")

        async with storage:
            assert storage._pool is not None
            mock_create_pool.assert_awaited_once_with(
                "postgresql://user:pass@localhost:5432/testdb"
            )
            mock_conn.execute.assert_awaited()

            symbol = Symbol("BTCUSD")
            interval = Interval("1h")
            timestamp = Timestamp(datetime(2026, 1, 1, 0, 0, 0, tzinfo=UTC))
            ohlcv = OHLCV(
                open=Decimal("100.0"),
                high=Decimal("105.0"),
                low=Decimal("95.0"),
                close=Decimal("102.0"),
                volume=Decimal("1000.0"),
            )

            await storage.store(symbol, interval, timestamp, ohlcv)

            call_args = mock_conn.execute.call_args[0]
            assert "INSERT INTO market_data" in call_args[0]
            assert call_args[1] == timestamp.value
            assert call_args[2] == "BTCUSD"
            assert call_args[3] == "1h"
            assert call_args[4] == Decimal("100.0")
            assert call_args[5] == Decimal("105.0")
            assert call_args[6] == Decimal("95.0")
            assert call_args[7] == Decimal("102.0")
            assert call_args[8] == Decimal("1000.0")

        mock_pool.close.assert_awaited_once()
        assert storage._pool is None


@pytest.mark.asyncio
async def test_postgres_storage_auto_connect_on_store() -> None:
    mock_conn = AsyncMock()
    mock_pool = MagicMock()

    class MockAcquireContext:
        async def __aenter__(self) -> AsyncMock:
            return mock_conn

        async def __aexit__(self, exc_type: object, exc_val: object, exc_tb: object) -> None:
            pass

    mock_pool.acquire.return_value = MockAcquireContext()
    mock_pool.close = AsyncMock()

    with patch("asyncpg.create_pool", new_callable=AsyncMock) as mock_create_pool:
        mock_create_pool.return_value = mock_pool
        storage = PostgresMarketDataStorage(dsn="postgresql://user:pass@localhost:5432/testdb")
        symbol = Symbol("BTCUSD")
        interval = Interval("1h")
        timestamp = Timestamp(datetime(2026, 1, 1, 0, 0, 0, tzinfo=UTC))
        ohlcv = OHLCV(
            open=Decimal("10.0"),
            high=Decimal("12.0"),
            low=Decimal("8.0"),
            close=Decimal("11.0"),
            volume=Decimal("500.0"),
        )

        await storage.store(symbol, interval, timestamp, ohlcv)
        assert storage._pool is not None
        await storage.disconnect()
        assert storage._pool is None


@pytest.mark.asyncio
async def test_postgres_storage_get_candles() -> None:
    mock_conn = AsyncMock()
    mock_pool = MagicMock()

    class MockAcquireContext:
        async def __aenter__(self) -> AsyncMock:
            return mock_conn

        async def __aexit__(self, exc_type: object, exc_val: object, exc_tb: object) -> None:
            pass

    mock_pool.acquire.return_value = MockAcquireContext()
    mock_pool.close = AsyncMock()

    mock_conn.fetch.return_value = [
        {
            "time": datetime(2026, 1, 1, 0, 0, 0, tzinfo=UTC),
            "open": "100.0",
            "high": "105.0",
            "low": "95.0",
            "close": "102.0",
            "volume": "1000.0",
        }
    ]

    with patch("asyncpg.create_pool", new_callable=AsyncMock) as mock_create_pool:
        mock_create_pool.return_value = mock_pool
        storage = PostgresMarketDataStorage(dsn="postgresql://user:pass@localhost:5432/testdb")
        symbol = Symbol("BTCUSD")
        interval = Interval("1h")
        start = Timestamp(datetime(2026, 1, 1, 0, 0, 0, tzinfo=UTC))
        end = Timestamp(datetime(2026, 1, 2, 0, 0, 0, tzinfo=UTC))

        candles = await storage.get_candles(symbol, interval, start, end)

        assert len(candles) == 1
        assert candles[0].symbol == symbol
        assert candles[0].interval == interval
        assert candles[0].ohlcv.close == Decimal("102.0")
        await storage.disconnect()
