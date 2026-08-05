"""JSON Schema for Order API response validation."""

ORDER_RESPONSE_SCHEMA = {
    "type": "object",
    "required": [
        "id", "customer_id", "restaurant_id", "address_id", "items", "notes", "estimated_delivery_minutes", "total_amount", "status", "created_at", "updated_at"
    ],
    "properties": {
        "id": {"type": "integer"},
        "customer_id": {"type": "integer"},
        "restaurant_id": {"type": "integer"},
        "address_id": {"type": "integer"},
        "items": {
            "type": "array",
            "minItems": 1,
            "items": {
                "type": "object",
                "required": ["id", "order_id", "menu_item_id", "quantity", "unit_price", "special_instructions", "created_at"],
                "properties": {
                    "id": {"type": "integer"},
                    "order_id": {"type": "integer"},
                    "menu_item_id": {"type": "integer"},
                    "quantity": {"type": "integer", "minimum": 1, "maximum": 99},
                    "unit_price": {"type": "number"},
                    "special_instructions": {"type": "string"},
                    "created_at": {"type": "string", "format": "date-time"},
                },
                "additionalProperties": False
            }
        },
        "notes": {"type": "string"},
        "min_order_amount": {"type": "number"},
        "estimated_delivery_minutes": {"type": "number", "minimum": 20},
        "total_amount": {"type": "number"},
        "status": {"type": "string", "enum": ["placed", "confirmed", "cancelled", "preparing", "ready", "picked_up", "delivered"]},
        "created_at": {"type": "string", "format": "date-time"},
        "updated_at": {"type": "string", "format": "date-time"},
    },
    "additionalProperties": False
}

ORDER_GET_SCHEMA = {
    "type": "object",
    "required": [
        "id", "customer_id", "restaurant_id", "address_id", "notes", "estimated_delivery_minutes", "total_amount", "status", "created_at", "updated_at"
    ],
    "properties": {
        "id": {"type": "integer"},
        "customer_id": {"type": "integer"},
        "restaurant_id": {"type": "integer"},
        "address_id": {"type": "integer"},
        "notes": {"type": "string"},
        "min_order_amount": {"type": "number"},
        "estimated_delivery_minutes": {"type": "number", "minimum": 20},
        "total_amount": {"type": "number"},
        "status": {"type": "string", "enum": ["placed", "confirmed", "cancelled", "preparing", "ready", "picked_up", "delivered"]},
        "created_at": {"type": "string", "format": "date-time"},
        "updated_at": {"type": "string", "format": "date-time"},
    },
    "additionalProperties": False
}

ORDER_LIST_SCHEMA = {
    "type": "array",
    "items": ORDER_GET_SCHEMA
}

ORDER_GET_BY_ID_SCHEMA = {
    "type": "object",
    "items": ORDER_RESPONSE_SCHEMA
}