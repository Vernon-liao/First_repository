import unittest
from random import Random

from role_module import (
    CampaignArchive,
    ChapterContext,
    CharacterManager,
    Role,
    RoleType,
    persistent_characters,
)
from src.profile_system import CharacterProfile


class RoleModuleTest(unittest.TestCase):
    def setUp(self) -> None:
        self.context = ChapterContext(
            chapter_id="ch-01",
            location="主城区",
            anomaly_level=4,
            killer_pool=["医生", "议员", "侍从"],
            player_faction_relations={"教会": 10, "警局": 15, "黑市": -5},
        )
        self.manager = CharacterManager(rng=Random(42))

    def test_has_role_type(self):
        self.assertEqual(RoleType.PERSISTENT.value, "persistent")
        self.assertEqual(RoleType.GENERATED.value, "generated")

    def test_persistent_pool_size(self):
        self.assertGreaterEqual(len(persistent_characters), 8)
        self.assertLessEqual(len(persistent_characters), 12)

    def test_chapter_load_includes_persistent_and_generated(self):
        graph = self.manager.load_chapter(self.context)
        p_count = sum(1 for r in graph.active_roles if r.role_type == RoleType.PERSISTENT)
        g_count = sum(1 for r in graph.active_roles if r.role_type == RoleType.GENERATED)
        self.assertGreaterEqual(p_count, 2)
        self.assertLessEqual(p_count, 4)
        self.assertGreaterEqual(g_count, 3)
        self.assertLessEqual(g_count, 8)

    def test_protected_slots_not_overridden(self):
        persistent = [
            Role("A", "教会联络人", RoleType.PERSISTENT, "主线引导者"),
            Role("B", "警局线人", RoleType.PERSISTENT, "线索保管者"),
        ]
        generated = self.manager.generate_dynamic_roles(self.context, persistent, force_count=6)
        for role in generated:
            self.assertNotEqual(role.key_function_slot, "主线引导者")
            self.assertNotEqual(role.key_function_slot, "线索保管者")

    def test_promote_deep_relation_roles(self):
        dynamic_roles = [
            Role("d1", "街头探子", RoleType.GENERATED, "外围目击者", relation_depth=80),
            Role("d2", "巡夜队员", RoleType.GENERATED, "治安变量", relation_depth=60),
        ]
        promoted = self.manager.promote_dynamic_to_candidates(dynamic_roles, threshold=70)
        self.assertEqual(len(promoted), 1)
        self.assertEqual(promoted[0].role_type, RoleType.CANDIDATE_PERSISTENT)

    def test_dynamic_roles_visible_in_ui_panels(self):
        graph = self.manager.load_chapter(self.context)
        relation_panel = self.manager.ui_relationship_panel(graph)
        npc_list = self.manager.ui_npc_list(graph)

        role_types_in_panel = {item["role_type"] for item in relation_panel}
        role_types_in_npc = {item["role_type"] for item in npc_list}

        self.assertIn(RoleType.PERSISTENT.value, role_types_in_panel)
        self.assertIn(RoleType.GENERATED.value, role_types_in_panel)
        self.assertIn(RoleType.GENERATED.value, role_types_in_npc)

    def test_settlement_promotes_and_writes_campaign_archive(self):
        graph = self.manager.load_chapter(self.context)
        archive = CampaignArchive()

        settlement = self.manager.settle_chapter(graph, archive, threshold=0)

        self.assertEqual(settlement.chapter_id, graph.chapter_id)
        self.assertGreaterEqual(len(settlement.promoted_candidates), 3)
        self.assertEqual(len(archive.settlements), 1)
        self.assertEqual(len(archive.candidate_persistent_roles), len(settlement.promoted_candidates))

    def test_profile_binding_drives_dialogue_and_behavior(self):
        role = Role("奥黛丽", "心理医生", RoleType.GENERATED, "外围目击者")
        profile = CharacterProfile(
            profile_version="1.0.0",
            id="npc_001",
            name="奥黛丽",
            alias="黑夜观察者",
            age_range="20-30",
            gender_presentation="feminine",
            pathway="观众",
            sequence_level=7,
            affiliation="值夜者",
            public_identity="心理医生",
            motivation="守护同伴",
            fear="失去理智",
            secret="曾接触禁忌封印",
            taboo="不提及旧日神名",
            speech_style="轻声且克制",
            clue_value=80,
            danger_level=60,
            trust_to_party=35,
            favorability=45,
            sanity_state="stable",
            corruption_state="tainted",
            injury_state="healthy",
            alive_state=True,
            relations=[],
            portrait_seed="audrey-night-001",
            style_tags=["gothic", "mystic"],
            key_features=["银色长发", "深色披风"],
        )

        self.manager.bind_profile(role, profile)
        tone = self.manager.npc_dialogue_tone(role)
        tendency = self.manager.npc_behavior_tendency(role)

        self.assertIn("守护同伴", tone)
        self.assertEqual(tendency, "assist")

    def test_chapter_start_report_contains_role_statistics(self):
        graph = self.manager.load_chapter(self.context)
        archive = CampaignArchive()
        self.manager.settle_chapter(graph, archive, threshold=100)

        report = self.manager.chapter_start_report(graph, archive)

        self.assertIn("常驻=", report)
        self.assertIn("动态=", report)
        self.assertIn("候选=", report)


if __name__ == "__main__":
    unittest.main()
