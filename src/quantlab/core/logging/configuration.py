"""Standard-library logging setup kept outside domain and application code."""

from __future__ import annotations

import logging.config
from typing import Any

from quantlab.core.config.settings import LoggingSettings


def configure_logging(settings: LoggingSettings) -> None:
    """Configure process logging from injected settings.

    Existing loggers are retained so third-party diagnostics remain observable. Application modules
    receive a named logger through composition rather than constructing mutable global loggers.
    """
    formatter = "json" if settings.json_logs else "standard"
    config: dict[str, Any] = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "standard": {
                "format": "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
            },
            "json": {
                "()": "quantlab.core.logging.formatters.JsonFormatter",
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": formatter,
                "stream": "ext://sys.stdout",
            },
        },
        "root": {"level": settings.level.upper(), "handlers": ["console"]},
    }
    logging.config.dictConfig(config)
