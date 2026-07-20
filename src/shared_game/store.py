from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from .models import Game

class GameStore:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init()

    def _connect(self):
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init(self):
        with self._connect() as conn:
            conn.execute("CREATE TABLE IF NOT EXISTS games (id TEXT PRIMARY KEY, player_id TEXT NOT NULL, state_json TEXT NOT NULL, updated_at TEXT NOT NULL)")

    def save(self, game: Game) -> Game:
        with self._connect() as conn:
            conn.execute("INSERT OR REPLACE INTO games (id, player_id, state_json, updated_at) VALUES (?, ?, ?, ?)", (game.id, game.player_id, json.dumps(game.to_dict()), game.updated_at))
        return game

    def get(self, game_id: str) -> Game:
        with self._connect() as conn:
            row = conn.execute("SELECT state_json FROM games WHERE id = ?", (game_id,)).fetchone()
        if row is None:
            raise KeyError(game_id)
        return Game.from_dict(json.loads(row["state_json"]))
