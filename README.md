# The Seven-Day Shared Game

A Build In Public University game for turning one meaningful goal into observable evidence.

Play the game: see [GAME.md](GAME.md).


The implementation is documented in [docs/marvin-witness-flow.md](docs/marvin-witness-flow.md). It detects explicit witness commitments in Marvin mentions, schedules a seven-day follow-up, persists the job ID, and only then posts the acknowledgement.

The guide uses OpenRouter when `OPENROUTER_API_KEY` is configured and deterministic stub mode otherwise. Stub mode is for local development only; it is not evidence of live model behavior.


## Core loop

1. Name one outcome.
2. Define the evidence.
3. Compare the goal with recent behavior.
4. Choose one seven-day experiment.
5. Add a witness.
6. Run and record the result.
7. Review reality and choose the next move.

## Local install

```bash
python -m venv .venv
. .venv/bin/activate
pip install -e .
pytest -q
```

## Model experiments

The first roster compares:

- `deepseek/deepseek-v4-flash` — default fast candidate
- `deepseek/deepseek-v4-pro` — deeper candidate

Assign a model to each player/game so the model is part of the receipt:

```bash
shared-game init --player flash-player --model deepseek/deepseek-v4-flash
shared-game init --player pro-player --model deepseek/deepseek-v4-pro
```

The API exposes the roster at `GET /models` and accepts `model` on `POST /games`. Every game and turn stores the assigned model. This makes later comparison possible without pretending two players had the same model when they did not.

Do not judge the models from one clever reply. Compare matched game prompts using completion rate, player continuation rate, stage drop-off, human ratings, evidence quality, latency, and cost. The current build records model identity; outcome and usage ledgers are the next experiment layer.

## CLI

```bash
shared-game init --player leo
shared-game turn <game-id> --response "Ship the first paid pilot by Friday"
shared-game status <game-id>
```

## API

```bash
uvicorn shared_game.api:app --host 127.0.0.1 --port 8788
curl http://127.0.0.1:8788/health
```

Create a game:

```bash
curl -X POST http://127.0.0.1:8788/games \\
  -H 'content-type: application/json' \\
  -d '{"player_id":"demo"}'
```

Submit a turn:

```bash
curl -X POST http://127.0.0.1:8788/games/<id>/turn \\
  -H 'content-type: application/json' \\
  -d '{"response":"Launch the first paid pilot by Friday."}'
```

## Configuration

```bash
LLM_PROVIDER=openrouter
OPENROUTER_API_KEY=redacted
OPENROUTER_MODEL=deepseek/deepseek-v4-flash
OPENROUTER_HTTP_REFERER=https://your-domain.example
OPENROUTER_X_TITLE=Shared Game Agent
SHARED_GAME_DB=/var/lib/shared-game-agent/game.sqlite3
```

Never commit `.env`, API keys, player data, or real email addresses. The email sequence in `content/email_sequence.json` is public-safe copy; delivery is intentionally not wired to an outbound provider yet.

## Deployment boundary

This repository is VPS-ready but not deployed by this build. A later deployment should add a service user, a persistent database path, reverse proxy/TLS, secret injection, rate limiting, authentication, backups, and an outbound email provider. The OpenRouter key must remain a VPS secret, never a repository value.
