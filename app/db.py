"""SQLite connection and query helpers — the data boundary.

Every request that touches data flows through here. The database file location is
read from the ANKI_DB_PATH environment variable (default: ``anki.db`` in the repo
root), which lets the test suite point at a throwaway database.
"""

from __future__ import annotations

import os
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCHEMA_PATH = ROOT / "data" / "schema.sql"


# Returns the file path of the database. Tests can point this to a temporary file instead.
def db_path() -> str:
    return os.environ.get("ANKI_DB_PATH", str(ROOT / "anki.db"))


# Opens a connection to the database so we can run queries.
def connect() -> sqlite3.Connection:
    conn = sqlite3.connect(db_path())
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


# Creates the database tables on first run if they don't already exist.
def init_db() -> None:
    schema = SCHEMA_PATH.read_text()
    with connect() as conn:
        conn.executescript(schema)


# --- decks -----------------------------------------------------------------


# Saves a new deck with the given name and returns it.
def insert_deck(name: str) -> dict:
    with connect() as conn:
        cur = conn.execute("INSERT INTO decks (name) VALUES (?)", (name,))
        deck_id = cur.lastrowid
    return get_deck(deck_id)


# Fetches one deck by ID. Returns None if it doesn't exist.
def get_deck(deck_id: int) -> dict | None:
    with connect() as conn:
        row = conn.execute("SELECT * FROM decks WHERE id = ?", (deck_id,)).fetchone()
    return dict(row) if row else None


# Returns every deck in the database, sorted by creation order.
def all_decks() -> list[dict]:
    with connect() as conn:
        rows = conn.execute("SELECT * FROM decks ORDER BY id").fetchall()
    return [dict(r) for r in rows]


# --- cards -----------------------------------------------------------------


# Saves a new flashcard to a deck and returns it.
def insert_card(deck_id: int, front: str, back: str) -> dict:
    with connect() as conn:
        cur = conn.execute(
            "INSERT INTO cards (deck_id, front, back) VALUES (?, ?, ?)",
            (deck_id, front, back),
        )
        card_id = cur.lastrowid
    return get_card(card_id)


# Fetches one card by ID. Returns None if it doesn't exist.
def get_card(card_id: int) -> dict | None:
    with connect() as conn:
        row = conn.execute("SELECT * FROM cards WHERE id = ?", (card_id,)).fetchone()
    return dict(row) if row else None


# Returns all cards belonging to a specific deck, sorted by creation order.
def cards_for_deck(deck_id: int) -> list[dict]:
    with connect() as conn:
        rows = conn.execute(
            "SELECT * FROM cards WHERE deck_id = ? ORDER BY id", (deck_id,)
        ).fetchall()
    return [dict(r) for r in rows]


# Updates a card's scheduling info (ease, interval, next due date) after a review.
def update_card_schedule(
    card_id: int, ease: float, interval_days: int, next_due: str
) -> dict:
    with connect() as conn:
        conn.execute(
            "UPDATE cards SET ease = ?, interval_days = ?, next_due = ? WHERE id = ?",
            (ease, interval_days, next_due, card_id),
        )
    return get_card(card_id)


# --- reviews ---------------------------------------------------------------


# Saves a review record for a card, storing the rating and whether it was correct.
def insert_review(card_id: int, rating: str, correct: int) -> dict:
    with connect() as conn:
        cur = conn.execute(
            "INSERT INTO reviews (card_id, rating, correct) VALUES (?, ?, ?)",
            (card_id, rating, correct),
        )
        review_id = cur.lastrowid
        row = conn.execute(
            "SELECT * FROM reviews WHERE id = ?", (review_id,)
        ).fetchone()
    return dict(row)


# Returns all review records for every card in a deck, sorted by creation order.
def reviews_for_deck(deck_id: int) -> list[dict]:
    with connect() as conn:
        rows = conn.execute(
            """
            SELECT reviews.* FROM reviews
            JOIN cards ON cards.id = reviews.card_id
            WHERE cards.deck_id = ?
            ORDER BY reviews.id
            """,
            (deck_id,),
        ).fetchall()
    return [dict(r) for r in rows]
