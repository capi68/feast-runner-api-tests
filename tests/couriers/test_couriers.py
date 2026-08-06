
"""Test for Couriers API"""

import allure
import  pytest

from tests.base.base_assertions import BaseAssertions
from tests.conftest import delivery_service, courier_service
from tests.factories.courier_factory import CourierFactory
from tests.factories.order_factory import OrderFactory
from tests.models.deliveries_models import Delivery
from tests.services.couriers_service import CouriersService
from tests.payloads.courier_payloads import courier_login_payload,courier_create_payload,courier_update_payload
from tests.payloads.deliveries_payloads import delivery_create_payload
from tests.schemas.couriers_schemas import LOGIN_COURIERS_SCHEMA,COURIERS_RESPONSE_SCHEMA,COURIERS_LIST_SCHEMA
from tests.utils.logger import get_logger
from tests.utils.constants import StatusCodes

logger = get_logger(__name__)


@pytest.mark.couriers
@allure.feature("Couriers")
class TestCouriers_Creation(BaseAssertions):
    """Test for POST /couriers - Couriers registration.
    Validates that the courier creation endpoint correctly
    handles valid input, missing fields, invalid data, and duplicate emails.
    """

    @allure.story("Create courier successfully")
    def test_create_courier_success(self, courier_service):
        """POST /couriers with all valid required fields should return 201.
        and response matching the Courier Response schema without password

        "vehicle_plate" fields was included; it is not in the documentation
        but is present in swagger.
        """
        service = courier_service
        payload = courier_create_payload()

        response = service.create(payload)

        self.using(response).assert_status_code_is(StatusCodes.CREATED)
        self.using(response).assert_schema(COURIERS_RESPONSE_SCHEMA)
        self.using(response).assert_response_has_key("id")
        self.using(response).assert_response_has_key_value("first_name", payload["first_name"])
        self.using(response).assert_response_has_key_value("email", payload["email"])
        self.using(response).assert_response_key_absent("password")
        self.using(response).assert_response_key_absent("password_hash")

        #CLEANUP
        service.delete_courier(response.json()["id"])


    @allure.story("Create courier with missing required fields")
    def test_create_courier_missing_fields(self, courier_service):
        """POST /couriers - with empty body should return 400.
        with message.
        """
        service = courier_service

        response = service.create({})

        self.using(response).assert_status_code_is(StatusCodes.BAD_REQUEST)
        self.using(response).assert_response_has_key("message")


    @allure.story("Create courier with invalid email")
    def test_create_courier_invalid_email(self,courier_service):
        """POST /couriers - with invalid format email should return 400.
        with message.
        """
        service = courier_service
        payload = courier_create_payload(email="not-an_email")

        response = service.create(payload)

        self.using(response).assert_status_code_is(StatusCodes.BAD_REQUEST)
        self.using(response).assert_response_has_key("message")


    @allure.story("Create courier with short password")
    def test_create_courier_short_password(self, courier_service):
        """POST /couriers - with short password, should return 400.
        with message invalid password
        """
        service = courier_service
        payload = courier_create_payload(password="ABC")

        response = service.create(payload)

        self.using(response).assert_status_code_is(StatusCodes.BAD_REQUEST)
        self.using(response).assert_response_has_key("message")


    @allure.story("Create courier with empty required fields")
    @pytest.mark.parametrize("field", ["first_name", "last_name", "email", "phone", "password", "vehicle_type"])
    def test_create_courier_empty_required_fields(self, courier_service, field):
        """ POST /couriers - with empty required fields should return 400.
        with message indicating which field are empty.
        """
        service = courier_service
        payload = courier_create_payload()
        payload[field] = ""

        response = service.create(payload)

        self.using(response).assert_status_code_is(StatusCodes.BAD_REQUEST)
        self.using(response).assert_response_has_key("message")


    @allure.title("Create courier with invalid data type fields")
    @allure.story("Create courier with invalid data type fields")
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.description("""
    Verify that the API rejects  invalid data types for required string fields.
    
    Expected: 
    - API returns HTTP 400 BAD REQUEST.
    - Response contains an error message.
    
    Actual:
    Some fields accept values that are implicitly converted instead of being rejected.
    Phone also accepts unrealistic values such as "1".

    Current API only validates that the field is a string.
    No validation exists to ensure a usable phone number.
    """)
    @pytest.mark.parametrize("field", ["first_name", "last_name", "email", "phone", "password", "vehicle_type", "license_plate"])
    def test_create_courier_invalid_field_type(self, field):
        """POST /couriers with invalid data type return 400
        with message.
        """
        with allure.step("Prepare payload with invalid data type."):
            service = CouriersService()
            payload = courier_create_payload()
            payload[field] = 1

            #attach payload
            allure.attach(
                str(payload),
                name="Request Payload",
                attachment_type=allure.attachment_type.TEXT
            )
        with allure.step("Send POST /customers request"):
            response = service.create(payload)

        with allure.step("Validate response."):
            self.using(response).assert_status_code_is(StatusCodes.BAD_REQUEST)
            self.using(response).assert_response_has_key("message")


    @allure.story("Create courier with duplicate email")
    def test_create_courier_duplicate_email(self, courier_service):
        """POST /couriers - with a duplicate email should return 409
        with a message.
        """
        service = courier_service
        payload = courier_create_payload()
        email = payload["email"]

        #first courier - should success
        response1 = service.create(payload)
        self.using(response1).assert_status_code_is(StatusCodes.CREATED)
        self.using(response1).assert_response_has_key_value("email", email)

        #second response - should conflict
        response2 = service.create(payload)
        self.using(response2).assert_status_code_is(StatusCodes.CONFLICT)
        self.using(response2).assert_response_has_key("message")

        #cleanup
        courier_id = response1.json()["id"]
        service.delete_courier(courier_id)


@pytest.mark.couriers
@allure.feature("Couriers")
class TestCourierRetrieval(BaseAssertions):
    """Tests GET /couriers - GET /couriers?available=true - GET /couriers/<id>"""

    @allure.story("List all couriers")
    def test_list_couriers(self, courier_service):
        """GET /couriers should return 200 with a list of active couriers.
        requires valid Authorization header.
        """
        response = courier_service.list()

        self.using(response).assert_status_code_is(StatusCodes.OK)
        self.using(response).assert_schema(COURIERS_LIST_SCHEMA)


    @allure.story("Get courier by id")
    def test_get_courier_by_id(self, courier_service):
        """GET /couriers/<id> - should return 200, and courier matching
        by id. Creates a courier first, then retrieves it by the returned id.
        """
        service = courier_service
        payload = courier_create_payload()

        #create courier
        response = service.create(payload)
        data = response.json()

        #get by id
        get_response = service.get_by_id(data["id"])

        self.using(get_response).assert_status_code_is(StatusCodes.OK)
        self.using(get_response).assert_schema(COURIERS_RESPONSE_SCHEMA)
        self.using(get_response).assert_response_has_key_value("id", data["id"])

        #CLEANUP
        service.delete_courier(data["id"])


    @allure.story("GET non-existent courier")
    def test_get_nonexist_courier(self, courier_service):
        """GET /couriers/999999 - should return 404
        when no courier exists with that id.
        """
        response = courier_service.get_by_id(999999)

        self.using(response).assert_status_code_is(StatusCodes.NOT_FOUND)
        self.using(response).assert_response_has_key("message")


    @allure.story("GET courier without auth.")
    def test_get_list_couriers_unauthorized(self):
        """GET couriers - without Authorization header should return 401."""

        service = CouriersService()

        response = service.list()

        self.using(response).assert_status_code_is(StatusCodes.UNAUTHORIZED)
        self.using(response).assert_response_has_key("message")

    @allure.title("Get list filtered by is_available")
    @allure.story("Get list of available couriers")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.description("""
        Verify that the API correctly filters couriers by the `is_available` query parameter.
        
        Expected:
        - API returns HTTP 200 OK.
        - Response contains only couriers with `is_available = true`.
        
        Actual:
        - API returns HTTP 200 OK.
        - Response includes both available and unavailable couriers.
        - The `is_available=true` query parameter is ignored.
        
        Current API does not apply the availability filter, returning incorrect data despite receiving the expected query parameter.
        """)
    def test_get_available_couriers_list(self, courier_service):
        """ GET /couriers?available=True - should return 200 and
        a list of available courier.
        """
        service = courier_service
        with allure.step("create 2 courier, one is_available True and other is_available False."):
            #courier 1
            payload1 = courier_create_payload(is_available=False)
            response1 = service.create(payload1)
            data1 = response1.json()

            #courier 2
            payload2 = courier_create_payload()
            response2 = service.create(payload2)
            data2 = response2.json()
        with allure.step("Send GET /couriers?is_available=true request"):
            #get list available couriers
            get_response = service.list(is_available=True)
            data = get_response.json()

        with allure.step("Validate response."):
            self.using(get_response).assert_status_code_is(StatusCodes.OK)
            self.using(get_response).assert_schema(COURIERS_LIST_SCHEMA)
            assert  all(courier["is_available"] == False for courier in data)

        with allure.step("Clean all resources created by factories."):
            #CLEANUP
            service.delete_courier(data1["id"])
            service.delete_courier(data2["id"])


@pytest.mark.couriers
@allure.feature("Couriers")
class TestCourierUpdate(BaseAssertions):
    """Tests for PUT /couriers/<id>."""

    @allure.story("Update courier successfully")
    def test_update_courier_success(self, courier_service):
        """PUT /couriers/<id> - should update the provided fields and return 200.
        Only the specific fields change: others remain untouched.
        """
        #create courier
        service = courier_service
        payload = courier_create_payload()
        response = service.create(payload)
        data = response.json()

        # update courier
        update_payload = courier_update_payload(
            first_name="Peter",
            last_name="Parker",
            vehicle_type="motorcycle",
            is_available=False
        )
        update_response = service.update(data["id"], update_payload)

        self.using(update_response).assert_status_code_is(StatusCodes.OK)
        self.using(update_response).assert_response_has_key_value("first_name", update_payload["first_name"])
        self.using(update_response).assert_response_has_key_value("last_name", update_payload["last_name"])
        self.using(update_response).assert_response_has_key_value("phone", data["phone"])
        self.using(update_response).assert_response_has_key_value("id", data["id"])

        #CLEANUP
        service.delete_courier(data["id"])


    @allure.story("Update courier with active delivery")
    def test_update_courier_active_delivery(self,
                                            delivery_service,
                                            courier_service,
                                            menu_service,
                                            menu_items_service,
                                            restaurant_service,
                                            address_service,
                                            customer_service,
                                            order_service):
        """PUT /couriers/<id> - should rejects update and return 400"""
        #Create courier via Factory
        factory = CourierFactory(courier_service)
        courier = factory.create()
        courier_id = courier["id"]

        #Create order placed via Factory
        order_factory = OrderFactory(order_service, address_service, customer_service, menu_items_service, menu_service, restaurant_service)
        order = order_factory.create()
        order_service.update(order["id"], {"status": "confirmed"})
        order_service.update(order["id"], {"status": "preparing"})
        order_service.update(order["id"], {"status": "ready"})

        #create delivery
        delivery = Delivery(order["id"], courier_id)
        payload = delivery_create_payload(delivery)
        response = delivery_service.create(payload)
        update = delivery_service.update(response.json()["id"], {"status": "picked_up"})

        update_response = delivery_service.update(response.json()["id"], {"is_available": True})

        self.using(update_response).assert_status_code_is(StatusCodes.BAD_REQUEST)
        self.using(update_response).assert_response_has_key("message")

        #CLEANUP
        delivery_service.update(response.json()["id"], {"status": "failed"})
        factory.cleanup(courier_id)
        order_service.update(order["id"], {"status": "delivered"})
        order_factory.cleanup_all(
            order["customer_id"], order["address_id"], order["menu_item_id"], order["menu_id"], order["restaurant_id"])


    @allure.story("Update nonexistent courier")
    def test_update_nonexist_courier(self, courier_service):
        """PUT /couriers/999999 - should return 400 with message.
        """
        # update courier
        update_data = courier_update_payload(
            first_name="Peter",
            last_name="Parker",
        )
        response = courier_service.update(999999, update_data)

        self.using(response).assert_status_code_is(StatusCodes.NOT_FOUND)
        self.using(response).assert_response_has_key("message")


@pytest.mark.couriers
@allure.feature("Couriers")
class TestCourierDelete(BaseAssertions):
    """Tests for DELETE /courier/<id>."""


    @allure.story("Delete courier successfully")
    def test_delete_courier_success(self, courier_service):
        """DELETE /couriers/<id> should return 200 with message."""

        #Create courier
        payload = courier_create_payload()
        response = courier_service.create(payload)
        data = response.json()

        #delete
        delete_response = courier_service.delete_courier(data["id"])

        self.using(delete_response).assert_status_code_is(StatusCodes.OK)
        self.using(delete_response).assert_response_has_key("message")


    @allure.story("Delete nonexistent courier")
    def test_delete_nonexistent_courier(self, courier_service):
        """DELETE/couriers/999999 - should return 404 with message"""

        response = courier_service.delete_courier(999999)

        self.using(response).assert_status_code_is(StatusCodes.NOT_FOUND)
        self.using(response).assert_response_has_key("message")


    @allure.story("Delete courier with active delivery")
    def test_delete_courier_active_delivery(self,
                                            menu_service,
                                            menu_items_service,
                                            restaurant_service,
                                            address_service,
                                            customer_service,
                                            order_service,
                                            courier_service,
                                            delivery_service):
        """DELETE /courier/<id> - with active delivery should return 409
        with message.
        """
        #Create courier via Factory
        factory = CourierFactory(courier_service)
        courier = factory.create()
        courier_id = courier["id"]

        #Create order placed via Factory
        order_factory = OrderFactory(order_service, address_service, customer_service, menu_items_service, menu_service, restaurant_service)
        order = order_factory.create()
        order_service.update(order["id"], {"status": "confirmed"})
        order_service.update(order["id"], {"status": "preparing"})
        order_service.update(order["id"], {"status": "ready"})

        #create delivery
        delivery = Delivery(order["id"], courier_id)
        payload = delivery_create_payload(delivery)
        response = delivery_service.create(payload)
        update = delivery_service.update(response.json()["id"], {"status": "picked_up"})

        delete_response = courier_service.delete_courier(courier_id)

        self.using(delete_response).assert_status_code_is(StatusCodes.CONFLICT)
        self.using(delete_response).assert_response_has_key("message")

        #CLEANUP
        delivery_service.update(response.json()["id"], {"status": "failed"})
        factory.cleanup(courier_id)
        order_service.update(order["id"], {"status": "delivered"})
        order_factory.cleanup_all(
            order["customer_id"], order["address_id"], order["menu_item_id"], order["menu_id"], order["restaurant_id"])

@pytest.mark.couriers
@allure.feature("Couriers")
class TestCouriersAuth(BaseAssertions):
    """Tests for Post /couriers/login."""

    @allure.story("Login courier success with valid credentials.")
    def test_login_success(self, courier_service):
        """POST /couriers/login with correct email/password should return 200
        with JWT token in the response body under the 'token' key.
        """
        payload = courier_login_payload("courier@feastrunner.com", "Courier123!")
        response = courier_service.login_courier(payload)

        self.using(response).assert_status_code_is(StatusCodes.OK)
        self.using(response).assert_response_has_key("token")
        self.using(response).assert_schema(LOGIN_COURIERS_SCHEMA)
        self.using(response).assert_response_has_key("message")

    @allure.story("Login courier with invalid credentials.")
    def test_login_wrong_password(self, courier_service):
        """POST /couriers/login with wrong password should return 401
        and message.
        """
        payload = courier_login_payload("courier@feastrunner.com", "123456789")
        response = courier_service.login_courier(payload)

        self.using(response).assert_status_code_is(StatusCodes.UNAUTHORIZED)
        self.using(response).assert_response_has_key("message")

    @allure.story("Login with missing fields")
    def test_login_missing_fields(self, courier_service):
        """POST /couriers/login with empty body should return 400."""

        response = courier_service.login_courier({})

        self.using(response).assert_status_code_is(StatusCodes.BAD_REQUEST)
        self.using(response).assert_response_has_key("message")