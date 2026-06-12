"""
EVENTBUS
PART OF JK'S CUSTOM LIBRARIES

This library exists to easily create events.
Created by JK
Copyright 2026
"""

# ibgbggbgbbfvb7zhnmijm,ikok.ol.pö-pö-ok,ujnhzbtfcrdxwsyqa<<<<<yxcvbnm,.äölkasdfghjklöä#qwertzuiopjntgok,humijmhzhgng
from collections import defaultdict, deque
from typing import Callable, TYPE_CHECKING

if TYPE_CHECKING:
    from game.events import EventType, GameEvent

"""Edited EventBus to fit Hell's Bar"""


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
        self._handlers: dict[EventType, list[Callable]] = defaultdict(list)
        self._queue: deque[GameEvent] = deque()
        self._fired_once: set[EventType] = set()  # one-shot events

    def subscribe(self, event: EventType, handler: Callable) -> None:
        """Register a handler for an event."""
        if handler not in self._handlers[event]:
            self._handlers[event].append(handler)

    def unsubscribe(self, event: EventType, handler: Callable) -> None:
        """Remove a handler. Silent if not registered."""
        try:
            self._handlers[event].remove(handler)
        except ValueError:
            pass

    def emit(self, event: GameEvent) -> None:
        """
        Fire an event. All subscribed handlers are called in order.
        Uses a copy of the handler list so handlers can safely
        unsubscribe during emit.
        """
        for handler in self._handlers.get(event.type, []):
            handler(event)

    def emit_once(self, event: GameEvent) -> bool:
        """Fire once if it hasn't fired before."""
        if event.type in self._fired_once:
            return False
        self._fired_once.add(event.type)
        self.emit(event)
        return True

    def clear(self, event: EventType | None = None) -> None:
        """Remove all handlers for an event, or all events if none given."""
        if event:
            self._handlers.pop(event, None)
        else:
            self._handlers.clear()

    def listeners(self, event: EventType) -> int:
        """Returns the number of handlers subscribed to an event."""
        return len(self._handlers.get(event, []))

    def queue(self, event: GameEvent) -> None:
        """Enqueue an event to be fired later by flush()."""
        self._queue.append(event)

    def flush(self) -> None:
        """Fire all queued events in order. Call once per game loop tick."""
        while self._queue:
            event, data = self._queue.popleft()
            self.emit(event)

    @staticmethod
    def make(event_type: EventType, **payload) -> GameEvent:
        return GameEvent(event_type, payload)
