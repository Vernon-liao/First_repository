import json

import pytest

from src.profile_system import (
    PROFILE_VERSION,
    CharacterProfile,
    StoryEngine,
    generate_profile_from_ai,
    profile_generation_prompt,
    validate_profile_payload,
)


def sample_payload():
    return {
        "profile_version": PROFILE_VERSION,
        "id": "npc_001",
        "name": "奥黛丽",
        "alias": "黑夜观察者",
        "age_range": "20-30",
        "gender_presentation": "feminine",
        "pathway": "观众",
        "sequence_level": 7,
        "affiliation": "值夜者",
        "public_identity": "心理医生",
        "motivation": "守护同伴",
        "fear": "失去理智",
        "secret": "曾接触禁忌封印",
        "taboo": "不提及旧日神名",
        "speech_style": "轻声且克制",
        "clue_value": 80,
        "danger_level": 60,
        "trust_to_party": 35,
        "favorability": 45,
        "sanity_state": "stable",
        "corruption_state": "tainted",
        "injury_state": "healthy",
        "alive_state": True,
        "relations": [
            {
                "target_id": "player_001",
                "relation_type": "player",
                "trust_delta": 20,
                "notes": "曾被救助",
            }
        ],
        "portrait_seed": "audrey-night-001",
        "style_tags": ["gothic", "mystic"],
        "key_features": ["银色长发", "深色披风"],
    }


def test_profile_payload_schema_valid():
    payload = sample_payload()
    validate_profile_payload(payload)


def test_profile_generation_requires_valid_schema():
    payload = sample_payload()
    del payload["pathway"]
    with pytest.raises(ValueError):
        generate_profile_from_ai(json.dumps(payload, ensure_ascii=False))


def test_prompt_mentions_schema_and_validation():
    prompt = profile_generation_prompt("蒸汽与神秘共存")
    assert "JSON Schema" in prompt
    assert "JSON 校验" in prompt


def test_story_engine_profile_driven_and_diff_log():
    profile = CharacterProfile(**sample_payload())
    engine = StoryEngine()

    assert "守护同伴" in engine.dialogue_line(profile)
    assert engine.betrayal_or_assist(profile) == "assist"

    profile.apply_chapter_updates(
        "chapter_2",
        trust_to_party=-40,
        corruption_state="corrupted",
        affiliation="极光会",
    )

    log = profile.diff_log()
    assert len(log) == 3
    assert any(item["field"] == "trust_to_party" for item in log)
    assert profile.corruption_state == "corrupted"
