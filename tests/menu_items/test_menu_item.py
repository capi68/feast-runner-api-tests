"""Test fot menu items API."""

import allure
import pytest

from tests.base.base_assertions import BaseAssertions
from tests.models.menu_items_model import MenuItem
from tests.payloads.menu_items_payloads import menu_item_create_payload,menu_item_update_payload
from tests.factories.menu_factory import MenuFactory
from tests.schemas.menu_items_schemas import MENU_ITEM_RESPONSE_SCHEMA, MENU_ITEMS_LIST_SCHEMA
from tests.utils.constants import StatusCodes

@pytest.mark.menu_items
@allure.feature("Menu Items")
class TestMenuItemsCreation(BaseAssertions):
    """Tests for POST /menu-items - menu items registration.

    validates that the menu-items creation endpoint correctly handles
    valid input. missing fields, invalid data.
    """

    @allure.story("Create menu item successfully")
    def test_create_menu_item_success(self, menu_service, menu_items_service):
        """POST /menu-items - with valida data and required fields should return 201.
        and a response matching with MenuItems Schema.
        """

        with allure.step("Create valid menu using factory"):
            menu_factory = MenuFactory(menu_service)
            menu = menu_factory.create()
            menu_id = menu["id"]

        with allure.step("Create a valid payload with menu_id"):
            menu_item = MenuItem(menu_id=menu_id)
            payload = menu_item_create_payload(menu_item)

        with allure.step("call the menu item service"):
            service = menu_items_service

        with allure.step("POST /menu-items request"):
            response = service.create(payload)

        with allure.step("Validate response."):
            self.using(response).assert_status_code_is(StatusCodes.CREATED)
            self.using(response).assert_response_has_key("id")
            self.using(response).assert_schema(MENU_ITEM_RESPONSE_SCHEMA)
            self.using(response).assert_response_has_key_value("name", payload["name"])
            self.using(response).assert_response_has_key_value("price", payload["price"])

        with allure.step("Clean data after test."):
            #CLEANUP
            menu_factory.cleanup(menu_id)
            menu_factory.cleanup_all()

    @allure.story("Create menu item with empty required fields")
    def test_create_menu_item_missing_field(self, menu_items_service):
        """POST /menu-items with empty body should return 400
        and message indicating which fields are missing.
        """

        response = menu_items_service.create({})

        self.using(response).assert_status_code_is(StatusCodes.BAD_REQUEST)
        self.using(response).assert_response_has_key("message")

    @allure.story("Create menu item with empty required fields")
    @pytest.mark.parametrize("field", ["menu_id", "name", "price", "category", "preparation_time_minutes"])
    def test_create_menu_item_empty_required_fields(self, menu_items_service, menu_service, restaurant_service, field):
        """POST /menu-items with empty required field, should return 400
        and a message indicating which fields are missing."""

        menu_factory = MenuFactory(menu_service, restaurant_service)
        menu = menu_factory.create()
        menu_id = menu["id"]
        restaurant_id = menu["restaurant_id"]

        menu_item = MenuItem(menu_id=menu_id)
        payload = menu_item_create_payload(menu_item)
        payload[field] = ""

        response = menu_items_service.create(payload)

        self.using(response).assert_status_code_is(StatusCodes.BAD_REQUEST)
        self.using(response).assert_response_has_key("message")

        #CLEANUP
        menu_factory.cleanup(menu_id)
        menu_factory.cleanup_all(restaurant_id)

    @allure.story("Create menu item with invalid category")
    def test_create_menu_item_invalid_category(self, menu_service, restaurant_service, menu_items_service):
        """POST /menu-items with invalid category 'gelato' should return 400.
        and message.
        """
        menu_factory = MenuFactory(menu_service, restaurant_service)
        menu = menu_factory.create()
        menu_id = menu["id"]
        restaurant_id = menu["restaurant_id"]

        menu_item = MenuItem(menu_id=menu_id)
        payload = menu_item_create_payload(menu_item)
        payload["category"] = "gelato"

        response = menu_items_service.create(payload)

        self.using(response).assert_status_code_is(StatusCodes.BAD_REQUEST)
        self.using(response).assert_response_has_key("message")

        #CLEANUP
        menu_factory.cleanup(menu_id)
        menu_factory.cleanup_all(restaurant_id)

    @allure.story("Create menu item with out of rage price")
    def test_create_menu_item_out_range_price(self, menu_service, restaurant_service, menu_items_service):
        """POST /menu-items without of range price should return 400.
        and message.
        """
        menu_factory = MenuFactory(menu_service, restaurant_service)
        menu = menu_factory.create()
        menu_id = menu["id"]
        restaurant_id = menu["restaurant_id"]

        menu_item = MenuItem(menu_id=menu_id)
        payload = menu_item_create_payload(menu_item)
        payload["price"] = 1000

        response = menu_items_service.create(payload)

        self.using(response).assert_status_code_is(StatusCodes.BAD_REQUEST)
        self.using(response).assert_response_has_key("message")

        #CLEANUP
        menu_factory.cleanup(menu_id)
        menu_factory.cleanup_all(restaurant_id)

    @allure.story("Create menu item with out of rage preparation")
    def test_create_menu_item_out_range_preparation(self, menu_service, restaurant_service, menu_items_service):
        """POST /menu-items without of range preparation should return 400.
        and message.
        """
        menu_factory = MenuFactory(menu_service, restaurant_service)
        menu = menu_factory.create()
        menu_id = menu["id"]
        restaurant_id = menu["restaurant_id"]

        menu_item = MenuItem(menu_id=menu_id)
        payload = menu_item_create_payload(menu_item)
        payload["preparation_time_minutes"] = 121

        response = menu_items_service.create(payload)

        self.using(response).assert_status_code_is(StatusCodes.BAD_REQUEST)
        self.using(response).assert_response_has_key("message")

        #CLEANUP
        menu_factory.cleanup(menu_id)
        menu_factory.cleanup_all(restaurant_id)

    @allure.story("Create menu item with non-existent menu")
    def test_create_menu_item_nonexist_menu(self, menu_items_service):
        """POST /menu-items with nonexist menu should return 404.
        And message.
        """
        menu_id = 999999
        menu_item = MenuItem(menu_id=menu_id)
        payload = menu_item_create_payload(menu_item)

        response = menu_items_service.create(payload)

        self.using(response).assert_status_code_is(StatusCodes.NOT_FOUND)
        self.using(response).assert_response_has_key("message")


@pytest.mark.menu_items
@allure.feature("Menu Items")
class TestMenuItemsRetrieval(BaseAssertions):
    """Tests for GET /menu-items - GET /menu-items?menu_id=
    and GET /menu-items/<id>
    """

    @allure.story("List of menu items")
    def test_list_menu_items(self, menu_items_service):
        """GET /menu-items should return 200 with a list of menu items
        filterable by menu_id
        """
        response = menu_items_service.list()

        self.using(response).assert_status_code_is(StatusCodes.OK)
        self.using(response).assert_schema(MENU_ITEMS_LIST_SCHEMA)

    @allure.story("List all menu items by menu_id")
    def test_list_menu_items_by_menu_id(self, menu_service, restaurant_service, menu_items_service):
        """GET /menu-items?menu_id= should return 200 with a list of menu items
        for specific menu.
        """
        menu_factory = MenuFactory(menu_service, restaurant_service)
        menu = menu_factory.create()
        menu_id = menu["id"]
        restaurant_id = menu["restaurant_id"]

        menu_item= MenuItem(menu_id=menu_id)

        #menu item 1
        payload1 = menu_item_create_payload(menu_item)
        menu_items_service.create(payload1)

        #menu item 2
        payload2 = menu_item_create_payload(
            menu_item,
            name="BBQ Chicken Pizza",
            description="Thin crust pizza topped with grilled chicken, BBQ sauce, red onions, and mozzarella cheese.",
            price=16.99,
            category="appetizer",
            preparation_time_minutes=20,
        )
        menu_items_service.create(payload2)

        #Get list by id
        get_response = menu_items_service.list(menu_id)
        data = get_response.json()

        self.using(get_response).assert_status_code_is(StatusCodes.OK)
        self.using(get_response).assert_schema(MENU_ITEMS_LIST_SCHEMA)
        assert all(menu_item["menu_id"] == menu_id for menu_item in data)
        assert len(data) == 2

        #CLEANUP
        menu_factory.cleanup(menu_id)
        menu_factory.cleanup_all(restaurant_id)

    @allure.story("Get menu item by id")
    def test_get_menu_item_by_id(self, menu_service,restaurant_service, menu_items_service):
        """GET /menu-items/<id> should return 200 with the menu item matching
        the specific ID.
        """
        menu_factory = MenuFactory(menu_service, restaurant_service)
        menu = menu_factory.create()
        menu_id = menu["id"]
        restaurant_id = menu["restaurant_id"]

        menu_item = MenuItem(menu_id=menu_id)
        payload = menu_item_create_payload(menu_item)

        response = menu_items_service.create(payload)

        data = response.json()

        #Get menu item by ID.
        get_response = menu_items_service.get_by_id(data["id"])

        self.using(get_response).assert_status_code_is(StatusCodes.OK)

        #CLEANUP
        menu_factory.cleanup(menu_id)
        menu_factory.cleanup_all(restaurant_id)


    @allure.story("Get non-existent menu item")
    def test_get_non_existent_menu_item(self, menu_items_service):
        """GET /menu-items/99999 should return 404 when no menu item exists with that ID."""
        response = menu_items_service.get_by_id(99999)

        self.using(response).assert_status_code_is(StatusCodes.NOT_FOUND)
        self.using(response).assert_response_has_key("message")


@pytest.mark.menu_items
@allure.feature("Menu Items")
class TestMenuItemUpdate(BaseAssertions):
    """Test for PUT /menu-items/<id>"""

    @allure.story("Update menu item successfully")
    def test_update_menu_item_success(self, menu_service,restaurant_service, menu_items_service):
        """PUT /menu-items/<id> should update the provided fields and return 200.
        Only the specified fields change, others remain untouched.
        """
        menu_factory = MenuFactory(menu_service, restaurant_service)
        menu = menu_factory.create()
        menu_id = menu["id"]
        restaurant_id = menu["restaurant_id"]

        menu_item = MenuItem(menu_id=menu_id)
        payload = menu_item_create_payload(menu_item)

        response = menu_items_service.create(payload)
        data = response.json()

        update_payload = menu_item_update_payload(name="BIG Margherita Pizza",price=16.99,preparation_time_minutes=35)

        update_response = menu_items_service.update(data["id"], update_payload)

        self.using(update_response).assert_status_code_is(StatusCodes.OK)
        self.using(update_response).assert_response_has_key_value("name", update_payload["name"])
        self.using(update_response).assert_response_has_key_value("price", update_payload["price"])
        self.using(update_response).assert_response_has_key_value("preparation_time_minutes", update_payload["preparation_time_minutes"])
        self.using(update_response).assert_response_has_key_value("category", "appetizer")

        #CLEANUP
        menu_factory.cleanup(menu_id)
        menu_factory.cleanup_all(restaurant_id)


    @allure.story("Update non-existent menu item.")
    def test_update_nonexist_menu_item(self, menu_items_service):
        """PUT /menu-items/999999 should return 404 and message."""

        menu_item_id = 999999
        update_payload = menu_item_update_payload(name="BIG Margherita Pizza", price=16.99,)
        response = menu_items_service.update(menu_item_id, update_payload)

        self.using(response).assert_status_code_is(StatusCodes.NOT_FOUND)
        self.using(response).assert_response_has_key("message")


    @allure.story("Update menu item timestamp.")
    def test_update_menu_item_timestamp(self, menu_service,restaurant_service, menu_items_service):
        """PUT /menu-items/<id> should update the provided fields and return 200.
        timestamp must change."""
        menu_factory = MenuFactory(menu_service, restaurant_service)
        menu = menu_factory.create()
        menu_id = menu["id"]
        restaurant_id = menu["restaurant_id"]

        menu_item = MenuItem(menu_id)
        payload= menu_item_create_payload(menu_item)

        response = menu_items_service.create(payload)
        data = response.json()

        update_payload = menu_item_update_payload(name="BIG Margherita Pizza")
        update_response = menu_items_service.update(data["id"], update_payload)
        update_data = update_response.json()

        self.using(update_response).assert_status_code_is(StatusCodes.OK)
        self.using(update_response).assert_response_has_key_value("name", update_payload["name"])
        assert update_data["updated_at"] > data["updated_at"]

        #CLEANUP
        menu_factory.cleanup(menu_id)
        menu_factory.cleanup_all(restaurant_id)

@pytest.mark.menu_items
@allure.feature("Menu Items")
class TestMenuItemDelete(BaseAssertions):
    """Test for DELETE /menu-items/<id>."""

    @allure.story("Delete menu item successfully")
    def test_delete_menu_item_success(self, menu_service,restaurant_service, menu_items_service):
        """DELETE /menu-items/<id> -should return 200 and delete menu permanently"""

        menu_factory = MenuFactory(menu_service, restaurant_service)
        menu = menu_factory.create()
        menu_id = menu["id"]
        restaurant_id = menu["restaurant_id"]

        menu_item = MenuItem(menu_id=menu_id)
        payload = menu_item_create_payload(menu_item)

        response = menu_items_service.create(payload)
        data = response.json()

        delete_response = menu_items_service.delete_menu_item(data["id"])

        self.using(delete_response).assert_status_code_is(StatusCodes.OK)
        self.using(delete_response).assert_response_has_key("message")

        #verify
        get_response = menu_items_service.get_by_id(data["id"])

        self.using(get_response).assert_status_code_is(StatusCodes.NOT_FOUND)

        #CLEANUP
        menu_factory.cleanup(menu_id)
        menu_factory.cleanup_all(restaurant_id)

    @allure.story("Delete non-existent menu item")
    def test_delete_nonexist_menu_item(self, menu_items_service):
        """DELETE /menu-items/999999 - should return 404 and message."""

        menu_item_id = 999999

        response = menu_items_service.delete_menu_item(menu_item_id)

        self.using(response).assert_status_code_is(StatusCodes.NOT_FOUND)
        self.using(response).assert_response_has_key("message")

