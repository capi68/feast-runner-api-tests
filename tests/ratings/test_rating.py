"Test for the Ratings API."

import allure
import pytest

from tests.base.base_assertions import BaseAssertions
from tests.models.ratings_model import Rating
from tests.factories.order_factory import OrderFactory
from tests.payloads.ratings_payloads import rating_create_payload
from tests.schemas.ratings_schemas import RATING_RESPONSE_SCHEMA, RATING_LIST_SCHEMA
from tests.utils.logger import get_logger
from tests.utils.constants import StatusCodes

logger = get_logger(__name__)

@pytest.mark.ratings
@allure.feature("Ratings")
class TestRatingsCreation(BaseAssertions):
    """Tests for POST /ratings - ratings registration.
    Validates that the ratings creation endpoint correctly handles
    valid input, missing fields, invalid data.
    """

    @allure.story("Create rating with valid data")
    def test_create_rating_success(
            self,
            menu_service,
            menu_items_service,
            restaurant_service,
            address_service,
            customer_service,
            order_service,
            rating_service
    ):
        """POST /ratings with all valid required fields should return 201
        and a response matching the Rating Response schema."""
        #Create order via factory
        factory = OrderFactory(order_service, address_service,customer_service,menu_items_service,menu_service,restaurant_service)
        order = factory.create()
        order_id = order["id"]
        order_service.update(order_id, {"status": "confirmed"})
        order_service.update(order_id, {"status": "preparing"})
        order_service.update(order_id, {"status": "ready"})
        order_service.update(order_id, {"status": "picked_up"})
        order_service.update(order_id, {"status": "delivered"})

        rating = Rating(order_id=order_id)
        payload = rating_create_payload(rating)
        response = rating_service.create(payload)

        self.using(response).assert_status_code_is(StatusCodes.CREATED)
        self.using(response).assert_schema(RATING_RESPONSE_SCHEMA)
        self.using(response).assert_response_has_key_value("order_id", order_id)

        #CLEANUP
        factory.cleanup_all(order["customer_id"],order["address_id"],order["menu_item_id"],order["menu_id"],order["restaurant_id"])


    @allure.story("Create rating with out of range food_score")
    def test_create_rating_out_rage_food_score(
            self,
            menu_service,
            menu_items_service,
            restaurant_service,
            address_service,
            customer_service,
            order_service,
            rating_service
    ):
        """POST /ratings with data out of range food_score
        should return 400 and message."""
        #Create order via factory
        factory = OrderFactory(order_service, address_service,customer_service,menu_items_service,menu_service,restaurant_service)
        order = factory.create()
        order_id = order["id"]
        order_service.update(order_id, {"status": "confirmed"})
        order_service.update(order_id, {"status": "preparing"})
        order_service.update(order_id, {"status": "ready"})
        order_service.update(order_id, {"status": "picked_up"})
        order_service.update(order_id, {"status": "delivered"})

        rating = Rating(order_id=order_id)
        payload = rating_create_payload(rating, food_score=6)
        response = rating_service.create(payload)

        self.using(response).assert_status_code_is(StatusCodes.BAD_REQUEST)
        self.using(response).assert_response_has_key("message")

        #CLEANUP
        factory.cleanup_all(order["customer_id"],order["address_id"],order["menu_item_id"],order["menu_id"],order["restaurant_id"])


    @allure.story("Create rating with out of range delivery_score")
    def test_create_rating_out_rage_delivery_score(
            self,
            menu_service,
            menu_items_service,
            restaurant_service,
            address_service,
            customer_service,
            order_service,
            rating_service
    ):
        """POST /ratings with data out of range delivery_score
        should return 400 and message."""
        #Create order via factory
        factory = OrderFactory(order_service, address_service,customer_service,menu_items_service,menu_service,restaurant_service)
        order = factory.create()
        order_id = order["id"]
        order_service.update(order_id, {"status": "confirmed"})
        order_service.update(order_id, {"status": "preparing"})
        order_service.update(order_id, {"status": "ready"})
        order_service.update(order_id, {"status": "picked_up"})
        order_service.update(order_id, {"status": "delivered"})

        rating = Rating(order_id=order_id)
        payload = rating_create_payload(rating, delivery_score=0)
        response = rating_service.create(payload)

        self.using(response).assert_status_code_is(StatusCodes.BAD_REQUEST)
        self.using(response).assert_response_has_key("message")

        #CLEANUP
        factory.cleanup_all(order["customer_id"],order["address_id"],order["menu_item_id"],order["menu_id"],order["restaurant_id"])


    @allure.story("Create rating with empty body")
    def test_create_rating_missing_fields(
            self,
            menu_service,
            menu_items_service,
            restaurant_service,
            address_service,
            customer_service,
            order_service,
            rating_service
    ):
        """POST /ratings with empty body should return 400 and message."""

        response = rating_service.create({})

        self.using(response).assert_status_code_is(StatusCodes.BAD_REQUEST)
        self.using(response).assert_response_has_key("message")


    @allure.story("Create rating with long comment")
    def test_create_rating_comment_exceeds_max_length(
            self,
            menu_service,
            menu_items_service,
            restaurant_service,
            address_service,
            customer_service,
            order_service,
            rating_service
    ):
        """POST /ratings with comment exceeds max_length should return 400 and message."""
        #Create order via factory
        factory = OrderFactory(order_service, address_service,customer_service,menu_items_service,menu_service,restaurant_service)
        order = factory.create()
        order_id = order["id"]
        order_service.update(order_id, {"status": "confirmed"})
        order_service.update(order_id, {"status": "preparing"})
        order_service.update(order_id, {"status": "ready"})
        order_service.update(order_id, {"status": "picked_up"})
        order_service.update(order_id, {"status": "delivered"})

        rating = Rating(order_id=order_id)
        payload = rating_create_payload(rating, comment="a" * 501)
        response = rating_service.create(payload)

        self.using(response).assert_status_code_is(StatusCodes.BAD_REQUEST)
        self.using(response).assert_response_has_key("message")

        #CLEANUP
        factory.cleanup_all(order["customer_id"],order["address_id"],order["menu_item_id"],order["menu_id"],order["restaurant_id"])


    @allure.story("Create rating with order not found")
    def test_create_rating_order_not_found(self, rating_service):
        """POST /ratings should return 400 and message."""
        rating = Rating(order_id=999999)
        payload = rating_create_payload(rating)
        response = rating_service.create(payload)

        self.using(response).assert_status_code_is(StatusCodes.NOT_FOUND)
        self.using(response).assert_response_has_key("message")


    @allure.story("Create rating an order has already been rated")
    def test_create_rating_order_already_rated(
            self,
            menu_service,
            menu_items_service,
            restaurant_service,
            address_service,
            customer_service,
            order_service,
            rating_service
    ):
        """POST /ratings an order has already been rated 409 and message."""
        #Create order via factory
        factory = OrderFactory(order_service, address_service,customer_service,menu_items_service,menu_service,restaurant_service)
        order = factory.create()
        order_id = order["id"]
        order_service.update(order_id, {"status": "confirmed"})
        order_service.update(order_id, {"status": "preparing"})
        order_service.update(order_id, {"status": "ready"})
        order_service.update(order_id, {"status": "picked_up"})
        order_service.update(order_id, {"status": "delivered"})

        #first rating
        rating = Rating(order_id=order_id)
        payload = rating_create_payload(rating)
        rating_service.create(payload)

        #second rating
        payload_2 = rating_create_payload(rating, food_score=2)
        response = rating_service.create(payload_2)

        self.using(response).assert_status_code_is(StatusCodes.CONFLICT)
        self.using(response).assert_response_has_key("message")

        #CLEANUP
        factory.cleanup_all(order["customer_id"],order["address_id"],order["menu_item_id"],order["menu_id"],order["restaurant_id"])


    @allure.story("Create rating with empty required fields")
    @pytest.mark.parametrize("field", ["order_id", "food_score", "delivery_score"])
    def test_create_rating_empty_required_fields(
            self,
            menu_service,
            menu_items_service,
            restaurant_service,
            address_service,
            customer_service,
            order_service,
            rating_service,
            field
    ):
        """POST /ratings with empty required fields return 400 and message."""
        #Create order via factory
        factory = OrderFactory(order_service, address_service,customer_service,menu_items_service,menu_service,restaurant_service)
        order = factory.create()
        order_id = order["id"]
        order_service.update(order_id, {"status": "confirmed"})
        order_service.update(order_id, {"status": "preparing"})
        order_service.update(order_id, {"status": "ready"})
        order_service.update(order_id, {"status": "picked_up"})
        order_service.update(order_id, {"status": "delivered"})

        rating = Rating(order_id=order_id)
        payload = rating_create_payload(rating)
        payload[field] = ""
        response = rating_service.create(payload)

        self.using(response).assert_status_code_is(StatusCodes.BAD_REQUEST)
        self.using(response).assert_response_has_key("message")

        #CLEANUP
        factory.cleanup_all(order["customer_id"],order["address_id"],order["menu_item_id"],order["menu_id"],order["restaurant_id"])

@pytest.mark.ratings
@allure.feature("Rating")
class TestRatingRetrieval(BaseAssertions):
    """Test GET /ratings - GET /ratings?order_id= - GET /ratings/<id>"""

    @allure.story("GET list of ratings")
    def test_list_rating(self, rating_service):
        """GET /ratings - should return a list of ratings."""

        response = rating_service.list()

        self.using(response).assert_status_code_is(StatusCodes.OK)
        self.using(response).assert_schema(RATING_LIST_SCHEMA)


    @allure.story("get rating by id")
    def test_get_by_id(
            self,
            rating_service,
            menu_service,
            menu_items_service,
            restaurant_service,
            address_service,
            customer_service,
            order_service,
    ):
        """GET /ratings/<id> - should return 200 with a  rating matching with ID.
        Creates an order first, then retrieves it by the returned id.
        """
        #Create order via factory
        factory = OrderFactory(order_service, address_service,customer_service,menu_items_service,menu_service,restaurant_service)
        order = factory.create()
        order_id = order["id"]
        order_service.update(order_id, {"status": "confirmed"})
        order_service.update(order_id, {"status": "preparing"})
        order_service.update(order_id, {"status": "ready"})
        order_service.update(order_id, {"status": "picked_up"})
        order_service.update(order_id, {"status": "delivered"})

        rating = Rating(order_id=order_id)
        payload = rating_create_payload(rating)
        response = rating_service.create(payload)
        data = response.json()

        #get by id
        get_response = rating_service.get_by_id(data["id"])

        self.using(get_response).assert_status_code_is(StatusCodes.OK)
        self.using(get_response).assert_schema(RATING_RESPONSE_SCHEMA)

        #CLEANUP
        factory.cleanup_all(order["customer_id"],order["address_id"],order["menu_item_id"],order["menu_id"],order["restaurant_id"])

    @allure.story("Get by id not found")
    def test_get_by_id_not_found(self, rating_service,):
        """GET /ratings/999999 - should return 204 with message."""

        response = rating_service.get_by_id(999999)

        self.using(response).assert_status_code_is(StatusCodes.NOT_FOUND)
        self.using(response).assert_response_has_key("message")


    @allure.story("get rating filtered by order_id")
    def test_get_list_filtered_by_order_id(
            self,
            rating_service,
            menu_service,
            menu_items_service,
            restaurant_service,
            address_service,
            customer_service,
            order_service,
    ):
        """GET /ratings?order_id= - should return 200 with a  rating matching with order_id.
        Creates two orders first, then retrieves it by the returned order_id.
        """
        #Create order via factory
        factory = OrderFactory(order_service, address_service,customer_service,menu_items_service,menu_service,restaurant_service)
        order = factory.create()
        order_id = order["id"]
        order_service.update(order_id, {"status": "confirmed"})
        order_service.update(order_id, {"status": "preparing"})
        order_service.update(order_id, {"status": "ready"})
        order_service.update(order_id, {"status": "picked_up"})
        order_service.update(order_id, {"status": "delivered"})

        rating = Rating(order_id=order_id)
        payload = rating_create_payload(rating)
        response = rating_service.create(payload)
        data = response.json()

        #get by id
        get_response = rating_service.list(data["id"])
        data = get_response.json()

        self.using(get_response).assert_status_code_is(StatusCodes.OK)
        self.using(get_response).assert_schema(RATING_LIST_SCHEMA)
        assert all(rating["order_id"] == order_id for rating in data)

        #CLEANUP
        factory.cleanup_all(order["customer_id"],order["address_id"],order["menu_item_id"],order["menu_id"],order["restaurant_id"])

