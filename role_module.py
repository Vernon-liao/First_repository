from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from random import Random
from typing import Dict, List, Sequence


class RoleType(str, Enum):
    """角色类型。"""

    PERSISTENT = "persistent"
    GENERATED = "generated"
    CANDIDATE_PERSISTENT = "candidate_persistent"


@dataclass(slots=True)
class Role:
    name: str
    title: str
    role_type: RoleType
    key_function_slot: str
    location_affinity: Sequence[str] = field(default_factory=list)
    relation_depth: int = 0
    metadata: Dict[str, str] = field(default_factory=dict)


@dataclass(slots=True)
class ChapterContext:
    chapter_id: str
    location: str
    anomaly_level: int
    killer_pool: Sequence[str]
    player_faction_relations: Dict[str, int]


@dataclass(slots=True)
class EventGraph:
    chapter_id: str
    active_roles: List[Role] = field(default_factory=list)


persistent_characters: List[Role] = [
    Role("伊莲娜", "教会联络人", RoleType.PERSISTENT, "主线引导者", ["旧教区", "主城区"]),
    Role("洛克", "黑市中间人", RoleType.PERSISTENT, "资源调度者", ["下城区", "码头"]),
    Role("韩默", "警局线人", RoleType.PERSISTENT, "线索保管者", ["警局", "主城区"]),
    Role("米拉", "报社编辑", RoleType.PERSISTENT, "舆情放大者", ["报社", "主城区"]),
    Role("布莱尔", "法医顾问", RoleType.PERSISTENT, "尸检解读者", ["停尸间", "警局"]),
    Role("诺亚", "码头调度员", RoleType.PERSISTENT, "物流通道守门人", ["码头", "下城区"]),
    Role("维姬", "档案馆管理员", RoleType.PERSISTENT, "历史档案解锁者", ["档案馆", "大学区"]),
    Role("奥尔森", "剧院经理", RoleType.PERSISTENT, "社交场引荐人", ["大剧院", "上城区"]),
    Role("塔莎", "地下诊所医生", RoleType.PERSISTENT, "伤情隐匿者", ["下城区", "贫民区"]),
    Role("格雷", "蒸汽工坊老板", RoleType.PERSISTENT, "装置供应者", ["工业区", "码头"]),
]


class CharacterManager:
    """章节角色装载与流转逻辑。"""

    PROTECTED_SLOTS = {"主线引导者", "线索保管者"}

    def __init__(self, rng: Random | None = None) -> None:
        self.rng = rng or Random()
        self._persistent_pool: List[Role] = list(persistent_characters)

    def load_chapter(self, context: ChapterContext) -> EventGraph:
        """章节装载流程：先注入常驻角色，再生成动态角色。"""
        graph = EventGraph(chapter_id=context.chapter_id)
        graph.active_roles.extend(self.inject_persistent_roles(context))
        graph.active_roles.extend(self.generate_dynamic_roles(context, graph.active_roles))
        return graph

    def inject_persistent_roles(self, context: ChapterContext, force_count: int | None = None) -> List[Role]:
        count = force_count if force_count is not None else self.rng.randint(2, 4)
        if count < 2 or count > 4:
            raise ValueError("常驻角色注入数量必须在 2~4 之间")

        weighted = sorted(
            self._persistent_pool,
            key=lambda role: (context.location in role.location_affinity, self.rng.random()),
            reverse=True,
        )
        return weighted[:count]

    def generate_dynamic_roles(
        self,
        context: ChapterContext,
        existing_roles: Sequence[Role],
        force_count: int | None = None,
    ) -> List[Role]:
        count = force_count if force_count is not None else self.rng.randint(3, 8)
        if count < 3 or count > 8:
            raise ValueError("动态角色生成数量必须在 3~8 之间")

        occupied_slots = {r.key_function_slot for r in existing_roles if r.role_type == RoleType.PERSISTENT}
        forbidden_slots = self.PROTECTED_SLOTS & occupied_slots

        dynamic_templates = [
            ("街头探子", "外围目击者"),
            ("灵知学徒", "异象记录者"),
            ("巡夜队员", "治安变量"),
            ("私家侦探", "嫌疑追踪者"),
            ("码头搬运工", "货单见证者"),
            ("剧院演员", "社交渗透者"),
            ("钟楼看守", "时间线校验者"),
            ("旅店账房", "住客轨迹保管者"),
            ("炼金助手", "违禁品接触者"),
            ("流浪神父", "精神干预者"),
        ]

        generated: List[Role] = []
        faction_bias = max(context.player_faction_relations.values(), default=0)
        suspect_hint = "/".join(context.killer_pool[:2]) if context.killer_pool else "未知"

        for idx in range(count):
            title, slot = dynamic_templates[idx % len(dynamic_templates)]
            if slot in forbidden_slots:
                slot = f"次级-{slot}"

            relation_depth = max(0, min(100, 20 + context.anomaly_level * 10 + faction_bias + self.rng.randint(-15, 15)))
            role = Role(
                name=f"{context.location}-{title}-{idx+1}",
                title=title,
                role_type=RoleType.GENERATED,
                key_function_slot=slot,
                location_affinity=[context.location],
                relation_depth=relation_depth,
                metadata={
                    "anomaly_level": str(context.anomaly_level),
                    "killer_hint": suspect_hint,
                },
            )
            generated.append(role)

        return generated

    def promote_dynamic_to_candidates(self, dynamic_roles: Sequence[Role], threshold: int = 70) -> List[Role]:
        """会话结束时将深关系动态角色升级为候选常驻角色。"""
        promoted: List[Role] = []
        for role in dynamic_roles:
            if role.role_type != RoleType.GENERATED:
                continue
            if role.relation_depth < threshold:
                continue
            promoted.append(
                Role(
                    name=role.name,
                    title=role.title,
                    role_type=RoleType.CANDIDATE_PERSISTENT,
                    key_function_slot=role.key_function_slot,
                    location_affinity=role.location_affinity,
                    relation_depth=role.relation_depth,
                    metadata={**role.metadata, "promoted_from": "generated"},
                )
            )
        return promoted
