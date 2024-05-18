"""
Main data loading functionalities.
"""
import re
from datetime import datetime, timedelta
import pandas as pd
from src.utils import Logging, pydantic_to_pandas, load_config, DataFormatter, COLUMN
from src.data_loading.noise_api import NoiseApi
from src.data_loading.models import NoiseRequestParams, Granularity

logger = Logging.get_console_logger()
config = load_config()

const_since_aliases = {
    "s": "seconds",
    "m": "minutes",
    "h": "hours",
    "d": "days",
}





def since_to_datetime(alias: str) -> datetime:
    """
    Based on a string represented time delta `alias`,
    create the datetime representing current time minus `alias`.
    E.g. alias = "2 w" is mapped to the date time two weeks before.
    """
    num = re.search(r"\d+", alias).group()
    num = int(num)
    unit = re.search(r"[a-zA-Z]+", alias).group()

    now = datetime.now()

    if unit in ["s", "m", "h", "d"]:
        unit = const_since_aliases[unit]
        time = timedelta(**{unit: num})

        result = now - time
    elif unit == "w":
        time = timedelta(days=num * 7)

        result = now - time
    elif unit == "M":
        time = timedelta(days=num * 30)

        result = now - time
    elif unit == "y":
        year = now.year - num

        result = now.replace(year=year)
    else:
        raise ValueError("Invalid time unit")

    return result


def get_location_stats(
    api: NoiseApi, location_id: str
) -> pd.DataFrame:
    """
    Make an API request for noise data at a specific location, in a specific time frame.
    """
    params = NoiseRequestParams(granularity=Granularity.life_time)

    aggregate_data = api.get_location_noise_data(location_id, params)
    stats_df = pydantic_to_pandas(aggregate_data.measurements)

    logger.info(f"Received {stats_df.shape[0]} rows of stats.")

    return stats_df


def get_locations(api: NoiseApi) -> pd.DataFrame:
    """
    Make an API request for all device locations.
    """
    locations = api.get_locations()
    locations_df = pydantic_to_pandas(locations.locations)

    logger.info(f"Received {locations_df.shape[0]} locations.")

    return locations_df


def get_location_noise(
    api: NoiseApi,
    location_id: str,
    start_time: datetime,
    end_time: datetime,
) -> pd.DataFrame:
    """
    Pull noise data for a given location and timeframe.
    """
    params = NoiseRequestParams(start=start_time, end=end_time)
    noise_data = api.get_location_noise_data(location_id, params)
    noise_df = pydantic_to_pandas(noise_data.measurements)

    logger.info(f"Received {noise_df.shape[0]} measurements.")

    return noise_df


def get_location_average_noise(
    api: NoiseApi, location_id: str, since: str = "2w"
):
    stats = get_location_stats(api, location_id, since)

    if stats.empty:
        return None

    return stats["mean"].mean()


def create_api(url: str = None):
    """
    Create noise api for data loading.
    """
    if url is None:
        url = config["api"]["url"]

    return NoiseApi(url)


class AppDataManager():
    """
    Class for collecting all the required data for the dashboard.
    """
    def __init__(self) -> None:
        self.api = create_api()
        self.data_formatter = DataFormatter()

        self.locations: pd.DataFrame = None
        self.location_stats: pd.DataFrame = None
        self.location_noise: pd.DataFrame = None

    def load_and_format_locations(self):
        locations = get_locations(self.api)
        locations = self.data_formatter._string_col_names_to_enum(locations)
        locations = self.data_formatter._set_data_types(locations)

        self.locations = locations

    def load_and_format_location_stats(self, location_id = str) -> None:
        """
        Load the life-time stats for the location.
        """
        stats = get_location_stats(self.api, location_id=location_id)
        stats = self.data_formatter._string_col_names_to_enum(stats)
        stats = self.data_formatter._set_data_types(stats)


        self.location_stats = stats
    
    def load_and_format_location_noise(self, location_id = str):
        """
        Load the last seven days of the location data.
        """
        self.load_and_format_location_stats(location_id=location_id)
        end = self.location_stats.loc[0, COLUMN.END]
        start = end - timedelta(days=7)

        noise_data = get_location_noise(self.api, location_id=location_id, start_time=start, end_time=end)
        noise_data = self.data_formatter._string_col_names_to_enum(noise_data)
        noise_data = self.data_formatter._set_data_types(noise_data)
        
        self.location_noise = noise_data


        
