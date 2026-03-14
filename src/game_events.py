from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, DefaultDict, Dict, Iterable, List
from uuid import uuid4


class GameEventType(str, Enum):
    SCENE_SWITCHED = "SCENE_SWITCHED"
    ROLL_RESOLVED = "ROLL_RESOLVED"
    CHARACTER_STATUS_CHANGED = "CHARACTER_STATUS_CHANGED"
    CLUE_UNLOCKED = "CLUE_UNLOCKED"


@dataclass(slots=True)
class GameEvent:
    event_type: GameEventType
    session_id: str
    chapter_id: str
    payload: Dict[str, Any]
    event_id: str = field(default_factory=lambda: str(uuid4()))
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class EventTable:
    """Simple append-only event table."""

    def __init__(self) -> None:
        self._rows: List[GameEvent] = []

    def insert(self, event: GameEvent) -> None:
        self._rows.append(event)

    def list_events(self, *, session_id: str | None = None, chapter_id: str | None = None) -> List[GameEvent]:
        events = self._rows
        if session_id is not None:
            events = [event for event in events if event.session_id == session_id]
        if chapter_id is not None:
            events = [event for event in events if event.chapter_id == chapter_id]
        return list(events)


Subscriber = Callable[[GameEvent], None]


class EventBus:
    def __init__(self, event_table: EventTable) -> None:
        self.event_table = event_table
        self._subscribers: DefaultDict[GameEventType, List[Subscriber]] = defaultdict(list)

    def subscribe(self, event_type: GameEventType, callback: Subscriber) -> None:
        self._subscribers[event_type].append(callback)

    def publish(self, event: GameEvent) -> None:
        self.event_table.insert(event)
        for callback in self._subscribers[event.event_type]:
            callback(event)


@dataclass(slots=True)
class ChapterState:
    session_id: str
    chapter_id: str
    current_scene: str = ""
    last_roll: Dict[str, Any] = field(default_factory=dict)
    character_statuses: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    unlocked_clues: List[str] = field(default_factory=list)


@dataclass(slots=True)
class ReplayResult:
    state: ChapterState
    ignored_event_ids: List[str]


class ChapterStateProjector:
    def apply_event(self, state: ChapterState, event: GameEvent) -> None:
        if event.event_type is GameEventType.SCENE_SWITCHED:
            scene_id = event.payload["scene_id"]
            state.current_scene = scene_id
            return

        if event.event_type is GameEventType.ROLL_RESOLVED:
            state.last_roll = {
                "actor_id": event.payload["actor_id"],
                "dice": event.payload["dice"],
                "result": event.payload["result"],
            }
            return

        if event.event_type is GameEventType.CHARACTER_STATUS_CHANGED:
            character_id = event.payload["character_id"]
            state.character_statuses[character_id] = dict(event.payload["status"])
            return

        if event.event_type is GameEventType.CLUE_UNLOCKED:
            clue_id = event.payload["clue_id"]
            if clue_id not in state.unlocked_clues:
                state.unlocked_clues.append(clue_id)
            return

        raise ValueError(f"Unknown event type: {event.event_type}")

    def rebuild(self, events: Iterable[GameEvent], *, session_id: str, chapter_id: str) -> ReplayResult:
        state = ChapterState(session_id=session_id, chapter_id=chapter_id)
        ignored_event_ids: List[str] = []

        for event in events:
            if event.session_id != session_id or event.chapter_id != chapter_id:
                continue
            try:
                self.apply_event(state, event)
            except (KeyError, TypeError, ValueError):
                ignored_event_ids.append(event.event_id)

        return ReplayResult(state=state, ignored_event_ids=ignored_event_ids)


class ChapterStateUI:
    """UI consumes events and only updates local render state from subscriptions."""

    def __init__(self, event_bus: EventBus, *, session_id: str, chapter_id: str) -> None:
        self.render_state = ChapterState(session_id=session_id, chapter_id=chapter_id)
        self._projector = ChapterStateProjector()

        for event_type in GameEventType:
            event_bus.subscribe(event_type, self._on_event)

    def _on_event(self, event: GameEvent) -> None:
        if (
            event.session_id != self.render_state.session_id
            or event.chapter_id != self.render_state.chapter_id
        ):
            return
        try:
            self._projector.apply_event(self.render_state, event)
        except (KeyError, TypeError, ValueError):
            return
