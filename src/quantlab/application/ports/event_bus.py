"""Port for dispatching domain events without coupling use cases to a broker."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Protocol

from quantlab.domain.events import DomainEvent

type EventHandler = Callable[[DomainEvent], Awaitable[None] | None]


@dataclass(frozen=True, slots=True)
class EventHandlerFailure:
    """Serializable summary of a handler failure during local dispatch."""

    handler_name: str
    error_type: str
    message: str


@dataclass(frozen=True, slots=True)
class EventDispatchResult:
    """Observability result returned after an event is offered to all subscribers."""

    event_id: str
    event_name: str
    delivered_handlers: int
    failures: tuple[EventHandlerFailure, ...]

    @property
    def succeeded(self) -> bool:
        """Return whether every registered handler completed successfully."""
        return not self.failures


class Subscription(Protocol):
    """Handle that removes a single event subscription."""

    def unsubscribe(self) -> None:
        """Remove the handler from the bus."""


class EventBus(Protocol):
    """Application-facing event publishing contract."""

    def subscribe(self, event_type: type[DomainEvent], handler: EventHandler) -> Subscription:
        """Register a handler for an event type."""

    async def publish(self, event: DomainEvent) -> EventDispatchResult:
        """Offer an event to its registered handlers."""
