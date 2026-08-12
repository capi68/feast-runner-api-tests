"""Factory for creating menu items preconditions.
Creates a menu item via the API and returns the response data.
Used when other entities (Order) need menu items for exist first.
"""

from tests.services.menu_items_service import MenuItemsService
from tests.payloads.menu_items_payloads import menu_item_create_payload
from tests.services.menu_service import MenuService
from tests.factories.menu_factory import MenuFactory
from tests.models.menu_items_model import MenuItem
from tests.services.restaurant_service import RestaurantService
from tests.utils.constants import StatusCodes
from tests.utils.logger import get_logger

logger = get_logger(__name__)

class MenuItemsFactory:
    """Creates Menu Items preconditions via the API.

    Dependency chain: Menu → MenuItems
    If no menu_id is provided, creates one automatically.
    """

    def __init__(self, menu_items_service: MenuItemsService, menu_service: MenuService, restaurant_service: RestaurantService):
        self._menu_items_service = menu_items_service
        self._menu_service = menu_service
        self._menu_factory = MenuFactory(menu_service, restaurant_service)
        self._created_menus = []

    def create(self, menu_id: int = None, **overrides):
        """Create a menu item with its dependencies and return the response JSON.

        Args:
            menu_id: ID of existing menu. If None, creates one.
            **overrides: Any fields to override in the default payload.

        Returns:
            dict: The created menu_item response from the API.
        """
        #Create menu dependency if not provided
        restaurant_id = None
        if menu_id is None:
            menu = self._menu_factory.create()
            menu_id = menu["id"]
            restaurant_id = menu["restaurant_id"]
        else:
            response = self._menu_service.get_by_id(menu_id)
            restaurant_id = response.json()["restaurant_id"]

        menu_item = MenuItem(menu_id=menu_id)
        payload = menu_item_create_payload(menu_item, **overrides)

        response = self._menu_items_service.create(payload)
        assert response.status_code == StatusCodes.CREATED, f"Factory failed to create menu item: {response.text}"

        data = response.json()
        data["restaurant_id"] = restaurant_id

        logger.info("Factory created menu item id=%s name='%s' for menu=%s", data["id"], data["name"], menu_id)
        return data

    def cleanup(self, menu_item_id: int) -> None:
        """Delete the menu item created by the factory.

        Note:
            The API may return HTTP 500 when the menu item is still referenced
            by another resource, such as an order item. In that case, the
            cleanup failure is logged as a warning."""

        response = self._menu_items_service.delete_menu_item(menu_item_id)
        if response.status_code == StatusCodes.OK:
            logger.info("Factory cleaned up menu item id=%s", menu_item_id)
        else:
            logger.warning(
                "Factory cleanup failed for menu item id=%s (%s): %s",
                menu_item_id,
                response.status_code,
                response.text
            )

    def cleanup_all(self, menu_id: int, restaurant_id: int) -> None:
        """Clean up all resources created by this factory"""
        self._menu_factory.cleanup(menu_id)
        self._menu_factory.cleanup_all(restaurant_id)




