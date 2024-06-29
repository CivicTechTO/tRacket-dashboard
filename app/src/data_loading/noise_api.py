"""
Base data loader definitions for issuing requests to the Webcommand Noise API.
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
from src.data_loading.models import Granularity

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
        params = (
            params.model_dump(exclude_unset=True, exclude_none=True)
            if params
            else None
        )

        response = httpx.get(full_url, params=params)
        logger.info(f"GET Request: {response.url}")

        response.raise_for_status()

        return response.json()

    def get_locations(self, location_id: str = None) -> LocationsData:
        """
        Get locations from the API.
        If ID is specified then info for only one location is pulled.
        """
        endpoint = "locations"
        if location_id:
            endpoint += f"/{location_id}"

        response = self._get(endpoint)

        return LocationsData(**response)

    def get_location_noise_data(
        self, location_id: str, params: NoiseRequestParams = None
    ) -> AbstractLocationNoiseData:
        """
        Get noise data for a location. Loading is paginated by default unless caller provides explicit page.
        """
        noise_data = self._get(f"locations/{location_id}/noise", params=params)

        collected_noise_data = {"measurements": []}
        collected_noise_data["measurements"].extend(noise_data["measurements"])

        params, paginate = self._paginate_check(params)

        if paginate:
            while len(noise_data["measurements"]) > 0:
                params.page += 1
                noise_data = self._get(
                    f"locations/{location_id}/noise", params=params
                )
                collected_noise_data["measurements"].extend(
                    noise_data["measurements"]
                )

        if params and params.granularity == Granularity.life_time:
            noise_data = AggregateLocationNoiseData(**collected_noise_data)
        else:
            noise_data = TimedLocationNoiseData(**collected_noise_data)

        return noise_data

    def _paginate_check(
        self, params: NoiseRequestParams
    ) -> tuple[NoiseRequestParams, bool]:
        """
        Decide if the API request should be paginated and set up the params accordingly.
        Only paginate if the user did not provide params or page and if its not an aggregate call.
        """

        paginate = False

        if params is None:
            params = NoiseRequestParams(**{"page": 0})
            paginate = True

        elif (
            params.page is None and params.granularity != Granularity.life_time
        ):
            params.page = 0
            paginate = True

        return params, paginate
