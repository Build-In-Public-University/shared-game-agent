#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from typing import Any

from shared_game.scheduler import JsonlScheduler
from shared_game.witness_flow import WitnessFlow
from shared_game.witness_store import WitnessStore

APP = os.getenv("XURL_APP", "marvin-x")
DB = os.getenv("SHARED_GAME_DB", "/var/lib/shared-game-agent/game.sqlite3")
QUEUE = os.getenv("WITNESS_QUEUE", "/var/lib/shared-game-agent/witness-jobs.jsonl")
DRY_RUN = os.getenv("WITNESS_DRY_RUN", "false").lower() == "true"

class XurlWriter:
    def reply(self, tweet_id: str, text: str) -> dict[str, Any]:
        if DRY_RUN:
            return {"id": f"dry-run-{tweet_id}"}
        result = subprocess.run(["xurl", "--app", APP, "reply", tweet_id, text], capture_output=True, text=True, check=True)
        return json.loads(result.stdout)

def mentions() -> list[dict[str, Any]]:
    result = subprocess.run(["xurl", "--app", APP, "mentions", "-n", "20"], capture_output=True, text=True, check=True)
    body = json.loads(result.stdout)
    data = body.get("data", body.get("tweets", []))
    return data if isinstance(data, list) else []

def main() -> None:
    store = WitnessStore(DB)
    flow = WitnessFlow(store, JsonlScheduler(QUEUE), XurlWriter())
    detected = 0
    for tweet in mentions():
        if store.get_by_tweet(str(tweet.get("id", ""))):
            continue
        try:
            flow.record(tweet)
        except ValueError:
            continue
        detected += 1
    print(json.dumps({"status": "ok", "detected_and_recorded": detected, "dry_run": DRY_RUN, "queue": QUEUE}))

if __name__ == "__main__":
    main()
