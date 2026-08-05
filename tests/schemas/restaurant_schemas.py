"""JSON Schemas for Restaurant API response validation."""

RESTAURANT_RESPONSE_SCHEMA = {
    "type": "object",
    "required": [
        "id", "name", "cuisine_type", "phone", "email", "opening_hours",
        "min_order_amount", "delivery_radius_km", "status", "created_at", "updated_at"
    ],
    "properties": {
        "id": {"type": "integer"},
        "name": {"type": "string"},
        "cuisine_type": {
            "type": "string",
            "enum": ["italian", "mexican", "japanese", "chinese", "american", "indian", "thai", "mediterranean"],
        },
        "phone": {"type": "string"},
        "email": {"type": "string"},
        "opening_hours": {"type": "string"},
        "min_order_amount": {"type": "number", "minimum": 1.00, "maximum": 500.00},
        "delivery_radius_km": {"type": "number", "minimum": 1, "maximum": 50},
        "status": {"type": "string", "enum": ["active", "suspended", "closed"]},
        "created_at": {"type": "string", "format": "date-time"},
        "updated_at": {"type": "string", "format": "date-time"},
    },
    "additionalProperties": False,
}

RESTAURANT_LIST_SCHEMA = {
    "type": "array",
    "items": RESTAURANT_RESPONSE_SCHEMA,
}

LOGIN_RESPONSE_SCHEMA = {
    "type": "object",
    "required": ["message", "token", "restaurant_id"],
    "properties": {
        "message": {"type": "string"},
        "token": {"type": "string"},
        "restaurant_id": {"type": "integer"},
    },
    "additionalProperties": False,
}
