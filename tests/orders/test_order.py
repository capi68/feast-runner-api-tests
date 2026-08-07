"""test for orders API"""

import allure
import pytest

from tests.base.base_assertions import BaseAssertions
from tests.models.order_model import Order
from tests.models.order_item_model import OrderItem
from tests.payloads.order_payloads import order_create_payload,order_update_payload
from tests.payloads.menu_items_payloads import menu_item_update_payload
from tests.factories.restaurant_factory import RestaurantFactory
from tests.factories.menu_item_factory import MenuItemsFactory
from tests.factories.address_factory import AddressFactory
from tests.factories.menu_factory import MenuFactory
from tests.factories.order_factory import OrderFactory
from tests.schemas.order_schemas import ORDER_RESPONSE_SCHEMA, ORDER_LIST_SCHEMA, ORDER_GET_BY_ID_SCHEMA
from tests.utils.constants import StatusCodes
from tests.utils.logger import get_logger

logger = get_logger(__name__)


@pytest.mark.orders
@allure.feature("Orders")
class TestOrdersCreation(BaseAssertions):
    """Tests for POST /orders - order registration.

    validates that the order creation endpoint correctly handles
    valid input. missing fields, invalid data.
    """

    @allure.story("Create order successfully")
    def test_create_order_success(
            self,menu_service,menu_items_service,restaurant_service,address_service,customer_service,order_service):
        """POST /orders - with valid data and required fields should return 201.
        and a response matching with Order Schema.
        """
        with allure.step("Create valid menu item using factory"):
            menu_item_factory = MenuItemsFactory(menu_items_service, menu_service, restaurant_service)
            menu_item = menu_item_factory.create()
            restaurant_id = menu_item["restaurant_id"]
            menu_id = menu_item["menu_id"]
            address_factory = AddressFactory(address_service, customer_service)
            address = address_factory.create()
            customer_id = address["customer_id"]
            address_id = address["id"]

        with allure.step("create a valid payload with customer_id, restaurant_id, address_id"):
            order_item = OrderItem(menu_item_id=menu_item["id"], quantity=3)

            order = Order(customer_id=customer_id,restaurant_id=restaurant_id,address_id=address_id,items=[order_item])
            service = order_service
            payload = order_create_payload(order)

        with allure.step("POST /order request"):
            response = service.create(payload)
            data = response.json()

            logger.info("DATA data=%s", data)

        with allure.step("Validate response."):
            self.using(response).assert_status_code_is(StatusCodes.CREATED)
            self.using(response).assert_schema(ORDER_RESPONSE_SCHEMA)
            self.using(response).assert_response_has_key_value("customer_id", customer_id)
            self.using(response).assert_response_has_key_value("restaurant_id", restaurant_id)
            self.using(response).assert_response_has_key_value("address_id", address_id)

            #CLEANUP
            order_service.update(data["id"], {"status": "cancelled"})
            menu_item_factory.cleanup_all(menu_id, restaurant_id)

            address_factory.cleanup(address_id)
            address_factory.cleanup_all(customer_id)


    @allure.story("Create Order with non-existent restaurant_id")
    def test_create_order_nonexistent_restaurant(
            self,menu_service,menu_items_service,restaurant_service,address_service,customer_service,order_service):
        """POST /orders - with non-existent restaurant_id must return 404.
        and message.
        """
        #Create menu item / menu / restaurant / address / customer via factory
        menu_item_factory = MenuItemsFactory(menu_items_service, menu_service, restaurant_service)
        menu_item = menu_item_factory.create()
        address_factory = AddressFactory(address_service, customer_service)
        address =  address_factory.create()
        address_id = address["id"]
        customer_id = address["customer_id"]

        #Create Order Item
        order_item = OrderItem(menu_item_id=menu_item["id"], quantity=1)

        #Create Order
        order = Order(
            customer_id=customer_id,
            restaurant_id=999999,
            address_id=address_id,
            items=[order_item])

        #Create payload
        service = order_service
        payload = order_create_payload(order)

        response = service.create(payload)
        data = response.json()

        self.using(response).assert_status_code_is(StatusCodes.NOT_FOUND)
        self.using(response).assert_response_has_key("message")

        #CLEANUP
        menu_item_factory.cleanup_all(menu_item["menu_id"], menu_item["restaurant_id"])

        address_factory.cleanup(address_id)
        address_factory.cleanup_all(customer_id)


    @allure.story("Create Order with non-existent customer_id")
    def test_create_order_nonexistent_customer_id(
            self,
            menu_service,
            menu_items_service,
            restaurant_service,
            address_service,
            customer_service,
            order_service
    ):
        """POST /orders - with non-existent customer_id must return 404.
        and message.
        """
        #Create menu item / menu / restaurant / address / customer via factory
        menu_item_factory = MenuItemsFactory(menu_items_service, menu_service, restaurant_service)
        menu_item = menu_item_factory.create()
        restaurant_id = menu_item["restaurant_id"]
        address_factory = AddressFactory(address_service, customer_service)
        address =  address_factory.create()
        address_id = address["id"]
        customer_id = address["customer_id"]


        #Create Order Item
        order_item = OrderItem(menu_item_id=menu_item["id"], quantity=1)

        #Create Order
        order = Order(
            customer_id=999999,
            restaurant_id=restaurant_id,
            address_id=address_id,
            items=[order_item]
        )

        #Create payload
        service = order_service
        payload = order_create_payload(order)

        response = service.create(payload)
        data = response.json()

        self.using(response).assert_status_code_is(StatusCodes.NOT_FOUND)
        self.using(response).assert_response_has_key("message")

        #CLEANUP
        menu_item_factory.cleanup(menu_item["id"])
        menu_item_factory.cleanup_all(menu_item["menu_id"], menu_item["restaurant_id"])

        address_factory.cleanup(address_id)
        address_factory.cleanup_all(customer_id)


    @allure.story("Create Order address not belong customer")
    def test_create_order_address_not_belong_customer(
            self,
            menu_service,
            menu_items_service,
            restaurant_service,
            address_service,
            customer_service,
            order_service
    ):
        """POST /orders - with address not belong to the specified customer
        return 400 and message.
        """
        #Create menu item / menu / restaurant / address / customer via factory
        menu_item_factory = MenuItemsFactory(menu_items_service, menu_service, restaurant_service)
        menu_item = menu_item_factory.create()
        restaurant_id = menu_item["restaurant_id"]
        address_factory = AddressFactory(address_service, customer_service)

        #address
        address =  address_factory.create()
        address_id = address["id"]
        customer_id = address["customer_id"]

        #Create Order Item
        order_item = OrderItem(menu_item_id=menu_item["id"], quantity=1)

        #Create Order
        order = Order(
            customer_id=customer_id,
            restaurant_id=restaurant_id,
            address_id=999999,
            items=[order_item]
        )

        #Create payload
        service = order_service
        payload = order_create_payload(order)

        response = service.create(payload)

        self.using(response).assert_status_code_is(StatusCodes.BAD_REQUEST)
        self.using(response).assert_response_has_key("message")

        #CLEANUP
        menu_item_factory.cleanup(menu_item["id"])
        menu_item_factory.cleanup_all(menu_item["menu_id"], menu_item["restaurant_id"])

        address_factory.cleanup(address_id)
        address_factory.cleanup_all(customer_id)



    @allure.story("Create Order without order item")
    def test_create_order_without_order_item(
            self,
            menu_service,
            menu_items_service,
            restaurant_service,
            address_service,
            customer_service,
            order_service
    ):
        """POST /orders - without order item should return 400 and message.
        """
        #Create menu item / menu / restaurant / address / customer via factory
        menu_item_factory = MenuItemsFactory(menu_items_service, menu_service, restaurant_service)
        menu_item = menu_item_factory.create()
        restaurant_id = menu_item["restaurant_id"]
        address_factory = AddressFactory(address_service, customer_service)

        #address
        address =  address_factory.create()
        address_id = address["id"]
        customer_id = address["customer_id"]

        #Create  Order Item
        order_item = OrderItem(menu_item_id=menu_item["id"], quantity=0)

        #Create Order
        order = Order(
            customer_id=customer_id,
            restaurant_id=restaurant_id,
            address_id=address_id,
            items=[order_item]
        )

        #Create payload
        service = order_service
        payload = order_create_payload(order)

        response = service.create(payload)
        data = response.json()

        self.using(response).assert_status_code_is(StatusCodes.BAD_REQUEST)
        self.using(response).assert_response_has_key("message")

        #CLEANUP
        menu_item_factory.cleanup(menu_item["id"])
        menu_item_factory.cleanup_all(menu_item["menu_id"], menu_item["restaurant_id"])

        address_factory.cleanup(address_id)
        address_factory.cleanup_all(customer_id)


    @allure.story("Create Order with menu_item not belong to the same restaurant")
    def test_create_order_menu_items_not_belong_restaurant(
            self,
            menu_service,
            menu_items_service,
            restaurant_service,
            address_service,
            customer_service,
            order_service
    ):
        """POST /orders - with order menu item not belong to the same restaurant
        should return 400 and message.
        """
        #Create menu item / menu / restaurant / address / customer via factory
        menu_item_factory = MenuItemsFactory(menu_items_service, menu_service, restaurant_service)

        #menu item 1
        menu_item_1 = menu_item_factory.create()
        restaurant_id_1 = menu_item_1["restaurant_id"]

        #menu item 2
        menu_item_2 =menu_item_factory.create()
        restaurant_id_2 = menu_item_2["restaurant_id"]

        #address
        address_factory = AddressFactory(address_service, customer_service)
        address =  address_factory.create()
        address_id = address["id"]
        customer_id = address["customer_id"]

        #Create  Order Item
        order_item = OrderItem(menu_item_id=menu_item_2["id"], quantity=3)

        #Create Order
        order = Order(
            customer_id=customer_id,
            restaurant_id=restaurant_id_1,
            address_id=address_id,
            items=[order_item]
        )

        #Create payload
        service = order_service
        payload = order_create_payload(order)

        response = service.create(payload)
        data = response.json()

        self.using(response).assert_status_code_is(StatusCodes.BAD_REQUEST)
        self.using(response).assert_response_has_key("message")

        #CLEANUP
        menu_item_factory.cleanup(menu_item_1["id"])
        menu_item_factory.cleanup_all(menu_item_1["menu_id"], menu_item_1["restaurant_id"])

        menu_item_factory.cleanup(menu_item_2["id"])
        menu_item_factory.cleanup_all(menu_item_2["menu_id"], menu_item_2["restaurant_id"])

        address_factory.cleanup(address_id)
        address_factory.cleanup_all(customer_id)


    @allure.story("Create Order with not available menu item")
    def test_create_order_not_available_menu_item(
            self,
            menu_service,
            menu_items_service,
            restaurant_service,
            address_service,
            customer_service,
            order_service
    ):
        """POST /orders - with not available menu item
        should return 400 and message.
        """
        #Create menu item / menu / restaurant / address / customer via factory
        menu_item_factory = MenuItemsFactory(menu_items_service, menu_service, restaurant_service)

        #menu item
        menu_item = menu_item_factory.create()
        restaurant_id = menu_item["restaurant_id"]
        menu_items_service.update(menu_item["id"], {"is_available": False})

        #address
        address_factory = AddressFactory(address_service, customer_service)
        address =  address_factory.create()
        address_id = address["id"]
        customer_id = address["customer_id"]

        #Create  Order Item
        order_item = OrderItem(menu_item_id=menu_item["id"], quantity=3)

        #Create Order
        order = Order(
            customer_id=customer_id,
            restaurant_id=restaurant_id,
            address_id=address_id,
            items=[order_item]
        )

        #Create payload
        service = order_service
        payload = order_create_payload(order)
        response = service.create(payload)
        data = response.json()

        self.using(response).assert_status_code_is(StatusCodes.BAD_REQUEST)
        self.using(response).assert_response_has_key("message")

        #CLEANUP
        menu_item_factory.cleanup(menu_item["id"])
        menu_item_factory.cleanup_all(menu_item["menu_id"], menu_item["restaurant_id"])

        address_factory.cleanup(address_id)
        address_factory.cleanup_all(customer_id)


    @allure.story("Create Order below minimum restaurant amount")
    def test_create_order_below_minimum_order_amount(
            self,
            menu_service,
            menu_items_service,
            restaurant_service,
            address_service,
            customer_service,
            order_service
    ):
        """POST /orders - with order below minimum restaurant amount
        should return 400 and message.
        """
        #Create menu item / menu / restaurant / address / customer via factory
        menu_item_factory = MenuItemsFactory(menu_items_service, menu_service, restaurant_service)

        #menu item
        menu_item = menu_item_factory.create()
        restaurant_id = menu_item["restaurant_id"]

        #address
        address_factory = AddressFactory(address_service, customer_service)
        address =  address_factory.create()
        address_id = address["id"]
        customer_id = address["customer_id"]

        #Create  Order Item
        order_item = OrderItem(menu_item_id=menu_item["id"], quantity=1)

        #Create Order
        order = Order(
            customer_id=customer_id,
            restaurant_id=restaurant_id,
            address_id=address_id,
            items=[order_item]
        )

        #Create payload
        service = order_service
        payload = order_create_payload(order)

        response = service.create(payload)
        data = response.json()


        self.using(response).assert_status_code_is(StatusCodes.BAD_REQUEST)
        self.using(response).assert_response_has_key("message")

        #CLEANUP
        menu_item_factory.cleanup(menu_item["id"])
        menu_item_factory.cleanup_all(menu_item["menu_id"], menu_item["restaurant_id"])

        address_factory.cleanup(address_id)
        address_factory.cleanup_all(customer_id)


    @allure.story("Estimate delivery time of an order")
    def test_create_order_estimated_delivery_time(
            self,
            menu_service,
            menu_items_service,
            restaurant_service,
            address_service,
            customer_service,
            order_service
    ):
        """POST /orders - Estimate delivery time of an order
         and verify compliance with standards.
        should return 201, and a response matching with Order Response.
        """
        #Create menu item / menu / restaurant / address / customer via factory
        menu_item_factory = MenuItemsFactory(menu_items_service, menu_service, restaurant_service)

        #menu item
        menu_item = menu_item_factory.create()
        restaurant_id = menu_item["restaurant_id"]
        preparation_time_minutes =menu_item["preparation_time_minutes"]

        #address
        address_factory = AddressFactory(address_service, customer_service)
        address =  address_factory.create()
        address_id = address["id"]
        customer_id = address["customer_id"]

        #Create  Order Item
        order_item = OrderItem(menu_item_id=menu_item["id"], quantity=3)

        #Create Order
        order = Order(
            customer_id=customer_id,
            restaurant_id=restaurant_id,
            address_id=address_id,
            items=[order_item]
        )

        #Create payload
        service = order_service
        payload = order_create_payload(order)

        response = service.create(payload)
        data = response.json()
        estimated_delivery_minutes = data["estimated_delivery_minutes"]

        self.using(response).assert_status_code_is(StatusCodes.CREATED)
        assert estimated_delivery_minutes == preparation_time_minutes + 20

        #CLEANUP
        service.delete_order(data["id"])
        menu_item_factory.cleanup(menu_item["id"])
        menu_item_factory.cleanup_all(menu_item["menu_id"], menu_item["restaurant_id"])

        address_factory.cleanup(address_id)
        address_factory.cleanup_all(customer_id)


    @allure.story("Calculate total amount from all order items")
    def test_create_order_calculates_total_amount(
            self,
            menu_service,
            menu_items_service,
            restaurant_service,
            address_service,
            customer_service,
            order_service
    ):
        """POST /orders - total_amount must equal the sum of
        (unit_price × quantity) for all items.
        should return 201, and a response matching with Order Response.
        """
        #Create menu item / menu / restaurant / address / customer via factory
        menu_item_factory = MenuItemsFactory(menu_items_service, menu_service, restaurant_service)

        #menu item 1
        menu_item_1 = menu_item_factory.create()
        restaurant_id = menu_item_1["restaurant_id"]
        item_price_1 = menu_item_1["price"]

        #menu item 2
        menu_item_2 = menu_item_factory.create(
            menu_id=menu_item_1["menu_id"],
            name="Pepperoni Pizza",
            description="Classic pepperoni pizza with mozzarella cheese, tomato sauce, crispy pepperoni slices, and oregano.",
            price=10.00,
            category="appetizer",
            preparation_time_minutes=18
        )
        item_price_2 = menu_item_2["price"]

        #address
        address_factory = AddressFactory(address_service, customer_service)
        address =  address_factory.create()
        address_id = address["id"]
        customer_id = address["customer_id"]

        #Create  Order Items
        order_item_1 = OrderItem(menu_item_id=menu_item_1["id"], quantity=3)
        order_item_2 = OrderItem(menu_item_id=menu_item_2["id"], quantity=1)

        #Create Order
        order = Order(
            customer_id=customer_id,
            restaurant_id=restaurant_id,
            address_id=address_id,
            items=[order_item_1, order_item_2]
        )

        #Create payload
        service = order_service
        payload = order_create_payload(order)

        response = service.create(payload)
        data = response.json()
        total_amount = data["total_amount"]

        total_expected = item_price_1 * order_item_1.quantity + item_price_2 * order_item_2.quantity

        self.using(response).assert_status_code_is(StatusCodes.CREATED)
        assert total_amount == total_expected

        #CLEANUP
        service.update(data["id"], {"status": "cancelled"})
        menu_item_factory.cleanup(menu_item_1["id"])
        menu_item_factory.cleanup(menu_item_2["id"])
        menu_item_factory.cleanup_all(menu_item_1["menu_id"], menu_item_1["restaurant_id"])

        address_factory.cleanup(address_id)
        address_factory.cleanup_all(customer_id)


    @allure.story("Unit price remains in order")
    def test_create_order_unit_price_remains(
            self,
            menu_service,
            menu_items_service,
            restaurant_service,
            address_service,
            customer_service,
            order_service
    ):
        """POST /orders - unit price remains in order.
        should return 201, and a response matching with Order Response.
        """
        #Create menu item / menu / restaurant / address / customer via factory
        menu_item_factory = MenuItemsFactory(menu_items_service, menu_service, restaurant_service)

        #menu item
        menu_item = menu_item_factory.create()
        restaurant_id = menu_item["restaurant_id"]
        item_price = menu_item["price"]

        #address
        address_factory = AddressFactory(address_service, customer_service)
        address =  address_factory.create()
        address_id = address["id"]
        customer_id = address["customer_id"]

        #Create  Order Items
        order_item = OrderItem(menu_item_id=menu_item["id"], quantity=2)


        #Create Order
        order = Order(
            customer_id=customer_id,
            restaurant_id=restaurant_id,
            address_id=address_id,
            items=[order_item]
        )

        #Create payload
        service = order_service
        payload = order_create_payload(order)

        response = service.create(payload)
        data = response.json()


        #modified price
        update_payload = menu_item_update_payload(price=15)
        update_response = menu_items_service.update(menu_item["id"], update_payload)
        self.using(update_response).assert_status_code_is(StatusCodes.OK)

        #Confirm unit price in order

        confirm_response = order_service.get_by_id(data["id"])
        confirm_data = confirm_response.json()

        self.using(confirm_response).assert_status_code_is(StatusCodes.OK)
        assert confirm_data["items"][0]["unit_price"] == item_price

        #CLEANUP
        service.delete_order(data["id"])
        menu_item_factory.cleanup(menu_item["id"])
        menu_item_factory.cleanup_all(menu_item["menu_id"], menu_item["restaurant_id"])

        address_factory.cleanup(address_id)
        address_factory.cleanup_all(customer_id)


@pytest.mark.orders
@allure.feature("Orders")
class TestOrderRetrieval(BaseAssertions):
    """Tests GET/orders - GET/orders?customer_id= - GET/orders?restaurant_id= -
    GET/orders?status= - GET/orders/<id> - GET/orders/<id>/items
    """

    @allure.story("Get List all")
    def test_get_list(
            self,
            menu_service,
            menu_items_service,
            restaurant_service,
            address_service,
            customer_service,
            order_service
    ):
        """GET /orders - should return a list of orders .
        and 200, and a response matching with Order List Response.
        """

        response = order_service.list()

        self.using(response).assert_status_code_is(StatusCodes.OK)
        self.using(response).assert_schema(ORDER_LIST_SCHEMA)


    @allure.story("Get order by ID.")
    def test_get_by_id(
            self,
            menu_service,
            menu_items_service,
            restaurant_service,
            address_service,
            customer_service,
            order_service
    ):
        """GET /orders/<id> - should return an order by id.
        and 200, and a response matching with Order Schema.
        """
        #Create order via factory
        factory = OrderFactory(order_service, address_service,customer_service,menu_items_service,menu_service,restaurant_service)
        order = factory.create()
        order_id = order["id"]

        #GET response
        get_response = order_service.get_by_id(order_id)

        self.using(get_response).assert_status_code_is(StatusCodes.OK)
        self.using(get_response).assert_schema(ORDER_GET_BY_ID_SCHEMA)


        #CLEANUP
        factory.cleanup(order_id)
        factory.cleanup_all(order["customer_id"],order["address_id"],order["menu_item_id"],order["menu_id"],order["restaurant_id"])


    @allure.story("Get order nonexistent id.")
    def test_get_nonexistent_id(self, order_service):
        """GET /orders/999999 - should return 404, and message.
        """
        #GET response
        get_response = order_service.get_by_id(999999)

        self.using(get_response).assert_status_code_is(StatusCodes.NOT_FOUND)
        self.using(get_response).assert_response_has_key("message")


    @allure.story("Get items in specific order by id.")
    def test_get_items_specific_order(
            self,
            menu_service,
            menu_items_service,
            restaurant_service,
            address_service,
            customer_service,
            order_service
    ):
        """GET/orders/<id>/items - should return order items in specific order by id.
        and 200.
        """
        #Create order via factory
        factory = OrderFactory(order_service, address_service,customer_service,menu_items_service,menu_service,restaurant_service)
        order = factory.create()
        order_id = order["id"]

        #GET response
        get_response = order_service.get_items_by_order(order_id)

        self.using(get_response).assert_status_code_is(StatusCodes.OK)

        #CLEANUP
        factory.cleanup(order_id)
        factory.cleanup_all(order["customer_id"],order["address_id"],order["menu_item_id"],order["menu_id"],order["restaurant_id"])


    @allure.story("Get orders filtered by customer_id.")
    def test_get_orders_by_customer_id(
            self,
            menu_service,
            menu_items_service,
            restaurant_service,
            address_service,
            customer_service,
            order_service
    ):
        """GET/orders?customer_id= - should return orders for specific customer_id.
        and 200.
        """
        #Create order via factory
        factory = OrderFactory(order_service, address_service,customer_service,menu_items_service,menu_service,restaurant_service)
        order = factory.create()
        order_id = order["id"]

        #GET response
        get_response = order_service.list(customer_id=order["customer_id"])
        get_data = get_response.json()


        self.using(get_response).assert_status_code_is(StatusCodes.OK)
        assert all(order["customer_id"] == order["customer_id"] for order in get_data)

        #CLEANUP
        factory.cleanup(order_id)
        factory.cleanup_all(order["customer_id"],order["address_id"],order["menu_item_id"],order["menu_id"],order["restaurant_id"])


    @allure.story("Get orders filtered by restaurant_id.")
    def test_get_orders_by_restaurant(
            self,
            menu_service,
            menu_items_service,
            restaurant_service,
            address_service,
            customer_service,
            order_service
    ):
        """GET/orders?restaurant_id= - should return orders for specific restaurant_id.
        and 200.
        """
        #Create order via factory
        factory = OrderFactory(order_service, address_service,customer_service,menu_items_service,menu_service,restaurant_service)
        order = factory.create()
        order_id = order["id"]

        #GET response
        get_response = order_service.list(restaurant_id=order["restaurant_id"])
        get_data = get_response.json()


        self.using(get_response).assert_status_code_is(StatusCodes.OK)
        assert all(order["restaurant_id"] == order["restaurant_id"] for order in get_data)

        #CLEANUP
        factory.cleanup(order_id)
        factory.cleanup_all(order["customer_id"],order["address_id"],order["menu_item_id"],order["menu_id"],order["restaurant_id"])


    @allure.story("Get orders filtered by status.")
    def test_get_orders_by_status(
            self,
            menu_service,
            menu_items_service,
            restaurant_service,
            address_service,
            customer_service,
            order_service
    ):
        """GET/orders?status= - should return orders for specific status.
        and 200.
        """
        #Create order via factory
        factory = OrderFactory(order_service, address_service,customer_service,menu_items_service,menu_service,restaurant_service)
        order = factory.create()
        order_id = order["id"]
        order_service.update(order_id, {"status": "confirmed"})

        #GET response filtered by status
        get_response = order_service.list(status="confirmed")
        get_data = get_response.json()


        self.using(get_response).assert_status_code_is(StatusCodes.OK)
        assert all(order["status"] == "confirmed" for order in get_data)

        #CLEANUP
        factory.cleanup(order_id)
        factory.cleanup_all(order["customer_id"],order["address_id"],order["menu_item_id"],order["menu_id"],order["restaurant_id"])


@pytest.mark.orders
@allure.feature("Orders")
class TestUpdateOrder(BaseAssertions):
    """Tests PUT /orders/<id>"""


    @allure.story("Update Order Successfully")
    def test_update_order_success(
            self,
            menu_service,
            menu_items_service,
            restaurant_service,
            address_service,
            customer_service,
            order_service
    ):
        """PUT /orders/<id> - should update the provided fields and return 200.
        Only the specified fields change; others remain untouched.
        """
        #Create order via factory
        factory = OrderFactory(order_service, address_service,customer_service,menu_items_service,menu_service,restaurant_service)
        order = factory.create()
        order_id = order["id"]

        #Update
        response = order_service.update(order_id, {"status": "cancelled"})
        update_data = response.json()

        self.using(response).assert_status_code_is(StatusCodes.OK)
        self.using(response).assert_response_has_key_value("status", "cancelled")
        self.using(response).assert_response_has_key_value("restaurant_id", order["restaurant_id"])
        self.using(response).assert_response_has_key_value("address_id", order["address_id"])
        self.using(response).assert_response_has_key_value("total_amount", order["total_amount"])

        #CLEANUP
        factory.cleanup_all(order["customer_id"],order["address_id"],order["menu_item_id"],order["menu_id"],order["restaurant_id"])

class TestOrderStatusMachine(BaseAssertions):
    """Tests for order status transitions
    (placed → confirmed → preparing → ready → picked_up → delivered).

    The state machine rules:
    - placed → confirmed, cancelled
    - confirmed → preparing, cancelled
    - preparing → ready
    - ready → picked_up
    - picked_up → delivered
    - cancelled → terminal
    - delivered → cancelled
    """

    @pytest.mark.parametrize("new_status", ["confirmed", "cancelled"])
    @allure.story("Update Order correctly status machine starting in placed")
    def test_status_transition_from_placed(
            self,
            new_status,
            menu_service,
            menu_items_service,
            restaurant_service,
            address_service,
            customer_service,
            order_service
    ):
        """PUT /orders/<id> - should update status  and return 200.
        correctly options:

        -placed to confirmed or cancelled.
        """
        #Create order via factory
        factory = OrderFactory(order_service, address_service,customer_service,menu_items_service,menu_service,restaurant_service)
        order = factory.create()
        order_id = order["id"]

        #Update
        update_payload = order_update_payload(status=new_status)
        response = order_service.update(order_id, update_payload)

        self.using(response).assert_status_code_is(StatusCodes.OK)
        self.using(response).assert_response_has_key_value("status", new_status)

        #CLEANUP
        if new_status == "confirmed":
            factory.cleanup(order_id)
        factory.cleanup_all(order["customer_id"],order["address_id"],order["menu_item_id"],order["menu_id"],order["restaurant_id"])


    @pytest.mark.parametrize("new_status", ["preparing", "ready", "picked_up", "delivered"])
    @allure.story("Update Order incorrect status machine starting in placed")
    def test_status_invalid_transition_from_placed(
            self,
            new_status,
            menu_service,
            menu_items_service,
            restaurant_service,
            address_service,
            customer_service,
            order_service
    ):
        """PUT /orders/<id> - should return 400.
        correctly options:

        -placed to confirmed or cancelled.
        """
        #Create order via factory
        factory = OrderFactory(order_service, address_service,customer_service,menu_items_service,menu_service,restaurant_service)
        order = factory.create()
        order_id = order["id"]

        #Update
        update_payload = order_update_payload(status=new_status)
        response = order_service.update(order_id, update_payload)
        data = response.json()

        self.using(response).assert_status_code_is(StatusCodes.BAD_REQUEST)
        self.using(response).assert_response_has_key("message")

        #CLEANUP
        factory.cleanup(order_id)
        factory.cleanup_all(order["customer_id"],order["address_id"],order["menu_item_id"],order["menu_id"],order["restaurant_id"])


    @pytest.mark.parametrize("new_status", ["preparing", "cancelled"])
    @allure.story("Update Order correctly status machine starting in confirmed")
    def test_status_transition_from_confirmed(
            self,
            new_status,
            menu_service,
            menu_items_service,
            restaurant_service,
            address_service,
            customer_service,
            order_service
    ):
        """PUT /orders/<id> - should update status  and return 200.
        correctly options:

        -confirmed to preparing or cancelled.
        """
        #Create order via factory
        factory = OrderFactory(order_service, address_service,customer_service,menu_items_service,menu_service,restaurant_service)
        order = factory.create()
        order_id = order["id"]
        order_service.update(order_id, {"status": "confirmed"})

        #Update
        update_payload = order_update_payload(status=new_status)
        response = order_service.update(order_id, update_payload)

        self.using(response).assert_status_code_is(StatusCodes.OK)
        self.using(response).assert_response_has_key_value("status", new_status)

        #CLEANUP
        if new_status == "preparing":
            factory.cleanup(order_id)
        factory.cleanup_all(order["customer_id"],order["address_id"],order["menu_item_id"],order["menu_id"],order["restaurant_id"])


    @pytest.mark.parametrize("new_status", ["ready", "picked_up", "delivered"])
    @allure.story("Update Order incorrect status machine starting in confirmed")
    def test_status_invalid_transition_from_confirmed(
            self,
            new_status,
            menu_service,
            menu_items_service,
            restaurant_service,
            address_service,
            customer_service,
            order_service
    ):
        """PUT /orders/<id> - should return 400.
        correctly options:

        -confirmed to preparing or cancelled.
        """
        #Create order via factory
        factory = OrderFactory(order_service, address_service,customer_service,menu_items_service,menu_service,restaurant_service)
        order = factory.create()
        order_id = order["id"]
        order_service.update(order_id, {"status": "confirmed"})

        #Update
        update_payload = order_update_payload(status=new_status)
        response = order_service.update(order["id"], update_payload)
        data = response.json()

        self.using(response).assert_status_code_is(StatusCodes.BAD_REQUEST)
        self.using(response).assert_response_has_key("message")

        #CLEANUP
        factory.cleanup(order_id)
        factory.cleanup_all(order["customer_id"],order["address_id"],order["menu_item_id"],order["menu_id"],order["restaurant_id"])


    @allure.story("Update Order correctly status machine starting in preparing")
    def test_status_transition_from_preparing(
            self,
            menu_service,
            menu_items_service,
            restaurant_service,
            address_service,
            customer_service,
            order_service
    ):
        """PUT /orders/<id> - should update status  and return 200.
        correctly options:

        -preparing to ready
        """
        #Create order via factory
        factory = OrderFactory(order_service, address_service,customer_service,menu_items_service,menu_service,restaurant_service)
        order = factory.create()
        order_id = order["id"]
        order_service.update(order_id, {"status": "confirmed"})
        order_service.update(order_id, {"status": "preparing"})

        #Update
        update_payload = order_update_payload(status="ready")
        response = order_service.update(order["id"], update_payload)
        data = response.json()

        self.using(response).assert_status_code_is(StatusCodes.OK)
        self.using(response).assert_response_has_key_value("status", "ready")

        #CLEANUP
        order_service.update(order_id, {"status": "picked_up"})
        order_service.update(order_id, {"status": "delivered"})
        factory.cleanup_all(order["customer_id"],order["address_id"],order["menu_item_id"],order["menu_id"],order["restaurant_id"])


    @pytest.mark.parametrize("new_status", [ "placed", "picked_up", "delivered"])
    @allure.story("Update Order incorrect status machine starting in preparing")
    def test_status_invalid_transition_from_preparing(
            self,
            new_status,
            menu_service,
            menu_items_service,
            restaurant_service,
            address_service,
            customer_service,
            order_service
    ):
        """PUT /orders/<id> - should return 400.
        correctly options:

        -preparing to ready.
        """
        #Create order via factory
        factory = OrderFactory(order_service, address_service,customer_service,menu_items_service,menu_service,restaurant_service)
        order = factory.create()
        order_id = order["id"]
        order_service.update(order_id, {"status": "confirmed"})
        order_service.update(order_id, {"status": "preparing"})

        #Update
        update_payload = order_update_payload(status=new_status)
        response = order_service.update(order["id"], update_payload)
        data = response.json()

        self.using(response).assert_status_code_is(StatusCodes.BAD_REQUEST)
        self.using(response).assert_response_has_key("message")

        #CLEANUP
        order_service.update(order_id, {"status": "ready"})
        order_service.update(order_id, {"status": "picked_up"})
        order_service.update(order_id, {"status": "delivered"})
        factory.cleanup_all(order["customer_id"],order["address_id"],order["menu_item_id"],order["menu_id"],order["restaurant_id"])


    @allure.story("Update Order correctly status machine starting in picked_up")
    def test_status_transition_from_picked_up(
            self,
            menu_service,
            menu_items_service,
            restaurant_service,
            address_service,
            customer_service,
            order_service
    ):
        """PUT /orders/<id> - should update status  and return 200.
        correctly options:

        -picked_up to delivered
        """
        #Create order via factory
        factory = OrderFactory(order_service, address_service,customer_service,menu_items_service,menu_service,restaurant_service)
        order = factory.create()
        order_id = order["id"]
        order_service.update(order_id, {"status": "confirmed"})
        order_service.update(order_id, {"status": "preparing"})
        order_service.update(order_id, {"status": "ready"})
        order_service.update(order_id, {"status": "picked_up"})

        #Update
        update_payload = order_update_payload(status="delivered")
        response = order_service.update(order["id"], update_payload)
        data = response.json()

        self.using(response).assert_status_code_is(StatusCodes.OK)
        self.using(response).assert_response_has_key_value("status", "delivered")

        #CLEANUP
        order_service.update(order_id, {"status": "delivered"})
        factory.cleanup_all(order["customer_id"],order["address_id"],order["menu_item_id"],order["menu_id"],order["restaurant_id"])


    @pytest.mark.parametrize("new_status", [ "placed", "cancelled", "confirmed", "preparing"])
    @allure.story("Update Order incorrect status machine starting in picked_up")
    def test_status_invalid_transition_from_picked_up(
            self,
            new_status,
            menu_service,
            menu_items_service,
            restaurant_service,
            address_service,
            customer_service,
            order_service
    ):
        """PUT /orders/<id> - should return 400.
        correctly options:

        -picked_up to delivered
        """
        #Create order via factory
        factory = OrderFactory(order_service, address_service,customer_service,menu_items_service,menu_service,restaurant_service)
        order = factory.create()
        order_id = order["id"]
        order_service.update(order_id, {"status": "confirmed"})
        order_service.update(order_id, {"status": "preparing"})
        order_service.update(order_id, {"status": "ready"})
        order_service.update(order_id, {"status": "picked_up"})

        #Update
        update_payload = order_update_payload(status=new_status)
        response = order_service.update(order["id"], update_payload)
        data = response.json()

        self.using(response).assert_status_code_is(StatusCodes.BAD_REQUEST)
        self.using(response).assert_response_has_key("message")

        #CLEANUP
        order_service.update(order_id, {"status": "delivered"})
        factory.cleanup_all(order["customer_id"],order["address_id"],order["menu_item_id"],order["menu_id"],order["restaurant_id"])



@pytest.mark.orders
@allure.feature("Orders")
class TestDeleteOrder(BaseAssertions):
    """Test for DELETE /orders/<id>."""


    @allure.story("DELETE an placed order successfully")
    def test_delete_placed_order_success(
            self,
            menu_service,
            menu_items_service,
            restaurant_service,
            address_service,
            customer_service,
            order_service
    ):
        """DELETE /orders/<id> - should cancelled order and return 200.
        """
        #Create order via factory
        factory = OrderFactory(order_service, address_service,customer_service,menu_items_service,menu_service,restaurant_service)
        order = factory.create()
        order_id = order["id"]

        #delete >> cancelled
        response = order_service.delete_order(order_id)

        self.using(response).assert_status_code_is(StatusCodes.OK)
        self.using(response).assert_response_has_key_value("status", "cancelled")

        #CLEANUP
        factory.cleanup_all(order["customer_id"],order["address_id"],order["menu_item_id"],order["menu_id"],order["restaurant_id"])


    @allure.story("DELETE a confirmed order successfully")
    def test_delete_confirmed_order_success(
            self,
            menu_service,
            menu_items_service,
            restaurant_service,
            address_service,
            customer_service,
            order_service
    ):
        """DELETE /orders/<id> - should cancelled order and return 200.
        """
        #Create order via factory
        factory = OrderFactory(order_service, address_service,customer_service,menu_items_service,menu_service,restaurant_service)
        order = factory.create()
        order_id = order["id"]
        order_service.update(order_id, {"status": "confirmed"})

        #delete >> cancelled
        response = order_service.delete_order(order_id)

        self.using(response).assert_status_code_is(StatusCodes.OK)
        self.using(response).assert_response_has_key_value("status", "cancelled")

        #CLEANUP
        factory.cleanup_all(order["customer_id"],order["address_id"],order["menu_item_id"],order["menu_id"],order["restaurant_id"])


    @allure.story("DELETE an order with status preparing")
    def test_delete_order_status_preparing(
            self,
            menu_service,
            menu_items_service,
            restaurant_service,
            address_service,
            customer_service,
            order_service
    ):
        """DELETE /orders/<id> - should not cancel order and return 400.
        """
        #Create order via factory
        factory = OrderFactory(order_service, address_service,customer_service,menu_items_service,menu_service,restaurant_service)
        order = factory.create()
        order_id = order["id"]
        order_service.update(order_id, {"status": "confirmed"})
        order_service.update(order_id, {"status": "preparing"})

        #delete >> cancelled
        response = order_service.delete_order(order["id"])

        self.using(response).assert_status_code_is(StatusCodes.BAD_REQUEST)
        self.using(response).assert_response_has_key("message")

        #CLEANUP
        order_service.update(order_id, {"status": "ready"})
        order_service.update(order_id, {"status": "picked_up"})
        order_service.update(order_id, {"status": "delivered"})
        factory.cleanup_all(order["customer_id"],order["address_id"],order["menu_item_id"],order["menu_id"],order["restaurant_id"])


    @allure.story("DELETE an order with status ready")
    def test_delete_order_status_ready(
            self,
            menu_service,
            menu_items_service,
            restaurant_service,
            address_service,
            customer_service,
            order_service
    ):
        """DELETE /orders/<id> - should not cancel order and return 400.
        """
        #Create order via factory
        factory = OrderFactory(order_service, address_service,customer_service,menu_items_service,menu_service,restaurant_service)
        order = factory.create()
        order_id = order["id"]
        order_service.update(order_id, {"status": "confirmed"})
        order_service.update(order_id, {"status": "preparing"})
        order_service.update(order_id, {"status": "ready"})

        #delete >> cancelled
        response = order_service.delete_order(order_id)

        self.using(response).assert_status_code_is(StatusCodes.BAD_REQUEST)
        self.using(response).assert_response_has_key("message")

        #CLEANUP
        order_service.update(order_id, {"status": "picked_up"})
        order_service.update(order_id, {"status": "delivered"})
        factory.cleanup_all(order["customer_id"],order["address_id"],order["menu_item_id"],order["menu_id"],order["restaurant_id"])


    @allure.story("DELETE an order with status picked_up")
    def test_delete_order_status_picked_up(
            self,
            menu_service,
            menu_items_service,
            restaurant_service,
            address_service,
            customer_service,
            order_service
    ):
        """DELETE /orders/<id> - should not cancel order and return 400.
        """
        #Create order via factory
        factory = OrderFactory(order_service, address_service,customer_service,menu_items_service,menu_service,restaurant_service)
        order = factory.create()
        order_id = order["id"]
        order_service.update(order_id, {"status": "confirmed"})
        order_service.update(order_id, {"status": "preparing"})
        order_service.update(order_id, {"status": "ready"})
        order_service.update(order_id, {"status": "picked_up"})

        #delete >> cancelled
        response = order_service.delete_order(order["id"])

        self.using(response).assert_status_code_is(StatusCodes.BAD_REQUEST)
        self.using(response).assert_response_has_key("message")

        order_service.update(order_id, {"status": "delivered"})
        factory.cleanup_all(order["customer_id"],order["address_id"],order["menu_item_id"],order["menu_id"],order["restaurant_id"])

    @pytest.mark.prueba
    @allure.story("DELETE nonexistent order")
    def test_delete_nonexist_order( self, order_service):
        """DELETE /orders/999999 - should return 404 and message.
        """
        order_id = 999999

        #delete >> cancelled
        response = order_service.delete_order(order_id)

        self.using(response).assert_status_code_is(StatusCodes.NOT_FOUND)
        self.using(response).assert_response_has_key("message")