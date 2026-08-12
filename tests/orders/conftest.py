import pytest

from tests.factories.courier_factory import CourierFactory
from tests.factories.menu_item_factory import MenuItemsFactory
from tests.factories.address_factory import AddressFactory
from tests.factories.order_factory import OrderFactory

@pytest.fixture
def ready_order(
        courier_service,
        order_service,
        restaurant_service,
        menu_service,
        menu_items_service,
        address_service,
        customer_service
):
    """Provide a courier and an order in READY status."""
    #Create courier via factory
    courier_factory = CourierFactory(courier_service)
    courier = courier_factory.create()
    courier_id = courier["id"]

    #create order via factory
    order_factory = OrderFactory(order_service, address_service, customer_service, menu_items_service, menu_service, restaurant_service)
    order = order_factory.create()
    order_id = order["id"]
    customer_id = order["customer_id"]
    restaurant_id = order["restaurant_id"]


    response = order_service.get_by_id(order_id)
    data = response.json()
    status = data["status"]

    yield {
        "order_id": order_id,
        "customer_id": customer_id,
        "restaurant_id": restaurant_id,
        "status": status
    }

    # Cleanup
    order_factory.cleanup(order["id"])
    order_factory.cleanup_all(
        order["customer_id"],
        order["address_id"],
        order["menu_item_id"],
        order["menu_id"],
        order["restaurant_id"],
    )

    courier_factory.cleanup(courier["id"])

@pytest.fixture
def create_menu_item_and_address(menu_items_service, menu_service, restaurant_service,address_service, customer_service):
    """Provide a menu_item and customer with valid address."""
    menu_item_factory = MenuItemsFactory(menu_items_service, menu_service, restaurant_service)
    menu_item = menu_item_factory.create()
    restaurant_id = menu_item["restaurant_id"]
    menu_id = menu_item["menu_id"]
    menu_item_id = menu_item["id"]

    address_factory = AddressFactory(address_service, customer_service)
    address = address_factory.create()
    customer_id = address["customer_id"]
    address_id = address["id"]

    yield {
        "menu_item_id": menu_item_id,
        "restaurant_id": restaurant_id,
        "address_id": address_id,
        "customer_id": customer_id
    }

    #cleanup
    menu_item_factory.cleanup(menu_item_id)
    menu_item_factory.cleanup_all(menu_id, restaurant_id)

    address_factory.cleanup(address_id)
    address_factory.cleanup_all(customer_id)