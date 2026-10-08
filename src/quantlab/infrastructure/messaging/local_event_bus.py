"""Deterministic in-process implementation of the application event-bus port."""

from __future__ import annotations

import inspect
from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass, field
from logging import Logger

from quantlab.application.ports.event_bus import (
    EventDispatchResult,
    EventHandler,
    EventHandlerFailure,
    Subscription,
)
from quantlab.domain.events import DomainEvent


@dataclass(slots=True)
class LocalEventBus:
    """Dispatch events sequentially to in-memory subscribers.

    The adapter is intentionally local and injectable. A broker-backed adapter can implement the
    same port in a later sprint without changing domain events or application code.
    """

    logger: Logger
    _subscribers: dict[type[DomainEvent], list[EventHandler]] = field(
        default_factory=lambda: defaultdict(list), init=False, repr=False
    )

    def subscribe(self, event_type: type[DomainEvent], handler: EventHandler) -> Subscription:
        """Register one handler and return a handle for explicit unsubscription."""
        self._subscribers[event_type].append(handler)
        return _LocalSubscription(self._remove_handler, event_type, handler)

    async def publish(self, event: DomainEvent) -> EventDispatchResult:
        """Deliver an event to matching subscribers while recording, not hiding, failures."""
        handlers = tuple(
            handler
            for subscribed_type, registered_handlers in self._subscribers.items()
            if isinstance(event, subscribed_type)
            for handler in registered_handlers
        )
        failures: list[EventHandlerFailure] = []
        delivered_handlers = 0

        for handler in handlers:
            try:
                result = handler(event)
                if inspect.isawaitable(result):
                    await result
                delivered_handlers += 1
            except Exception as error:
                failure = EventHandlerFailure(
                    handler_name=_handler_name(handler),
                    error_type=type(error).__name__,
                    message=str(error),
                )
                failures.append(failure)
                self.logger.exception(
                    "Event handler failed",
                    extra={
                        "event_id": str(event.event_id),
                        "event_name": event.event_name,
                        "handler": failure.handler_name,
                    },
                )

        return EventDispatchResult(
            event_id=str(event.event_id),
            event_name=event.event_name,
            delivered_handlers=delivered_handlers,
            failures=tuple(failures),
        )

    def _remove_handler(self, event_type: type[DomainEvent], handler: EventHandler) -> None:
        """Remove a handler if it is still subscribed."""
        handlers = self._subscribers.get(event_type)
        if handlers is None:
            return
        try:
            handlers.remove(handler)
        except ValueError:
            return
        if not handlers:
            del self._subscribers[event_type]


@dataclass(frozen=True, slots=True)
class _LocalSubscription:
    """Single-use-friendly subscription implementation."""

    remove_handler: Callable[[type[DomainEvent], EventHandler], None]
    event_type: type[DomainEvent]
    handler: EventHandler

    def unsubscribe(self) -> None:
        """Remove the associated handler."""
        self.remove_handler(self.event_type, self.handler)


def _handler_name(handler: EventHandler) -> str:
    """Return a useful handler identifier for logs and reports."""
    return getattr(handler, "__qualname__", repr(handler))
