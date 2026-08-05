"""Payload builders for Menu Items API requests."""

from  tests.models.menu_items_model import MenuItem

def menu_item_create_payload(item: MenuItem, **overrides) -> dict:
    """Build a valid payload for POST /menu-items."""
    payload = {
        "menu_id": item.menu_id,
        "name": item.name,
        "description": item.description,
        "price": item.price,
        "category": item.category,
        "preparation_time_minutes": item.preparation_time_minutes,
    }
    payload.update(overrides)

    return  payload

def menu_item_update_payload(**kwargs) -> dict:
    """Build a payload for PUT /menu-items/<id> with only provided fields."""
    return {k: v for k, v in kwargs.items() if v is not None}

