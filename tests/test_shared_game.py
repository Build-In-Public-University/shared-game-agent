import json
from pathlib import Path

from fastapi.testclient import TestClient

from shared_game import STAGES
from shared_game.api import app
from shared_game.model_registry import available_models


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


def test_email_sequence_is_public_safe():
    path = Path(__file__).parents[1] / "content" / "email_sequence.json"
    data = json.loads(path.read_text())
    assert len(data["emails"]) == 9
    assert data["emails"][0]["id"] == "welcome"
    assert data["emails"][-1]["id"] == "follow-up"
