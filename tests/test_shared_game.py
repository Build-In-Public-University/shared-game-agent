import json
from pathlib import Path

from fastapi.testclient import TestClient

from shared_game import STAGES
from shared_game.api import app
from shared_game.model_registry import available_models
from shared_game.scheduler import ScheduledJob
from shared_game.witness import build_commitment, detect_witness_request
from shared_game.witness_flow import WitnessFlow
from shared_game.witness_store import WitnessStore


def test_stage_contract():
    assert len(STAGES) == 7
    assert STAGES[0][0] == "name_outcome"
    assert STAGES[-1][0] == "review_choose"


def test_model_roster_contains_flash_and_pro():
    assert available_models() == [
        "deepseek/deepseek-v4-flash",
        "deepseek/deepseek-v4-pro",
    ]


def test_game_api_progresses_and_completes(monkeypatch, tmp_path):
    from shared_game import api
    monkeypatch.setattr(api, "store", api.GameStore(tmp_path / "game.sqlite3"))
    monkeypatch.setattr(api.llm, "guide", lambda **kwargs: "Keep the evidence concrete.")
    client = TestClient(app)
    created = client.post("/games", json={"player_id": "test-player"})
    assert created.status_code == 200
    game_id = created.json()["id"]
    assert created.json()["stage"] == "name_outcome"
    for index in range(7):
        response = client.post(f"/games/{game_id}/turn", json={"response": f"evidence {index}"})
        assert response.status_code == 200
    final = client.get(f"/games/{game_id}").json()
    assert final["status"] == "complete"
    assert len(final["turns"]) == 7
    rejected = client.post(f"/games/{game_id}/turn", json={"response": "late"})
    assert rejected.status_code == 409


def test_game_can_be_assigned_a_specific_model(monkeypatch, tmp_path):
    from shared_game import api
    monkeypatch.setattr(api, "store", api.GameStore(tmp_path / "game.sqlite3"))
    monkeypatch.setattr(api.llm, "guide", lambda **kwargs: "Keep the evidence concrete.")
    client = TestClient(app)
    created = client.post("/games", json={"player_id": "pro-player", "model": "deepseek/deepseek-v4-pro"})
    assert created.status_code == 200
    assert created.json()["model"] == "deepseek/deepseek-v4-pro"
    assert created.json()["turns"][0]["model"] == "deepseek/deepseek-v4-pro"
    turn = client.post(f"/games/{created.json()['id']}/turn", json={"response": "ship the pilot"})
    assert turn.status_code == 200
    assert turn.json()["game"]["turns"][0]["model"] == "deepseek/deepseek-v4-pro"


def test_unknown_model_is_rejected(monkeypatch, tmp_path):
    from shared_game import api
    monkeypatch.setattr(api, "store", api.GameStore(tmp_path / "game.sqlite3"))
    client = TestClient(app)
    response = client.post("/games", json={"player_id": "bad", "model": "not/a-real-model"})
    assert response.status_code == 422


def test_witness_detection_and_ordered_acknowledgement(tmp_path):
    tweet = {
        "id": "2079261354448302166",
        "conversation_id": "2079260209118122399",
        "author": "leo_guinan",
        "created_at": "2026-07-20T17:45:12Z",
        "text": "Useful leading indicators: Sales closed. I have my scoreboard. @marvin_panics is my witness.",
    }
    assert detect_witness_request(tweet)
    commitment = build_commitment(tweet)
    assert commitment.follow_up_at == "2026-07-27T17:45:12+00:00"

    events = []
    class FakeScheduler:
        def schedule(self, *, kind, run_at, payload):
            events.append(("schedule", kind, run_at, payload))
            return ScheduledJob(id="job-123", kind=kind, run_at=run_at, payload=payload)
    class FakeWriter:
        def reply(self, tweet_id, text):
            assert events[0][0] == "schedule"
            events.append(("reply", tweet_id, text))
            return {"id": "ack-456"}

    result = WitnessFlow(WitnessStore(tmp_path / "witness.sqlite3"), FakeScheduler(), FakeWriter()).record(tweet)
    assert result.status == "acknowledged"
    assert result.schedule_id == "job-123"
    assert result.acknowledgement_tweet_id == "ack-456"
    assert [event[0] for event in events] == ["schedule", "reply"]


def test_witness_dry_run_ack_can_be_upgraded_once(tmp_path):
    tweet = {
        "id": "2", "conversation_id": "2", "text": "I will make one sale. @marvin_panics is my witness.",
        "created_at": "2026-07-20T00:00:00Z",
    }
    store = WitnessStore(tmp_path / "witness.sqlite3")
    existing = build_commitment(tweet)
    existing.schedule_id = "job-existing"
    existing.acknowledgement_tweet_id = "dry-run-2"
    existing.status = "acknowledged"
    store.save(existing)
    replies = []
    class Scheduler:
        def schedule(self, **kwargs):
            raise AssertionError("must not schedule a duplicate job")
    class Writer:
        def reply(self, tweet_id, text):
            replies.append((tweet_id, text))
            return {"id": "live-2"}
    result = WitnessFlow(store, Scheduler(), Writer()).record(tweet)
    assert result.acknowledgement_tweet_id == "live-2"
    assert len(replies) == 1


def test_witness_request_requires_explicit_language():
    assert not detect_witness_request({"id": "1", "text": "@marvin_panics nice thread"})


def test_email_sequence_is_public_safe():
    path = Path(__file__).parents[1] / "content" / "email_sequence.json"
    data = json.loads(path.read_text())
    assert len(data["emails"]) == 9
    assert data["emails"][0]["id"] == "welcome"
    assert data["emails"][-1]["id"] == "follow-up"
