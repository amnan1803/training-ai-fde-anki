# CLAUDE.md

## Setup

```bash
pip install -e .
```

Requires Python 3.12+. All dependencies (FastAPI, uvicorn, anthropic, pytest) are declared in `pyproject.toml` and installed by the command above.

## Run

```bash
uvicorn app.main:app --reload
```

On first run the app creates `anki.db` and seeds two sample decks automatically. The web UI is at `http://127.0.0.1:8000` and the interactive API docs are at `http://127.0.0.1:8000/docs`.

## Test

```bash
pytest
```

Tests live in `tests/`. Each test gets a fresh throwaway SQLite database via the `client` fixture in `tests/conftest.py` — no setup needed and no `anki.db` is touched.

The suite runs without an `ANTHROPIC_API_KEY`. The one AI-dependent test monkeypatches the environment.

## Optional: AI endpoint

```bash
cp .env.example .env
# edit .env and set ANTHROPIC_API_KEY=your-key
```

Without a key the app runs fine. Only `POST /decks/{id}/generate` is affected — it returns a 503 instead of cards.

## Architecture

```
app/main.py       Entry point. Runs DB init and seeding on startup, registers routes.
app/routes.py     All HTTP endpoints. Receives requests, validates input, delegates, returns JSON.
app/services.py   Business logic only — scheduling, due filtering, stats calculation.
app/db.py         All SQLite access. The only file that runs SQL.
app/models.py     Pydantic shapes for request bodies and response payloads.
app/ai.py         Claude API call for card generation. Self-contained.
app/seed.py       Creates sample decks/cards/reviews on first run.
data/schema.sql   Three tables: decks, cards, reviews.
```

Request flow: `routes.py` → `services.py` (if logic needed) → `db.py` → back up to `routes.py` → JSON response.

## Three conventions to get right

**1. All SQL goes in `db.py` only.**
`routes.py` and `services.py` never query the database directly — they call functions in `db.py`. If you are writing a SQL query anywhere other than `db.py`, it belongs there instead.

**2. `routes.py` holds no logic.**
Route functions check that a resource exists (raising 404 if not), then immediately call `db` or `services`. Any filtering, calculation, or decision-making belongs in `services.py`, not in the route function itself.

**3. Always guard with a resource check before acting.**
Every route that takes an ID checks `if db.get_deck(deck_id) is None: raise HTTPException(404)` before doing anything else. Add the same guard when writing new endpoints — do not assume the ID is valid.

## Known issues (flagged for verification)

- `POST /decks/{id}/generates` in `routes.py` has a trailing `s` in the path that does not match the documented `/generate`. Verify whether this has been fixed on your branch.
- `services.is_due` and `services.deck_stats` contain bugs that the Week 1 exercise asks you to find and fix — do not treat the current behaviour as correct.
