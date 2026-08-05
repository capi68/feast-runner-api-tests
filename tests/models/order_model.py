"""Order domain model."""

from tests.base.base_model import BaseModel
from tests.models.order_item_model import OrderItem

class Order(BaseModel):
    """Represents an order entity."""

    def __init__(
            self,
            items: list[OrderItem],
            customer_id: int | None = None,
            restaurant_id: int | None = None,
            address_id: int | None = None,
            notes: str = "Especial combo",
    ):
        super().__init__()
        self.customer_id = customer_id
        self.restaurant_id = restaurant_id
        self.address_id = address_id
        self.items = items
        self.notes = notes