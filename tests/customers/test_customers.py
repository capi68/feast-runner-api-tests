"""Test for the Customers API."""

import allure
import pytest

from tests.base.base_assertions import BaseAssertions
from tests.conftest import customer_service
from tests.factories.order_factory import OrderFactory
from tests.services.customer_service import CustomerService
from tests.payloads.customers_payloads import customer_create_payload,customer_login_payload,customer_update_payload
from tests.schemas.customers_schema import CUSTOMER_RESPONSE_SCHEMA,CUSTOMER_LIST_SCHEMA,CUSTOMER_LOGIN_SCHEMA
from tests.utils.logger import get_logger
from tests.utils.constants import StatusCodes

logger = get_logger(__name__)


@pytest.mark.customers
@allure.feature("Customers")
class TestCustomerCreation(BaseAssertions):
    """Tests for POST /customers - Customer registration.
    Validates that the customer creation endpoint correctly handles
    valid input, missing fields, invalid data, and duplicate emails.
    """

    @allure.story("Create customer with valid data")
    @pytest.mark.smoke
    def test_create_customer_success(self):
        """POST /customers with all valid required fields should return 201
        and a response matching the CustomerResponse schema without password"""
        service = CustomerService()
        payload = customer_create_payload()

        response = service.create(payload)

        self.using(response).assert_status_code_is(StatusCodes.CREATED)
        self.using(response).assert_response_key_absent("password_hash")
        self.using(response).assert_response_key_absent("password")
        self.using(response).assert_schema(CUSTOMER_RESPONSE_SCHEMA)
        self.using(response).assert_response_has_key_value("email", payload["email"])
        self.using(response).assert_response_has_key("id")

    @allure.story("Create customer with missing required fields")
    def test_create_customer_missing_fields(self, customer_service):
        """POST /cutomers with empty body should return 400.
        with message."""

        response = customer_service.create({})

        self.using(response).assert_status_code_is(StatusCodes.BAD_REQUEST)
        self.using(response).assert_response_has_key("message")

    @allure.story("Create customer with invalid email")
    def test_create_customer_invalid_email(self, customer_service):
        """POST /customers with invalid email should return 400.
        with message. The API validates email before attempting DB insertion."""

        payload = customer_create_payload()
        payload["email"] = "not-an-email"

        response = customer_service.create(payload)

        self.using(response).assert_status_code_is(StatusCodes.BAD_REQUEST)
        self.using(response).assert_response_has_key("message")


    @allure.story("Create customer with short password")
    def test_create_customer_short_password(self, customer_service):
        """POST /customers with short password, should return 400.
        and message invalid password."""

        payload = customer_create_payload()
        payload["password"] = "123"

        response = customer_service.create(payload)

        self.using(response).assert_status_code_is(StatusCodes.BAD_REQUEST)
        self.using(response).assert_response_has_key("message")


    @allure.story("Create customer with empty required fields")
    @pytest.mark.parametrize("field", ["first_name", "last_name", "email", "phone", "password"])
    def test_create_customer_empty_required_fields(self,customer_service, field):
        """POST /customers with empty required fields return 400
        with message indicating which field are empty."""

        payload = customer_create_payload()
        payload[field] = ""

        response = customer_service.create(payload)

        self.using(response).assert_status_code_is(StatusCodes.BAD_REQUEST)
        self.using(response).assert_response_has_key("message")


    @allure.title("Create customer with invalid data type")
    @allure.story("Create customer with invalid data type")
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
    @pytest.mark.parametrize("field", ["first_name", "last_name", "email", "phone"])
    def test_create_customer_invalid_fields_type(self, field):
        """POST /customers with invalid data type return 400
        with message."""

        with allure.step("Prepare payload with invalid data type."):
            service = CustomerService()
            payload = customer_create_payload()
            payload[field] = 1

            #attach payload
            allure.attach(
                str(payload),
                name="Request Payload",
                attachment_type=allure.attachment_type.TEXT
            )
        with allure.step("Send POST /customers request"):
            response = service.create(payload)

            #attach response API
            allure.attach(
                response.text,
                name="Response Body",
                attachment_type=allure.attachment_type.JSON
            )

        with allure.step("Validate response."):
            self.using(response).assert_status_code_is(StatusCodes.BAD_REQUEST)
            self.using(response).assert_response_has_key("message")


    @allure.title("Create customer with invalid data type in password field")
    @allure.story("Create customer with invalid data type in password field")
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.description("""
    Verify that de API rejects  invalid data types for password field.
    
    Expected: 
    - API returns HTTP 400 BAD REQUEST.
    - Response contains an error message.
    
    Actual:
    -Password with integer value returns HTTP 500 Internal Server Error.
    """)
    def test_create_customer_invalid_password_type(self):
        """POST /customers with invalid password data type return 400
        with message."""

        with allure.step("Prepare payload with invalid data type."):
            service = CustomerService()
            payload = customer_create_payload()
            payload["password"] = 1

            #attach payload
            allure.attach(
                str(payload),
                name="Request Payload",
                attachment_type=allure.attachment_type.TEXT
            )
        with allure.step("Send POST /customers request"):
            response = service.create(payload)

            #attach response API
            allure.attach(
                response.text,
                name="Response Body",
                attachment_type=allure.attachment_type.JSON
            )

        with allure.step("Validate response."):
            self.using(response).assert_status_code_is(StatusCodes.BAD_REQUEST)
            self.using(response).assert_response_has_key("message")


    @allure.story("Create customer with duplicate email")
    def test_create_customer_duplicate_email(self, customer_service):
        """POST /customers with an email that already exists should return 409.
        Email uniqueness is enforced at both API and database level."""

        service = customer_service
        payload = customer_create_payload()
        email = payload["email"]

        #first customer - should success
        response1 = service.create(payload)
        self.using(response1).assert_status_code_is(StatusCodes.CREATED)
        self.using(response1).assert_response_has_key_value("email", email)

        #second customer - should conflict
        response2 = service.create(payload)
        self.using(response2).assert_status_code_is(StatusCodes.CONFLICT)
        self.using(response2).assert_response_has_key("message")

        #CLEANUP
        customer_id = response1.json()["id"]
        service.delete_customer(customer_id)


@pytest.mark.customers
@allure.feature("Customers")
class TestCustomerRetrieval(BaseAssertions):
    """ Tests  for GET /customers and GET /customers/<id>.
    Validates listing and individual retrieval with auth.
    """

    @allure.story("List all customers")
    @pytest.mark.smoke
    def test_list_customers(self, customer_service):
        """GET /customers should return 200 with a list of active customers.
        requires valid Authorization header.
        """

        response = customer_service.list()

        self.using(response).assert_status_code_is(StatusCodes.OK)
        self.using(response).assert_schema(CUSTOMER_LIST_SCHEMA)

    @allure.story("Get customer by id.")
    def test_get_customer_by_id(self, customer_service):
        """ GET /customers/<id> should return 200, and customer matching
        by id. Creates a customer first, then retrieves it by the returned id.
        """
        service = customer_service
        payload = customer_create_payload()

        #create customer
        create_response = service.create(payload)
        customer_id = create_response.json()["id"]

        #get customer by id
        get_response = service.get_by_id(customer_id)

        self.using(get_response).assert_status_code_is(StatusCodes.OK)
        self.using(get_response).assert_schema(CUSTOMER_RESPONSE_SCHEMA)
        self.using(get_response).assert_response_has_key_value("id", customer_id)

        #CLEANUP
        customer_service.delete_customer(customer_id)


    @allure.story("Get non-existent customer.")
    def test_get_customer_not_found(self, customer_service):
        """GET /customers/999999 should return 404 when no customer exists with that id."""

        response = customer_service.get_by_id(999999)

        self.using(response).assert_status_code_is(StatusCodes.NOT_FOUND)
        self.using(response).assert_response_has_key("message")


    @allure.story("Get List customers without auth.")
    def test_list_customers_unauthorized(self):
        """GET /customers without Authorization header should return 401."""

        service = CustomerService() #no token

        response = service.list()

        self.using(response).assert_status_code_is(StatusCodes.UNAUTHORIZED)
        self.using(response).assert_response_has_key("message")

@pytest.mark.customers
@allure.feature("Customers")
class TestCustomerUpdate(BaseAssertions):
    """Test for PUT /customers/<id>."""
    @pytest.mark.customers
    def test_update_customer_success(self, customer_service):
        """PUT /customers/<id> should update the provided fields and return 200.
        Only the specific fields change; others remain untouched.
        """
        #create customer
        payload = customer_create_payload()
        create_response = CustomerService().create(payload)
        customer_id = create_response.json()["id"]

        # update customer
        update_data = customer_update_payload(
            first_name="Maria",
            last_name="Perez",
            phone="+0000000000",
            password="newpass123!"
        )
        update_response = customer_service.update(customer_id, update_data)

        self.using(update_response).assert_status_code_is(StatusCodes.OK)
        self.using(update_response).assert_schema(CUSTOMER_RESPONSE_SCHEMA)
        self.using(update_response).assert_response_has_key_value("first_name", "Maria")
        self.using(update_response).assert_response_has_key_value("last_name", "Perez")
        self.using(update_response).assert_response_key_absent("password_hash")
        self.using(update_response).assert_response_key_absent("password")

        #CLEANUP
        customer_service.delete_customer(customer_id)


    @allure.story("Try update nonexist customer")
    def test_update_nonexist_customer(self, customer_service):
        """PUT /customers/999999 should return 404 and message.
        """
        update_data = customer_update_payload(
            first_name="Maria",
        )
        update_response = customer_service.update(999999, update_data)

        self.using(update_response).assert_status_code_is(StatusCodes.NOT_FOUND)
        self.using(update_response).assert_response_has_key("message")



@pytest.mark.customers
@allure.feature("Customers")
class TestCustomerDelete(BaseAssertions):
    """Test for DELETE /customers/<id>."""

    @allure.story("Delete customer success.")
    def test_delete_customer_success(self, customer_service):
        """DELETE /customers/<id> should return 200 and message."""

        #create customer
        payload = customer_create_payload()
        create_response = CustomerService().create(payload)
        customer_id = create_response.json()["id"]

        #delete customer
        delete_response = customer_service.delete_customer(customer_id)

        self.using(delete_response).assert_status_code_is(StatusCodes.OK)
        self.using(delete_response).assert_response_has_key("message")


    @allure.story("Try delete nonexist customer.")
    def test_delete_nonexist_customer(self, customer_service):
        """DELETE /customers/999999 should return 404 and message."""

        delete_response = customer_service.delete_customer(999999)

        self.using(delete_response).assert_status_code_is(StatusCodes.NOT_FOUND)
        self.using(delete_response).assert_response_has_key("message")


    @allure.story("Delete customer with active orders.")
    def test_delete_customer_with_active_order(
            self,
            menu_service,
            menu_items_service,
            restaurant_service,
            address_service,
            customer_service,
            order_service
    ):
        """DELETE /customers/<id> with active orders should return 409 and message."""

        #Create order via factory
        factory = OrderFactory(order_service, address_service,customer_service,menu_items_service,menu_service,restaurant_service)
        order = factory.create()
        order_id = order["id"]
        customer_id = order["customer_id"]

        response = customer_service.delete_customer(customer_id)

        self.using(response).assert_status_code_is(StatusCodes.CONFLICT)
        self.using(response).assert_response_has_key("message")

        #CLEANUP
        factory.cleanup(order_id)
        factory.cleanup_all(order["customer_id"],order["address_id"],order["menu_item_id"],order["menu_id"],order["restaurant_id"])


@pytest.mark.customers
@allure.feature("Customers")
@pytest.mark.auth
class TestCustomerAuth(BaseAssertions):
    """Tests for Post /customers/login."""

    @allure.story("Login customer success with valid credentials.")
    @pytest.mark.smoke
    def test_login_success(self, customer_service):
        """POST /customers/login with correct email/password should return 200
        with JWT token in the response body under the 'token' key.
        """
        service= customer_service
        payload = customer_login_payload("customer@feastrunner.com", "Customer123!")

        response = service.login(payload)

        self.using(response).assert_status_code_is(StatusCodes.OK)
        self.using(response).assert_response_has_key("token")
        self.using(response).assert_schema(CUSTOMER_LOGIN_SCHEMA)
        self.using(response).assert_response_has_key("message")

    @allure.story("Login customer with invalid credentials.")
    @pytest.mark.smoke
    def test_login_wrong_password(self, customer_service):
        """POST /customers/login with wrong password should return 401
        and message.
        """
        service= customer_service
        payload = customer_login_payload("customer@feastrunner.com", "12345678")

        response = service.login(payload)

        self.using(response).assert_status_code_is(StatusCodes.UNAUTHORIZED)
        self.using(response).assert_response_has_key("message")


    @allure.story("Login with missing fields")
    def test_login_missing_fields(self, customer_service):
        """POST /customers/login with empty body should return 400."""
        service = customer_service

        response = service.login({})

        self.using(response).assert_status_code_is(StatusCodes.BAD_REQUEST)
        self.using(response).assert_response_has_key("message")