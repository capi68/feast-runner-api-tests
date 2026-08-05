"""Payload builders for Order API requests."""

from tests.models.order_model import Order
from tests.models.order_item_model import OrderItem
from tests.payloads.order_item_payload import order_item_create_payload


def order_create_payload(order: Order,  customer_id: int = None, restaurant_id: int = None, address_id: int = None, **overrides) -> dict:
    """Build a valid payload for POST /orders."""

    payload = {
        "customer_id": customer_id or order.customer_id,
        "restaurant_id": restaurant_id or order.restaurant_id,
        "address_id": address_id or order.address_id,
        "notes": order.notes,
        "items": [
            order_item_create_payload(item)
            for item in order.items
        ]
    }
    payload.update(overrides)

    return  payload

def order_update_payload(**kwargs) -> dict:
    """Build a payload for PUT /orders/<id> with only provided fields."""
    return {k: v for k, v in kwargs.items() if v is not None}

