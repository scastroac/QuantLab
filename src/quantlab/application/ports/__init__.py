"""Outbound contracts implemented by infrastructure adapters."""

from quantlab.application.ports.event_bus import EventBus, EventDispatchResult, EventHandler

__all__ = ["EventBus", "EventDispatchResult", "EventHandler"]
