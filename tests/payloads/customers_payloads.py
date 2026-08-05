"""Payloads builders for customer API requests."""

import uuid
from tests.models.customer_model import Customer

def customer_create_payload(customer: Customer = None, **overrides) -> dict:
    """Build a valid Payload for POST /customers/."""

    if customer is None:
        customer = Customer()
    uid = uuid.uuid4().hex[:8]
    payload = {
        "first_name": customer.first_name,
        "last_name": customer.last_name,
        "email": customer.email or f"ana_{uid}@email.com",
        "phone": customer.phone,
        "password": customer.password,
    }
    payload.update(overrides)

    return payload

def customer_update_payload(**kwargs) -> dict:
    """Build a payload for PUT /customers/<id> - with only provided fields."""
    return {k: v for k, v in kwargs.items() if v is not None}

def customer_login_payload(email: str, password: str) -> dict:
    """Build a payload for POST /customers/login"""
    return {"email": email, "password": password}
