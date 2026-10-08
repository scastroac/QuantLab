"""Structured logging formatter without a dependency on an external logging service."""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from typing import Any


class JsonFormatter(logging.Formatter):
    """Serialize stable log record fields as a JSON line."""

    _standard_attributes = frozenset(logging.LogRecord("", 0, "", 0, "", (), None).__dict__)

    def format(self, record: logging.LogRecord) -> str:
        """Format a record while preserving application-provided structured fields."""
        payload: dict[str, Any] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        payload.update(
            {
                key: value
                for key, value in record.__dict__.items()
                if key not in self._standard_attributes and not key.startswith("_")
            }
        )
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, default=str, ensure_ascii=False)
