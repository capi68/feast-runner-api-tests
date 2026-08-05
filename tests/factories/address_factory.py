"""Factory for creating addresses preconditions.
Creates an address via the API and returns the response data.
Used when other entities (Order) need address for exist first.
"""

from tests.services.address_service import AddressService
from tests.payloads.address_payloads import address_create_payload
from tests.services.customer_service import CustomerService
from tests.factories.customer_factory import CustomerFactory
from tests.models.address_model import Address
from tests.utils.constants import StatusCodes
from tests.utils.logger import get_logger

logger = get_logger(__name__)

class AddressFactory:
    """Creates address preconditions via the API."""

    def __init__(self, address_service: AddressService, customer_service: CustomerService = None):
        self._address_service = address_service
        self._customer_factory = CustomerFactory(customer_service)


    def create(self, customer_id: int = None, **overrides):
        """Create an address with its dependencies and return the response JSON.

        Args:
            customer_id: ID of existing customer. If None, creates one.
            **overrides: Any fields to override in the default payload.

        Returns:
            dict: The created addresses response from the API.
        """

        #create customer dependency if not provided
        if customer_id is None:
            customer = self._customer_factory.create()
            customer_id = customer["id"]

        address = Address(customer_id=customer_id)
        payload = address_create_payload(address, customer_id)
        payload.update(overrides)

        response = self._address_service.create(payload)

        assert response.status_code == StatusCodes.CREATED, f"Factory failed to create address: {response.text}"

        data = response.json()
        data["customer_id"] = customer_id

        logger.info("Factory created address id=%s for customer=%s", data["id"], customer_id)

        return data


    def cleanup(self, address_id) -> None:
        """Clean up address created by this factory"""
        response = self._address_service.delete_address(address_id)
        if response.status_code == StatusCodes.OK:
            logger.info("Factory cleaned up address id=%s", address_id)
        else:
            logger.warning(
                "Factory cleanup failed for address id=%s (%s): %s",
                address_id,
                response.status_code,
                response.text
            )

    def cleanup_all(self, customer_id: int) -> None:
        """Clean up all resources created by this factory"""
        self._customer_factory.cleanup(customer_id)