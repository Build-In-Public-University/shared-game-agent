from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from .llm import LLMClient
from .models import Game
from .store import GameStore
from .model_registry import available_models, default_model

ROOT = Path(__file__).resolve().parents[2]
DB_PATH = os.getenv("SHARED_GAME_DB", str(ROOT / "shared_game.sqlite3"))
store = GameStore(DB_PATH)
llm = LLMClient()
app = FastAPI(title="Shared Game Agent", version="0.1.0")

class CreateGameRequest(BaseModel):
    player_id: str = Field(min_length=1, max_length=120)
    model: str | None = None

class TurnRequest(BaseModel):
    response: str = Field(min_length=1, max_length=10000)

@app.get("/health")
def health() -> dict[str, Any]:
    return {"status": "ok", "service": "shared-game-agent", "llm_mode": "openrouter" if llm.live else "stub"}

@app.get("/email-sequence")
def email_sequence() -> dict[str, Any]:
    return json.loads((ROOT / "content" / "email_sequence.json").read_text())

@app.get("/models")
def models() -> dict[str, Any]:
    return {"default_model": default_model(), "models": available_models()}

@app.post("/games")
def create_game(req: CreateGameRequest) -> dict[str, Any]:
    try:
        game = Game.new(req.player_id, req.model)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    store.save(game)
    return game.to_dict()

@app.get("/games/{game_id}")
def get_game(game_id: str) -> dict[str, Any]:
    try:
        return store.get(game_id).to_dict()
    except KeyError:
        raise HTTPException(status_code=404, detail="game not found")

@app.post("/games/{game_id}/turn")
def submit_turn(game_id: str, req: TurnRequest) -> dict[str, Any]:
    try:
        game = store.get(game_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="game not found")
    if game.status != "active":
        raise HTTPException(status_code=409, detail="game is already complete")
    history = [turn.__dict__ for turn in game.turns if turn.response]
    try:
        reply = llm.guide(stage=game.stage, prompt=game.current_prompt, response=req.response, history=history, model=game.model)
        game.apply_turn(req.response, reply)
        store.save(game)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    return {"game": game.to_dict(), "guide_reply": reply, "llm_mode": "openrouter" if llm.live else "stub"}
