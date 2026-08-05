"""Service layer for Deliveries API interactions."""

import requests

from tests import services
from tests.base.base_service import BaseService
from tests.utils.endpoints import DeliveryEndpoints

class DeliveryService(BaseService):
    """HTTP service for deliveries CRUD."""

    def list(self, courier_id: int = None, status: str = None) -> requests.Response:
        """GET /deliveries - list all deliveries."""
        params = {}

        if courier_id is not None:
            params["courier_id"] = courier_id

        if status is not None:
            params["status"] = status

        return self.get(DeliveryEndpoints.BASE, params=params)

    def create(self, payload: dict) -> requests.Response:
        """POST /deliveries - register a new delivery."""
        return  self.post(DeliveryEndpoints.BASE, data=payload)

    def get_by_id(self, delivery_id: int) -> requests.Response:
        """GET /deliveries/<id> get delivery by id."""
        endpoint = DeliveryEndpoints.DETAIL.format(delivery_id=delivery_id)
        return self.get(endpoint)

    def update(self, delivery_id: int, payload: dict) -> requests.Response:
        """put /deliveries/<id> - update delivery status field."""
        endpoint = DeliveryEndpoints.DETAIL.format(delivery_id=delivery_id)
        return self.put(endpoint, data=payload)