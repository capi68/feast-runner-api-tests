"""Payloads builders for Courier API requests."""

import uuid
from tests.models.couriers_model import Courier

def courier_create_payload(courier: Courier = None, **overrides) -> dict:
    """Build a valid payload for POST /couriers."""

    if courier is None:
        courier = Courier()
    uid = uuid.uuid4().hex[:8]
    payload =  {
        "first_name": courier.first_name,
        "last_name": courier.last_name,
        "email": courier.email or f"carlos_{uid}@email.com",
        "phone": courier.phone,
        "password": courier.password,
        "vehicle_type": courier.vehicle_type,
        "license_plate": courier.license_plate,
    }
    payload.update(overrides)

    return payload

def courier_update_payload(**kwargs) -> dict:
    """Build a payload for PUT /couriers/<id> - with only provided fields."""
    return {k: v for k, v in kwargs.items() if v is not None}

def courier_login_payload(email: str, password: str) -> dict:
    """Build a payload for POST /couriers/login."""
    return  { "email": email, "password": password}