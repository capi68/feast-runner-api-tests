"""Centralized API endpoint definitions."""


class RestaurantEndpoints:
    BASE = "/restaurants"
    DETAIL = "/restaurants/{restaurant_id}"
    LOGIN = "/restaurants/login"


class MenuEndpoints:
    BASE = "/menus"
    DETAIL = "/menus/{menu_id}"


class MenuItemEndpoints:
    BASE = "/menu-items"
    DETAIL = "/menu-items/{item_id}"


class CustomerEndpoints:
    BASE = "/customers"
    DETAIL = "/customers/{customer_id}"
    LOGIN = "/customers/login"


class AddressEndpoints:
    BASE = "/addresses"
    DETAIL = "/addresses/{address_id}"


class CourierEndpoints:
    BASE = "/couriers"
    DETAIL = "/couriers/{courier_id}"
    LOGIN = "/couriers/login"


class OrderEndpoints:
    BASE = "/orders"
    DETAIL = "/orders/{order_id}"
    ITEMS = "/orders/{order_id}/items"


class DeliveryEndpoints:
    BASE = "/deliveries"
    DETAIL = "/deliveries/{delivery_id}"


class RatingEndpoints:
    BASE = "/ratings"
    DETAIL = "/ratings/{rating_id}"
