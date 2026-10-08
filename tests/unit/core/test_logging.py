"""Tests for process logging adapters."""

from __future__ import annotations

import json
import logging
import logging.config
import sys

from quantlab.core.config.settings import LoggingSettings
from quantlab.core.logging.configuration import configure_logging
from quantlab.core.logging.formatters import JsonFormatter


def test_configure_logging_selects_json_formatter(monkeypatch: object) -> None:
    """Configuration delegates a fully resolved JSON logging dictionary to stdlib logging."""
    captured: dict[str, object] = {}

    def capture(config: dict[str, object]) -> None:
        captured.update(config)

    monkeypatch.setattr(logging.config, "dictConfig", capture)  # type: ignore[attr-defined]

    configure_logging(LoggingSettings(level="debug", json=True))

    handlers = captured["handlers"]
    root = captured["root"]
    assert isinstance(handlers, dict)
    assert isinstance(root, dict)
    assert handlers["console"]["formatter"] == "json"
    assert root["level"] == "DEBUG"


def test_json_formatter_preserves_structured_context_and_exception() -> None:
    """JSON logs retain safe contextual fields and a rendered exception when supplied."""
    logger = logging.getLogger("tests.json_formatter")
    try:
        raise ValueError("test failure")
    except ValueError:
        record = logger.makeRecord(
            logger.name,
            logging.ERROR,
            __file__,
            1,
            "Operation %s",
            ("failed",),
            exc_info=sys.exc_info(),
            extra={"experiment_id": "infrastructure-test"},
        )

    payload = json.loads(JsonFormatter().format(record))

    assert payload["message"] == "Operation failed"
    assert payload["experiment_id"] == "infrastructure-test"
    assert payload["exception"].startswith("Traceback")
    assert payload["timestamp"].endswith("+00:00")
