import time
import uuid


class OrchestrationService:
    def model_available(self) -> bool:
        return True

    def generate_narrative(self, command: str, session_id: str) -> dict:
        started = time.perf_counter()
        mock_text = (
            f"【旁白】你下达了‘{command}’，远方钟楼传来第十三声钟响，"
            "雾中出现一名自称引路人的旅者，递来一张写着古堡坐标的羊皮卷。"
        )
        duration_ms = int((time.perf_counter() - started) * 1000)
        return {
            "eventId": str(uuid.uuid4()),
            "sessionId": session_id,
            "module": "orchestration",
            "durationMs": duration_ms,
            "narrative": mock_text,
        }
