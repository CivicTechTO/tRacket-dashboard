from src.data_loading.noise_api import (
    NoiseApi
)
from src.data_loading.models import (
    LocationsData,
    LocationNoiseData,
    NoiseRequestParams,
)
from src.data_loading.main import (
    create_api
)

from src.utils import (
    get_current_dir,
    pydantic_to_pandas,
    load_config
)
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


def test_noise_model():
    dummy_data = {
        'measurements': [
            {'timestamp': '2024-02-04T23:32:58-04:00', 'min': 48.60495758, 'max': 62.83390045, 'mean': 49.10095596}]}
    location_data = LocationNoiseData(**dummy_data)
    
    assert len(location_data.measurements) == 1


def test_plain_get_request(noise_api: NoiseApi):
    result = noise_api._get(f"locations/{V1_API_TEST_ID}/noise")
    df = pydantic_to_pandas(LocationNoiseData(**result).measurements)
   
    assert len(df) > 0 
    

def test_plain_get_request_lifetime(noise_api: NoiseApi):
    result = noise_api._get(f"locations/{V1_API_TEST_ID}/noise", params=NoiseRequestParams(**{"granularity": "life-time"}))
    df = pydantic_to_pandas(LocationNoiseData(**result).measurements)
    assert len(df) > 0 

def test_noise_api_measurements(noise_api: NoiseApi):
    """
    Load locations from the API and save.
    """
    result = noise_api.get_location_noise_data(location_id=V1_API_TEST_ID)
    df = pydantic_to_pandas(result.measurements)
    df.to_csv(
        os.path.join(CURRENT_DIR, "data/location_noise_api_sample.csv"),
        index=False,
    )

    assert isinstance(result, LocationNoiseData)


def test_noise_api_measurements_lifetime(noise_api: NoiseApi):
    """
    Load locations from the API and save.
    """
    api_params = NoiseRequestParams(granularity="life-time")
    result = noise_api.get_location_noise_data(location_id=V1_API_TEST_ID, params=api_params)
    df = pydantic_to_pandas(result.measurements)

    df.to_csv(
        os.path.join(CURRENT_DIR, "data/location_noise_api_lifetime.csv"),
        index=False,
    )
    assert len(result.measurements) == 1


#################################
### LEGACY WEBCOMMAND LOADING ###
#################################


# @pytest.fixture
# def url_builder() -> URLBuilder:
#     """
#     Create URL builder object.
#     """
#     return URLBuilder(TOKEN)


# @pytest.fixture
# def data_formatter() -> DataFormatter:
#     """
#     Create dataformatter object.
#     """
#     return DataFormatter()


# @pytest.fixture
# def data_loader(url_builder: URLBuilder) -> WebcommandDataLoader:

#     """
#     Create a data loader for fetching data from the API.
#     """
#     return WebcommandDataLoader(url_builder)


# def test_load_all_and_save(
#     data_loader: WebcommandDataLoader, data_formatter: DataFormatter
# ):
#     """
#     Create a backup of the API data for all devices.
#     """
#     raw_data = data_loader.load_noise_data(limit=1000, all_columns=True)
#     df = data_formatter._raw_to_dataframe(raw_data)
#     df.to_csv(os.path.join(CURRENT_DIR, "data/full_backup.csv"), index=False)

#     assert df.shape[0] > 0


# def test_device_stats(url_builder: URLBuilder):
#     url = url_builder.build_device_stats_fetch_url("a99")

#     assert get_url_response_status(url)


# @pytest.fixture
# def hourly_query(url_builder: URLBuilder, limit=None):
#     return url_builder.build_hourly_fetch_url(
#         device_id=TEST_DEVICE_ID, limit=limit
#     )


# def test_hourly_fetch_and_save(
#     data_loader: WebcommandDataLoader,
#     hourly_query: str,
#     data_formatter: DataFormatter,
# ):
#     base_url = data_loader.url_builder._build_base_query_url()
#     query_url = data_loader.url_builder._add_query_to_base_url(
#         base_url, hourly_query
#     )

#     raw_data = data_loader._fetch_from_url(query_url)
#     df = data_formatter._raw_to_dataframe(raw_data)
#     df.to_csv(os.path.join(CURRENT_DIR, "data/sample_hourly.csv"), index=False)

#     assert df.shape[0] > 0


# @pytest.mark.parametrize(
#     "query",
#     [
#         f"""
#         SELECT COUNT(*) FROM {TABLE.NOISE.value}
#         """,
#         (
#             f"SELECT YEAR({COLUMN.TIMESTAMP.value}) AS year_, MONTH({COLUMN.TIMESTAMP.value}) AS month_, DAY({COLUMN.TIMESTAMP.value}) AS day_, HOUR({COLUMN.TIMESTAMP.value}) AS hour_, "
#             f"MIN({COLUMN.MIN.value}), MAX({COLUMN.MAX.value}) "
#             f"FROM {TABLE.NOISE.value} "
#             f"WHERE {COLUMN.DEVICEID.value} = 'gabe3' "
#             "GROUP BY year_, month_, day_, hour_ "
#             "LIMIT 10"
#         ),
#         (
#             f"SELECT DATE({COLUMN.TIMESTAMP.value}) AS date_, HOUR({COLUMN.TIMESTAMP.value}) AS hour_, "
#             f"MIN({COLUMN.MIN.value}), MAX({COLUMN.MAX.value}) "
#             f"FROM {TABLE.NOISE.value} "
#             f"WHERE {COLUMN.DEVICEID.value} = 'gabe3' "
#             "GROUP BY date_, hour_  "
#             "LIMIT 10"
#         ),
#         (
#             f"SELECT {COLUMN.DEVICEID.value}, "
#             f"IF(MAX(DATE({COLUMN.TIMESTAMP.value})) >= '2024-01-21', True, False) AS test "
#             f"FROM {TABLE.NOISE.value} "
#             f"GROUP BY {COLUMN.DEVICEID.value} ORDER BY {COLUMN.DEVICEID.value} "
#         ),
#     ],
# )
# def test_query_response_status(url_builder: URLBuilder, query: str):
#     base_url = url_builder._build_base_query_url()
#     query_url = url_builder._add_query_to_base_url(base_url, query)

#     assert get_url_response_status(query_url)


# def test_device_count(data_loader: WebcommandDataLoader):
#     raw_data = data_loader.load_device_stats(device_id="a99")

#     assert isinstance(raw_data[0][COLUMN.COUNT.value], int)


# def test_system_stats_fetch_and_save(
#     data_loader: WebcommandDataLoader, data_formatter: DataFormatter
# ):
#     raw_data = data_loader.load_system_stats()
#     df = data_formatter._raw_to_dataframe(raw_data)

#     df.to_csv(
#         os.path.join(CURRENT_DIR, "data/sample_system_data.csv"), index=False
#     )

#     assert isinstance(raw_data[0][COLUMN.COUNT.value], int)


# def test_system_stats_url(url_builder: URLBuilder):
#     url = url_builder.build_system_stats_fetch_url()

#     assert get_url_response_status(url)


# def test_device_max_stat(data_loader: WebcommandDataLoader):
#     raw_data = data_loader.load_device_stats(device_id="a99")

#     assert isinstance(raw_data[0][COLUMN.MAXNOISE.value], (int, float))


# def test_device_id_fetch_url(url_builder: URLBuilder):
#     """
#     Check that API replies for device id request.
#     """
#     url = url_builder.build_device_id_fetch_url()

#     assert get_url_response_status(url)


# def test_data_fetch_url(url_builder: URLBuilder):
#     """
#     Check that API replies to data request.
#     """
#     url = url_builder.build_data_fetch_url(limit=10)

#     assert get_url_response_status(url)


# def test_device_location_url(url_builder: URLBuilder):
#     """
#     Test loading the location data.
#     """
#     url = url_builder.build_device_location_fetch_url()

#     assert get_url_response_status(url)


# @pytest.fixture
# def raw_data(
#     url_builder: URLBuilder, data_loader: WebcommandDataLoader
# ) -> List[dict]:
#     """
#     Grab raw API data.
#     """
#     url = url_builder.build_data_fetch_url(limit=10, all_columns=True)
#     raw_data = data_loader._fetch_from_url(url)

#     return raw_data


# def test_fetching_and_save(
#     raw_data: List[dict],
#     data_loader: WebcommandDataLoader,
#     data_formatter: DataFormatter,
# ):
#     """
#     Fetch 10 rows from the API, save sample.
#     """
#     df = data_formatter._raw_to_dataframe(raw_data)

#     df.to_csv(os.path.join(CURRENT_DIR, "data/sample_scrape.csv"), index=False)

#     assert isinstance(df, pd.DataFrame) and len(raw_data) > 0


# def test_formatting_and_save(
#     raw_data: List[dict],
#     data_loader: WebcommandDataLoader,
#     data_formatter: DataFormatter,
# ):
#     """
#     Test the formatting and save.
#     """
#     df = data_formatter.process_records_to_dataframe(raw_data)
#     df.to_csv(
#         os.path.join(CURRENT_DIR, "data/sample_formatted.csv"), index=False
#     )

#     assert isinstance(df, pd.DataFrame) and all(
#         [col in COLUMN for col in df.columns]
#     )


# def test_device_loc_fetch_and_save(
#     data_loader: WebcommandDataLoader, data_formatter: DataFormatter
# ):
#     location_data = data_loader.load_location_data()
#     location_data_df = data_formatter.process_records_to_dataframe(
#         location_data
#     )

#     location_data_df.to_csv(
#         os.path.join(CURRENT_DIR, "data/sample_device_loc.csv"), index=False
#     )

#     assert location_data_df.shape[0] > 0


# def test_device_id_fetch_and_save(
#     data_loader: WebcommandDataLoader, data_formatter: DataFormatter
# ):
#     """
#     Test fetching the device IDs and save.
#     """
#     raw_id_data = data_loader.load_device_ids()
#     id_data_df = data_formatter.process_records_to_dataframe(raw_id_data)

#     id_data_df.to_csv(
#         os.path.join(CURRENT_DIR, "data/sample_device_ids.csv"), index=False
#     )

#     assert id_data_df.shape[0] > 0


# def test_device_data_load(
#     data_loader: WebcommandDataLoader, data_formatter: DataFormatter
# ):
#     """
#     Test loading data for 1 device.
#     """
#     raw_data = data_loader.load_noise_data(device_id=TEST_DEVICE_ID, limit=10)
#     df = data_formatter.process_records_to_dataframe(raw_data)

#     assert df[COLUMN.DEVICEID].nunique() == 1
