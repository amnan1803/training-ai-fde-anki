"""HTTP endpoints — where requests enter the app.

Each route delegates business logic to services.py and data access to db.py, then
serializes the result through the Pydantic models in models.py.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from . import ai, db, services
from .models import (
    Card,
    CardCreate,
    CardDraft,
    Deck,
    DeckCreate,
    GenerateRequest,
    ReviewCreate,
    Stats,
)

router = APIRouter()


# Returns the full list of all decks the user has created.
@router.get("/decks", response_model=list[Deck])
def list_decks() -> list[dict]:
    return db.all_decks()


# Creates a new deck with the name you provide and returns it.
@router.post("/decks", response_model=Deck)
def create_deck(payload: DeckCreate) -> dict:
    return db.insert_deck(payload.name)


# Returns one deck by its ID, including all its cards. Returns 404 if the deck doesn't exist.
@router.get("/decks/{deck_id}", response_model=Deck)
def get_deck(deck_id: int) -> dict:
    deck = db.get_deck(deck_id)
    if deck is None:
        raise HTTPException(status_code=404, detail="Deck not found")
    deck["cards"] = db.cards_for_deck(deck_id)
    return deck


# Adds a new flashcard (front + back) to a deck. Returns 404 if the deck doesn't exist.
@router.post("/decks/{deck_id}/cards", response_model=Card)
def add_card(deck_id: int, payload: CardCreate) -> dict:
    if db.get_deck(deck_id) is None:
        raise HTTPException(status_code=404, detail="Deck not found")
    return db.insert_card(deck_id, payload.front, payload.back)


# Returns only the cards that are due for review today or overdue. Returns 404 if the deck doesn't exist.
@router.get("/decks/{deck_id}/due", response_model=list[Card])
def get_due(deck_id: int) -> list[dict]:
    if db.get_deck(deck_id) is None:
        raise HTTPException(status_code=404, detail="Deck not found")
    return services.due_cards(deck_id)


# Records how well you remembered a card (again/hard/good/easy) and reschedules it. Returns 404 if the card doesn't exist.
@router.post("/cards/{card_id}/review", response_model=Card)
def review(card_id: int, payload: ReviewCreate) -> dict:
    if db.get_card(card_id) is None:
        raise HTTPException(status_code=404, detail="Card not found")
    return services.review_card(card_id, payload.rating.value)


# Returns study stats for a deck: total cards, how many are due, reviews done, and retention rate. Returns 404 if the deck doesn't exist.
@router.get("/decks/{deck_id}/stats", response_model=Stats)
def stats(deck_id: int) -> dict:
    if db.get_deck(deck_id) is None:
        raise HTTPException(status_code=404, detail="Deck not found")
    return services.deck_stats(deck_id)


# Uses Claude AI to generate flashcards about a topic and saves them to the deck. Returns 503 if no API key is set.
@router.post("/decks/{deck_id}/generate", response_model=list[CardDraft])
def generate(deck_id: int, payload: GenerateRequest) -> list[dict]:
    if db.get_deck(deck_id) is None:
        raise HTTPException(status_code=404, detail="Deck not found")
    try:
        drafts = ai.generate_cards(payload.topic, payload.count)
    except ai.AINotConfigured:
        raise HTTPException(
            status_code=503, detail="AI not configured — set ANTHROPIC_API_KEY"
        )
    return [db.insert_card(deck_id, d["front"], d["back"]) for d in drafts]
