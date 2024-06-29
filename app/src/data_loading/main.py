"""
Main data loading functionalities.
"""
import re
from datetime import datetime, timedelta
from typing import Dict
import pandas as pd
from src.utils import (
    Logging,
    pydantic_to_pandas,
    load_config,
    DataFormatter,
    COLUMN,
)
from src.data_loading.noise_api import NoiseApi
from src.data_loading.models import NoiseRequestParams, Granularity

logger = Logging.get_console_logger()
config = load_config()


class AppDataManager:
    """
    Class for collecting all the required data for the dashboard.
    """

    def __init__(self) -> None:
        self.config = load_config()
        self.api = self._create_api()

        self.data_formatter = DataFormatter()

        # data store
        self.locations: pd.DataFrame = None
        self.location_stats: pd.DataFrame = None
        self.location_noise: Dict[Granularity, pd.DataFrame] = dict()
        self.location_info: pd.DataFrame = None

    def _create_api(self, url: str = None) -> NoiseApi:
        """
        Create noise api for data loading.
        """
        if url is None:
            url = config["api"]["url"]

        return NoiseApi(url)

    def _request_location_stats(
        self, api: NoiseApi, location_id: str
    ) -> pd.DataFrame:
        """
        Make an API request for life-time, aggregate noise data at a specific location.
        """
        params = NoiseRequestParams(granularity=Granularity.life_time)

        aggregate_data = api.get_location_noise_data(location_id, params)
        stats_df = pydantic_to_pandas(aggregate_data.measurements)

        logger.info(f"Received {stats_df.shape[0]} rows of stats.")

        return stats_df

    def _request_locations(
        self, api: NoiseApi, location_id: str = None
    ) -> pd.DataFrame:
        """
        Make an API request for all device locations.
        """
        locations = api.get_locations(location_id=location_id)
        locations_df = pydantic_to_pandas(locations.locations)

        logger.info(f"Received {locations_df.shape[0]} locations.")

        return locations_df

    def _request_location_noise(
        self,
        api: NoiseApi,
        location_id: str,
        start_time: datetime,
        end_time: datetime,
        granularity: Granularity = Granularity.hourly,
    ) -> pd.DataFrame:
        """
        Pull noise data for a given location and timeframe.
        """
        params = NoiseRequestParams(
            start=start_time, end=end_time, granularity=granularity
        )
        noise_data = api.get_location_noise_data(location_id, params)
        noise_df = pydantic_to_pandas(noise_data.measurements)

        logger.info(f"Received {noise_df.shape[0]} measurements.")

        return noise_df

    def load_and_format_location_info(self, location_id: str) -> pd.DataFrame:
        """
        Load and format the device location info for one location.
        """
        location_info = self._request_locations(self.api, location_id=location_id)
        location_info = self.data_formatter._string_col_names_to_enum(
            location_info
        )
        location_info = self.data_formatter._set_data_types(location_info)

        self.location_info = location_info

        return location_info

    def is_noise_available(self, location_id: str) -> bool:
        """
        Check if there is noise data available.
        """
        if self.location_stats is None:
            self.load_and_format_location_stats(location_id=location_id)

        return self.location_stats[COLUMN.COUNT].values[0] == 0

    def get_radius(self, location_id: str) -> int:
        """
        Return the radius for the device.
        """
        if self.location_info is None:
            self.load_and_format_location_info(location_id=location_id)

        info = self.location_info.to_dict("records")[0]
        radius = info[COLUMN.RADIUS]

        return radius

    def get_label(self, location_id: str) -> int:
        """
        Return the label for the device.
        """
        if self.location_info is None:
            self.load_and_format_location_info(location_id=location_id)

        info = self.location_info.to_dict("records")[0]
        label = info[COLUMN.LABEL]

        return label

    def get_active_status(self, location_id: str) -> int:
        """
        Return the activity status for the device.
        """
        if self.location_info is None:
            self.load_and_format_location_info(location_id=location_id)

        info = self.location_info.to_dict("records")[0]
        active = info[COLUMN.ACTIVE]

        return active

    def load_and_format_locations(self):
        """
        Load and format the device location data for the whole system.
        """
        locations = self._request_locations(self.api)
        locations = self.data_formatter._string_col_names_to_enum(locations)
        locations = self.data_formatter._set_data_types(locations)

        if self.config["map"]["filter_active"].lower() == "true":
            locations = self._filter_active(locations)
            logger.info(
                f"Filtered active only to {locations.shape[0]} locations."
            )

        if self.config["map"]["deduplicate"].lower() == "true":
            locations = self._deduplicate(locations)
            logger.info(f"Deduplicated to {locations.shape[0]} locations.")

        self.locations = locations

    def _deduplicate(self, locations: pd.DataFrame) -> pd.DataFrame:
        """
        Keep unique device IDs only.
        """
        return locations.groupby(COLUMN.DEVICEID).first().reset_index()

    def _filter_active(self, locations: pd.DataFrame) -> pd.DataFrame:
        """
        Keep active locations only.
        """
        return locations[locations[COLUMN.ACTIVE] == True]

    def load_and_format_location_stats(self, location_id=str) -> pd.DataFrame:
        """
        Load the life-time aggregate stats for the location.
        """
        stats = self._request_location_stats(self.api, location_id=location_id)
        stats = self.data_formatter._string_col_names_to_enum(stats)
        stats = self.data_formatter._set_data_types(stats)

        self.location_stats = stats

        return stats

    def load_and_format_location_noise(
        self, location_id: str, granularity: Granularity
    ):
        """
        Load the last seven days of the noise data at a specific location.
        """
        if self.location_stats is None:
            self.load_and_format_location_stats(location_id=location_id)

        end = self.location_stats.loc[0, COLUMN.END]
        start = end - timedelta(days=7)

        noise_data = self._request_location_noise(
            self.api,
            location_id=location_id,
            start_time=start,
            end_time=end,
            granularity=granularity,
        )
        noise_data = self.data_formatter._string_col_names_to_enum(noise_data)
        noise_data = self.data_formatter._set_data_types(noise_data)

        if self.config["plot"]["fill_gaps"].lower() == "true":
            noise_data = self.data_formatter._fill_missing_times(
                noise_data, freq="H"
            )

        self.location_noise[granularity] = noise_data
