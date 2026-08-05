"""Service layer for Order API interactions."""

import requests
from tests.base.base_service import BaseService
from tests.utils.endpoints import OrderEndpoints

class OrderService(BaseService):
    """HTTP service for Order CRUD."""

    def list(self, customer_id:int = None, restaurant_id: int = None, status: str = None) -> requests.Response:
        """GET /orders - list all menu items optionally filtered by customer_id, restaurant_id and status"""
        params = {}

        if customer_id is not None:
            params["customer_id"] = customer_id

        if restaurant_id is not None:
            params["restaurant_id"] = restaurant_id

        if status is not None:
            params["status"] = status

        return self.get(OrderEndpoints.BASE, params=params)

    def create(self, payload: dict) -> requests.Response:
        """POST /orders - register a new order."""
        return self.post(OrderEndpoints.BASE, data=payload)

    def get_by_id(self, order_id: int) -> requests.Response:
        """GET /orders/<id> - get order by id."""
        endpoint = OrderEndpoints.DETAIL.format(order_id=order_id)
        return self.get(endpoint)

    def update(self, order_id: int, payload: dict) -> requests.Response:
        """PUT /orders/<id> - update orders fields."""
        endpoint = OrderEndpoints.DETAIL.format(order_id=order_id)
        return self.put(endpoint, data=payload)

    def delete_order(self, order_id: int) -> requests.Response:
        """DELETE /orders/<id> cancel an order."""
        endpoint = OrderEndpoints.DETAIL.format(order_id=order_id)
        return self.delete(endpoint)

    def get_items_by_order(self, order_id: int) -> requests.Response:
        """GET /orders/<id>/items get items for a specific order."""
        endpoint = OrderEndpoints.ITEMS.format(order_id=order_id)
        return self.get(endpoint)

