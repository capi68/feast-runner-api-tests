"""Couriers domain model."""

from tests.base.base_model import BaseModel

class Courier(BaseModel):
    """Represents a Couriers entity."""

    def __init__(
            self,
            first_name: str = "Carlos",
            last_name: str = "Ramirez",
            email: str | None = None,
            phone: str = "+1987654321",
            password: str = "Courier123!",
            vehicle_type: str = "bicycle",
            license_plate: str = "XYZ-789",
            is_available: bool = True,
            is_active: bool = True
    ):
        super().__init__()
        self.first_name = first_name
        self.last_name = last_name
        self.email = email
        self.phone = phone
        self.password = password
        self.vehicle_type = vehicle_type
        self.license_plate = license_plate
        self.is_available = is_available
        self.is_active = is_active