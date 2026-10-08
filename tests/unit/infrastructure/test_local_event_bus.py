"""Tests for the local event-bus adapter."""

from __future__ import annotations

import logging
from dataclasses import dataclass

import pytest

from quantlab.domain.events import DomainEvent
from quantlab.infrastructure.messaging import LocalEventBus


@dataclass(frozen=True, kw_only=True, slots=True)
class InfrastructureEvent(DomainEvent):
    """Technical test event with no business meaning."""

    value: str


@pytest.mark.asyncio
async def test_publish_delivers_sync_and_async_handlers() -> None:
    """The adapter supports both handler styles in registration order."""
    logger = logging.getLogger("tests.event_bus")
    bus = LocalEventBus(logger=logger)
    received: list[str] = []

    def sync_handler(event: DomainEvent) -> None:
        received.append(f"sync:{event.event_name}")

    async def async_handler(event: DomainEvent) -> None:
        received.append(f"async:{event.event_name}")

    bus.subscribe(InfrastructureEvent, sync_handler)
    bus.subscribe(InfrastructureEvent, async_handler)

    result = await bus.publish(InfrastructureEvent(value="test"))

    assert result.succeeded is True
    assert result.delivered_handlers == 2
    assert received == ["sync:InfrastructureEvent", "async:InfrastructureEvent"]


@pytest.mark.asyncio
async def test_publish_records_a_failure_and_continues_delivery() -> None:
    """One extension failure is observable without preventing independent subscribers."""
    logger = logging.getLogger("tests.event_bus")
    bus = LocalEventBus(logger=logger)
    received: list[str] = []

    def failing_handler(event: DomainEvent) -> None:
        raise RuntimeError(f"failed for {event.event_name}")

    def healthy_handler(event: DomainEvent) -> None:
        received.append(event.event_name)

    bus.subscribe(InfrastructureEvent, failing_handler)
    bus.subscribe(InfrastructureEvent, healthy_handler)

    result = await bus.publish(InfrastructureEvent(value="test"))

    assert result.succeeded is False
    assert result.delivered_handlers == 1
    assert result.failures[0].error_type == "RuntimeError"
    assert received == ["InfrastructureEvent"]


@pytest.mark.asyncio
async def test_subscription_can_be_removed() -> None:
    """Subscribers have an explicit lifecycle and do not require global cleanup."""
    logger = logging.getLogger("tests.event_bus")
    bus = LocalEventBus(logger=logger)
    received: list[str] = []

    def handler(event: DomainEvent) -> None:
        received.append(event.event_name)

    subscription = bus.subscribe(InfrastructureEvent, handler)
    subscription.unsubscribe()

    result = await bus.publish(InfrastructureEvent(value="test"))

    assert result.delivered_handlers == 0
    assert received == []
