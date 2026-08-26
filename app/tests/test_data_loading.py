from src.data_loading.noise_api import NoiseApi
from src.data_loading.models import (
    LocationsData,
    TimedLocationNoiseData,
    NoiseRequestParams,
    AggregateLocationNoiseData,
    NoiseTimed,
)
from src.data_loading.main import AppDataManager
from src.data_loading.models import Granularity
from src.data_loading import noise_api as noise_api_module
from src.utils import (
    COLUMN,
    get_current_dir,
    pydantic_to_pandas,
    load_config,
)
import pytest
import os
import asyncio
import pandas as pd
from pydantic import ValidationError
from datetime import datetime

### TEST PARAMS ###

CONFIG = load_config()
CURRENT_DIR = get_current_dir(__file__)
V1_API_TEST_ID = "572250"


### TEST v1 API ###


def test_timezone_aware():
    noise_measure = NoiseTimed(
        **{
            "min": 0.0,
            "max": 0.0,
            "mean": 0.0,
            "timestamp": "2024-11-10T08:32:08-04:00",
        }
    )

    d = noise_measure.timestamp

    assert verify_timezone_aware(d)


def verify_timezone_aware(d: datetime) -> bool:
    return d.tzinfo is not None and d.tzinfo.utcoffset(d) is not None


def test_noise_api_params():
    with pytest.raises(ValidationError) as e:
        NoiseRequestParams(page=-1)


@pytest.fixture
def noise_api() -> NoiseApi:
    """
    Noise API for data loading.
    """
    data_manager = AppDataManager()

    return data_manager._create_api()


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


def test_noise_api_paginated_batches_stop_at_empty_page(monkeypatch):
    pages = {
        0: [{"timestamp": "2024-02-04T23:00:00-04:00", "min": 1, "max": 2, "mean": 1.5}],
        1: [{"timestamp": "2024-02-04T23:01:00-04:00", "min": 2, "max": 3, "mean": 2.5}],
        2: [{"timestamp": "2024-02-04T23:02:00-04:00", "min": 3, "max": 4, "mean": 3.5}],
        3: [],
        4: [{"timestamp": "2024-02-04T23:04:00-04:00", "min": 5, "max": 6, "mean": 5.5}],
        5: [{"timestamp": "2024-02-04T23:05:00-04:00", "min": 6, "max": 7, "mean": 6.5}],
    }
    requested_pages = []

    class FakeResponse:
        def __init__(self, page):
            self.url = f"https://example.test/noise?page={page}"
            self._data = {"measurements": pages[page]}

        def raise_for_status(self):
            pass

        def json(self):
            return self._data

    class FakeAsyncClient:
        def __init__(self, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, traceback):
            pass

        async def get(self, url, params=None):
            page = params["page"]
            requested_pages.append(page)
            return FakeResponse(page)

    monkeypatch.setattr(noise_api_module.httpx, "AsyncClient", FakeAsyncClient)

    noise_api = NoiseApi("https://example.test/")
    result = noise_api.get_location_noise_data(
        "location-1"
    )

    assert len(result.measurements) == 3
    assert requested_pages == [0, 1, 2, 3, 4, 5][:noise_api.page_batch_size + 1]  # Should stop after empty page


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


def test_data_manager_loads_raw_and_hourly_noise(monkeypatch):
    data_manager = AppDataManager()
    data_manager.location_stats = pd.DataFrame(
        {
            COLUMN.START: [datetime(2024, 1, 1)],
            COLUMN.END: [datetime(2024, 2, 5)],
        }
    )
    requested_granularities = []
    requested_ranges = []
    active_requests = 0
    max_active_requests = 0

    async def fake_async_get_location_noise_data(location_id, params=None):
        nonlocal active_requests, max_active_requests
        requested_granularities.append(params.granularity)
        requested_ranges.append((params.start, params.end))
        active_requests += 1
        max_active_requests = max(max_active_requests, active_requests)
        await asyncio.sleep(0)
        active_requests -= 1
        return TimedLocationNoiseData(
            measurements=[
                NoiseTimed(
                    timestamp="2024-02-04T23:00:00-04:00",
                    min=48.0,
                    max=62.0,
                    mean=49.0,
                )
            ]
        )

    monkeypatch.setattr(
        data_manager.api,
        "async_get_location_noise_data",
        fake_async_get_location_noise_data,
    )
    data_manager.config["plot"]["fill_gaps"] = "false"

    data_manager.load_and_format_location_noise_parallel(
        location_id="location-1",
        start=datetime(2024, 2, 4),
        end=datetime(2024, 2, 5),
    )

    assert set(requested_granularities) == {
        Granularity.raw,
        Granularity.hourly,
    }
    assert requested_ranges == [(datetime(2024, 2, 4), datetime(2024, 2, 5))] * 2
    assert max_active_requests == 2
    assert set(data_manager.location_noise) == {
        Granularity.raw,
        Granularity.hourly,
    }
