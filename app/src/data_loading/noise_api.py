from urllib.parse import urljoin
import httpx
from src.utils import Logging
from src.data_loading.models import *

logger = Logging.get_console_logger()


class NoiseApi:
    """
    Data loader from WebCOMAND API
    """

    def __init__(self, url: str):
        self.url = url

    def _get(self, url: str, params: dict = None) -> dict:
        """
        Get data from the API.
        """
        response = httpx.get(urljoin(self.url, url), params=params)
        logger.info(f"GET Request: {url}")

        response.raise_for_status()
        return response.json()

    def get_locations(self) -> LocationsData:
        """
        Get locations from the API.
        """
        response = self._get("locations")
        return LocationsData(**response)

    def get_location_noise_data(
            self, location_id: str,
            params: NoiseRequestParams) -> LocationNoiseData:
        """
        Get noise data for a location.
        """
        noise_data = self._get(f"locations/{location_id}/noise",
                               params=params.model_dump())
        return LocationNoiseData(**noise_data)
