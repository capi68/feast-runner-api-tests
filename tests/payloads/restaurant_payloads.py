"""Payload builders for Restaurant API requests."""

import uuid
from tests.models.restaurant_model import Restaurant


def restaurant_create_payload(restaurant: Restaurant = None, **overrides) -> dict:
    """Build a valid payload for POST /restaurants."""
    if restaurant is None:
        restaurant = Restaurant()
    uid = uuid.uuid4().hex[:8]
    payload = {
        "name": restaurant.name,
        "cuisine_type": restaurant.cuisine_type,
        "phone": restaurant.phone,
        "email": restaurant.email or f"restaurant_{uid}@feastrunner.com",
        "password": restaurant.password,
        "opening_hours": restaurant.opening_hours,
        "min_order_amount": restaurant.min_order_amount,
        "delivery_radius_km": restaurant.delivery_radius_km,
    }
    payload.update(overrides)

    return payload


def restaurant_update_payload(**kwargs) -> dict:
    """Build a payload for PUT /restaurants/<id> with only the provided fields."""
    return {k: v for k, v in kwargs.items() if v is not None}


def restaurant_login_payload(email: str, password: str) -> dict:
    """Build a payload for POST /restaurants/login."""
    return {"email": email, "password": password}
