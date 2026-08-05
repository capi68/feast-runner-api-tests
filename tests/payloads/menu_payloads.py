"""Payload builders for Menu API requests."""

from tests.models.menu_model import Menu


def menu_create_payload(menu: Menu = None, restaurant_id: int = None, **overrides) -> dict:
    """Build a valid payload for POST /menus."""
    if menu is None:
        menu = Menu()
    payload = {
        "restaurant_id": restaurant_id or menu.restaurant_id,
        "name": menu.name,
        "description": menu.description,
    }
    payload.update(overrides)

    return payload

def menu_update_payload(**kwargs) -> dict:
    """Build a payload for PUT /menus/<id> with only the provided fields."""
    return {k: v for k, v in kwargs.items() if v is not None}
