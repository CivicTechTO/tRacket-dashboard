"""
Base data loader definitions for issuing requests to the Webcommand Noise API.
"""
import asyncio
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

    def __init__(self, url: str, request_timeout: float = 60.0):
        self.url = url
        self.timeout = httpx.Timeout(request_timeout, connect=10.0)
        self.page_batch_size = 3  # Number of pages to fetch concurrently when paginating

    async def _async_get(
        self,
        client: httpx.AsyncClient,
        endpoint: str,
        params: NoiseRequestParams = None,
    ) -> dict:
        """
        Get data from the API and return as a json/dict.
        """
        full_url = urljoin(self.url, endpoint)
        params = (
            params.model_dump(exclude_unset=True, exclude_none=True)
            if params
            else None
        )

        response = await client.get(full_url, params=params)
        logger.info(f"GET Request: {response.url}")

        response.raise_for_status()

        return response.json()

    def _get(self, endpoint: str, params: NoiseRequestParams = None) -> dict:
        """Get data from the API synchronously."""
        return asyncio.run(self._async_get_with_client(endpoint, params))

    async def _async_get_with_client(
        self, endpoint: str, params: NoiseRequestParams = None
    ) -> dict:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            return await self._async_get(client, endpoint, params)

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
        return asyncio.run(
            self.async_get_location_noise_data(location_id, params=params)
        )

    async def async_get_location_noise_data(
        self,
        location_id: str,
        params: NoiseRequestParams = None,
    ) -> AbstractLocationNoiseData:
        """Get location noise data using bounded concurrent page batches."""
        if self.page_batch_size < 1:
            raise ValueError("page_batch_size must be at least 1")

        params, paginate = self._paginate_check(params)
        endpoint = f"locations/{location_id}/noise"

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            noise_data = await self._async_get(client, endpoint, params=params)

            collected_measurements = list(noise_data["measurements"])

            if paginate and collected_measurements:
                next_page = params.page + 1
                while True:
                    page_numbers = range(
                        next_page, next_page + self.page_batch_size
                    )
                    page_results = await asyncio.gather(
                        *(
                            self._async_get(
                                client,
                                endpoint,
                                params.model_copy(update={"page": page}),
                            )
                            for page in page_numbers
                        )
                    )

                    reached_end = False
                    for page_data in page_results:
                        measurements = page_data["measurements"]
                        if not measurements:
                            reached_end = True
                            break
                        collected_measurements.extend(measurements)

                    if reached_end:
                        break

                    next_page += self.page_batch_size

        if params.granularity == Granularity.life_time:
            return AggregateLocationNoiseData(
                measurements=collected_measurements
            )

        return TimedLocationNoiseData(measurements=collected_measurements)

    def _paginate_check(
        self, params: NoiseRequestParams
    ) -> tuple[NoiseRequestParams, bool]:
        """
        Decide if the API request should be paginated and set up the params accordingly.
        Only paginate if the user did not provide params or page and if its not an aggregate call.
        """

        paginate = False

        if params is None:
            params = NoiseRequestParams(page=0)
            paginate = True

        elif (
            params.page is None and params.granularity != Granularity.life_time
        ):
            params = params.model_copy(update={"page": 0})
            paginate = True

        return params, paginate
