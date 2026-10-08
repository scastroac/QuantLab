"""Market data pipeline service."""

import logging
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from quantlab.application.ports.event_bus import EventBus
from quantlab.application.ports.market import (
    MarketDataCollector,
    MarketDataStorage,
    MarketDataValidator,
)
from quantlab.domain.events.market import DataCollected, DataStored, DataValidated
from quantlab.domain.value_objects.market import OHLCV, Interval, Symbol, Timestamp

logger = logging.getLogger(__name__)


class BasicMarketDataValidator(MarketDataValidator):
    """Basic validation mapping raw dict to OHLCV."""

    def validate(self, raw_data: dict[str, Any]) -> OHLCV:
        """Parse required fields into OHLCV."""
        try:
            return OHLCV(
                open=Decimal(str(raw_data["open"])),
                high=Decimal(str(raw_data["high"])),
                low=Decimal(str(raw_data["low"])),
                close=Decimal(str(raw_data["close"])),
                volume=Decimal(str(raw_data["volume"])),
            )
        except (KeyError, ValueError) as e:
            raise ValueError(f"Invalid market data: {e}") from e


class MarketDataPipeline:
    """Orchestrates the collection, validation, and storage of market data."""

    def __init__(
        self,
        collector: MarketDataCollector,
        validator: MarketDataValidator,
        storage: MarketDataStorage,
        event_bus: EventBus,
    ) -> None:
        self.collector = collector
        self.validator = validator
        self.storage = storage
        self.event_bus = event_bus

    async def run_pipeline(
        self, symbol_name: str, interval_name: str, start_dt: datetime, end_dt: datetime
    ) -> None:
        """Run the collection pipeline for a given symbol and time range."""
        symbol = Symbol(symbol_name)
        interval = Interval(interval_name)
        start = Timestamp(start_dt)
        end = Timestamp(end_dt)

        logger.info(f"Starting pipeline for {symbol_name} {interval_name}")

        async for raw_data in self.collector.collect(symbol, interval, start, end):
            # 1. Collect
            ts_str = str(raw_data.get("timestamp", ""))
            try:
                # Basic parsing for timestamp from ISO format for the event
                dt = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=UTC)
            except ValueError:
                logger.warning(f"Skipping record with invalid timestamp: {ts_str}")
                continue

            current_ts = Timestamp(dt)

            await self.event_bus.publish(
                DataCollected(
                    symbol=symbol,
                    interval=interval,
                    timestamp=current_ts,
                    raw_data=raw_data,
                )
            )

            # 2. Validate
            try:
                ohlcv = self.validator.validate(raw_data)
            except ValueError as e:
                logger.warning(f"Validation failed for {symbol_name} at {current_ts.value}: {e}")
                continue

            await self.event_bus.publish(
                DataValidated(
                    symbol=symbol,
                    interval=interval,
                    timestamp=current_ts,
                    ohlcv=ohlcv,
                )
            )

            # 3. Store
            await self.storage.store(symbol, interval, current_ts, ohlcv)
            await self.event_bus.publish(
                DataStored(
                    symbol=symbol,
                    interval=interval,
                    timestamp=current_ts,
                )
            )
