"""
EVENTBUS
PART OF JK'S CUSTOM LIBRARIES

This library exists to easily create events.
Created by JK
Copyright 2026
"""

from collections import defaultdict, deque
from typing import Callable


class EventBus:
    """
    Publish/subscribe event system. Decouples scenes and systems.

    Usage:
        bus = EventBus()

        def on_death(data):
            print(f"Player died: {data['cause']}")

        bus.subscribe("player_died", on_death)
        bus.emit("player_died", {"cause": "fall"})
        bus.unsubscribe("player_died", on_death)
    """

    def __init__(self) -> None:
        self._handlers: dict[str, list[Callable]] = defaultdict(list)
        self._queue: deque[tuple[str, dict]] = deque()

    def subscribe(self, event: str, handler: Callable) -> None:
        """Register a handler for an event."""
        if handler not in self._handlers[event]:
            self._handlers[event].append(handler)

    def unsubscribe(self, event: str, handler: Callable) -> None:
        """Remove a handler. Silent if not registered."""
        try:
            self._handlers[event].remove(handler)
        except ValueError:
            pass

    def emit(self, event: str, data: dict | None = None) -> None:
        """
        Fire an event. All subscribed handlers are called in order.
        Uses a copy of the handler list so handlers can safely
        unsubscribe during emit.
        """
        payload = data or {}
        specific = list(self._handlers.get(event, []))
        wildcards = list(self._handlers.get('*', []))
        for handler in specific:
            handler(payload)
        for handler in wildcards:
            handler({**payload, '_event': event})

    def clear(self, event: str | None = None) -> None:
        """Remove all handlers for an event, or all events if none given."""
        if event:
            self._handlers.pop(event, None)
        else:
            self._handlers.clear()

    def listeners(self, event: str) -> int:
        """Returns the number of handlers subscribed to an event."""
        return len(self._handlers.get(event, []))

    def queue(self, event: str, data: dict | None = None) -> None:
        """Enqueue an event to be fired later by flush()."""
        self._queue.append((event, data or {}))

    def flush(self) -> None:
        """Fire all queued events in order. Call once per game loop tick."""
        while self._queue:
            event, data = self._queue.popleft()
            self.emit(event, data)
