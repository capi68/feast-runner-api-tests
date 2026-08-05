"""Service layer for Menu API interactions."""

import requests
from tests.base.base_service import BaseService
from tests.utils.endpoints import MenuEndpoints


class MenuService(BaseService):
    """HTTP service for menu CRUD and state management."""

    def list(self, restaurant_id: int = None) -> requests.Response:
        """GET /menus — list menus, optionally filtered by restaurant_id."""
        params = {}
        if restaurant_id:
            params["restaurant_id"] = restaurant_id
        return self.get(MenuEndpoints.BASE, params=params)

    def create(self, payload: dict) -> requests.Response:
        """POST /menus — create a new menu."""
        return self.post(MenuEndpoints.BASE, data=payload)

    def get_by_id(self, menu_id: int) -> requests.Response:
        """GET /menus/<id> — get menu by ID."""
        endpoint = MenuEndpoints.DETAIL.format(menu_id=menu_id)
        return self.get(endpoint)

    def update(self, menu_id: int, payload: dict) -> requests.Response:
        """PUT /menus/<id> — update menu fields or status."""
        endpoint = MenuEndpoints.DETAIL.format(menu_id=menu_id)
        return self.put(endpoint, data=payload)

    def delete_menu(self, menu_id: int) -> requests.Response:
        """DELETE /menus/<id> — delete a menu."""
        endpoint = MenuEndpoints.DETAIL.format(menu_id=menu_id)
        return self.delete(endpoint)
