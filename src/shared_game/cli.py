from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from .llm import LLMClient
from .models import Game
from .store import GameStore


def main() -> None:
    parser = argparse.ArgumentParser(prog="shared-game")
    parser.add_argument("--db", default=os.getenv("SHARED_GAME_DB", "shared_game.sqlite3"))
    sub = parser.add_subparsers(dest="command", required=True)
    init = sub.add_parser("init"); init.add_argument("--player", required=True); init.add_argument("--model")
    turn = sub.add_parser("turn"); turn.add_argument("game_id"); turn.add_argument("--response", required=True)
    status = sub.add_parser("status"); status.add_argument("game_id")
    args = parser.parse_args()
    store = GameStore(args.db)
    if args.command == "init":
        game = Game.new(args.player, args.model); store.save(game); print(json.dumps(game.to_dict(), indent=2)); return
    game = store.get(args.game_id)
    if args.command == "status": print(json.dumps(game.to_dict(), indent=2)); return
    if args.command == "turn":
        if game.status != "active": raise SystemExit("game is already complete")
        history = [turn.__dict__ for turn in game.turns if turn.response]
        reply = LLMClient().guide(stage=game.stage, prompt=game.current_prompt, response=args.response, history=history, model=game.model)
        game.apply_turn(args.response, reply); store.save(game); print(json.dumps({"guide_reply": reply, "game": game.to_dict()}, indent=2))


if __name__ == "__main__":
    main()
