from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from typing import Any
import re

WITNESS_HANDLE = "@marvin_panics"

@dataclass
class WitnessCommitment:
    id: str
    source_tweet_id: str
    conversation_id: str
    author: str
    text: str
    committed_at: str
    follow_up_at: str
    tag: str = "witnessed-commitment"
    schedule_id: str = ""
    acknowledgement_tweet_id: str = ""
    status: str = "detected"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def detect_witness_request(tweet: dict[str, Any]) -> bool:
    text = tweet.get("text", "")
    lowered = text.lower()
    has_handle = WITNESS_HANDLE in lowered
    witness_language = any(term in lowered for term in ("witness", "witnessed", "hold me accountable", "record this"))
    commitment_language = any(term in lowered for term in ("goal", "outcome", "commit", "i will", "by ", "sales", "sale"))
    return bool(has_handle and witness_language and commitment_language)


def build_commitment(tweet: dict[str, Any], *, now: datetime | None = None) -> WitnessCommitment:
    if not detect_witness_request(tweet):
        raise ValueError("tweet does not contain an explicit Marvin witness commitment")
    created = _parse_time(tweet.get("created_at"))
    follow_up = created + timedelta(days=7)
    return WitnessCommitment(
        id=f"x-{tweet['id']}",
        source_tweet_id=str(tweet["id"]),
        conversation_id=str(tweet.get("conversation_id") or tweet["id"]),
        author=str(tweet.get("author") or "unknown"),
        text=str(tweet["text"]),
        committed_at=created.isoformat(),
        follow_up_at=follow_up.isoformat(),
    )


def _parse_time(value: str | None) -> datetime:
    if not value:
        return datetime.now(timezone.utc)
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def acknowledgement_text(commitment: WitnessCommitment) -> str:
    date = commitment.follow_up_at[:10]
    return f"Recorded. Follow-up scheduled for {date}. The scoreboard gets a week to become inconvenient." 
