"""Menu item domain model."""

from tests.base.base_model import BaseModel

class MenuItem(BaseModel):
    """Represents a menu item entity."""

    def __init__(
            self,
            menu_id: int,
            name: str = "Margherita Pizza",
            description: str = "Classic Margherita pizza with fresh mozzarella, tomato sauce, basil, and a crispy thin crust.",
            price: float = 12.99,
            category: str = "appetizer",
            preparation_time_minutes: int = 25,
            is_available: bool = True
    ):
        super().__init__()
        self.menu_id = menu_id
        self.name = name
        self.description = description
        self.price = price
        self.category = category
        self.preparation_time_minutes = preparation_time_minutes
        self.is_available = is_available