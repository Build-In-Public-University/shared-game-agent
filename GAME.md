# The Seven-Day Shared Game

Build In Public University game contract

## The premise

You have one meaningful outcome. Your stated intention is a hypothesis. Your behavior and receipts are the measurement.

The game gives you seven days to compare the two without turning the process into a motivational performance.

## How to play

Create a game and answer one prompt at a time:

1. Name one outcome that matters within 30 days.
2. Define the evidence that would prove movement.
3. Compare the goal with your recent behavior.
4. Choose one small seven-day behavioral experiment.
5. Choose a witness or public receipt.
6. Run the experiment and record what happened.
7. Review reality and choose the next move.

## Rules

- One outcome. Not a life redesign.
- Evidence outranks explanation.
- The experiment must be small enough to run this week.
- A miss is a result, not a moral verdict.
- AI may identify contradictions; it cannot manufacture evidence.
- Do not claim success without a receipt.
- Keep private player data private.

## Start locally

```bash
python -m venv .venv
. .venv/bin/activate
pip install -e .

python -m shared_game.cli --db game.sqlite3 init --player your-name
```

The CLI returns a `game_id`. Submit a turn with:

```bash
python -m shared_game.cli --db game.sqlite3 turn <game-id> \
  --response "Ship the first paid pilot by Friday."
```

## Play through the API

```bash
uvicorn shared_game.api:app --host 127.0.0.1 --port 8788

curl -X POST http://127.0.0.1:8788/games \
  -H 'content-type: application/json' \
  -d '{"player_id":"demo", "model":"deepseek/deepseek-v4-flash"}'
```

The game can be played with either:

- `deepseek/deepseek-v4-flash`
- `deepseek/deepseek-v4-pro`

The assigned model is recorded with the game and each turn. That makes model comparison possible without pretending different players used the same guide.

## What counts as finishing?

A game is complete when all seven prompts have a response. Completion is not success. The final receipt should state:

- what the player expected
- what actually happened
- what evidence was created
- what contradicted the original story
- what the player will do next

## Build In Public University receipt

A useful public report contains:

```text
Outcome:
Evidence before:
Experiment:
Witness or receipt:
Result:
Miss or contradiction:
Next move:
Model used:
```

Redact names, private conversations, contact details, credentials, and anything the participant did not consent to publish. The point is inspectable learning, not accidental exposure.
