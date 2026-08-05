"""Payload builder for Deliveries API requests."""

from tests.models.deliveries_models import Delivery

def delivery_create_payload(delivery: Delivery = None, order_id: int = None, courier_id: int = None, **overrides) -> dict:
    """Build a valid payload for POST /deliveries."""

    if delivery is None:
        delivery = Delivery()

    payload =  {
        "order_id": order_id or delivery.order_id,
        "courier_id": courier_id or delivery.courier_id,
        "distance_km": delivery.distance_km,
    }
    payload.update(overrides)

    return payload

def delivery_update_status_payload(status: str) -> dict:
    """Build a payload for PUT /deliveries/<id> with status provided field."""
    return {"status": status}
