"""JSON Schemas for Address API response validation."""

ADDRESS_RESPONSE_SCHEMA = {
    "type": "object",
    "required": [
        "id", "customer_id", "label", "street", "city", "state", "zip_code"
    ],

    "properties": {
        "id": {"type": "integer"},
        "customer_id": {"type": "integer"},
        "label": {"type": "string"},
        "street": {"type": "string"},
        "city": {"type": "string"},
        "state": {"type": "string"},
        "zip_code": {"type": "string"},
        "latitude": {"type": "number", "minimum": -90, "maximum": 90},
        "longitude": {"type": "number", "minimum": -180, "maximum": 180},
        "is_default": {"type": "boolean"},
        "created_at": {"type": "string", "format": "date-time"},
        "updated_at": {"type": "string", "format": "date-time"},
    },
    "additionalProperties": False
}

ADDRESS_LIST_SCHEMA = {
    "type": "array",
    "items": ADDRESS_RESPONSE_SCHEMA,
}