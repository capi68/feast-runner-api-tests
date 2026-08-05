"""Constants and enumerations for the test framework."""


class CuisineTypes:
    ITALIAN = "italian"
    MEXICAN = "mexican"
    JAPANESE = "japanese"
    CHINESE = "chinese"
    AMERICAN = "american"
    INDIAN = "indian"
    THAI = "thai"
    MEDITERRANEAN = "mediterranean"
    ALL = [ITALIAN, MEXICAN, JAPANESE, CHINESE, AMERICAN, INDIAN, THAI, MEDITERRANEAN]


class RestaurantStatuses:
    ACTIVE = "active"
    SUSPENDED = "suspended"
    CLOSED = "closed"
    ALL = [ACTIVE, SUSPENDED, CLOSED]
    TERMINAL = [CLOSED]


class MenuStatuses:
    DRAFT = "draft"
    ACTIVE = "active"
    ARCHIVED = "archived"
    ALL = [DRAFT, ACTIVE, ARCHIVED]
    TERMINAL = [ARCHIVED]


class MenuItemCategories:
    APPETIZER = "appetizer"
    MAIN = "main"
    SIDE = "side"
    DESSERT = "dessert"
    BEVERAGE = "beverage"
    COMBO = "combo"
    ALL = [APPETIZER, MAIN, SIDE, DESSERT, BEVERAGE, COMBO]


class VehicleTypes:
    BICYCLE = "bicycle"
    MOTORCYCLE = "motorcycle"
    CAR = "car"
    SCOOTER = "scooter"
    ALL = [BICYCLE, MOTORCYCLE, CAR, SCOOTER]


class OrderStatuses:
    PLACED = "placed"
    CONFIRMED = "confirmed"
    PREPARING = "preparing"
    READY = "ready"
    PICKED_UP = "picked_up"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"
    ALL = [PLACED, CONFIRMED, PREPARING, READY, PICKED_UP, DELIVERED, CANCELLED]
    TERMINAL = [DELIVERED, CANCELLED]
    CANCELLABLE = [PLACED, CONFIRMED]


class DeliveryStatuses:
    ASSIGNED = "assigned"
    PICKED_UP = "picked_up"
    IN_TRANSIT = "in_transit"
    DELIVERED = "delivered"
    FAILED = "failed"
    ALL = [ASSIGNED, PICKED_UP, IN_TRANSIT, DELIVERED, FAILED]
    TERMINAL = [DELIVERED, FAILED]


class StatusCodes:
    OK = 200
    CREATED = 201
    BAD_REQUEST = 400
    UNAUTHORIZED = 401
    NOT_FOUND = 404
    CONFLICT = 409
    INTERNAL_ERROR = 500
