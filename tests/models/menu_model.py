"""Menu domain model."""

from tests.base.base_model import BaseModel


class Menu(BaseModel):
    """Represents a menu entity belonging to a restaurant."""

    def __init__(
        self,
        restaurant_id: int | None = None,
        name: str = "Lunch Menu",
        description: str = "Available 11am-3pm",
    ):
        super().__init__()
        self.restaurant_id = restaurant_id
        self.name = name
        self.description = description
