from src.data_loading.noise_api import NoiseApi
from src.data_loading.models import (
    LocationsData,
    TimedLocationNoiseData,
    NoiseRequestParams,
    AggregateLocationNoiseData,
)
from src.data_loading.main import create_api
from src.data_loading.models import Granularity
from src.utils import get_current_dir, pydantic_to_pandas, load_config
import pytest
import os
from pydantic import ValidationError

### TEST PARAMS ###

CONFIG = load_config()
CURRENT_DIR = get_current_dir(__file__)
V1_API_TEST_ID = "572250"


### TEST v1 API ###


def test_noise_api_params():
    with pytest.raises(ValidationError) as e:
        NoiseRequestParams(page=-1)


@pytest.fixture
def noise_api() -> NoiseApi:
    """
    Noise API for data loading.
    """

    return create_api()


def test_noise_api_locations(noise_api: NoiseApi):
    """
    Load locations from the API and save.
    """
    result = noise_api.get_locations()

    df = pydantic_to_pandas(result.locations)
    df.to_csv(
        os.path.join(CURRENT_DIR, "data/location_api_sample.csv"), index=False
    )

    assert isinstance(result, LocationsData)


def test_timed_noise_model():
    dummy_raw_data = {
        "measurements": [
            {
                "timestamp": "2024-02-04T23:32:58-04:00",
                "min": 48.60495758,
                "max": 62.83390045,
                "mean": 49.10095596,
            }
        ]
    }
    timed_noise_data = TimedLocationNoiseData(**dummy_raw_data)

    assert len(timed_noise_data.measurements) == 1


def test_hourly_noise_model():
    dummy_hourly_data = {
        "measurements": [
            {
                "timestamp": "2024-02-04T23:00:00-04:00",
                "min": 48.53691864,
                "max": 62.83390045,
                "mean": 49.0464433,
            },
        ]
    }

    timed_noise_data = TimedLocationNoiseData(**dummy_hourly_data)

    assert len(timed_noise_data.measurements) == 1


def test_life_time_noise_model():
    dummy_data = {
        "measurements": [
            {
                "start": "2024-02-04 23:32:58",
                "end": "2024-03-27 17:54:30",
                "count": 14341,
                "min": 35.77902985,
                "max": 92.33490753,
                "mean": 46.82144099,
            }
        ]
    }
    aggregate_noise_data = AggregateLocationNoiseData(**dummy_data)

    assert len(aggregate_noise_data.measurements) == 1


def test_plain_get_request(noise_api: NoiseApi):
    result = noise_api._get(f"locations/{V1_API_TEST_ID}/noise")
    df = pydantic_to_pandas(TimedLocationNoiseData(**result).measurements)

    assert len(df) > 0


def test_plain_lifetime_get_request_lifetime(noise_api: NoiseApi):
    result = noise_api._get(
        f"locations/{V1_API_TEST_ID}/noise",
        params=NoiseRequestParams(granularity=Granularity.life_time),
    )
    df = pydantic_to_pandas(AggregateLocationNoiseData(**result).measurements)
    assert len(df) > 0


def test_noise_api_measurements(noise_api: NoiseApi):
    """
    Load locations from the API and save.
    """
    result = noise_api.get_location_noise_data(
        location_id=V1_API_TEST_ID, params=NoiseRequestParams(page=1)
    )
    df = pydantic_to_pandas(result.measurements)
    df.to_csv(
        os.path.join(CURRENT_DIR, "data/location_noise_api_sample.csv"),
        index=False,
    )

    assert isinstance(result, TimedLocationNoiseData)


def test_noise_api_measurements_lifetime(noise_api: NoiseApi):
    """
    Load locations from the API and save.
    """
    api_params = NoiseRequestParams(granularity=Granularity.life_time)
    result = noise_api.get_location_noise_data(
        location_id=V1_API_TEST_ID, params=api_params
    )
    df = pydantic_to_pandas(result.measurements)

    df.to_csv(
        os.path.join(CURRENT_DIR, "data/location_noise_api_lifetime.csv"),
        index=False,
    )
    assert len(result.measurements) == 1


def test_noise_api_measurements_hourly(noise_api: NoiseApi):
    """
    Load locations from the API and save.
    """
    api_params = NoiseRequestParams(granularity=Granularity.hourly, page=1)
    result = noise_api.get_location_noise_data(
        location_id=V1_API_TEST_ID, params=api_params
    )
    df = pydantic_to_pandas(result.measurements)

    df.to_csv(
        os.path.join(CURRENT_DIR, "data/location_noise_api_hourly.csv"),
        index=False,
    )
    assert len(result.measurements) > 0
