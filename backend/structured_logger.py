import json
import logging
from datetime import datetime, timezone

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("backend")


def log_event(event_id: str, session_id: str, module: str, duration_ms: int):
    logger.info(
        json.dumps(
            {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "eventId": event_id,
                "sessionId": session_id,
                "module": module,
                "durationMs": duration_ms,
            },
            ensure_ascii=False,
        )
    )
