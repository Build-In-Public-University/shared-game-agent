from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Protocol
import json
import uuid

@dataclass
class ScheduledJob:
    id: str
    kind: str
    run_at: str
    payload: dict[str, Any]
    status: str = "scheduled"

class Scheduler(Protocol):
    def schedule(self, *, kind: str, run_at: str, payload: dict[str, Any]) -> ScheduledJob: ...

class JsonlScheduler:
    """Durable handoff queue consumed by the VPS worker/systemd timer."""
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def schedule(self, *, kind: str, run_at: str, payload: dict[str, Any]) -> ScheduledJob:
        job = ScheduledJob(id=f"job-{uuid.uuid4()}", kind=kind, run_at=run_at, payload=payload)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(asdict(job), sort_keys=True) + "\n")
        return job
