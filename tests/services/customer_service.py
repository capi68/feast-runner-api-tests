""" Service layer for Menu API interactions."""

import requests
from tests.base.base_service import BaseService
from tests.utils.endpoints import CustomerEndpoints

class CustomerService(BaseService):
    """HTTP service for customer CRUD and state management."""

    def list(self):
        """GET /customers - list all active customers."""
        return self.get(CustomerEndpoints.BASE)

    def create(self, payload: dict) ->requests.Response:
        """POST /customers - register a new customer."""
        return self.post(CustomerEndpoints.BASE, data=payload)

    def get_by_id(self, customer_id: int) -> requests.Response:
        """GET /customers/<id> - get a customer by ID."""
        endpoint = CustomerEndpoints.DETAIL.format(customer_id=customer_id)
        return self.get(endpoint)

    def update(self, customer_id: int, payload: dict) -> requests.Response:
        """PUT /customers/<id> - update customer fields."""

        endpoint = CustomerEndpoints.DETAIL.format(customer_id=customer_id)
        return  self.put(endpoint, data=payload)

    def delete_customer(self, customer_id: int) -> requests.Response:
        """DELETE /customerd/<id> - permanently delete customer."""

        endpoint = CustomerEndpoints.DETAIL.format(customer_id=customer_id)
        return  self.delete(endpoint)

    def login(self, payload: dict) -> requests.Response:
        """POST /customers/login - authenticate and get JWT token."""
        return self.post(CustomerEndpoints.LOGIN, data=payload)

