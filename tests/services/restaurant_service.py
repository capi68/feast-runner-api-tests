"""Service layer for Restaurant API interactions."""

import requests
from tests.base.base_service import BaseService
from tests.utils.endpoints import RestaurantEndpoints


class RestaurantService(BaseService):
    """HTTP service for restaurant CRUD and authentication."""

    def list(self) -> requests.Response:
        """GET /restaurants — list all non-closed restaurants."""
        return self.get(RestaurantEndpoints.BASE)

    def create(self, payload: dict) -> requests.Response:
        """POST /restaurants — register a new restaurant."""
        return self.post(RestaurantEndpoints.BASE, data=payload)

    def get_by_id(self, restaurant_id: int) -> requests.Response:
        """GET /restaurants/<id> — get restaurant by ID."""
        endpoint = RestaurantEndpoints.DETAIL.format(restaurant_id=restaurant_id)
        return self.get(endpoint)

    def update(self, restaurant_id: int, payload: dict) -> requests.Response:
        """PUT /restaurants/<id> — update restaurant fields."""
        endpoint = RestaurantEndpoints.DETAIL.format(restaurant_id=restaurant_id)
        return self.put(endpoint, data=payload)

    def delete_restaurant(self, restaurant_id: int) -> requests.Response:
        """DELETE /restaurants/<id> — permanently delete restaurant."""
        endpoint = RestaurantEndpoints.DETAIL.format(restaurant_id=restaurant_id)
        return self.delete(endpoint)

    def login(self, payload: dict) -> requests.Response:
        """POST /restaurants/login — authenticate and get JWT token."""
        return self.post(RestaurantEndpoints.LOGIN, data=payload)
