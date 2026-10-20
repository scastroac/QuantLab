"""Domain service for cleaning, deduplicating and detecting gaps in market data."""

from __future__ import annotations

import re
from collections.abc import Sequence
from datetime import timedelta

from quantlab.domain.entities.market import Candle
from quantlab.domain.events.market import GapDetected
from quantlab.domain.value_objects.market import Interval, Timestamp

_INTERVAL_RE = re.compile(r"^(\d+)([smhdw])$")


def interval_to_timedelta(interval: Interval) -> timedelta:
    """Convert a quantitative interval into a standard timedelta.

    Supports seconds (s), minutes (m), hours (h), days (d), weeks (w).
    """
    match = _INTERVAL_RE.match(interval.name)
    if not match:
        raise ValueError(f"Interval {interval.name!r} cannot be converted to a fixed timedelta")

    value, unit = int(match.group(1)), match.group(2)
    if unit == "s":
        return timedelta(seconds=value)
    if unit == "m":
        return timedelta(minutes=value)
    if unit == "h":
        return timedelta(hours=value)
    if unit == "d":
        return timedelta(days=value)
    if unit == "w":
        return timedelta(weeks=value)

    raise ValueError(f"Unsupported interval unit: {unit!r}")


class MarketDataCleaner:
    """Domain service responsible for sanitizing candle series and reporting anomalies."""

    def clean(self, candles: Sequence[Candle]) -> tuple[list[Candle], list[GapDetected]]:
        """Deduplicate, sort chronologically, and detect missing gaps between candles.

        Args:
            candles: Raw input candles.

        Returns:
            A tuple containing:
                - The sanitized list of candles (sorted and deduplicated).
                - A list of GapDetected domain events for any missing intervals.
        """
        if not candles:
            return [], []

        symbol = candles[0].symbol
        interval = candles[0].interval

        # Ensure all candles belong to the same symbol and interval
        for candle in candles:
            if candle.symbol != symbol or candle.interval != interval:
                raise ValueError("All candles in a batch must share the same symbol and interval")

        # 1. Sort chronologically
        sorted_candles = sorted(candles, key=lambda c: c.timestamp.value)

        # 2. Deduplicate keeping the latest candle per timestamp
        deduplicated: list[Candle] = []
        for candle in sorted_candles:
            if deduplicated and deduplicated[-1].timestamp.value == candle.timestamp.value:
                # Replace with latest occurrence
                deduplicated[-1] = candle
            else:
                deduplicated.append(candle)

        # 3. Detect gaps if interval can be represented as a fixed delta
        gaps: list[GapDetected] = []
        try:
            delta = interval_to_timedelta(interval)
        except ValueError:
            # For intervals like '1M' or '1y' with variable calendar days,
            # skip fixed delta gap detection
            return deduplicated, gaps

        for i in range(1, len(deduplicated)):
            prev_ts = deduplicated[i - 1].timestamp.value
            curr_ts = deduplicated[i].timestamp.value

            time_diff = curr_ts - prev_ts
            if time_diff > delta:
                missing_count = int(time_diff / delta) - 1
                if missing_count > 0:
                    expected_dt = prev_ts + delta
                    gaps.append(
                        GapDetected(
                            symbol=symbol,
                            interval=interval,
                            expected_timestamp=Timestamp(expected_dt),
                            actual_timestamp=deduplicated[i].timestamp,
                            missing_intervals=missing_count,
                        )
                    )

        return deduplicated, gaps
