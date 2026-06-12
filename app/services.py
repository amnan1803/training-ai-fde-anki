"""Business logic: spaced-repetition scheduling, due checks, and deck stats.

This is where a request's logic lives, between the HTTP layer (routes.py) and the
data layer (db.py).
"""

from __future__ import annotations

from datetime import date, timedelta

from . import db

EASE_FLOOR = 1.3


# Calculates when a card should appear next and how easy it should feel, based on your rating.
def schedule_next(rating: str, interval: int, ease: float) -> tuple[int, float]:
    if rating == "again":
        return 0, max(EASE_FLOOR, ease - 0.20)
    if rating == "hard":
        return max(1, round(interval * 1.2)), max(EASE_FLOOR, ease - 0.15)
    if rating == "good":
        return max(1, round(interval * ease)), ease
    if rating == "easy":
        return max(1, round(interval * ease * 1.3)), ease + 0.15
    raise ValueError(f"unknown rating: {rating}")


# Checks whether a card should be shown today — true if the due date is today or already passed.
def is_due(card: dict, today: str | None = None) -> bool:
    today = today or date.today().isoformat()
    # "<=" means due today or overdue; ">" would be future cards only
    return card["next_due"] <= today


# Saves your review rating for a card, then moves its next due date forward based on how well you did.
def review_card(card_id: int, rating: str) -> dict:
    card = db.get_card(card_id)
    correct = 1 if rating in ("good", "easy") else 0
    db.insert_review(card_id, rating, correct)

    interval, ease = schedule_next(rating, card["interval_days"], card["ease"])
    next_due = (date.today() + timedelta(days=interval)).isoformat()
    return db.update_card_schedule(card_id, ease, interval, next_due)


# Filters all cards in a deck and returns only the ones you need to study today.
def due_cards(deck_id: int) -> list[dict]:
    cards = db.cards_for_deck(deck_id)
    return [c for c in cards if is_due(c)]


# Builds a summary for a deck: how many cards, how many are due, total reviews, and what percentage you got right.
def deck_stats(deck_id: int) -> dict:
    cards = db.cards_for_deck(deck_id)
    reviews = db.reviews_for_deck(deck_id)
    correct = sum(r["correct"] for r in reviews)
    # Guard against ZeroDivisionError when a deck has no reviews yet
    retention = correct / len(reviews) if reviews else 0.0
    due = [c for c in cards if is_due(c)]
    return {
        "total_cards": len(cards),
        "due_count": len(due),
        "reviews_done": len(reviews),
        "retention": round(retention, 2),
    }
