"""JSON Schemas for ratings API response validation."""

RATING_RESPONSE_SCHEMA = {
    "type": "object",
    "required": [
        "id", "order_id", "food_score",
        "delivery_score", "comment", "created_at"
    ],
    "properties": {
        "id": {"type": "integer"},
        "order_id": {"type": "integer"},
        "food_score": {"type": "number", "minimum": 1, "maximum": 5},
        "delivery_score": {"type": "number", "minimum": 1, "maximum": 5},
        "comment": {"type": "string", "maxLength": 500},
        "created_at": {"type": "string", "format": "date-time"},
    },
    "additionalProperties": False
}

RATING_LIST_SCHEMA = {
    "type": "array",
    "items": RATING_RESPONSE_SCHEMA
}