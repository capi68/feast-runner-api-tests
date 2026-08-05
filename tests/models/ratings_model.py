"""Ratings domain model."""

from tests.base.base_model import BaseModel

class Rating(BaseModel):
    """Represents a Rating entity."""

    def __init__(
            self,
            order_id: int | None = None,
            food_score: int = 4,
            delivery_score: int = 5,
            comment: str = "Great food, fast delivery!",
    ):
        super().__init__()
        self.order_id = order_id
        self.food_score = food_score
        self.delivery_score = delivery_score
        self.comment = comment