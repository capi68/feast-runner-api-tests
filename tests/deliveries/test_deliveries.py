"""Test for Deliveries API."""

import allure
import pytest

from tests.base.base_assertions import BaseAssertions
from tests.models.deliveries_models import Delivery
from tests.payloads.deliveries_payloads import delivery_create_payload, delivery_update_status_payload
from tests.schemas.deliveries_schemas import DELIVERIES_RESPONSE_SCHEMA, DELIVERIES_LIST_SCHEMA
from tests.factories.courier_factory import CourierFactory
from tests.factories.order_factory import OrderFactory
from tests.utils.constants import StatusCodes
from tests.utils.logger import get_logger

logger = get_logger(__name__)

@pytest.mark.deliveries
@allure.feature("Deliveries")
class TestDeliveryCreation(BaseAssertions):
    """Tests for POST /deliveries - delivery creation.

    Validates that deliveries can be created with valid data,
    require an order and available courier.
    """

    @allure.story("Create delivery successfully")
    def test_create_delivery_success(self,delivery_service,ready_order_with_courier):
        """POST /deliveries with order_id, courier_id and valid data.
         should return 201 and matching with Deliveries Response Schema"""
        courier = ready_order_with_courier["courier"]
        order = ready_order_with_courier["order"]

        courier_id = courier["id"]
        order_id = order["id"]

        delivery = Delivery(order_id=order_id, courier_id=courier_id)
        payload = delivery_create_payload(delivery)
        response = delivery_service.create(payload)
        data = response.json()

        self.using(response).assert_status_code_is(StatusCodes.CREATED)
        self.using(response).assert_schema(DELIVERIES_RESPONSE_SCHEMA)
        self.using(response).assert_response_has_key_value("order_id", order["id"])
        self.using(response).assert_response_has_key_value("courier_id", courier_id)


    @allure.story("Create delivery invalid distance")
    def test_create_delivery_invalid_distance(self,delivery_service,ready_order_with_courier):
        """POST /deliveries with invalid distance_km.
         should return 400 with message"""
        courier = ready_order_with_courier["courier"]
        order = ready_order_with_courier["order"]

        courier_id = courier["id"]
        order_id = order["id"]

        delivery = Delivery(order_id=order_id, courier_id=courier_id)
        payload = delivery_create_payload(delivery, distance_km=150)
        response = delivery_service.create(payload)

        self.using(response).assert_status_code_is(StatusCodes.BAD_REQUEST)
        self.using(response).assert_response_has_key("message")

    @allure.story("Create delivery order placed status")
    def test_create_delivery_order_placed_status(
            self,delivery_service,courier_service,order_service,restaurant_service,menu_service,menu_items_service,address_service,customer_service):
        """POST /deliveries with  order placed status.
         should return 400 and message."""
        #Create courier via factory
        courier_factory = CourierFactory(courier_service)
        courier = courier_factory.create()
        courier_id = courier["id"]

        #create order via factory
        order_factory = OrderFactory(order_service, address_service, customer_service, menu_items_service, menu_service, restaurant_service)
        order = order_factory.create()

        delivery = Delivery(order_id=order["id"], courier_id=courier_id)
        payload = delivery_create_payload(delivery)
        response = delivery_service.create(payload)

        self.using(response).assert_status_code_is(StatusCodes.BAD_REQUEST)
        self.using(response).assert_response_has_key("message")

        #CLEANUP
        order_service.update(order["id"], {"status": "cancelled"})
        order_factory.cleanup_all(order["customer_id"], order["address_id"], order["menu_item_id"], order["menu_id"], order["restaurant_id"])
        courier_factory.cleanup(courier_id)


    @allure.story("Create delivery order preparing status")
    def test_create_delivery_order_preparing_status(
            self,delivery_service,courier_service,order_service,restaurant_service,menu_service,menu_items_service,address_service,customer_service):
        """POST /deliveries with  order preparing status.
         should return 400 and message."""
        #Create courier via factory
        courier_factory = CourierFactory(courier_service)
        courier = courier_factory.create()
        courier_id = courier["id"]

        #create order via factory
        order_factory = OrderFactory(order_service, address_service, customer_service, menu_items_service, menu_service, restaurant_service)
        order = order_factory.create()
        order_service.update(order["id"], {"status": "confirmed"})
        order_service.update(order["id"], {"status": "preparing"})

        delivery = Delivery(order_id=order["id"], courier_id=courier_id)
        payload = delivery_create_payload(delivery)
        response = delivery_service.create(payload)

        self.using(response).assert_status_code_is(StatusCodes.BAD_REQUEST)
        self.using(response).assert_response_has_key("message")

        #CLEANUP
        order_service.update(order["id"], {"status": "ready"})
        order_service.update(order["id"], {"status": "picked_up"})
        order_service.update(order["id"], {"status": "delivered"})
        order_factory.cleanup_all(order["customer_id"], order["address_id"], order["menu_item_id"], order["menu_id"], order["restaurant_id"])
        courier_factory.cleanup(courier_id)


    @allure.story("Create delivery order confirmed status")
    def test_create_delivery_order_confirmed_status(
            self,delivery_service,courier_service,order_service,restaurant_service,menu_service,menu_items_service,address_service,customer_service):
        """POST /deliveries with  order confirmed status.
         should return 400 and message."""
        #Create courier via factory
        courier_factory = CourierFactory(courier_service)
        courier = courier_factory.create()
        courier_id = courier["id"]

        #create order via factory
        order_factory = OrderFactory(order_service, address_service, customer_service, menu_items_service, menu_service, restaurant_service)
        order = order_factory.create()
        order_service.update(order["id"], {"status": "confirmed"})

        delivery = Delivery(order_id=order["id"], courier_id=courier_id)
        payload = delivery_create_payload(delivery)
        response = delivery_service.create(payload)

        self.using(response).assert_status_code_is(StatusCodes.BAD_REQUEST)
        self.using(response).assert_response_has_key("message")

        #CLEANUP
        order_service.update(order["id"], {"status": "cancelled"})
        order_factory.cleanup_all(order["customer_id"], order["address_id"], order["menu_item_id"], order["menu_id"], order["restaurant_id"])
        courier_factory.cleanup(courier_id)


    @allure.story("Create delivery order cancelled status")
    def test_create_delivery_order_cancelled_status(
            self,delivery_service,courier_service,order_service,restaurant_service,menu_service,menu_items_service,address_service,customer_service):
        """POST /deliveries with  order cancelled status.
         should return 400 and message."""
        #Create courier via factory
        courier_factory = CourierFactory(courier_service)
        courier = courier_factory.create()
        courier_id = courier["id"]

        #create order via factory
        order_factory = OrderFactory(order_service, address_service, customer_service, menu_items_service, menu_service, restaurant_service)
        order = order_factory.create()
        order_service.update(order["id"], {"status": "cancelled"})

        delivery = Delivery(order_id=order["id"], courier_id=courier_id)
        payload = delivery_create_payload(delivery)
        response = delivery_service.create(payload)

        self.using(response).assert_status_code_is(StatusCodes.BAD_REQUEST)
        self.using(response).assert_response_has_key("message")

        #CLEANUP
        order_factory.cleanup_all(order["customer_id"], order["address_id"], order["menu_item_id"], order["menu_id"], order["restaurant_id"])
        courier_factory.cleanup(courier_id)

    @allure.story("Create delivery order delivered status")
    def test_create_delivery_order_delivered_status(self,delivery_service,order_service, ready_order_with_courier):
        """POST /deliveries with  order delivered status.
         should return 400 and message."""
        courier = ready_order_with_courier["courier"]
        order = ready_order_with_courier["order"]

        courier_id = courier["id"]
        order_id = order["id"]

        order_service.update(order_id, {"status": "picked_up"})
        order_service.update(order_id, {"status": "delivered"})

        delivery = Delivery(order_id=order["id"], courier_id=courier_id)
        payload = delivery_create_payload(delivery)
        response = delivery_service.create(payload)

        self.using(response).assert_status_code_is(StatusCodes.BAD_REQUEST)
        self.using(response).assert_response_has_key("message")


    @allure.story("Create delivery order picked_up status")
    def test_create_delivery_order_picked_up_status(self,delivery_service,order_service,ready_order_with_courier):
        """POST /deliveries with  order picked_up status.
         should return 400 and message."""
        courier = ready_order_with_courier["courier"]
        order = ready_order_with_courier["order"]

        courier_id = courier["id"]
        order_id = order["id"]
        order_service.update(order_id, {"status": "picked_up"})

        delivery = Delivery(order_id=order_id, courier_id=courier_id)
        payload = delivery_create_payload(delivery)
        response = delivery_service.create(payload)

        self.using(response).assert_status_code_is(StatusCodes.BAD_REQUEST)
        self.using(response).assert_response_has_key("message")


    @allure.title("Create a duplicated delivery for one order must return 409")
    @allure.story("Create delivery duplicate")
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.description("""
    According to the API documentation, attempting to create a duplicate delivery should return 409 Conflict.

    However, after the first delivery is created, the associated order status is automatically changed from READY to PICKED_UP.

    A second POST request therefore fails the order status validation first, returning 400 Bad Request, making the documented 409 
    Conflict scenario unreachable.
    """)
    def test_create_delivery_duplicate(
            self,delivery_service,order_service,ready_order_with_courier):
        """POST /deliveries duplicate should return 409 with message"""
        with allure.step("create order with courier"):
            courier = ready_order_with_courier["courier"]
            order = ready_order_with_courier["order"]

            courier_id = courier["id"]
            order_id = order["id"]

        with allure.step("Create first delivery"):
            #first delivery
            delivery = Delivery(order_id=order_id, courier_id=courier_id)
            payload = delivery_create_payload(delivery)
            delivery_service.create(payload)

        with allure.step("create second delivery for same order"):
            #second delivery
            response_2 = delivery_service.create(payload)

        with allure.step("Validate response"):
            self.using(response_2).assert_status_code_is(StatusCodes.CONFLICT)
            self.using(response_2).assert_response_has_key("message")


    @allure.story("Create delivery inactive courier")
    def test_create_delivery_inactive_courier(
            self,delivery_service,order_service,ready_order_with_courier):
        """POST /deliveries with nonexistent courier return 404 with message"""
        order = ready_order_with_courier["order"]
        order_id = order["id"]

        payload = delivery_create_payload(order_id=order_id, courier_id=999999)
        response = delivery_service.create(payload)

        self.using(response).assert_status_code_is(StatusCodes.NOT_FOUND)
        self.using(response).assert_response_has_key("message")


    @allure.story("Create delivery courier unavailable")
    def test_create_delivery_courier_unavailable(
            self,delivery_service,courier_service,order_service,restaurant_service,menu_service,menu_items_service,address_service,customer_service):
        """POST /deliveries with courier unavailable.
         should return 409 and message"""
        #Create courier via factory
        courier_factory = CourierFactory(courier_service)
        courier = courier_factory.create()
        courier_id = courier["id"]

        #create first order via factory
        order_factory = OrderFactory(order_service, address_service, customer_service, menu_items_service, menu_service, restaurant_service)
        order = order_factory.create()
        order_service.update(order["id"], {"status": "confirmed"})
        order_service.update(order["id"], {"status": "preparing"})
        order_service.update(order["id"], {"status": "ready"})

        delivery = Delivery(order_id=order["id"], courier_id=courier_id)
        payload = delivery_create_payload(delivery)
        delivery_service.create(payload)

        #create second order via factory
        second_order = order_factory.create()
        order_service.update(second_order["id"], {"status": "confirmed"})
        order_service.update(second_order["id"], {"status": "preparing"})
        order_service.update(second_order["id"], {"status": "ready"})

        delivery = Delivery(order_id=second_order["id"], courier_id=courier_id)
        payload = delivery_create_payload(delivery)
        response = delivery_service.create(payload)

        self.using(response).assert_status_code_is(StatusCodes.CONFLICT)
        self.using(response).assert_response_has_key("message")

        #CLEANUP
        order_service.update(order["id"], {"status": "delivered"})
        order_service.update(second_order["id"], {"status": "picked_up"})
        order_service.update(second_order["id"], {"status": "delivered"})
        order_factory.cleanup_all(order["customer_id"], order["address_id"], order["menu_item_id"], order["menu_id"], order["restaurant_id"])
        order_factory.cleanup_all(second_order["customer_id"],
                                  second_order["address_id"],
                                  second_order["menu_item_id"],
                                  second_order["menu_id"],
                                  second_order["restaurant_id"])
        courier_factory.cleanup(courier_id)


    @allure.story("Create delivery resource not found")
    def test_create_delivery_nonexistent_order(self, delivery_service, courier_service):
        """POST /deliveries with nonexistent order should return 404 with message"""

        order_id = 999999

        #Create courier via factory
        courier_factory = CourierFactory(courier_service)
        courier = courier_factory.create()
        courier_id = courier["id"]

        payload = delivery_create_payload(order_id=order_id, courier_id=courier_id)
        response = delivery_service.create(payload)

        self.using(response).assert_status_code_is(StatusCodes.NOT_FOUND)
        self.using(response).assert_response_has_key("message")

        #CLEANUP
        courier_factory.cleanup(courier_id)


@pytest.mark.deliveries
@allure.feature("Deliveries")
class TestDeliveryRetrieval(BaseAssertions):
    """Tests GET /deliveries - GET /deliveries?courier_id= -
        GET /deliveries?status= - GET /deliveries/<id>"""


    def test_get_list(self, delivery_service):
        """GET /deliveries - should return 200 and a list of deliveries."""

        response = delivery_service.list()

        self.using(response).assert_status_code_is(StatusCodes.OK)
        self.using(response).assert_schema(DELIVERIES_LIST_SCHEMA)


    @allure.story("Get list deliveries filtered by status")
    def test_get_list_by_status(
            self,delivery_service,order_service,ready_order_with_courier):
        """GET /deliveries?status= - should return 200 and a list of deliveries filtered by status"""
        courier = ready_order_with_courier["courier"]
        order = ready_order_with_courier["order"]

        courier_id = courier["id"]
        order_id = order["id"]

        delivery = Delivery(order_id=order_id, courier_id=courier_id)
        payload = delivery_create_payload(delivery)
        response = delivery_service.create(payload)
        data = response.json()
        delivery_service.update(data["id"], {"status": "picked_up"})

        #GET filtered list
        get_response = delivery_service.list(status="picked_up")
        get_data = get_response.json()

        self.using(get_response).assert_status_code_is(StatusCodes.OK)
        assert  all(delivery["status"] == "picked_up" for delivery in get_data)


    @allure.story("Get list deliveries filtered by courier_id")
    def test_get_list_by_courier_id(
            self,delivery_service,order_service,ready_order_with_courier):
        """GET /deliveries?courier_id= - should return 200 and a
        list of deliveries filtered by courier_id
        """
        courier = ready_order_with_courier["courier"]
        order = ready_order_with_courier["order"]

        courier_id = courier["id"]
        order_id = order["id"]

        delivery = Delivery(order_id=order_id, courier_id=courier_id)
        payload = delivery_create_payload(delivery)

        #GET filtered list by courier_id
        get_response = delivery_service.list(courier_id)
        get_data = get_response.json()

        self.using(get_response).assert_status_code_is(StatusCodes.OK)
        assert  all(delivery["courier_id"] == courier_id for delivery in get_data)


    @allure.story("Get delivery by id")
    def test_get_delivery_by_id(
            self,delivery_service,order_service,ready_order_with_courier):
        """GET /<id> - should return 200 and delivery matching by id.
        """
        courier = ready_order_with_courier["courier"]
        order = ready_order_with_courier["order"]

        courier_id = courier["id"]
        order_id = order["id"]

        delivery = Delivery(order_id=order_id, courier_id=courier_id)
        payload = delivery_create_payload(delivery)
        response = delivery_service.create(payload)
        data = response.json()

        #GET by id
        get_response = delivery_service.get_by_id(data["id"])

        self.using(get_response).assert_status_code_is(StatusCodes.OK)
        self.using(get_response).assert_response_has_key_value("id", data["id"])


@pytest.mark.deliveries
@allure.feature("Deliveries")
class TestUpdateDelivery(BaseAssertions):
    """Test for PUT /deliveries/<id>"""

    @allure.story("Update delivery status starting in assigned")
    @pytest.mark.parametrize("new_status", ["picked_up", "failed"])
    def test_update_status_starting_assigned(
            self,delivery_service,ready_assigned_delivery, new_status):
        """PUT /orders/<id> - should update status  and return 200.
        correctly options:
        - assigned to picked_up/failed
        - 'picked_up' status update 'picked_up_at'"""
        delivery = ready_assigned_delivery["delivery"]
        delivery_id = delivery["id"]

        #update
        update_payload = delivery_update_status_payload(status=new_status)
        response = delivery_service.update(delivery_id, update_payload)
        data = response.json()

        self.using(response).assert_status_code_is(StatusCodes.OK)
        self.using(response).assert_response_has_key_value("status", new_status)
        self.using(response).assert_response_has_key_value("id", delivery["id"])
        if new_status == "picked_up":
            assert data["picked_up_at"] is not None


    @allure.story("Update delivery incorrect  status starting in assigned")
    @pytest.mark.parametrize("new_status", ["in_transit", "delivered"])
    def test_update_incorrect_status_starting_assigned(
            self,delivery_service,ready_assigned_delivery, new_status):
        """PUT /orders/<id> - should return 400.
        correctly options:

        -assigned to picked_up/failed."""
        delivery = ready_assigned_delivery["delivery"]
        delivery_id = delivery["id"]

        #update
        update_data = delivery_update_status_payload(status=new_status)
        response = delivery_service.update(delivery["id"], update_data)

        self.using(response).assert_status_code_is(StatusCodes.BAD_REQUEST)
        self.using(response).assert_response_has_key("message")


    @allure.story("Update delivery status starting in picked_up")
    @pytest.mark.parametrize("new_status", ["in_transit", "failed"])
    def test_update_status_starting_picked_up(
            self,delivery_service, courier_service, ready_assigned_delivery, new_status):
        """PUT /orders/<id> - should update status  and return 200.
        correctly options:
        -picked_up to in_transit/failed
        - 'failed' status sets is_available = True for courier.
        """
        delivery = ready_assigned_delivery["delivery"]
        delivery_id = delivery["id"]
        delivery_service.update(delivery_id, {"status": "picked_up"})

        #update
        update_data = delivery_update_status_payload(status=new_status)
        response = delivery_service.update(delivery["id"], update_data)

        get_courier_response = courier_service.get_by_id(delivery["courier_id"])

        self.using(response).assert_status_code_is(StatusCodes.OK)
        self.using(response).assert_response_has_key_value("status", new_status)
        self.using(response).assert_response_has_key_value("id", delivery["id"])
        if new_status == "failed":
            assert get_courier_response.json()["is_available"] == True


    @allure.story("Update delivery incorrect  status starting in picked_up")
    @pytest.mark.parametrize("new_status", ["assigned", "delivered"])
    def test_update_incorrect_status_starting_picked_up(
            self,delivery_service,ready_assigned_delivery, new_status):
        """PUT /orders/<id> - should return 400.
        correctly options:
        -picked_up to in_transit/failed"""
        delivery = ready_assigned_delivery["delivery"]
        delivery_id = delivery["id"]
        delivery_service.update(delivery_id, {"status": "picked_up"})

        #update
        update_data = delivery_update_status_payload(status=new_status)
        response = delivery_service.update(delivery["id"], update_data)

        self.using(response).assert_status_code_is(StatusCodes.BAD_REQUEST)
        self.using(response).assert_response_has_key("message")


    @allure.story("Update delivery status starting in in_transit")
    @pytest.mark.parametrize("new_status", ["delivered", "failed"])
    def test_update_status_starting_in_transit(
            self,delivery_service,ready_assigned_delivery,new_status):
        """PUT /orders/<id> - should update status  and return 200.
        correctly options:
        -in_transit to delivered/failed
        - 'delivered' status update delivered_at"""
        delivery = ready_assigned_delivery["delivery"]
        delivery_id = delivery["id"]
        delivery_service.update(delivery_id, {"status": "picked_up"})
        delivery_service.update(delivery_id, {"status": "in_transit"})

        #update
        update_data = delivery_update_status_payload(status=new_status)
        response = delivery_service.update(delivery["id"], update_data)
        data = response.json()

        self.using(response).assert_status_code_is(StatusCodes.OK)
        self.using(response).assert_response_has_key_value("status", new_status)
        self.using(response).assert_response_has_key_value("id", delivery["id"])
        if new_status == "delivered":
            assert data["delivered_at"] is not None


    @allure.story("Update delivery incorrect  status starting in in_transit")
    @pytest.mark.parametrize("new_status", ["assigned", "picked_up"])
    def test_update_incorrect_status_starting_in_transit(
            self,delivery_service,ready_assigned_delivery, new_status):
        """PUT /orders/<id> - should return 400.
        correctly options:

        -in_transit to delivered/failed
        """
        delivery = ready_assigned_delivery["delivery"]
        delivery_id = delivery["id"]
        delivery_service.update(delivery_id, {"status": "picked_up"})
        delivery_service.update(delivery_id, {"status": "in_transit"})

        #update
        update_data = delivery_update_status_payload(status=new_status)
        response = delivery_service.update(delivery["id"], update_data)

        self.using(response).assert_status_code_is(StatusCodes.BAD_REQUEST)
        self.using(response).assert_response_has_key("message")


    @allure.story("Update delivery status starting in delivered")
    @pytest.mark.parametrize("new_status", ["assigned", "picked_up", "in_transit","failed"])
    def test_update_status_starting_in_delivered(
            self,delivery_service,ready_assigned_delivery,new_status):
        """PUT /orders/<id> - should return 400.
        correctly options:

        -delivered to X
        """
        delivery = ready_assigned_delivery["delivery"]
        delivery_id = delivery["id"]
        delivery_service.update(delivery_id, {"status": "picked_up"})
        delivery_service.update(delivery_id, {"status": "in_transit"})
        delivery_service.update(delivery_id, {"status": "delivered"})

        update_data = delivery_update_status_payload(status=new_status)
        response = delivery_service.update(delivery["id"], update_data)

        self.using(response).assert_status_code_is(StatusCodes.BAD_REQUEST)
        self.using(response).assert_response_has_key("message")


    @allure.story("Update delivery  status starting in failed")
    @pytest.mark.parametrize("new_status", ["assigned", "picked_up", "in_transit", "delivered"])
    def test_update_incorrect_status_starting_in_failed(
            self,delivery_service,ready_assigned_delivery,new_status):
        """PUT /orders/<id> - should return 400.
        correctly options:

        -failed to X
        """
        delivery = ready_assigned_delivery["delivery"]
        delivery_id = delivery["id"]
        delivery_service.update(delivery_id, {"status": "failed"})

        #update
        update_data = delivery_update_status_payload(status=new_status)
        response = delivery_service.update(delivery["id"], update_data)

        self.using(response).assert_status_code_is(StatusCodes.BAD_REQUEST)
        self.using(response).assert_response_has_key("message")

