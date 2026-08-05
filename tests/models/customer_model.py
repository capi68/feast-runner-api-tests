"""Customer domain model."""

from tests.base.base_model import BaseModel

class Customer(BaseModel):
    """Represents a customer entity."""

    def __init__(
            self,
            first_name: str = "Ana",
            last_name: str = "Lopez",
            email: str | None = None,
            phone: str = "+1234567890",
            password: str = "Customer123!",
    ):
        super().__init__()
        self.first_name = first_name
        self.last_name = last_name
        self.email = email
        self.phone = phone
        self.password = password