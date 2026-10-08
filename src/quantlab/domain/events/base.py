"""Technology-independent event base class."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import UUID, uuid4


@dataclass(frozen=True, kw_only=True, slots=True)
class DomainEvent:
    """Base event carrying only observability metadata.

    Concrete business events will live beside this primitive in later sprints. The event bus depends
    only on this abstraction, never on a collector, model, storage engine or framework.
    """

    event_id: UUID = field(default_factory=uuid4)
    occurred_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    @property
    def event_name(self) -> str:
        """Return the event's stable human-readable name."""
        return type(self).__name__
