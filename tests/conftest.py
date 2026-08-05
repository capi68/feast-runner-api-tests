"""Root conftest — shared fixtures for the entire test suite.

Fixtures at two scopes:
- session: auth tokens, service instances shared across all tests
- function: fresh data per individual test
"""

import pytest
from tests.config.settings import config
from tests.services.menu_items_service import MenuItemsService
from tests.services.restaurant_service import RestaurantService
from tests.services.customer_service import CustomerService
from tests.services.address_service import AddressService
from tests.services.order_service import OrderService
from tests.services.menu_service import MenuService
from tests.services.couriers_service import CouriersService
from tests.services.deliveries_service import DeliveryService
from tests.services.ratings_service import RatingService
from tests.payloads.restaurant_payloads import restaurant_login_payload
from tests.payloads.customers_payloads import customer_login_payload
from tests.payloads.courier_payloads import courier_login_payload
from tests.utils.logger import get_logger

logger = get_logger(__name__)


# ─────────────────────────────────────────────────────────────
#  SESSION SCOPE — shared across entire test run
# ─────────────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def restaurant_auth_token():
    """Authenticate with admin restaurant credentials and return JWT token.

    This fixture runs once per session. All tests share this token.
    """
    service = RestaurantService()
    payload = restaurant_login_payload(
        email=config.admin_restaurant_email,
        password=config.admin_restaurant_password,
    )
    response = service.login(payload)
    assert response.status_code == 200, f"Auth failed: {response.text}"
    token = response.json()["token"]
    logger.info("Session auth token obtained (restaurant)")
    return token


@pytest.fixture(scope="session")
def restaurant_service(restaurant_auth_token):
    """Provide an authenticated RestaurantService for the session."""
    return RestaurantService(token=restaurant_auth_token)


@pytest.fixture(scope="session")
def menu_service(restaurant_auth_token):
    """Provide an authenticated MenuService for the session."""
    return MenuService(token=restaurant_auth_token)

@pytest.fixture(scope="session")
def menu_items_service(restaurant_auth_token):
    """Provide an authenticated MenuItemsService for the session."""
    return  MenuItemsService(token=restaurant_auth_token)

@pytest.fixture(scope="session")
def delivery_service(restaurant_auth_token):
    """Provide an authenticated DeliveryService for the session."""
    return  DeliveryService(token=restaurant_auth_token)

# ─────────────────────────────────────────────────────────────
#  SESSION SCOPE — Customer services
# ─────────────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def customer_auth_token():
    """Authenticate with admin customer credentials and return JWT token.
    This fixture runs once per session. All tests share this token.
    """
    service = CustomerService()
    payload = customer_login_payload(
        email=config.admin_customer_email,
        password=config.admin_customer_password,
    )

    response = service.login(payload)
    assert response.status_code == 200, f"Auth failed: {response.text}"
    token = response.json()["token"]
    logger.info("Session auth token obtained (customer)")
    return token

@pytest.fixture(scope="session")
def customer_service(customer_auth_token):
    """Provide an authenticated CustomerService for the session."""
    return CustomerService(token=customer_auth_token)

@pytest.fixture(scope="session")
def address_service(customer_auth_token):
    """Provide an authenticated AddressService."""
    return  AddressService(customer_auth_token)

@pytest.fixture(scope="session")
def order_service(customer_auth_token):
    """Provide an authenticated AddressService."""
    return  OrderService(customer_auth_token)

@pytest.fixture(scope="session")
def rating_service(customer_auth_token):
    """Provide an authenticated RatingService"""
    return RatingService(customer_auth_token)


# ─────────────────────────────────────────────────────────────
#  SESSION SCOPE — Courier services
# ─────────────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def courier_auth_token():
    """Authenticate with admin courier credentials and return JWT token.

    This fixture runs once per session. All tests share this token.
    """
    service = CouriersService()
    payload = courier_login_payload(
        email=config.admin_courier_email,
        password=config.admin_courier_password,
    )
    response = service.login_courier(payload)
    assert response.status_code == 200, f"Auth failed: {response.text}"
    token = response.json()["token"]
    logger.info("Session auth token obtained (courier)")
    return token

@pytest.fixture(scope="session")
def courier_service(courier_auth_token):
    """Provide an authenticated CourierService"""
    return  CouriersService(courier_auth_token)
# ─────────────────────────────────────────────────────────────
#  FUNCTION SCOPE — fresh per test
# ─────────────────────────────────────────────────────────────

@pytest.fixture(scope="function")
def base_url():
    """Return the base API URL."""
    return config.base_url
