"""Address domain model."""

from tests.base.base_model import BaseModel

class Address(BaseModel):
    """Represent an Address entity."""

    def __init__(
            self,
            customer_id: int | None = None,
            label: str = "Home",
            street: str = "123 Main Street",
            city: str = "Miami",
            state: str = "Florida",
            zip_code: str = "33101",
            latitude: float| None = 25.761681,
            longitude: float| None = -80.191788,
            is_default: bool = False,
    ):
        super().__init__()
        self.customer_id = customer_id
        self.label = label
        self.street = street
        self.city = city
        self.state = state
        self.zip_code =  zip_code
        self.latitude = latitude
        self.longitude = longitude
        self.is_default = is_default