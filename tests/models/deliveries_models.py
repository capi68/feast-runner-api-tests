"""Deliveries domain model."""

from tests.base.base_model import BaseModel

class Delivery(BaseModel):
    """Represents a delivery entity."""

    def __init__(
            self,
            order_id: int | None = None,
            courier_id: int | None = None,
            distance_km: float | None = 5.2,
            picked_up_at: str | None = None,
            delivered_at: str | None = None
    ):
        super().__init__()
        self.order_id = order_id
        self.courier_id = courier_id
        self.distance_km = distance_km
        self.picked_up_at = picked_up_at
        self.delivered_at = delivered_at

