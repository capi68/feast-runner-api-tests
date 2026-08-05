"""Payloads builders for Address API requests."""

from tests.models.address_model import Address

def address_create_payload(address: Address, customer_id: int, **overrides) -> dict:
    """Build a valid payload for POST /Addresses."""

    if address is None:
        address = Address()

    payload = {
        "customer_id": customer_id or address.customer_id,
        "label": address.label,
        "street": address.street,
        "city": address.city,
        "state": address.state,
        "zip_code": address.zip_code,
        "latitude": address.latitude,
        "longitude": address.longitude,
        "is_default": address.is_default
    }
    payload.update(overrides)

    return payload

def address_update_payload(**kwargs) -> dict:
    """Build a payload for PUT /addresses/<id> with only provided fields."""
    return {k: v for k, v in kwargs.items() if v is not None}
