import unittest
from random import Random

from role_module import (
    ChapterContext,
    CharacterManager,
    Role,
    RoleType,
    persistent_characters,
)


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


if __name__ == "__main__":
    unittest.main()
