from __future__ import annotations

from typing import Any, Protocol
from .scheduler import Scheduler
from .witness import WitnessCommitment, acknowledgement_text, build_commitment
from .witness_store import WitnessStore

class XWriter(Protocol):
    def reply(self, tweet_id: str, text: str) -> dict[str, Any]: ...

class WitnessFlow:
    def __init__(self, store: WitnessStore, scheduler: Scheduler, x_writer: XWriter):
        self.store = store
        self.scheduler = scheduler
        self.x_writer = x_writer

    def record(self, tweet: dict[str, Any]) -> WitnessCommitment:
        existing = self.store.get_by_tweet(str(tweet["id"]))
        if existing:
            return existing
        commitment = build_commitment(tweet)
        job = self.scheduler.schedule(
            kind="witness_follow_up",
            run_at=commitment.follow_up_at,
            payload={"commitment_id": commitment.id, "source_tweet_id": commitment.source_tweet_id, "conversation_id": commitment.conversation_id, "tag": commitment.tag},
        )
        commitment.schedule_id = job.id
        commitment.status = "scheduled"
        self.store.save(commitment)
        acknowledgement = self.x_writer.reply(commitment.source_tweet_id, acknowledgement_text(commitment))
        commitment.acknowledgement_tweet_id = str(acknowledgement.get("id", ""))
        commitment.status = "acknowledged" if commitment.acknowledgement_tweet_id else "scheduled"
        return self.store.save(commitment)
