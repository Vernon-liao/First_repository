import json
import sqlite3
import uuid
from datetime import datetime, timezone


class CampaignStateService:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_db()

    def _connect(self):
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS campaigns (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    session_id TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS campaign_events (
                    id TEXT PRIMARY KEY,
                    campaign_id TEXT NOT NULL,
                    session_id TEXT NOT NULL,
                    text TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (campaign_id) REFERENCES campaigns(id)
                )
                """
            )

    def ping(self) -> bool:
        try:
            with self._connect() as conn:
                conn.execute("SELECT 1")
            return True
        except sqlite3.Error:
            return False

    def create_campaign(self, name: str, session_id: str) -> dict:
        campaign_id = str(uuid.uuid4())
        created_at = datetime.now(timezone.utc).isoformat()
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO campaigns (id, name, session_id, created_at) VALUES (?, ?, ?, ?)",
                (campaign_id, name, session_id, created_at),
            )

        return {
            "id": campaign_id,
            "name": name,
            "sessionId": session_id,
            "createdAt": created_at,
            "events": [],
        }

    def get_campaign(self, campaign_id: str) -> dict:
        with self._connect() as conn:
            campaign_row = conn.execute(
                "SELECT id, name, session_id, created_at FROM campaigns WHERE id = ?",
                (campaign_id,),
            ).fetchone()
            event_rows = conn.execute(
                "SELECT id, text, session_id, created_at FROM campaign_events WHERE campaign_id = ? ORDER BY created_at",
                (campaign_id,),
            ).fetchall()

        if not campaign_row:
            return {"error": "Campaign not found", "id": campaign_id}

        events = [
            {
                "id": row[0],
                "text": row[1],
                "sessionId": row[2],
                "createdAt": row[3],
            }
            for row in event_rows
        ]

        return {
            "id": campaign_row[0],
            "name": campaign_row[1],
            "sessionId": campaign_row[2],
            "createdAt": campaign_row[3],
            "events": events,
            "snapshot": json.dumps({"eventCount": len(events)}, ensure_ascii=False),
        }

    def append_event(self, campaign_id: str, text: str, session_id: str) -> dict:
        event_id = str(uuid.uuid4())
        created_at = datetime.now(timezone.utc).isoformat()
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO campaign_events (id, campaign_id, session_id, text, created_at) VALUES (?, ?, ?, ?, ?)",
                (event_id, campaign_id, session_id, text, created_at),
            )

        return {
            "id": event_id,
            "campaignId": campaign_id,
            "sessionId": session_id,
            "text": text,
            "createdAt": created_at,
        }
