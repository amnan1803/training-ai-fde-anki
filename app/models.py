"""Pydantic request/response models — the serialization boundary."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel


# The four words you can use to rate a card after you review it.
class Rating(str, Enum):
    again = "again"
    hard = "hard"
    good = "good"
    easy = "easy"


# What you send when creating a new deck — just the name you want to give it.
class DeckCreate(BaseModel):
    name: str


# What you send when adding a new card — the question on the front and the answer on the back.
class CardCreate(BaseModel):
    front: str
    back: str


# The full details of a card that the API sends back to you, including its study schedule.
class Card(BaseModel):
    id: int
    deck_id: int
    front: str
    back: str
    ease: float
    interval_days: int
    next_due: str
    created_at: str


# The full details of a deck that the API sends back to you, with an optional list of its cards.
class Deck(BaseModel):
    id: int
    name: str
    created_at: str
    cards: list[Card] | None = None


# What you send when submitting a review — just the rating word (again, hard, good, or easy).
class ReviewCreate(BaseModel):
    rating: Rating


# The summary numbers the API sends back when you ask for a deck's stats.
class Stats(BaseModel):
    total_cards: int
    due_count: int
    reviews_done: int
    retention: float


# What you send when asking Claude to generate cards — the topic you want cards about and how many.
class GenerateRequest(BaseModel):
    topic: str
    count: int


# A card that Claude drafted but hasn't been saved yet — just the front and back text, no ID.
class CardDraft(BaseModel):
    front: str
    back: str
