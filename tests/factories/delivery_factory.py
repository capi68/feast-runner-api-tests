"""Factory for creating delivery preconditions.
Creates a delivery via the API and returns the response data.
Used when an entity need a delivery for exist first.
"""
from tests.conftest import order_service
from tests.models.deliveries_models import Delivery
from tests.factories.courier_factory import CourierFactory
from tests.factories.order_factory import OrderFactory
from tests.payloads.deliveries_payloads import delivery_create_payload
from tests.services.couriers_service import CouriersService
from tests.services.deliveries_service import DeliveryService
from tests.services.menu_service import MenuService
from tests.services.menu_items_service import MenuItemsService
from tests.services.order_service import OrderService
from tests.services.restaurant_service import RestaurantService
from tests.services.address_service import AddressService
from tests.services.customer_service import CustomerService
from tests.utils.constants import StatusCodes
from tests.utils.logger import get_logger

logger = get_logger(__name__)

class DeliveryFactory:
    """Creates delivery preconditions via the API."""

    def __init__(self,
                 delivery_service: DeliveryService,
                 courier_service: CouriersService,
                 order_service: OrderService,
                 address_service: AddressService,
                 customer_service: CustomerService,
                 menu_items_service: MenuItemsService,
                 menu_service: MenuService,
                 restaurant_service: RestaurantService
                 ):
        self._service = delivery_service
        self._order_service = order_service
        self._order_factory = OrderFactory(
            order_service,
            address_service,
            customer_service,
            menu_items_service,
            menu_service,
            restaurant_service)
        self._courier_factory = CourierFactory(courier_service)

    def create(self, order_id: int = None, courier_id: int = None, **overrides) -> dict:
        """Create a delivery with its dependencies and return the response JSON.

        Args:
            order_id: ID if existing order. If None, creates one.
            courier_id: ID of existing courier. If None, creates one.
            **overrides: Any fields to override in the default payload.
        Returns:
            dict: The created order response from the API.
        """

        #Create courier via Factory
        if courier_id is None:
            courier = self._courier_factory.create()
            courier_id = courier["id"]

        #Create order via Factory
        if order_id is None:
            order = self._order_factory.create()
            self._order_service.update(order["id"], {"status": "confirmed"})
            self._order_service.update(order["id"], {"status": "preparing"})
            self._order_service.update(order["id"], {"status": "ready"})
        else:
            response = self._order_service.get_by_id(order_id)
            order = response.json()


        order_id = order["id"]
        customer_id = order["customer_id"]
        address_id = order["address_id"]
        menu_item_id = order["menu_item_id"]
        menu_id = order["menu_id"]
        restaurant_id = order["restaurant_id"]

        #create delivery
        delivery = Delivery(order_id=order_id, courier_id=courier_id)
        payload = delivery_create_payload(delivery, **overrides)
        create_response = self._service.create(payload)

        assert create_response.status_code == StatusCodes.CREATED
        data = create_response.json()
        data["customer_id"] = customer_id
        data["address_id"] = address_id
        data["menu_item_id"] = menu_item_id
        data["menu_id"] = menu_id
        data["restaurant_id"] = restaurant_id

        return  data

    def cleanup(self, delivery_id: int) -> None:
        """DELETE delivery created by this factory."""
        response = self._service.update(delivery_id, {"status": "failed"})

        if response.status_code == StatusCodes.OK:
            logger.info("Factory cleaned up delivery id=%s", delivery_id)
        else:
            logger.warning(
                "Factory cleanup failed for delivery =%s (%s): s%",
                delivery_id,
                response.status_code,
                response.text
            )
    def cleanup_all(self,order_id: int,courier_id: int, customer_id: int, address_id: int, menu_item_id: int, menu_id: int, restaurant_id: int) -> None:
        """Clean up all resources created by this factory."""
        self._order_service.update(order_id, {"status": "delivered"})

        self._order_factory.cleanup_all(customer_id, address_id,menu_item_id,menu_id,restaurant_id)
        self._courier_factory.cleanup(courier_id)




