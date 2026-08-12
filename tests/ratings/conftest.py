import pytest

from tests.factories.order_factory import OrderFactory

@pytest.fixture
def delivered_order(
        menu_service,
        menu_items_service,
        restaurant_service,
        address_service,
        customer_service,
        order_service,
        rating_service
):
    """Provide a delivered order."""
    #Create order via factory
    factory = OrderFactory(order_service, address_service,customer_service,menu_items_service,menu_service,restaurant_service)
    order = factory.create()
    order_id = order["id"]
    order_service.update(order_id, {"status": "confirmed"})
    order_service.update(order_id, {"status": "preparing"})
    order_service.update(order_id, {"status": "ready"})
    order_service.update(order_id, {"status": "picked_up"})
    order_service.update(order_id, {"status": "delivered"})

    yield {
        "order_id": order_id
    }

    #cleanup
    factory.cleanup_all(
        order["customer_id"],
        order["address_id"],
        order["menu_item_id"],
        order["menu_id"],
        order["restaurant_id"],
    )