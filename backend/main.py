from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from orchestration import OrchestrationService
from state_service import CampaignStateService
from structured_logger import log_event

app = FastAPI(title="Desktop TRPG Backend", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

state_service = CampaignStateService("../data/campaign_state.db")
orchestrator = OrchestrationService()


@app.get("/api/health")
def health_check():
    model_available = orchestrator.model_available()
    db_available = state_service.ping()
    return {
        "model": {"available": model_available, "provider": "mock-llm"},
        "database": {"available": db_available, "engine": "sqlite"},
    }


@app.post("/api/campaigns")
def create_campaign(payload: dict):
    session_id = payload.get("sessionId", "local-session")
    campaign = state_service.create_campaign(payload["name"], session_id)
    return campaign


@app.get("/api/campaigns/{campaign_id}")
def get_campaign(campaign_id: str):
    return state_service.get_campaign(campaign_id)


@app.post("/api/campaigns/{campaign_id}/events")
def add_event(campaign_id: str, payload: dict):
    session_id = payload.get("sessionId", "local-session")
    event = state_service.append_event(campaign_id, payload["text"], session_id)
    return event


@app.post("/api/orchestration/narrative")
def get_narrative(payload: dict):
    session_id = payload.get("sessionId", "local-session")
    result = orchestrator.generate_narrative(
        command=payload.get("command", "继续剧情"),
        session_id=session_id,
    )
    log_event(
        module="orchestration",
        event_id=result["eventId"],
        session_id=session_id,
        duration_ms=result["durationMs"],
    )
    return result
