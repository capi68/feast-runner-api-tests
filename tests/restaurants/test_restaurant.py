"""Tests for the Restaurants API"""

import allure
import pytest

from tests.base.base_assertions import BaseAssertions
from tests.services.restaurant_service import RestaurantService
from tests.payloads.restaurant_payloads import (
    restaurant_create_payload,
    restaurant_update_payload,
    restaurant_login_payload,
)
from tests.schemas.restaurant_schemas import RESTAURANT_RESPONSE_SCHEMA, LOGIN_RESPONSE_SCHEMA
from tests.utils.constants import RestaurantStatuses, StatusCodes


@allure.feature("Restaurants")
@pytest.mark.restaurants
class TestRestaurantCreation(BaseAssertions):
    """Tests for POST /restaurants — restaurant registration.

    Validates that the restaurant creation endpoint correctly handles
    valid input, missing fields, invalid data, and duplicate emails.
    """

    @allure.story("Create restaurant with valid data")
    @pytest.mark.smoke
    def test_create_restaurant_success(self):
        """POST /restaurants with all valid required fields should return 201
        and a response matching the RestaurantResponse schema without password."""
        service = RestaurantService()
        payload = restaurant_create_payload()

        response = service.create(payload)

        self.using(response).assert_status_code_is(StatusCodes.CREATED)
        self.using(response).assert_response_key_absent("password_hash")
        self.using(response).assert_response_key_absent("password")
        self.using(response).assert_schema(RESTAURANT_RESPONSE_SCHEMA)
        self.using(response).assert_response_has_key_value("email", payload["email"])
        self.using(response).assert_response_has_key_value("status", RestaurantStatuses.ACTIVE)

    @allure.story("Create restaurant with missing required fields")
    def test_create_restaurant_missing_fields(self):
        """POST /restaurants with empty body should return 400
        with a message indicating which fields are missing."""
        service = RestaurantService()

        response = service.create({})

        self.using(response).assert_status_code_is(StatusCodes.BAD_REQUEST)
        self.using(response).assert_response_has_key("message")

    @allure.story("Create restaurant with invalid email")
    def test_create_restaurant_invalid_email(self):
        """POST /restaurants with malformed email should return 400.
        The API validates email format before attempting DB insertion."""
        service = RestaurantService()
        payload = restaurant_create_payload()
        payload["email"] = "not-an-email"

        response = service.create(payload)

        self.using(response).assert_status_code_is(StatusCodes.BAD_REQUEST)

    @allure.story("Create restaurant with invalid cuisine type")
    def test_create_restaurant_invalid_cuisine(self):
        """POST /restaurants with cuisine_type not in allowed values should return 400.
        Allowed: italian, mexican, japanese, chinese, american, indian, thai, mediterranean."""
        service = RestaurantService()
        payload = restaurant_create_payload()
        payload["cuisine_type"] = "martian"

        response = service.create(payload)

        self.using(response).assert_status_code_is(StatusCodes.BAD_REQUEST)

    @allure.story("Create restaurant with min_order_amount out of range")
    def test_create_restaurant_min_order_too_high(self):
        """POST /restaurants with min_order_amount > 500 should return 400.
        Valid range: 1.00 - 500.00."""
        service = RestaurantService()
        payload = restaurant_create_payload()
        payload["min_order_amount"] = 999.99

        response = service.create(payload)

        self.using(response).assert_status_code_is(StatusCodes.BAD_REQUEST)

    @allure.story("Create restaurant with delivery_radius_km out of range")
    def test_create_restaurant_radius_too_large(self):
        """POST /restaurants with delivery_radius_km > 50 should return 400.
        Valid range: 1 - 50."""
        service = RestaurantService()
        payload = restaurant_create_payload()
        payload["delivery_radius_km"] = 100

        response = service.create(payload)

        self.using(response).assert_status_code_is(StatusCodes.BAD_REQUEST)

    @allure.story("Create restaurant with short password")
    def test_create_restaurant_short_password(self):
        """POST /restaurants with password < 8 characters should return 400."""
        service = RestaurantService()
        payload = restaurant_create_payload()
        payload["password"] = "short"

        response = service.create(payload)

        self.using(response).assert_status_code_is(StatusCodes.BAD_REQUEST)

    @allure.story("Create restaurant with duplicate email")
    def test_create_restaurant_duplicate_email(self, restaurant_service):
        """POST /restaurants with an email that already exists should return 409.
        Email uniqueness is enforced at both API and database level."""
        payload = restaurant_create_payload()

        # First creation — should succeed
        response1 = RestaurantService().create(payload)
        self.using(response1).assert_status_code_is(StatusCodes.CREATED)

        # Second creation with same email — should conflict
        response2 = RestaurantService().create(payload)
        self.using(response2).assert_status_code_is(StatusCodes.CONFLICT)

        # Cleanup
        restaurant_id = response1.json()["id"]
        restaurant_service.delete_restaurant(restaurant_id)


@allure.feature("Restaurants")
@pytest.mark.restaurants
class TestRestaurantRetrieval(BaseAssertions):
    """Tests for GET /restaurants and GET /restaurants/<id>.

    Validates listing and individual retrieval with auth.
    """

    @allure.story("List all restaurants")
    @pytest.mark.smoke
    def test_list_restaurants(self, restaurant_service):
        """GET /restaurants should return 200 with a list of non-closed restaurants.
        Requires valid Authorization header."""
        response = restaurant_service.list()

        self.using(response).assert_status_code_is(StatusCodes.OK)
        self.using(response).assert_response_is_list()

    @allure.story("Get restaurant by ID")
    def test_get_restaurant_by_id(self, restaurant_service):
        """GET /restaurants/<id> should return the restaurant matching that ID.
        Creates a restaurant first, then retrieves it by the returned ID."""
        payload = restaurant_create_payload()
        create_resp = RestaurantService().create(payload)
        restaurant_id = create_resp.json()["id"]

        response = restaurant_service.get_by_id(restaurant_id)

        self.using(response).assert_status_code_is(StatusCodes.OK)
        self.using(response).assert_response_has_key_value("id", restaurant_id)
        self.using(response).assert_schema(RESTAURANT_RESPONSE_SCHEMA)

        # Cleanup
        restaurant_service.delete_restaurant(restaurant_id)

    @allure.story("Get non-existent restaurant")
    def test_get_restaurant_not_found(self, restaurant_service):
        """GET /restaurants/99999 should return 404 when no restaurant exists with that ID."""
        response = restaurant_service.get_by_id(99999)

        self.using(response).assert_status_code_is(StatusCodes.NOT_FOUND)

    @allure.story("List restaurants without auth")
    @pytest.mark.auth
    def test_list_restaurants_unauthorized(self):
        """GET /restaurants without Authorization header should return 401."""
        service = RestaurantService()  # No token

        response = service.list()

        self.using(response).assert_status_code_is(StatusCodes.UNAUTHORIZED)


@allure.feature("Restaurants")
@pytest.mark.restaurants
class TestRestaurantUpdate(BaseAssertions):
    """Tests for PUT /restaurants/<id>."""

    @allure.story("Update restaurant fields")
    def test_update_restaurant_success(self, restaurant_service):
        """PUT /restaurants/<id> should update the provided fields and return 200.
        Only the specified fields change; others remain untouched."""
        payload = restaurant_create_payload()
        create_resp = RestaurantService().create(payload)
        restaurant_id = create_resp.json()["id"]

        update_data = restaurant_update_payload(
            min_order_amount=25.00,
            opening_hours="10:00-22:00"
        )
        response = restaurant_service.update(restaurant_id, update_data)

        self.using(response).assert_status_code_is(StatusCodes.OK)
        self.using(response).assert_response_has_key_value("min_order_amount", 25.00)
        self.using(response).assert_response_has_key_value("opening_hours", "10:00-22:00")

        # Cleanup
        restaurant_service.delete_restaurant(restaurant_id)

    @allure.story("Suspend and reactivate restaurant")
    def test_restaurant_status_toggle(self, restaurant_service):
        """PUT /restaurants/<id> with status changes should follow the state machine.
        active → suspended → active is valid."""
        payload = restaurant_create_payload()
        create_resp = RestaurantService().create(payload)
        restaurant_id = create_resp.json()["id"]

        # Suspend
        response = restaurant_service.update(restaurant_id, {"status": "suspended"})
        self.using(response).assert_status_code_is(StatusCodes.OK)
        self.using(response).assert_response_has_key_value("status", "suspended")

        # Reactivate
        response = restaurant_service.update(restaurant_id, {"status": "active"})
        self.using(response).assert_status_code_is(StatusCodes.OK)
        self.using(response).assert_response_has_key_value("status", "active")

        # Cleanup
        restaurant_service.delete_restaurant(restaurant_id)

    @allure.story("Cannot transition from terminal status")
    def test_restaurant_closed_is_terminal(self, restaurant_service):
        """PUT /restaurants/<id> with status=closed makes the restaurant terminal.
        No further transitions are allowed from 'closed'."""
        payload = restaurant_create_payload()
        create_resp = RestaurantService().create(payload)
        restaurant_id = create_resp.json()["id"]

        # Close it
        restaurant_service.update(restaurant_id, {"status": "closed"})

        # Try to reactivate — should fail
        response = restaurant_service.update(restaurant_id, {"status": "active"})
        self.using(response).assert_status_code_is(StatusCodes.BAD_REQUEST)

        # Cleanup (force delete since it's closed)
        restaurant_service.delete_restaurant(restaurant_id)


@allure.feature("Restaurants")
@pytest.mark.restaurants
class TestRestaurantDelete(BaseAssertions):
    """Tests for DELETE /restaurants/<id>."""

    @allure.story("Delete restaurant without menus")
    def test_delete_restaurant_success(self, restaurant_service):
        """DELETE /restaurants/<id> should return 200 when restaurant has no active menus."""
        payload = restaurant_create_payload()
        create_resp = RestaurantService().create(payload)
        restaurant_id = create_resp.json()["id"]

        response = restaurant_service.delete_restaurant(restaurant_id)
        self.using(response).assert_status_code_is(StatusCodes.OK)

        # Verify it's gone
        get_resp = restaurant_service.get_by_id(restaurant_id)
        self.using(get_resp).assert_status_code_is(StatusCodes.NOT_FOUND)

    @allure.story("Cannot delete restaurant with active menus")
    def test_delete_restaurant_with_active_menu(self, restaurant_service, menu_service):
        """DELETE /restaurants/<id> should return 409 when restaurant has active menus.
        Must deactivate/delete menus first."""
        payload = restaurant_create_payload()
        create_resp = RestaurantService().create(payload)
        restaurant_id = create_resp.json()["id"]

        # Create and activate a menu
        from tests.payloads.menu_payloads import menu_create_payload
        menu_payload = menu_create_payload(restaurant_id=restaurant_id)
        menu_resp = menu_service.create(menu_payload)
        menu_id = menu_resp.json()["id"]
        menu_service.update(menu_id, {"status": "active"})

        # Try to delete — should fail
        response = restaurant_service.delete_restaurant(restaurant_id)
        self.using(response).assert_status_code_is(StatusCodes.CONFLICT)

        # Cleanup: archive menu, then delete restaurant
        menu_service.update(menu_id, {"status": "archived"})
        menu_service.delete_menu(menu_id)
        restaurant_service.delete_restaurant(restaurant_id)


@allure.feature("Restaurants")
@pytest.mark.restaurants
@pytest.mark.auth
class TestRestaurantAuth(BaseAssertions):
    """Tests for POST /restaurants/login."""

    @allure.story("Login with valid credentials")
    @pytest.mark.smoke
    def test_login_success(self):
        """POST /restaurants/login with correct email/password should return 200
        with a JWT token in the response body under the 'token' key."""
        service = RestaurantService()
        payload = restaurant_login_payload("admin@feastrunner.com", "Restaurant123!")

        response = service.login(payload)

        self.using(response).assert_status_code_is(StatusCodes.OK)
        self.using(response).assert_schema(LOGIN_RESPONSE_SCHEMA)
        self.using(response).assert_response_has_key("token")

    @allure.story("Login with wrong password")
    def test_login_wrong_password(self):
        """POST /restaurants/login with incorrect password should return 401."""
        service = RestaurantService()
        payload = restaurant_login_payload("admin@feastrunner.com", "WrongPassword")

        response = service.login(payload)

        self.using(response).assert_status_code_is(StatusCodes.UNAUTHORIZED)

    @allure.story("Login with missing fields")
    def test_login_missing_fields(self):
        """POST /restaurants/login with empty body should return 400."""
        service = RestaurantService()

        response = service.login({})

        self.using(response).assert_status_code_is(StatusCodes.BAD_REQUEST)
