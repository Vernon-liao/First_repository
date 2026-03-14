from __future__ import annotations

from dataclasses import dataclass, field
from time import perf_counter
from typing import Any, Dict, List, Literal


NarrativeMode = Literal["ok", "timeout"]
ImageMode = Literal["ok", "failure"]
SaveMode = Literal["ok", "interrupted"]


@dataclass(slots=True)
class StepRecord:
    name: str
    fallback_used: bool
    latency_ms: float
    detail: str


@dataclass(slots=True)
class CampaignRunResult:
    campaign_id: str
    chapter_id: str
    chapter_settled: bool
    rollback_applied: bool
    events: List[str]
    logs: List[Dict[str, Any]]
    performance: Dict[str, float]
    checkpoints: List[Dict[str, Any]]
    fallback_summary: Dict[str, bool]


@dataclass(slots=True)
class CampaignSimulator:
    campaign_id: str
    _events: List[str] = field(default_factory=list)
    _logs: List[Dict[str, Any]] = field(default_factory=list)
    _checkpoints: List[Dict[str, Any]] = field(default_factory=list)

    def _record(self, step: str, source: str, fallback_used: bool, latency_ms: float, detail: str) -> None:
        self._logs.append(
            {
                "step": step,
                "source": source,
                "fallback_used": fallback_used,
                "latency_ms": round(latency_ms, 2),
                "detail": detail,
            }
        )

    def _checkpoint(self, reason: str, payload: Dict[str, Any]) -> None:
        snap = {"reason": reason, "payload": payload}
        self._checkpoints.append(snap)

    def _run_narration(self, mode: NarrativeMode) -> StepRecord:
        started = perf_counter()
        if mode == "timeout":
            latency_ms = (perf_counter() - started) * 1000
            return StepRecord(
                name="narration",
                fallback_used=True,
                latency_ms=latency_ms,
                detail="narrative_timeout_fallback_template",
            )
        latency_ms = (perf_counter() - started) * 1000
        return StepRecord("narration", False, latency_ms, "narrative_model_ok")

    def _run_image(self, mode: ImageMode) -> StepRecord:
        started = perf_counter()
        if mode == "failure":
            latency_ms = (perf_counter() - started) * 1000
            return StepRecord(
                name="image",
                fallback_used=True,
                latency_ms=latency_ms,
                detail="image_placeholder_uri",
            )
        latency_ms = (perf_counter() - started) * 1000
        return StepRecord("image", False, latency_ms, "image_model_ok")

    def _save_progress(self, mode: SaveMode, payload: Dict[str, Any]) -> StepRecord:
        started = perf_counter()
        if mode == "interrupted":
            latency_ms = (perf_counter() - started) * 1000
            return StepRecord(
                name="save",
                fallback_used=True,
                latency_ms=latency_ms,
                detail="save_interrupted_rollback_to_last_checkpoint",
            )
        self._checkpoint("chapter_end", payload)
        latency_ms = (perf_counter() - started) * 1000
        return StepRecord("save", False, latency_ms, "save_ok")

    def run_chapter_flow(
        self,
        chapter_id: str,
        narrative_mode: NarrativeMode = "ok",
        image_mode: ImageMode = "ok",
        save_mode: SaveMode = "ok",
    ) -> CampaignRunResult:
        self._events = ["CAMPAIGN_CREATED", "CHAPTER_1_STARTED"]
        self._logs = []
        self._checkpoints = []

        first_screen_started = perf_counter()
        self._checkpoint("campaign_created", {"chapter_id": chapter_id, "state": "bootstrapped"})
        first_screen_ms = (perf_counter() - first_screen_started) * 1000

        narration = self._run_narration(narrative_mode)
        self._record("chapter_step_1", "narrative", narration.fallback_used, narration.latency_ms, narration.detail)
        self._events.append("NARRATION_READY")

        image = self._run_image(image_mode)
        self._record("chapter_step_2", "image", image.fallback_used, image.latency_ms, image.detail)
        self._events.append("IMAGE_READY")

        step_started = perf_counter()
        self._events.append("ROLL_RESOLVED")
        single_step_ms = (perf_counter() - step_started) * 1000

        settlement_payload = {
            "chapter_id": chapter_id,
            "summary": "第一章结算完成",
            "events": list(self._events),
        }
        save = self._save_progress(save_mode, settlement_payload)
        self._record("chapter_settlement", "persistence", save.fallback_used, save.latency_ms, save.detail)

        rollback_applied = False
        chapter_settled = True
        if save_mode == "interrupted":
            rollback_applied = True
            # fallback: restore last checkpoint and still finish settlement with degraded mode
            restored = self._checkpoints[-1] if self._checkpoints else {"reason": "none", "payload": {}}
            self._events.append("ROLLBACK_PERFORMED")
            self._checkpoint("chapter_end_recovered", {"restored_from": restored["reason"], **settlement_payload})

        self._events.append("CHAPTER_1_SETTLED")

        return CampaignRunResult(
            campaign_id=self.campaign_id,
            chapter_id=chapter_id,
            chapter_settled=chapter_settled,
            rollback_applied=rollback_applied,
            events=list(self._events),
            logs=list(self._logs),
            performance={
                "first_screen_ms": round(first_screen_ms, 2),
                "single_step_response_ms": round(single_step_ms, 2),
            },
            checkpoints=list(self._checkpoints),
            fallback_summary={
                "narrative_fallback": narration.fallback_used,
                "image_fallback": image.fallback_used,
                "save_recovery": save.fallback_used,
            },
        )


def build_demo_campaign_save() -> Dict[str, Any]:
    simulator = CampaignSimulator(campaign_id="demo-campaign-v0.1")
    result = simulator.run_chapter_flow(chapter_id="chapter-1")
    return {
        "campaign_id": result.campaign_id,
        "chapter_id": result.chapter_id,
        "chapter_settled": result.chapter_settled,
        "events": result.events,
        "checkpoints": result.checkpoints,
        "logs": result.logs,
        "performance": result.performance,
        "version": "v0.1",
    }
