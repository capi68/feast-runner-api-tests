"""JSON Schemas for Order Items API response validations."""

MENU_ITEM_RESPONSE_SCHEMA = {
    "type": "object",
    "required": [
        "id", "menu_id", "name", "price", "category",
        "preparation_time_minutes", "description", "is_available", "created_at", "updated_at"
    ],
    "properties": {
        "id": {"type": "integer"},
        "menu_id": {"type": "integer"},
        "name": {"type": "string"},
        "price": {"type": "number", "minimum": 0.01, "maximum": 999.99},
        "category": {"type": "string", "enum": ["appetizer", "main", "side", "dessert", "beverage", "combo"]},
        "preparation_time_minutes": {"type": "integer"},
        "description": {"type": "string"},
        "is_available": {"type": "boolean"},
        "created_at": {"type": "string", "format": "date-time"},
        "updated_at": {"type": "string", "format": "date-time"},
    },
    "additionalProperties": False
}

MENU_ITEMS_LIST_SCHEMA = {
    "type": "array",
    "items": MENU_ITEM_RESPONSE_SCHEMA
}