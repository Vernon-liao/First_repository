from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[1] / "backend"))

from orchestration import OrchestrationService
from state_service import CampaignStateService


def test_orchestration_returns_mock_narrative():
    svc = OrchestrationService()
    data = svc.generate_narrative("前进", "s-1")

    assert data["sessionId"] == "s-1"
    assert data["module"] == "orchestration"
    assert "旁白" in data["narrative"]


def test_campaign_state_service_crud(tmp_path):
    db_file = tmp_path / "state.db"
    svc = CampaignStateService(str(db_file))

    created = svc.create_campaign("测试战役", "s-2")
    event = svc.append_event(created["id"], "第一条事件", "s-2")
    loaded = svc.get_campaign(created["id"])

    assert created["name"] == "测试战役"
    assert event["campaignId"] == created["id"]
    assert len(loaded["events"]) == 1
    assert loaded["events"][0]["text"] == "第一条事件"
