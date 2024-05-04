import re
import os
from datetime import datetime, timedelta
from typing import List
import pandas as pd
from src.utils import Logging
from src.data_loading.noise_api import NoiseApi
from src.data_loading.models import LocationNoiseData, NoiseRequestParams
from dotenv import load_dotenv

logger = Logging.get_console_logger()

const_since_aliases = {
    "s": "seconds",
    "m": "minutes",
    "h": "hours",
    "d": "days",
}


def since_to_datetime(alias: str):
    num = re.search(r"\d+", alias).group()
    num = int(num)
    unit = re.search(r"[a-zA-Z]+", alias).group()

    now = datetime.now()

    if unit in ["s", "m", "h", "d"]:
        unit = const_since_aliases[unit]
        time = timedelta(**{unit: num})
        return now - time
    elif unit == "w":
        time = timedelta(days=num * 7)
        return now - time
    elif unit == "M":
        time = timedelta(days=num * 30)
        return now - time
    elif unit == "y":
        year = now.year - num
        return now.replace(year=year)
    else:
        raise ValueError("Invalid time unit")


def get_location_stats(api: NoiseApi, location_id: str, since: str):
    params = NoiseRequestParams(start=since_to_datetime(since))
    location_data = api.get_location_noise_data(location_id, params)
    stats = pd.DataFrame(data.measurements.model_dump())
    return stats


def get_locations(api: NoiseApi):
    return api.get_locations()


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
    if not url:
        load_dotenv()
        url = os.getenv("API_URL")

    if not url:
        url = "https://noisemeter.webcomand.com/api/v1/"

    return NoiseApi(url)
