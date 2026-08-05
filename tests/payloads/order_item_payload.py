"""Payload builder for Order Item."""

from tests.models.order_item_model import OrderItem

def order_item_create_payload(order_item: OrderItem, **overrides) -> dict:
    """Build a valid order item for Orders."""

    payload = {
        "menu_item_id": order_item.menu_item_id,
        "quantity": order_item.quantity,
        "special_instructions": order_item.special_instructions
    }
    payload.update(overrides)

    return payload