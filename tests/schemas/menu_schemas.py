"""JSON Schemas for Menu API response validation."""

MENU_RESPONSE_SCHEMA = {
    "type": "object",
    "required": ["id", "restaurant_id", "name", "status", "created_at", "updated_at"],
    "properties": {
        "id": {"type": "integer"},
        "restaurant_id": {"type": "integer"},
        "name": {"type": "string"},
        "description": {"type": ["string", "null"]},
        "status": {"type": "string", "enum": ["draft", "active", "archived"]},
        "created_at": {"type": "string", "format": "date-time"},
        "updated_at": {"type": "string", "format": "date-time"},
    },
    "additionalProperties": False,
}

MENU_LIST_SCHEMA = {
    "type": "array",
    "items": MENU_RESPONSE_SCHEMA,
}
