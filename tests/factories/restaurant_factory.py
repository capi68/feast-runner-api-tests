"""Factory for creating Restaurant preconditions.

Creates a restaurant via the API and returns the response data.
Used when other entities (Menu, Order, etc.) need a restaurant to exist first.
"""

from tests.services.restaurant_service import RestaurantService
from tests.payloads.restaurant_payloads import restaurant_create_payload
from tests.utils.constants import StatusCodes
from tests.utils.logger import get_logger

logger = get_logger(__name__)


class RestaurantFactory:
    """Creates restaurant preconditions via the API."""

    def __init__(self, service: RestaurantService = None):
        self._service = service or RestaurantService()

    def create(self, **overrides) -> dict:
        """Create a restaurant and return the response JSON.

        Args:
            **overrides: Any fields to override in the default payload.

        Returns:
            dict: The created restaurant response from the API.
        """
        payload = restaurant_create_payload()
        payload.update(overrides)

        response = self._service.create(payload)
        assert response.status_code == StatusCodes.CREATED, f"Factory failed to create restaurant: {response.text}"

        data = response.json()
        logger.info("Factory created restaurant id=%s name='%s'", data["id"], data["name"])
        return data

    def cleanup(self, restaurant_id: int) -> None:
        """Delete a restaurant created by the factory."""
        response = self._service.delete_restaurant(restaurant_id)
        if response.status_code == StatusCodes.OK:
            logger.info("Factory cleaned up restaurant id=%s", restaurant_id)
        else:
            logger.warning(
                "Factory cleanup failed for restaurant id=%s (%s): %s",
                restaurant_id,
                response.status_code,
                response.text
            )
