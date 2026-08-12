import pytest

from tests.factories.courier_factory import CourierFactory
from tests.factories.delivery_factory import DeliveryFactory
from tests.factories.order_factory import OrderFactory

@pytest.fixture
def ready_order_with_courier(
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
    order_service.update(order["id"], {"status": "confirmed"})
    order_service.update(order["id"], {"status": "preparing"})
    order_service.update(order["id"], {"status": "ready"})

    yield {
        "courier": courier,
        "order": order,
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
def ready_assigned_delivery(
        delivery_service,
        courier_service,
        order_service,
        address_service,
        customer_service,
        menu_items_service,
        menu_service,
        restaurant_service
):
    """Provide a delivery in ASSIGNED status."""
    #Create delivery assigned via Factory
    factory = DeliveryFactory(delivery_service,
                              courier_service,
                              order_service,
                              address_service,
                              customer_service,
                              menu_items_service,
                              menu_service,
                              restaurant_service)
    delivery = factory.create()
    delivery_id = delivery["id"]

    yield {
        "delivery": delivery
    }

    #Cleanup
    current_delivery = delivery_service.get_by_id(delivery_id).json()
    if current_delivery["status"] not in ("failed", "delivered"):
        factory.cleanup(delivery_id)

    factory.cleanup_all(
        delivery["order_id"],
        delivery["courier_id"],
        delivery["customer_id"],
        delivery["address_id"],
        delivery["menu_item_id"],
        delivery["menu_id"],
        delivery["restaurant_id"],
    )


