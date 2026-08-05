"""JSON Schema for customer API response validation."""

CUSTOMER_RESPONSE_SCHEMA = {
    "type": "object",
    "required": [
        "id", "first_name", "last_name", "email", "phone", "is_active", "created_at", "updated_at"
    ],
    "properties": {
        "id": {"type": "integer"},
        "first_name": {"type": "string"},
        "last_name": {"type": "string"},
        "email": {"type": "string", "format": "email"},
        "phone": {"type": "string"},
        "is_active": {"type": "boolean"},
        "created_at": {"type": "string", "format": "date-time"},
        "updated_at": {"type": "string", "format": "date-time"},
    },
    "additionalProperties": False,
}

CUSTOMER_LIST_SCHEMA = {
    "type": "array",
    "items": CUSTOMER_RESPONSE_SCHEMA
}

CUSTOMER_LOGIN_SCHEMA = {
    "type": "object",
    "required": ["message", "token", "customer_id"],
    "properties": {
        "message": {"type": "string"},
        "token": {"type": "string"},
        "customer_id": {"type": "integer"},
    },
    "additionalProperties": False,
}