"""Pydantic request/response models — the serialization boundary."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel


# The four possible ratings you can give a card after reviewing it.
class Rating(str, Enum):
    again = "again"
    hard = "hard"
    good = "good"
    easy = "easy"


# The data you send when creating a new deck — just a name.
class DeckCreate(BaseModel):
    name: str


# The data you send when adding a new card — the question side and the answer side.
class CardCreate(BaseModel):
    front: str
    back: str


# The full shape of a card returned by the API, including its scheduling info.
class Card(BaseModel):
    id: int
    deck_id: int
    front: str
    back: str
    ease: float
    interval_days: int
    next_due: str
    created_at: str


# The full shape of a deck returned by the API, optionally including its cards.
class Deck(BaseModel):
    id: int
    name: str
    created_at: str
    cards: list[Card] | None = None


# The data you send when submitting a review — just the rating.
class ReviewCreate(BaseModel):
    rating: Rating


# The shape of the stats response — totals and retention percentage for a deck.
class Stats(BaseModel):
    total_cards: int
    due_count: int
    reviews_done: int
    retention: float


# The data you send when asking Claude to generate cards — a topic and how many cards you want.
class GenerateRequest(BaseModel):
    topic: str
    count: int


# A draft card returned by the AI before it gets saved — just front and back, no ID yet.
class CardDraft(BaseModel):
    front: str
    back: str
