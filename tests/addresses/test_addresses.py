"""Test for addresses API."""

import allure
import pytest

from tests.base.base_assertions import BaseAssertions
from tests.conftest import address_service
from tests.models.address_model import Address
from tests.payloads.address_payloads import address_create_payload,address_update_payload
from tests.factories.customer_factory import CustomerFactory
from tests.schemas.adresses_schemas import ADDRESS_RESPONSE_SCHEMA, ADDRESS_LIST_SCHEMA
from tests.utils.constants import StatusCodes


@pytest.mark.addresses
@allure.feature("Addresses")
class TestAddressesCreation(BaseAssertions):
    """Tests for POST /addresses - addresses registration.

    Validates that the address creation endpoint correctly handles
    valid input, missing fields, invalid data.
    """

    @allure.story("Create an address successfully")
    @pytest.mark.smoke
    def test_create_addresses_success(self, address_service, customer_service):
        """POST /addresses - with valid data and required fields should return 201.
        and a response matching the AddressResponse schema.
        """
        with allure.step("create customer using factory"):
            customer_factory = CustomerFactory(customer_service)
            customer = customer_factory.create()

            service = address_service

        with allure.step("create a valid payload with customer_id"):
            address = Address(customer_id=customer["id"])
            payload = address_create_payload(address, customer["id"])

        with allure.step("POST /addresses request"):
            response = service.create(payload)
            data = response.json()

        with allure.step("Validate response."):
            self.using(response).assert_status_code_is(StatusCodes.CREATED)
            self.using(response).assert_response_has_key("id")
            self.using(response).assert_schema(ADDRESS_RESPONSE_SCHEMA)
            self.using(response).assert_response_has_key_value("street", payload["street"])
            self.using(response).assert_response_has_key_value("city", payload["city"])

        with allure.step("Clean data after test."):
            #CLEANUP
            service.delete_address(data["id"])
            customer_factory.cleanup(customer["id"])


    @allure.story("Create address with missing required fields")
    def test_create_address_missing_fields(self, address_service):
        """POST /addresses with empty body should return 400
        with message indicating which fields are missing.
        """
        response = address_service.create({})

        self.using(response).assert_status_code_is(StatusCodes.BAD_REQUEST)
        self.using(response).assert_response_has_key("message")


    @allure.story("Create address with empty required fields")
    @pytest.mark.parametrize("field", ["customer_id", "label", "street", "city", "state", "zip_code"])
    def test_create_address_empty_required_fields(self, address_service, customer_service, field):
        """POST /addresses with empty required fields should return 400
        and a message indicating which fields are missing.
        """
        customer_factory = CustomerFactory(customer_service)
        customer = customer_factory.create()

        address = Address(customer_id=customer["id"])
        payload = address_create_payload(address, customer["id"])
        payload[field] = ""

        response = address_service.create(payload)

        self.using(response).assert_status_code_is(StatusCodes.BAD_REQUEST)
        self.using(response).assert_response_has_key("message")

        #CLEANUP
        customer_factory.cleanup(customer["id"])


    @allure.story("Create address with invalid latitude")
    def test_create_address_invalid_latitude(self, customer_service, address_service):
        """POST /addresses with invalid latitude should return 400.
        And message. The API validates latitude before attempting DB insertion.
        """
        customer_factory = CustomerFactory(customer_service)
        customer = customer_factory.create()

        address = Address(customer_id=customer["id"])
        payload = address_create_payload(address, customer["id"])
        payload["latitude"] = -100

        response = address_service.create(payload)

        self.using(response).assert_status_code_is(StatusCodes.BAD_REQUEST)
        self.using(response).assert_response_has_key("message")

        #CLEANUP
        customer_factory.cleanup(customer["id"])


    @allure.story("Create address with invalid longitude")
    def test_create_address_invalid_longitude(self, customer_service, address_service):
        """POST /addresses with invalid longitude should return 400.
        And message. The API validates longitude before attempting DB insertion.
        """
        customer_factory = CustomerFactory(customer_service)
        customer = customer_factory.create()

        address = Address(customer_id=customer["id"])
        payload = address_create_payload(address, customer["id"])
        payload["longitude"] = 190.01

        response = address_service.create(payload)

        self.using(response).assert_status_code_is(StatusCodes.BAD_REQUEST)
        self.using(response).assert_response_has_key("message")

        #CLEANUP
        customer_factory.cleanup(customer["id"])


    @allure.story("Create address with nonexist customer")
    def test_create_address_nonexistent_customer(self, address_service):
        """POST /addresses with nonexist customer should return 404.
        And message.
        """

        address = Address(customer_id=999999)
        payload = address_create_payload(address, customer_id=999999)

        response = address_service.create(payload)

        self.using(response).assert_status_code_is(StatusCodes.NOT_FOUND)
        self.using(response).assert_response_has_key("message")


    @allure.story("Only one default address per customer")
    def test_create_new_default_address_replaces_previous_default(self, customer_service, address_service):
        """POST /addresses Creating a new default address should unset the previous default
        address for the same customer should return 409 and message.
        """
        customer_factory = CustomerFactory(customer_service)
        customer = customer_factory.create()
        customer_id = customer["id"]

        # Address 1
        address1 = Address(customer_id=customer_id)
        payload1 = address_create_payload(address1, customer_id)
        payload1["is_default"] = True

        response1 = address_service.create(payload1)
        data1 = response1.json()

        self.using(response1).assert_status_code_is(StatusCodes.CREATED)

        #Address 2
        address2 = Address(customer_id=customer_id)
        payload2 = address_create_payload(address2, customer_id)
        payload2["label"] = "work"
        payload2["street"] = "321 Main St"
        payload2["is_default"] = True

        response2 = address_service.create(payload2)

        self.using(response2).assert_status_code_is(StatusCodes.CREATED)

        #check address 1 is_default = False
        get_response = address_service.get_by_id(data1["id"])

        self.using(get_response).assert_status_code_is(StatusCodes.OK)
        self.using(get_response).assert_response_has_key_value("is_default", False)

        #CLEANUP
        customer_factory.cleanup(customer["id"])


@pytest.mark.addresses
@allure.feature("Addresses")
class TestAddressesRetrieval(BaseAssertions):
    """Test for GET /addresses - GET /addresses?customer_id= and GET /addresses/<id>"""

    @allure.story("List all addresses")
    def test_list_addresses(self, address_service):
        """GET /addresses should return 200 with a list of addresses
        filterable by customer_id
        """
        response = address_service.list()

        self.using(response).assert_status_code_is(StatusCodes.OK)
        self.using(response).assert_schema(ADDRESS_LIST_SCHEMA)


    @allure.story("List all addresses by customer_id")
    def test_list_addresses_customer_id(self, address_service, customer_service):
        """GET /addresses?customer_id= should return 200 with a list of addresses
        for specific customer.
        """
        customer_factory = CustomerFactory(customer_service)
        customer = customer_factory.create()
        customer_id = customer["id"]

        # Address 1
        address1 = Address(customer_id=customer_id)
        payload1 = address_create_payload(address1, customer_id)

        response_1 = address_service.create(payload1)
        data_1 =  response_1.json()

        #Address 2
        address2 = Address(customer_id=customer_id)
        payload2 = address_create_payload(address2, customer_id, label="work", street="321 Main St")

        response_2 = address_service.create(payload2)
        data_2 =  response_2.json()

        get_response = address_service.list(customer_id)
        data = get_response.json()

        self.using(get_response).assert_status_code_is(StatusCodes.OK)
        self.using(get_response).assert_schema(ADDRESS_LIST_SCHEMA)
        for address in data:
            assert address["customer_id"] == customer_id
        assert len(data) == 2

        #CLEANUP
        address_service.delete_address(data_1["id"])
        address_service.delete_address(data_2["id"])
        customer_factory.cleanup(customer_id)


    @allure.story("Get addresses by id")
    def test_get_addresses_by_id(self, address_service, customer_service):
        """GET /addresses/<id> should return 200 with the address matching the
        specified ID.
        """
        customer_factory = CustomerFactory(customer_service)
        customer = customer_factory.create()
        customer_id = customer["id"]

        address = Address(customer_id=customer_id)
        payload = address_create_payload(address, customer_id)

        response = address_service.create(payload)

        data = response.json()

        get_response = address_service.get_by_id(data["id"])

        self.using(get_response).assert_status_code_is(StatusCodes.OK)

        #CLEANUP
        customer_factory.cleanup(customer_id)


    @allure.story("Get non-existent address")
    def test_get_address_not_found(self, address_service):
        """GET /address/99999 should return 404 when no address exists with that ID."""
        response = address_service.get_by_id(99999)

        self.using(response).assert_status_code_is(StatusCodes.NOT_FOUND)
        self.using(response).assert_response_has_key("message")


@pytest.mark.addresses
@allure.feature("Addresses")
class TestAddressesUpdate(BaseAssertions):
    """Tests for PUT /addresses/<id>."""

    @allure.story("Update Address fields.")
    def test_update_address_success(self, customer_service, address_service):
        """PUT /addresses/<id> should update the provided fields and return 200.
        Only the specified fields change; others remain untouched."""

        customer_factory = CustomerFactory(customer_service)
        customer = customer_factory.create()
        customer_id = customer["id"]

        address = Address(customer_id)
        payload= address_create_payload(address, customer_id)

        response = address_service.create(payload)
        data = response.json()

        update_payload = address_update_payload(label="work", city="321 north St.")

        update_response = address_service.update(data["id"], update_payload)

        self.using(update_response).assert_status_code_is(StatusCodes.OK)
        self.using(update_response).assert_response_has_key_value("label", update_payload["label"])
        self.using(update_response).assert_response_has_key_value("city", update_payload["city"])
        self.using(update_response).assert_response_has_key_value("zip_code", data["zip_code"])

        #CLEANUP
        customer_factory.cleanup(customer_id)


    @allure.story("Update non-existent Address.")
    def test_update_nonexist_address(self, address_service):
        """PUT /addresses/999999 should return 404 and message."""

        address_id = 999999
        update_payload = address_update_payload(label="work", city="321 north St.")
        response = address_service.update(address_id, update_payload)

        self.using(response).assert_status_code_is(StatusCodes.NOT_FOUND)
        self.using(response).assert_response_has_key("message")


    @allure.story("Update address timestamp.")
    def test_update_address_timestamp(self, customer_service, address_service):
        """PUT /addresses/<id> should update the provided fields and return 200.
        timestamp must change."""

        customer_factory = CustomerFactory(customer_service)
        customer = customer_factory.create()
        customer_id = customer["id"]

        address = Address(customer_id)
        payload= address_create_payload(address, customer_id)

        response = address_service.create(payload)
        data = response.json()

        update_payload = address_update_payload(label="work")

        update_response = address_service.update(data["id"], update_payload)
        update_data = update_response.json()

        self.using(update_response).assert_status_code_is(StatusCodes.OK)
        self.using(update_response).assert_response_has_key_value("label", update_payload["label"])
        assert update_data["updated_at"] > data["updated_at"]

        #CLEANUP
        customer_factory.cleanup(customer_id)

@pytest.mark.addresses
@allure.feature("Addresses")
class TestAddressDelete(BaseAssertions):
    """Test for DELETE /addressess/<id>."""

    @pytest.mark.prueba
    @allure.story("Delete address successfully")
    def test_delete_address_success(self, customer_service, address_service):
        """DELETE /addresses/<id> - should return 200 and delete the address permanently."""

        customer_factory = CustomerFactory(customer_service)
        customer = customer_factory.create()
        customer_id = customer["id"]

        address = Address(customer_id)
        payload = address_create_payload(address, customer_id)

        response = address_service.create(payload)
        data = response.json()

        delete_response = address_service.delete_address(data["id"])

        self.using(delete_response).assert_status_code_is(StatusCodes.OK)
        self.using(delete_response).assert_response_has_key("message")

        #Verify
        get_response = address_service.get_by_id(data["id"])
        self.using(get_response).assert_status_code_is(StatusCodes.NOT_FOUND)

        #CLEANUP
        customer_factory.cleanup(customer_id)


    @allure.story("Delete non-existent address")
    def test_delete_nonexist_address(self, address_service):
        """DELETE /addresses/999999 - should return 404 and message."""

        address_id = 999999

        response = address_service.delete_address(address_id)

        self.using(response).assert_status_code_is(StatusCodes.NOT_FOUND)
        self.using(response).assert_response_has_key("message")