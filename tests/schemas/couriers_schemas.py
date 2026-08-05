"""JSON Schemas for Couriers API response validations."""

COURIERS_RESPONSE_SCHEMA = {
    "type": "object",
    "required": [
        "id", "first_name", "last_name", "email", "phone", "vehicle_type",
        "license_plate", "is_available", "is_active", "created_at", "updated_at"
    ],
    "properties": {
        "id": {"type": "integer"},
        "first_name": {"type": "string"},
        "last_name": {"type": "string"},
        "email": {"type": "string", "format": "email"},
        "phone": {"type": "string"},
        "vehicle_type": {"type": "string", "enum": ["bicycle", "motorcycle", "car", "scooter"]},
        "is_available": {"type": "boolean"},
        "is_active": {"type": "boolean"},
        "license_plate": {"type": "string"},
        "created_at": {"type": "string", "format": "date-time"},
        "updated_at": {"type": "string", "format": "date-time"},
    },
    "additionalProperties": False
}

COURIERS_LIST_SCHEMA = {
    "type": "array",
    "items": COURIERS_RESPONSE_SCHEMA
}

LOGIN_COURIERS_SCHEMA = {
    "type": "object",
    "required": ["message", "token", "courier_id"],
    "properties": {
        "message": {"type": "string"},
        "token": {"type": "string"},
        "courier_id":  {"type": "integer"}
    },
    "additionalProperties": False
}