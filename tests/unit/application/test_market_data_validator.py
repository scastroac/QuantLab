"""Unit tests for BasicMarketDataValidator."""

from __future__ import annotations

from decimal import Decimal

import pytest

from quantlab.application.services.market_data_pipeline import BasicMarketDataValidator


def test_validator_parses_valid_record() -> None:
    validator = BasicMarketDataValidator()
    raw = {
        "open": "100.5",
        "high": "110.0",
        "low": "99.0",
        "close": "105.25",
        "volume": "5000",
    }
    ohlcv = validator.validate(raw)

    assert ohlcv.open == Decimal("100.5")
    assert ohlcv.high == Decimal("110.0")
    assert ohlcv.low == Decimal("99.0")
    assert ohlcv.close == Decimal("105.25")
    assert ohlcv.volume == Decimal("5000")


@pytest.mark.parametrize(
    "missing_key",
    ["open", "high", "low", "close", "volume"],
)
def test_validator_rejects_missing_keys(missing_key: str) -> None:
    validator = BasicMarketDataValidator()
    raw = {
        "open": "100.0",
        "high": "110.0",
        "low": "95.0",
        "close": "105.0",
        "volume": "1000",
    }
    del raw[missing_key]

    with pytest.raises(ValueError, match="Invalid market data"):
        validator.validate(raw)


@pytest.mark.parametrize(
    "invalid_val",
    ["abc", "", None],
)
def test_validator_rejects_non_numeric_values(invalid_val: str | None) -> None:
    validator = BasicMarketDataValidator()
    raw = {
        "open": invalid_val,
        "high": "110.0",
        "low": "95.0",
        "close": "105.0",
        "volume": "1000",
    }

    with pytest.raises(ValueError, match="Invalid market data"):
        validator.validate(raw)  # type: ignore[arg-type]
