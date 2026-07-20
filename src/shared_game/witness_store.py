from __future__ import annotations

from pathlib import Path
import json
import sqlite3
from .witness import WitnessCommitment

class WitnessStore:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.path) as conn:
            conn.execute("CREATE TABLE IF NOT EXISTS witness_commitments (id TEXT PRIMARY KEY, source_tweet_id TEXT UNIQUE NOT NULL, state_json TEXT NOT NULL)")

    def save(self, commitment: WitnessCommitment) -> WitnessCommitment:
        with sqlite3.connect(self.path) as conn:
            conn.execute("INSERT OR REPLACE INTO witness_commitments (id, source_tweet_id, state_json) VALUES (?, ?, ?)", (commitment.id, commitment.source_tweet_id, json.dumps(commitment.to_dict(), sort_keys=True)))
        return commitment

    def get_by_tweet(self, tweet_id: str) -> WitnessCommitment | None:
        with sqlite3.connect(self.path) as conn:
            row = conn.execute("SELECT state_json FROM witness_commitments WHERE source_tweet_id = ?", (tweet_id,)).fetchone()
        return WitnessCommitment(**json.loads(row[0])) if row else None
