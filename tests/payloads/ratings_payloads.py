"""Payload builders for Rating API requests."""

from tests.models.ratings_model import Rating

def rating_create_payload(rating: Rating = None, **overrides) -> dict:
    """Build a valid payload for POST /ratings."""

    if rating is None:
        rating = Rating()

    payload = {
        "order_id": rating.order_id,
        "food_score": rating.food_score,
        "delivery_score": rating.delivery_score,
        "comment": rating.comment,
    }
    payload.update(overrides)

    return payload
