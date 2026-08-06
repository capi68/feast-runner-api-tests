"""Factory for creating order preconditions.
Creates an order via the API and returns the response data.
Used when an entity need an order for exist first.
"""
from tests.conftest import order_service
from tests.models.order_model import Order
from tests.models.order_item_model import OrderItem
from tests.factories.addresses_factory import AddressFactory
from tests.factories.menu_items_factory import MenuItemsFactory
from tests.services.menu_service import MenuService
from tests.services.menu_items_service import MenuItemsService
from tests.services.order_service import OrderService
from tests.services.restaurant_service import RestaurantService
from tests.services.address_service import AddressService
from tests.services.customer_service import CustomerService
from tests.payloads.order_payloads import order_create_payload
from tests.utils.constants import StatusCodes
from tests.utils.logger import get_logger

logger = get_logger(__name__)

class OrderFactory:
    """Creates Order preconditions via the API."""

    def __init__(
            self,
            order_service: OrderService,
            address_service: AddressService,
            customer_service: CustomerService,
            menu_items_service: MenuItemsService,
            menu_service: MenuService,
            restaurant_service: RestaurantService
    ):
        self._order_service = order_service
        self._address_service = address_service
        self._address_factory = AddressFactory(address_service, customer_service)
        self._menu_items_factory = MenuItemsFactory(menu_items_service, menu_service, restaurant_service)

    def create(self, address_id: int = None, menu_item_id: int = None, **overrides) -> dict:
        """Create a menu item with its dependencies and return the response JSON.

        Args:
            address_id: ID if existing address. If None, creates one.
            menu_item_id: ID of existing menu item. If None, creates one.
            **overrides: Any fields to override in the default payload.
        Returns:
            dict: The created order response from the API.
        """

        customer_id = None
        restaurant_id = None

        if menu_item_id is None:
            menu_item = self._menu_items_factory.create()
            menu_item_id = menu_item["id"]
            restaurant_id = menu_item["restaurant_id"]

        item = OrderItem(menu_item_id=menu_item_id,quantity=2)

        if address_id is None:
            address = self._address_factory.create()
        else:
            response = self._address_service.get_by_id(address_id)
            address = response.json()

        customer_id = address["customer_id"]
        address_id = address["id"]

        #Create order
        order = Order(items=[item], customer_id=customer_id, restaurant_id=restaurant_id, address_id=address_id)
        payload = order_create_payload(order, **overrides)
        response = self._order_service.create(payload)

        assert response.status_code == StatusCodes.CREATED
        data = response.json()

        return data

    def cleanup(self, order_id: int) -> None:
        """DELETE order created by this factory."""

        response = self._order_service.delete_order(order_id)

        if response.status_code == StatusCodes.OK:
            logger.info("Factory cleaned up order id=%s", order_id)
        else:
            logger.warning(
                "Factory cleanup failed for order id=%s, (%s): %s",
                order_id,
                response.status_code,
                response.text
            )

    def cleanup_all(self, customer_id: int, address_id: int, menu_item_id: int, menu_id: int, restaurant_id: int) -> None:
        """Clean up all resources created by this factory."""
        self._address_factory.cleanup(address_id)
        self._address_factory.cleanup_all(customer_id)

        self._menu_items_factory.cleanup(menu_item_id)
        self._menu_items_factory.cleanup_all(menu_id, restaurant_id)
