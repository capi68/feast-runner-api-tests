"""Service layer for Address API interactions"""

import requests
from tests.base.base_service import BaseService
from tests.utils.endpoints import AddressEndpoints

class AddressService(BaseService):
    """HTTP service for Address CRUD and authentication."""

    def list(self, customer_id: int = None) -> requests.Response:
        """GET /addresses - list all address, optionally filtered by customer_id"""
        if customer_id is None:
            return self.get(AddressEndpoints.BASE)

        return self.get(AddressEndpoints.BASE, params={"customer_id": customer_id})

    def create(self, payload: dict) -> requests.Response:
        """POST /addresses - register a new address"""
        return self.post(AddressEndpoints.BASE, data=payload)

    def get_by_id(self, address_id: int) -> requests.Response:
        """GET /addressses/<id> - get address by ID."""
        endpoint = AddressEndpoints.DETAIL.format(address_id=address_id)
        return self.get(endpoint)

    def update(self, address_id: int, payload: dict) -> requests.Response:
        """PUT /addresses/<id> - update address fields."""
        endpoint = AddressEndpoints.DETAIL.format(address_id=address_id)
        return self.put(endpoint, payload)

    def delete_address(self, address_id: int) -> requests.Response:
        """DELETE /addresses/<id> - permanently delete address."""
        endpoint = AddressEndpoints.DETAIL.format(address_id=address_id)
        return self.delete(endpoint)