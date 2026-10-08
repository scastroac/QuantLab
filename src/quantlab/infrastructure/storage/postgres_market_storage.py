"""PostgreSQL based market data storage adapter."""

import asyncpg  # type: ignore[import-untyped]

from quantlab.application.ports.market import MarketDataStorage
from quantlab.domain.value_objects.market import OHLCV, Interval, Symbol, Timestamp


class PostgresMarketDataStorage(MarketDataStorage):
    """Stores validated market data in PostgreSQL/TimescaleDB."""

    def __init__(self, dsn: str) -> None:
        self.dsn = dsn
        self._pool: asyncpg.Pool | None = None

    async def connect(self) -> None:
        """Initialize the connection pool and ensure table exists."""
        if self._pool is None:
            self._pool = await asyncpg.create_pool(self.dsn)
            async with self._pool.acquire() as conn:
                await conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS market_data (
                        time TIMESTAMPTZ NOT NULL,
                        symbol VARCHAR(50) NOT NULL,
                        interval VARCHAR(10) NOT NULL,
                        open NUMERIC NOT NULL,
                        high NUMERIC NOT NULL,
                        low NUMERIC NOT NULL,
                        close NUMERIC NOT NULL,
                        volume NUMERIC NOT NULL,
                        PRIMARY KEY (time, symbol, interval)
                    );
                    """
                )
                # Ideally here we would also convert it to a hypertable for TimescaleDB:
                # await conn.execute(
                #     "SELECT create_hypertable('market_data', 'time', if_not_exists => TRUE);"
                # )

    async def store(
        self, symbol: Symbol, interval: Interval, timestamp: Timestamp, ohlcv: OHLCV
    ) -> None:
        """Insert OHLCV data into the market_data table."""
        if self._pool is None:
            await self.connect()

        if self._pool is None:
            raise RuntimeError("Failed to connect to database")

        async with self._pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO market_data (time, symbol, interval, open, high, low, close, volume)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                ON CONFLICT (time, symbol, interval) DO UPDATE
                SET open = EXCLUDED.open,
                    high = EXCLUDED.high,
                    low = EXCLUDED.low,
                    close = EXCLUDED.close,
                    volume = EXCLUDED.volume;
                """,
                timestamp.value,
                symbol.name,
                interval.name,
                float(ohlcv.open),
                float(ohlcv.high),
                float(ohlcv.low),
                float(ohlcv.close),
                float(ohlcv.volume),
            )
