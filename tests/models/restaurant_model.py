"""Restaurant domain model."""

from tests.base.base_model import BaseModel


class Restaurant(BaseModel):
    """Represents a restaurant entity."""

    def __init__(
        self,
        name: str = "Mario's Pizzeria",
        cuisine_type: str = "italian",
        phone: str = "+1234567890",
        email: str | None = None,
        password: str = "Restaurant123!",
        opening_hours: str = "09:00-23:00",
        min_order_amount: float = 15.00,
        delivery_radius_km: float = 10.0,
    ):
        super().__init__()
        self.name = name
        self.cuisine_type = cuisine_type
        self.phone = phone
        self.email = email
        self.password = password
        self.opening_hours = opening_hours
        self.min_order_amount = min_order_amount
        self.delivery_radius_km = delivery_radius_km
