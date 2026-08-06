"""Service layer for Couriers API interactions."""

import requests
from tests.base.base_service import BaseService
from tests.utils.endpoints import CourierEndpoints
from tests.utils.logger import get_logger

logger = get_logger(__name__)

class CouriersService(BaseService):
    """HTTP Service for couriers CRUD and authentication."""

    def list(self, is_available: bool = None) -> requests.Response:
        """GET /couriers - list all active couriers, optionally filtered by available status"""
        params = {}

        if is_available is not None:
            params["is_available"] = str(is_available).lower()

        return self.get(CourierEndpoints.BASE, params=params)

    def create(self, payload: dict) -> requests.Response:
        """POST /couriers - register a new courier."""
        return self.post(CourierEndpoints.BASE, data=payload)

    def get_by_id(self, courier_id: int) -> requests.Response:
        """GET /couriers/<id> - get courier by id."""
        endpoint = CourierEndpoints.DETAIL.format(courier_id=courier_id)
        return  self.get(endpoint)

    def update(self, courier_id: int, payload: dict) -> requests.Response:
        """PUT /couriers/<id> - update courier fields."""
        endpoint = CourierEndpoints.DETAIL.format(courier_id=courier_id)
        return self.put(endpoint, payload)

    def delete_courier(self, courier_id: int) -> requests.Response:
        """DELETE /couriers/<id> - permanently delete courier."""
        endpoint = CourierEndpoints.DETAIL.format(courier_id=courier_id)
        return self.delete(endpoint)

    def login_courier(self, payload: dict) -> requests.Response:
        """LOGIN /couriers/login - authenticate and get JWT Token."""
        return self.post(CourierEndpoints.LOGIN, data=payload)