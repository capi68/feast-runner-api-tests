"""Service layer for Ratings API interactions."""

import requests
from tests.base.base_service import BaseService
from tests.utils.endpoints import RatingEndpoints

class RatingService(BaseService):
    """HTTP service for ratings CRUD."""

    def list(self, order_id:int = None) -> requests.Response:
        """GET /ratings - list all ratings optionally filtered by order_id."""
        if order_id is None:
            return self.get(RatingEndpoints.BASE)
        return self.get(RatingEndpoints.BASE, params={"order_id": order_id})

    def create(self, payload: dict) -> requests.Response:
        """POST /ratings - register a new rating."""
        return self.post(RatingEndpoints.BASE, data=payload)

    def get_by_id(self, rating_id: int) -> requests.Response:
        """GET /ratings/<id> - get rating by ID."""
        endpoint = RatingEndpoints.DETAIL.format(rating_id=rating_id)
        return self.get(endpoint)