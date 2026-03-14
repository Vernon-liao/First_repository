from src.game_events import (
    ChapterStateProjector,
    ChapterStateUI,
    EventBus,
    EventTable,
    GameEvent,
    GameEventType,
)


def build_event(event_type: GameEventType, payload: dict, event_id: str) -> GameEvent:
    return GameEvent(
        event_id=event_id,
        event_type=event_type,
        session_id="session-1",
        chapter_id="chapter-1",
        payload=payload,
    )


def test_event_written_and_ui_updates_from_subscription_only():
    event_table = EventTable()
    bus = EventBus(event_table)
    ui = ChapterStateUI(bus, session_id="session-1", chapter_id="chapter-1")

    bus.publish(
        build_event(
            GameEventType.SCENE_SWITCHED,
            {"scene_id": "scene-docks"},
            "evt-1",
        )
    )

    stored = event_table.list_events(session_id="session-1", chapter_id="chapter-1")
    assert len(stored) == 1
    assert stored[0].event_id == "evt-1"
    assert ui.render_state.current_scene == "scene-docks"


def test_replay_rebuild_matches_live_projection():
    event_table = EventTable()
    bus = EventBus(event_table)
    ui = ChapterStateUI(bus, session_id="session-1", chapter_id="chapter-1")

    events = [
        build_event(GameEventType.SCENE_SWITCHED, {"scene_id": "scene-a"}, "evt-1"),
        build_event(
            GameEventType.ROLL_RESOLVED,
            {"actor_id": "pc-1", "dice": "1d100", "result": 83},
            "evt-2",
        ),
        build_event(
            GameEventType.CHARACTER_STATUS_CHANGED,
            {"character_id": "npc-7", "status": {"sanity": "fractured", "hp": 12}},
            "evt-3",
        ),
        build_event(GameEventType.CLUE_UNLOCKED, {"clue_id": "clue-ark-02"}, "evt-4"),
    ]

    for event in events:
        bus.publish(event)

    projector = ChapterStateProjector()
    replay = projector.rebuild(
        event_table.list_events(),
        session_id="session-1",
        chapter_id="chapter-1",
    )

    assert replay.ignored_event_ids == []
    assert replay.state.current_scene == ui.render_state.current_scene
    assert replay.state.last_roll == ui.render_state.last_roll
    assert replay.state.character_statuses == ui.render_state.character_statuses
    assert replay.state.unlocked_clues == ui.render_state.unlocked_clues


def test_replay_ignores_malformed_events_and_continues():
    event_table = EventTable()
    malformed = build_event(GameEventType.SCENE_SWITCHED, {"wrong": "field"}, "evt-bad")
    valid = build_event(GameEventType.CLUE_UNLOCKED, {"clue_id": "clue-ok"}, "evt-ok")
    event_table.insert(malformed)
    event_table.insert(valid)

    replay = ChapterStateProjector().rebuild(
        event_table.list_events(),
        session_id="session-1",
        chapter_id="chapter-1",
    )

    assert replay.ignored_event_ids == ["evt-bad"]
    assert replay.state.unlocked_clues == ["clue-ok"]
