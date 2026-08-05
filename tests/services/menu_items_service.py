"""Service layer for Menu Items API interactions."""

import  requests
from tests.base.base_service import BaseService
from tests.utils.endpoints import MenuItemEndpoints

class MenuItemsService(BaseService):
    """HTTP service for menu items CRUD."""

    def list(self, menu_id: int = None) -> requests.Response:
        """GET /menu-items - list all menu items optionally filtered by menu_id"""
        if menu_id is None:
            return self.get(MenuItemEndpoints.BASE)

        return  self.get(MenuItemEndpoints.BASE, params={"menu_id": menu_id})

    def create(self, payload: dict) -> requests.Response:
        """POST /menu-items - register a new menu item."""
        return self.post(MenuItemEndpoints.BASE, data=payload)

    def get_by_id(self, item_id: int) -> requests.Response:
        """GET /menu-items/<id> - get menu item by id."""
        endpoint = MenuItemEndpoints.DETAIL.format(item_id=item_id)
        return self.get(endpoint)

    def update(self, item_id: int, payload: dict) -> requests.Response:
        """PUT /menu-items/<id> - update menu item fields."""
        endpoint = MenuItemEndpoints.DETAIL.format(item_id=item_id)
        return self.put(endpoint, data=payload)

    def delete_menu_item(self, item_id: int) -> requests.Response:
        """DELETE /menu-items/<id> - permanently delete menu item."""
        endpoint = MenuItemEndpoints.DETAIL.format(item_id=item_id)
        return self.delete(endpoint)