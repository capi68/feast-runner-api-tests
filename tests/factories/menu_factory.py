"""Factory for creating Menu preconditions.

Handles the dependency chain: Restaurant → Menu.
Automatically creates a restaurant if none is provided.
"""

from tests.services.menu_service import MenuService
from tests.services.restaurant_service import RestaurantService
from tests.payloads.menu_payloads import menu_create_payload
from tests.factories.restaurant_factory import RestaurantFactory
from tests.utils.constants import StatusCodes
from tests.utils.logger import get_logger

logger = get_logger(__name__)


class MenuFactory:
    """Creates menu preconditions via the API.
    If no restaurant_id is provided, creates one automatically.
    """

    def __init__(self, menu_service: MenuService, restaurant_service: RestaurantService = None):
        self._menu_service = menu_service
        self._restaurant_factory = RestaurantFactory(restaurant_service)
        self._created_restaurants = []

    def create(self, restaurant_id: int = None, **overrides) -> dict:
        """Create a menu with its dependencies and return the response JSON.

        Args:
            restaurant_id: ID of existing restaurant. If None, creates one.
            **overrides: Any fields to override in the default payload.

        Returns:
            dict: The created menu response from the API.
        """
        # Create restaurant dependency if not provided
        if restaurant_id is None:
            restaurant = self._restaurant_factory.create()
            restaurant_id = restaurant["id"]

        payload = menu_create_payload(restaurant_id=restaurant_id, **overrides)

        response = self._menu_service.create(payload)
        assert response.status_code == StatusCodes.CREATED, f"Factory failed to create menu: {response.text}"

        data = response.json()
        data["restaurant_id"] = restaurant_id
        logger.info("Factory created menu id=%s name='%s' for restaurant=%s", data["id"], data["name"], restaurant_id)
        return data

    def cleanup(self, menu_id: int) -> None:
        """Delete a menu created by the factory."""
        response = self._menu_service.delete_menu(menu_id)
        if response.status_code == StatusCodes.OK:
            logger.info("Factory cleaned up menu id=%s", menu_id)
        else:
            logger.warning(
                "Factory cleanup failed for menu id=%s (%s): %s",
                menu_id,
                response.status_code,
                response.text
            )

    def cleanup_all(self, restaurant_id: int) -> None:
        """Clean up all resources created by this factory."""
        self._restaurant_factory.cleanup(restaurant_id)
