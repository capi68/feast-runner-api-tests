"""Item Order model."""

from tests.base.base_model import BaseModel

class OrderItem(BaseModel):
    """Represents an order item."""

    def __init__(
            self,
            menu_item_id: int |None = None,
            quantity: int = 2,
            special_instructions: str | None = "No Onion"
    ):
        super().__init__()
        self.menu_item_id = menu_item_id
        self.quantity = quantity
        self.special_instructions = special_instructions
