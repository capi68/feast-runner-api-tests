"""Factory for creating Courier preconditions.
Creates a Courier via the API and returns the response data.
Used when deliveries entity need a courier for exist first.
"""

from tests.services.couriers_service import CouriersService
from tests.payloads.courier_payloads import courier_create_payload
from tests.utils.constants import StatusCodes
from tests.utils.logger import get_logger

logger = get_logger(__name__)


class CourierFactory:
    """Creates Courier preconditions via the API."""

    def __init__(self, courier_service: CouriersService = None):
        self._service = courier_service or CouriersService()

    def create(self, **overrides) -> dict:
        """Create a Courier and return the response JSON.

        Args:
            **overrides: Any fields to override in the default payload.
        Returns:
            dict: The created courier response from the API.
        """

        payload = courier_create_payload()
        payload.update(overrides)

        response = self._service.create(payload)
        assert response.status_code == StatusCodes.CREATED, f"Factory failed to create courier: {response.text}"

        data = response.json()

        logger.info("Factory created courier id=%s, first_name=%s, email=%s", data["id"], data["first_name"], data["email"])

        return data

    def cleanup(self, courier_id: int) -> None:
        """Delete a courier created by factory."""
        response = self._service.delete_courier(courier_id)

        if response.status_code == StatusCodes.OK:
            logger.info("Factory cleaned up courier id=%s", courier_id)
        else:
            logger.warning(
                "Factory cleanup failed for courier id=%s (%s): %s",
                courier_id,
                response.status_code,
                response.text
            )