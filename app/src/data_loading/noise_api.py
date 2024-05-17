"""
Base data loader definitions for issuing requests.
"""
from urllib.parse import urljoin
import httpx
from src.utils import Logging
from src.data_loading.models import (
    AggregateLocationNoiseData,
    TimedLocationNoiseData,
    NoiseRequestParams,
    LocationsData,
    AbstractLocationNoiseData,
)

logger = Logging.get_console_logger()


class NoiseApi:
    """
    Data loader from WebCOMAND API v1.
    """

    def __init__(self, url: str):
        self.url = url

    def _get(self, endpoint: str, params: NoiseRequestParams = None) -> dict:
        """
        Get data from the API and return as a json/dict.
        """
        full_url = urljoin(self.url, endpoint)
        params = params.model_dump(exclude_unset=True) if params else None

        response = httpx.get(full_url, params=params)
        logger.info(f"GET Request: {response.url}")

        response.raise_for_status()

        return response.json()

    def get_locations(self) -> LocationsData:
        """
        Get locations from the API.
        """
        response = self._get("locations")

        return LocationsData(**response)

    def get_location_noise_data(
        self, location_id: str, params: NoiseRequestParams = None
    ) -> AbstractLocationNoiseData:
        """
        Get noise data for a location.
        """
        noise_data = self._get(f"locations/{location_id}/noise", params=params)

        if params and params.granularity == "life-time":
            noise_data = AggregateLocationNoiseData(**noise_data)
        else:
            noise_data = TimedLocationNoiseData(**noise_data)

        return noise_data
