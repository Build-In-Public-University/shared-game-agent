from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any
import uuid

from .model_registry import default_model, validate_model

STAGES = [
    ("name_outcome", "Name one outcome that matters within 30 days."),
    ("define_evidence", "Define the evidence that would prove movement."),
    ("expose_contradiction", "Compare the goal with recent behavior."),
    ("choose_experiment", "Choose one seven-day behavioral experiment."),
    ("add_witness", "Choose a witness or public receipt."),
    ("run_record", "Run the experiment and record the result."),
    ("review_choose", "Review reality and choose the next move."),
]


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class Turn:
    stage: str
    prompt: str
    model: str = ""
    response: str = ""
    guide_reply: str = ""
    created_at: str = field(default_factory=now)


@dataclass
class Game:
    id: str
    player_id: str
    model: str = field(default_factory=default_model)
    status: str = "active"
    stage_index: int = 0
    turns: list[Turn] = field(default_factory=list)
    created_at: str = field(default_factory=now)
    updated_at: str = field(default_factory=now)

    @classmethod
    def new(cls, player_id: str, model: str | None = None) -> "Game":
        assigned_model = validate_model(model or default_model())
        game = cls(id=str(uuid.uuid4()), player_id=player_id, model=assigned_model)
        game.turns.append(Turn(stage=STAGES[0][0], prompt=STAGES[0][1], model=assigned_model))
        return game

    @property
    def stage(self) -> str:
        return STAGES[self.stage_index][0]

    @property
    def current_prompt(self) -> str:
        return STAGES[self.stage_index][1]

    def apply_turn(self, response: str, guide_reply: str) -> None:
        if self.status != "active":
            raise ValueError("game is already complete")
        if not response.strip():
            raise ValueError("response must not be blank")
        self.turns[-1].response = response.strip()
        self.turns[-1].guide_reply = guide_reply
        self.updated_at = now()
        if self.stage_index == len(STAGES) - 1:
            self.status = "complete"
            return
        self.stage_index += 1
        self.turns.append(Turn(stage=self.stage, prompt=self.current_prompt, model=self.model))

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["stage"] = self.stage
        data["current_prompt"] = self.current_prompt if self.status == "active" else None
        data["turns"] = [asdict(turn) for turn in self.turns]
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Game":
        assigned_model = data.get("model", default_model())
        validate_model(assigned_model)
        turns = [
            Turn(model=assigned_model, **{key: value for key, value in turn.items() if key != "model"})
            for turn in data.get("turns", [])
        ]
        return cls(
            id=data["id"], player_id=data["player_id"], model=assigned_model, status=data.get("status", "active"),
            stage_index=data.get("stage_index", 0), turns=turns,
            created_at=data.get("created_at", now()), updated_at=data.get("updated_at", now()),
        )
