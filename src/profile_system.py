from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Literal
import copy
import json
import re


PROFILE_VERSION = "1.0.0"


def profile_json_schema() -> Dict[str, Any]:
    """Return the strict JSON schema used for profile generation and validation."""
    relation_schema = {
        "type": "object",
        "additionalProperties": False,
        "required": ["target_id", "relation_type", "trust_delta", "notes"],
        "properties": {
            "target_id": {"type": "string", "minLength": 1},
            "relation_type": {
                "type": "string",
                "enum": ["player", "npc", "faction", "unknown"],
            },
            "trust_delta": {"type": "integer", "minimum": -100, "maximum": 100},
            "notes": {"type": "string"},
        },
    }

    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "object",
        "additionalProperties": False,
        "required": [
            "profile_version",
            "id",
            "name",
            "alias",
            "age_range",
            "gender_presentation",
            "pathway",
            "sequence_level",
            "affiliation",
            "public_identity",
            "motivation",
            "fear",
            "secret",
            "taboo",
            "speech_style",
            "clue_value",
            "danger_level",
            "trust_to_party",
            "favorability",
            "sanity_state",
            "corruption_state",
            "injury_state",
            "alive_state",
            "relations",
            "portrait_seed",
            "style_tags",
            "key_features",
        ],
        "properties": {
            "profile_version": {"type": "string", "pattern": r"^\d+\.\d+\.\d+$"},
            "id": {"type": "string", "minLength": 1},
            "name": {"type": "string", "minLength": 1},
            "alias": {"type": "string"},
            "age_range": {"type": "string"},
            "gender_presentation": {"type": "string"},
            "pathway": {"type": "string"},
            "sequence_level": {"type": "integer", "minimum": 0, "maximum": 9},
            "affiliation": {"type": "string"},
            "public_identity": {"type": "string"},
            "motivation": {"type": "string"},
            "fear": {"type": "string"},
            "secret": {"type": "string"},
            "taboo": {"type": "string"},
            "speech_style": {"type": "string"},
            "clue_value": {"type": "integer", "minimum": 0, "maximum": 100},
            "danger_level": {"type": "integer", "minimum": 0, "maximum": 100},
            "trust_to_party": {"type": "integer", "minimum": -100, "maximum": 100},
            "favorability": {"type": "integer", "minimum": -100, "maximum": 100},
            "sanity_state": {
                "type": "string",
                "enum": ["stable", "strained", "fractured", "broken"],
            },
            "corruption_state": {
                "type": "string",
                "enum": ["pure", "tainted", "corrupted", "abyssal"],
            },
            "injury_state": {
                "type": "string",
                "enum": ["healthy", "wounded", "critical", "dying"],
            },
            "alive_state": {"type": "boolean"},
            "relations": {"type": "array", "items": relation_schema},
            "portrait_seed": {"type": "string"},
            "style_tags": {"type": "array", "items": {"type": "string"}},
            "key_features": {"type": "array", "items": {"type": "string"}},
        },
    }


@dataclass
class ProfileDiffEntry:
    chapter: str
    field: str
    before: Any
    after: Any


@dataclass
class CharacterProfile:
    profile_version: str
    id: str
    name: str
    alias: str
    age_range: str
    gender_presentation: str
    pathway: str
    sequence_level: int
    affiliation: str
    public_identity: str
    motivation: str
    fear: str
    secret: str
    taboo: str
    speech_style: str
    clue_value: int
    danger_level: int
    trust_to_party: int
    favorability: int
    sanity_state: Literal["stable", "strained", "fractured", "broken"]
    corruption_state: Literal["pure", "tainted", "corrupted", "abyssal"]
    injury_state: Literal["healthy", "wounded", "critical", "dying"]
    alive_state: bool
    relations: List[Dict[str, Any]]
    portrait_seed: str
    style_tags: List[str]
    key_features: List[str]

    _diff_log: List[ProfileDiffEntry] = field(default_factory=list, init=False, repr=False)

    def to_dict(self) -> Dict[str, Any]:
        payload = {
            "profile_version": self.profile_version,
            "id": self.id,
            "name": self.name,
            "alias": self.alias,
            "age_range": self.age_range,
            "gender_presentation": self.gender_presentation,
            "pathway": self.pathway,
            "sequence_level": self.sequence_level,
            "affiliation": self.affiliation,
            "public_identity": self.public_identity,
            "motivation": self.motivation,
            "fear": self.fear,
            "secret": self.secret,
            "taboo": self.taboo,
            "speech_style": self.speech_style,
            "clue_value": self.clue_value,
            "danger_level": self.danger_level,
            "trust_to_party": self.trust_to_party,
            "favorability": self.favorability,
            "sanity_state": self.sanity_state,
            "corruption_state": self.corruption_state,
            "injury_state": self.injury_state,
            "alive_state": self.alive_state,
            "relations": self.relations,
            "portrait_seed": self.portrait_seed,
            "style_tags": self.style_tags,
            "key_features": self.key_features,
        }
        return copy.deepcopy(payload)

    def apply_chapter_updates(self, chapter: str, **changes: Any) -> None:
        for field_name, value in changes.items():
            if not hasattr(self, field_name):
                raise AttributeError(f"Unknown profile field: {field_name}")
            before = copy.deepcopy(getattr(self, field_name))
            if before != value:
                setattr(self, field_name, value)
                self._diff_log.append(
                    ProfileDiffEntry(
                        chapter=chapter,
                        field=field_name,
                        before=before,
                        after=copy.deepcopy(value),
                    )
                )

    def diff_log(self) -> List[Dict[str, Any]]:
        return [
            {
                "chapter": item.chapter,
                "field": item.field,
                "before": item.before,
                "after": item.after,
            }
            for item in self._diff_log
        ]


def _ensure_type(field_name: str, value: Any, expected_type: type) -> None:
    if not isinstance(value, expected_type):
        raise ValueError(f"Invalid profile schema: {field_name} must be {expected_type.__name__}")


def validate_profile_payload(payload: Dict[str, Any]) -> None:
    schema = profile_json_schema()

    required = set(schema["required"])
    missing = required - set(payload.keys())
    if missing:
        raise ValueError(f"Invalid profile schema: missing fields {sorted(missing)}")

    unknown = set(payload.keys()) - set(schema["properties"].keys())
    if unknown:
        raise ValueError(f"Invalid profile schema: unknown fields {sorted(unknown)}")

    _ensure_type("profile_version", payload["profile_version"], str)
    if re.match(r"^\d+\.\d+\.\d+$", payload["profile_version"]) is None:
        raise ValueError("Invalid profile schema: profile_version must use semver format")

    string_fields = [
        "id",
        "name",
        "alias",
        "age_range",
        "gender_presentation",
        "pathway",
        "affiliation",
        "public_identity",
        "motivation",
        "fear",
        "secret",
        "taboo",
        "speech_style",
        "portrait_seed",
    ]
    for field_name in string_fields:
        _ensure_type(field_name, payload[field_name], str)

    int_ranges = {
        "sequence_level": (0, 9),
        "clue_value": (0, 100),
        "danger_level": (0, 100),
        "trust_to_party": (-100, 100),
        "favorability": (-100, 100),
    }
    for field_name, (low, high) in int_ranges.items():
        _ensure_type(field_name, payload[field_name], int)
        if payload[field_name] < low or payload[field_name] > high:
            raise ValueError(f"Invalid profile schema: {field_name} out of range")

    _ensure_type("alive_state", payload["alive_state"], bool)

    for field_name in ["style_tags", "key_features", "relations"]:
        _ensure_type(field_name, payload[field_name], list)

    for item in payload["style_tags"] + payload["key_features"]:
        _ensure_type("style/key item", item, str)

    allowed_sanity = {"stable", "strained", "fractured", "broken"}
    allowed_corruption = {"pure", "tainted", "corrupted", "abyssal"}
    allowed_injury = {"healthy", "wounded", "critical", "dying"}
    if payload["sanity_state"] not in allowed_sanity:
        raise ValueError("Invalid profile schema: sanity_state invalid")
    if payload["corruption_state"] not in allowed_corruption:
        raise ValueError("Invalid profile schema: corruption_state invalid")
    if payload["injury_state"] not in allowed_injury:
        raise ValueError("Invalid profile schema: injury_state invalid")

    allowed_relation_types = {"player", "npc", "faction", "unknown"}
    for relation in payload["relations"]:
        _ensure_type("relation", relation, dict)
        relation_required = {"target_id", "relation_type", "trust_delta", "notes"}
        if relation_required - set(relation.keys()):
            raise ValueError("Invalid profile schema: relation missing fields")
        if set(relation.keys()) - relation_required:
            raise ValueError("Invalid profile schema: relation has unknown fields")
        _ensure_type("relation.target_id", relation["target_id"], str)
        _ensure_type("relation.notes", relation["notes"], str)
        _ensure_type("relation.trust_delta", relation["trust_delta"], int)
        if relation["relation_type"] not in allowed_relation_types:
            raise ValueError("Invalid profile schema: relation_type invalid")


def profile_generation_prompt(world_context: str) -> str:
    """Prompt template forcing AI to return strict schema-compliant JSON only."""
    schema = json.dumps(profile_json_schema(), ensure_ascii=False)
    return (
        "你是角色生成器。必须输出一个且仅一个 JSON 对象，不允许 markdown、不允许额外解释。\n"
        "硬性约束：输出必须满足下述 JSON Schema；若无法满足，返回 error 字段说明失败原因。\n"
        f"JSON Schema: {schema}\n"
        f"世界背景: {world_context}\n"
        "输出前请自检并进行 JSON 校验，确保合法后再输出。"
    )


def generate_profile_from_ai(raw_output: str) -> CharacterProfile:
    payload = json.loads(raw_output)
    validate_profile_payload(payload)
    if payload.get("profile_version") != PROFILE_VERSION:
        raise ValueError(
            f"Unsupported profile version: {payload.get('profile_version')}, expected {PROFILE_VERSION}"
        )
    return CharacterProfile(**payload)


class StoryEngine:
    """Drive game behavior from profile fields instead of hard-coded plot branches."""

    def dialogue_line(self, profile: CharacterProfile) -> str:
        tone = {
            "stable": "冷静",
            "strained": "急促",
            "fractured": "混乱",
            "broken": "失序",
        }[profile.sanity_state]
        relation_hint = "信任" if profile.trust_to_party >= 20 else "戒备"
        return f"[{tone}/{relation_hint}] {profile.name}以{profile.speech_style}说道：我追求{profile.motivation}。"

    def clue_drop_chance(self, profile: CharacterProfile) -> float:
        base = profile.clue_value / 100
        trust_bonus = max(profile.trust_to_party, 0) / 200
        sanity_penalty = 0.15 if profile.sanity_state in {"fractured", "broken"} else 0
        return max(0.0, min(1.0, base + trust_bonus - sanity_penalty))

    def betrayal_or_assist(self, profile: CharacterProfile) -> Literal["betray", "assist", "neutral"]:
        if not profile.alive_state or profile.injury_state == "dying":
            return "neutral"
        if profile.danger_level > 70 and profile.trust_to_party < -20:
            return "betray"
        if profile.favorability > 30 and profile.trust_to_party > 20:
            return "assist"
        return "neutral"
