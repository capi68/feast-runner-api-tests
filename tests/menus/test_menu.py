"""Tests for the Menus API"""

import allure
import pytest

from tests.base.base_assertions import BaseAssertions
from tests.services.menu_service import MenuService
from tests.payloads.menu_payloads import menu_create_payload
from tests.schemas.menu_schemas import MENU_RESPONSE_SCHEMA, MENU_LIST_SCHEMA
from tests.factories.restaurant_factory import RestaurantFactory
from tests.utils.constants import MenuStatuses, StatusCodes


@allure.feature("Menus")
@pytest.mark.menus
class TestMenuCreation(BaseAssertions):
    """Tests for POST /menus — menu creation.

    Validates that menus can be created with valid data,
    require an active restaurant, and start in 'draft' status.
    """

    @allure.story("Create menu with valid data")
    @pytest.mark.smoke
    def test_create_menu_success(self, restaurant_service, menu_service):
        """POST /menus with valid restaurant_id and name should return 201.
        New menus always start in 'draft' status."""
        # Precondition: create a restaurant
        factory = RestaurantFactory(restaurant_service)
        restaurant = factory.create()

        payload = menu_create_payload(restaurant_id=restaurant["id"])
        response = menu_service.create(payload)

        self.using(response).assert_status_code_is(StatusCodes.CREATED)
        self.using(response).assert_schema(MENU_RESPONSE_SCHEMA)
        self.using(response).assert_response_has_key_value("status", MenuStatuses.DRAFT)
        self.using(response).assert_response_has_key_value("restaurant_id", restaurant["id"])

        # Cleanup
        menu_service.delete_menu(response.json()["id"])
        restaurant_service.delete_restaurant(restaurant["id"])

    @allure.story("Create menu with missing required fields")
    def test_create_menu_missing_fields(self, menu_service):
        """POST /menus with empty body should return 400."""
        response = menu_service.create({})

        self.using(response).assert_status_code_is(StatusCodes.BAD_REQUEST)
        self.using(response).assert_response_has_key("message")

    @allure.story("Create menu for non-existent restaurant")
    def test_create_menu_restaurant_not_found(self, menu_service):
        """POST /menus with restaurant_id that doesn't exist should return 404."""
        payload = menu_create_payload(restaurant_id=99999)
        response = menu_service.create(payload)

        self.using(response).assert_status_code_is(StatusCodes.NOT_FOUND)

@allure.feature("Menus")
@pytest.mark.menus
class TestMenuRetrieval(BaseAssertions):
    """Tests for GET /menus and GET /menus/<id>."""

    @allure.story("List all menus")
    @pytest.mark.smoke
    def test_list_menus(self, menu_service):
        """GET /menus should return 200 with a list of menus."""
        response = menu_service.list()

        self.using(response).assert_status_code_is(StatusCodes.OK)
        self.using(response).assert_schema(MENU_LIST_SCHEMA)


    @allure.story("Get menu by ID")
    def test_get_menu_by_id(self, restaurant_service, menu_service):
        """GET /menus/<id> should return the menu matching that ID."""
        factory = RestaurantFactory(restaurant_service)
        restaurant = factory.create()
        menu_payload = menu_create_payload(restaurant_id=restaurant["id"])
        create_resp = menu_service.create(menu_payload)
        menu_id = create_resp.json()["id"]

        response = menu_service.get_by_id(menu_id)

        self.using(response).assert_status_code_is(StatusCodes.OK)
        self.using(response).assert_response_has_key_value("id", menu_id)
        self.using(response).assert_schema(MENU_RESPONSE_SCHEMA)

        # Cleanup
        menu_service.delete_menu(menu_id)
        restaurant_service.delete_restaurant(restaurant["id"])

    @allure.story("Get non-existent menu")
    def test_get_menu_not_found(self, menu_service):
        """GET /menus/99999 should return 404."""
        response = menu_service.get_by_id(99999)

        self.using(response).assert_status_code_is(StatusCodes.NOT_FOUND)

    @allure.story("List menus without auth")
    @pytest.mark.auth
    def test_list_menus_unauthorized(self):
        """GET /menus without Authorization header should return 401."""
        service = MenuService()  # No token

        response = service.list()

        self.using(response).assert_status_code_is(StatusCodes.UNAUTHORIZED)


@allure.feature("Menus")
@pytest.mark.menus
class TestMenuStateMachine(BaseAssertions):
    """Tests for menu status transitions (draft → active → archived).

    The state machine rules:
    - draft → active, archived
    - active → draft, archived
    - archived → (nothing, terminal)
    - Only ONE active menu per restaurant
    """

    @allure.story("Activate a draft menu")
    def test_activate_menu(self, restaurant_service, menu_service):
        """PUT /menus/<id> with status='active' should transition from draft.
        Activating a menu makes it visible to customers."""
        factory = RestaurantFactory(restaurant_service)
        restaurant = factory.create()
        menu_resp = menu_service.create(menu_create_payload(restaurant_id=restaurant["id"]))
        menu_id = menu_resp.json()["id"]

        response = menu_service.update(menu_id, {"status": "active"})

        self.using(response).assert_status_code_is(StatusCodes.OK)
        self.using(response).assert_response_has_key_value("status", MenuStatuses.ACTIVE)

        # Cleanup
        menu_service.update(menu_id, {"status": "archived"})
        menu_service.delete_menu(menu_id)
        restaurant_service.delete_restaurant(restaurant["id"])

    @allure.story("Archive an active menu")
    def test_archive_menu(self, restaurant_service, menu_service):
        """PUT /menus/<id> with status='archived' should work from both draft and active.
        Archived is a terminal state."""
        factory = RestaurantFactory(restaurant_service)
        restaurant = factory.create()
        menu_resp = menu_service.create(menu_create_payload(restaurant_id=restaurant["id"]))
        menu_id = menu_resp.json()["id"]

        # Activate first
        menu_service.update(menu_id, {"status": "active"})

        # Archive
        response = menu_service.update(menu_id, {"status": "archived"})
        self.using(response).assert_status_code_is(StatusCodes.OK)
        self.using(response).assert_response_has_key_value("status", MenuStatuses.ARCHIVED)

        # Cleanup
        menu_service.delete_menu(menu_id)
        restaurant_service.delete_restaurant(restaurant["id"])

    @allure.story("Cannot transition from archived (terminal)")
    def test_archived_is_terminal(self, restaurant_service, menu_service):
        """PUT /menus/<id> with any status change from 'archived' should return 400.
        Archived is a terminal state — no further transitions allowed."""
        factory = RestaurantFactory(restaurant_service)
        restaurant = factory.create()
        menu_resp = menu_service.create(menu_create_payload(restaurant_id=restaurant["id"]))
        menu_id = menu_resp.json()["id"]

        # Archive directly from draft
        menu_service.update(menu_id, {"status": "archived"})

        # Try to activate — should fail
        response = menu_service.update(menu_id, {"status": "active"})
        self.using(response).assert_status_code_is(StatusCodes.BAD_REQUEST)

        # Cleanup
        menu_service.delete_menu(menu_id)
        restaurant_service.delete_restaurant(restaurant["id"])

    @allure.story("Only one active menu per restaurant")
    def test_one_active_menu_per_restaurant(self, restaurant_service, menu_service):
        """Attempting to activate a second menu for the same restaurant should return 409.
        Business rule: only one active menu allowed per restaurant at a time."""
        factory = RestaurantFactory(restaurant_service)
        restaurant = factory.create()

        # Create and activate first menu
        menu1_resp = menu_service.create(menu_create_payload(restaurant_id=restaurant["id"]))
        menu1_id = menu1_resp.json()["id"]
        menu_service.update(menu1_id, {"status": "active"})

        # Create second menu and try to activate
        menu2_resp = menu_service.create(
            menu_create_payload(restaurant_id=restaurant["id"])
        )
        menu2_id = menu2_resp.json()["id"]
        response = menu_service.update(menu2_id, {"status": "active"})

        self.using(response).assert_status_code_is(StatusCodes.CONFLICT)

        # Cleanup
        menu_service.update(menu1_id, {"status": "archived"})
        menu_service.delete_menu(menu1_id)
        menu_service.delete_menu(menu2_id)
        restaurant_service.delete_restaurant(restaurant["id"])


@allure.feature("Menus")
@pytest.mark.menus
class TestMenuDelete(BaseAssertions):
    """Tests for DELETE /menus/<id>."""

    @allure.story("Delete menu without pending orders")
    def test_delete_menu_success(self, restaurant_service, menu_service):
        """DELETE /menus/<id> should return 200 when menu has no items in pending orders."""
        factory = RestaurantFactory(restaurant_service)
        restaurant = factory.create()
        menu_resp = menu_service.create(menu_create_payload(restaurant_id=restaurant["id"]))
        menu_id = menu_resp.json()["id"]

        response = menu_service.delete_menu(menu_id)
        self.using(response).assert_status_code_is(StatusCodes.OK)

        # Verify it's gone
        get_resp = menu_service.get_by_id(menu_id)
        self.using(get_resp).assert_status_code_is(StatusCodes.NOT_FOUND)

        # Cleanup
        restaurant_service.delete_restaurant(restaurant["id"])

    @allure.story("Delete non-existent menu")
    def test_delete_menu_not_found(self, menu_service):
        """DELETE /menus/99999 should return 404."""
        response = menu_service.delete_menu(99999)

        self.using(response).assert_status_code_is(StatusCodes.NOT_FOUND)