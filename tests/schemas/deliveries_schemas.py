"""JSON Schemas for Deliveries API response Validation."""

DELIVERIES_RESPONSE_SCHEMA = {
    "type": "object",
    "required": [
        "id", "order_id", "courier_id", "status", "distance_km", "picked_up_at", "delivered_at","created_at", "updated_at"
    ],
    "properties": {
        "id": {"type": "integer"},
        "order_id": {"type": "integer"},
        "courier_id": {"type": "integer"},
        "distance_km": {"type": "number"},
        "picked_up_at": {"type": ["string", "null"]},
        "delivered_at": {"type": ["string", "null"]},
        "status": {"type": "string", "enum": ["assigned", "picked_up", "in_transit", "delivered", "failed"]},
        "created_at": {"type": "string", "format": "date-time"},
        "updated_at": {"type": "string", "format": "date-time"},
    },
    "additionalProperties": False
}

DELIVERIES_LIST_SCHEMA = {
    "type": "array",
    "items": DELIVERIES_RESPONSE_SCHEMA
}