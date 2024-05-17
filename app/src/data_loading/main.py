import re
from datetime import datetime, timedelta
import pandas as pd
from src.utils import Logging, pydantic_to_pandas, load_config
from src.data_loading.noise_api import NoiseApi
from src.data_loading.models import NoiseRequestParams

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
    api: NoiseApi, location_id: str, since: str
) -> pd.DataFrame:
    """
    Make an API request for noise data at a specific location, in a specific time frame.
    """
    params = NoiseRequestParams(start=since_to_datetime(since))
    location_data = api.get_location_noise_data(location_id, params)
    stats = pydantic_to_pandas(location_data.measurements)

    return stats


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
    start_time: datetime = None,
    end_time: datetime = None,
):
    # if no start time is provided, set it to 2 weeks ago
    # this is a temporary workaround for a bug in the API
    if not start_time:
        start_time = since_to_datetime("2w")

    params = NoiseRequestParams(start=start_time, end=end_time)
    location_data = api.get_location_noise_data(location_id, params)

    return location_data


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
