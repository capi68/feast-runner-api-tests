"""Factory for creating Customer preconditions.
Creates a Customer via the API and returns the response data.
Used when other entities (Address, Order, etc.) need a customer for exist first.
"""

from tests.services.customer_service import CustomerService
from tests.payloads.customers_payloads import customer_create_payload
from tests.utils.constants import StatusCodes
from tests.utils.logger import get_logger

logger = get_logger(__name__)

class CustomerFactory:
    """Creates Customer preconditions via the API."""

    def __init__(self, service: CustomerService = None):
        self._service = service or CustomerService()

    def create(self, **overrides) -> dict:
        """Create a Customer and return the response JSON.

        Args:
            **overrides: Any fields to override in the default payload.
        Returns:
            dict: The created customer response from the API.
        """

        payload = customer_create_payload()
        payload.update(overrides)

        response = self._service.create(payload)
        assert response.status_code == StatusCodes.CREATED, f"factory failed to create customer: {response.text}"

        data = response.json()

        logger.info("Factory created customer id=%s, first_name='%s', email='%s'", data["id"], data["first_name"], data["email"])
        return data

    def cleanup(self, customer_id: int) -> None:
        """Delete a customer created by the factory."""
        response = self._service.delete_customer(customer_id)

        if response.status_code == StatusCodes.OK:
            logger.info("Factory cleaned up customer id=%s", customer_id)
        else:
            logger.warning(
                "Factory cleanup failed for customer id=%s (%s): %s",
                customer_id,
                response.status_code,
                response.text,
            )
