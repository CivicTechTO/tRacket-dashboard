"""
Classes that handle the dataloading and transformations for the dashboard.
"""
import requests
import pandas as pd
from typing import List, Optional, Dict, Any
from src.utils import COLUMN, TABLE, Logging, load_config, get_date_string
from abc import abstractmethod

logger = Logging.get_console_logger()


class URLBuilder(object):
    def __init__(self, api_token: str) -> None:
        self.api_token = api_token
        self._config = load_config()

    def _build_base_url(self) -> str:
        """
        Build the base of the API url.
        """
        url = (
            "https://noisemeter.webcomand.com/io_comand_webservice/"
            f"get?token={self.api_token}"
        )

        return url

    def _build_base_query_url(self) -> str:
        """
        Build base URL for queries, only the SELECT clause need to be added.
        """
        base_url = self._build_base_url()
        query_url = base_url + ("&format=application/json" "&query=")

        return query_url

    @staticmethod
    def _add_query_to_base_url(base_query_url: str, query: str) -> str:
        """Concatenate the query base with the actual SQL query."""
        return base_query_url + query

    def build_device_stats_fetch_url(self, device_id: str) -> str:
        base_query_url = self._build_base_query_url()
        query = (
            f"SELECT COUNT(*) AS {COLUMN.COUNT.value}, "
            f"MIN({COLUMN.TIMESTAMP.value}) AS {COLUMN.MINDATE.value}, "
            f"MAX({COLUMN.TIMESTAMP.value}) AS {COLUMN.MAXDATE.value}, "
            f"MAX({COLUMN.MAX.value}) AS {COLUMN.MAXNOISE.value} "
            f"FROM {TABLE.NOISE.value} "
            f"WHERE {COLUMN.DEVICEID.value} = '{device_id}' "
        )

        query_url = self._add_query_to_base_url(base_query_url, query)

        return query_url

    def build_device_id_fetch_url(self) -> str:
        """
        Get URL for fetching unique device IDs.
        """
        device_url = (
            f"{self._build_base_query_url()}"
            f"SELECT {COLUMN.DEVICEID.value} "
            f"FROM {TABLE.NOISE.value} "
            f"GROUP BY {COLUMN.DEVICEID.value} ORDER BY {COLUMN.DEVICEID.value} "
        )

        return device_url

    def build_data_fetch_url(
        self,
        device_id: Optional[str] = None,
        limit: Optional[int] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        all_columns: Optional[bool] = False,
    ) -> str:
        """
        Construct data query URL for webcommand.

        Params
        ------
        device_id: str, filter to one device id
        limit: int, input for the LIMIT clause
        all_columns: bool, if return all available columns
        """
        base_url = self._build_base_query_url()

        if all_columns:
            select_clause = "SELECT * "
        else:
            select_clause = f"SELECT {COLUMN.TIMESTAMP.value}, {COLUMN.DEVICEID.value}, {COLUMN.MIN.value}, {COLUMN.MAX.value}, {COLUMN.MEAN.value} "

        data_url = (
            f"{base_url}" f"{select_clause}" f"FROM {TABLE.NOISE.value} "
        )

        if device_id:
            data_url += f"WHERE ({COLUMN.DEVICEID.value} = '{device_id}') "

        if start_date:
            data_url += (
                f"AND (DATE({COLUMN.TIMESTAMP.value}) >= '{start_date}') "
            )
        if end_date:
            data_url += (
                f"AND (DATE({COLUMN.TIMESTAMP.value}) <= '{end_date}') "
            )

        data_url += f"ORDER BY {COLUMN.TIMESTAMP.value} DESC "

        if limit:
            data_url += f"LIMIT {limit}"

        return data_url

    def build_hourly_fetch_url(
        self, device_id: str, limit: Optional[int] = None
    ) -> str:
        base_url = self._build_base_query_url()
        query = f"""
            SELECT DATE({COLUMN.TIMESTAMP.value}) AS {COLUMN.DATE.value}, HOUR({COLUMN.TIMESTAMP.value}) AS {COLUMN.HOUR.value},
            MIN({COLUMN.MIN.value}) AS {COLUMN.MINNOISE.value},
            MAX({COLUMN.MAX.value}) AS {COLUMN.MAXNOISE.value}
            FROM {TABLE.NOISE.value}
            """
        if device_id:
            query += f"""
                WHERE {COLUMN.DEVICEID.value} = '{device_id}'
                """
        query += f"""
            GROUP BY {COLUMN.DATE.value}, {COLUMN.HOUR.value}
            ORDER BY {COLUMN.DATE.value}, {COLUMN.HOUR.value}
            """
        if limit:
            query += f"""LIMIT {limit}"""

        query_url = self._add_query_to_base_url(base_url, query)

        return query_url

    def build_system_stats_fetch_url(self) -> str:
        """
        Build URL for fetching system/device aggregate stats for last two weeks.
        The query organizes data into two columns - 1 and 2-weeks prior.
        """
        base_url = self._build_base_query_url()
        threshold = int(self._config["constants"]["noise_threshold"])
        two_week_prior_date = get_date_string(days_before_today=14)
        one_week_prior_date = get_date_string(days_before_today=7)

        current_week_condition = (
            f"DATE({COLUMN.TIMESTAMP.value}) >= '{one_week_prior_date}'"
        )
        prior_week_condition = f"""
            (DATE({COLUMN.TIMESTAMP.value}) >= '{two_week_prior_date}') AND (DATE({COLUMN.TIMESTAMP.value}) < '{one_week_prior_date}')
            """

        query_string = f"""
            SELECT 
                {COLUMN.DEVICEID.value},
                COUNT(IF({current_week_condition}, 1, Null)) AS {COLUMN.COUNT.value},
                COUNT(IF({prior_week_condition}, 1, Null)) AS {COLUMN.COUNT_PRIOR.value},
                AVG(IF({current_week_condition}, {COLUMN.MIN.value}, Null)) AS {COLUMN.AVGMIN.value},
                AVG(IF({prior_week_condition}, {COLUMN.MIN.value}, Null)) AS {COLUMN.AVGMIN_PRIOR.value},
                SUM(IF(({COLUMN.MAX.value} > {threshold}) AND ({current_week_condition}), 1, 0)) AS {COLUMN.OUTLIERCOUNT.value},
                SUM(IF(({COLUMN.MAX.value} > {threshold}) AND ({prior_week_condition}), 1, 0)) AS {COLUMN.OUTLIERCOUNT_PRIOR.value}
            FROM {TABLE.NOISE.value}
            GROUP BY {COLUMN.DEVICEID.value}
            WHERE DATE({COLUMN.TIMESTAMP.value}) >= '{two_week_prior_date}'
            """

        data_url = self._add_query_to_base_url(base_url, query_string)

        return data_url


class DataFormatter(object):
    """
    Base class for handling data loading for the dashboard.
    """

    def __init__(self) -> None:
        pass

    @staticmethod
    def _string_col_names_to_enum(df: pd.DataFrame) -> pd.DataFrame:
        """
        Map the string col names to enums, filter rest to only the enums.
        """
        new_df = df.rename(
            columns={column_enum.value: column_enum for column_enum in COLUMN}
        )

        new_df = new_df[[col for col in COLUMN if col in new_df.columns]]

        return new_df

    @staticmethod
    def _enum_col_names_to_string(df: pd.DataFrame) -> pd.DataFrame:
        """
        Map the COLUMN enums to their value in the column names.
        """
        new_df = df.rename(
            columns={col_enum: col_enum.value for col_enum in COLUMN}
        )

        return new_df

    @staticmethod
    def _set_data_types(df: pd.DataFrame) -> pd.DataFrame:
        """
        Sets the right data types for noise data columns in place.
        """
        mapper = {
            COLUMN.TIMESTAMP: "datetime64[ns]",
            COLUMN.MIN: int,
            COLUMN.MAX: int,
            COLUMN.MEAN: float,
            COLUMN.COUNT: int,
            COLUMN.DATE: "datetime64[ns]",
            COLUMN.HOUR: int,
            COLUMN.MAXNOISE: int,
            COLUMN.MINNOISE: int,
            COLUMN.MINDATE: "datetime64[ns]",
            COLUMN.MAXDATE: "datetime64[ns]",
        }

        for col, type_ in mapper.items():
            if col in df.columns:
                df[col] = df[col].astype(type_)

        return df

    @staticmethod
    def _raw_to_dataframe(raw_data: List[Dict[str, Any]]) -> pd.DataFrame:
        """
        Turn the API response to a pandas df.
        """

        return pd.DataFrame(raw_data)

    def process_records_to_dataframe(
        self, raw_data: List[Dict[str, Any]]
    ) -> pd.DataFrame:
        """
        Turn the raw, records format into a dataframe with preset column names and datatypes.
        """
        # list of dict to dataframe
        df = self._raw_to_dataframe(raw_data)

        # col name reset and filter by column enum
        df = self._string_col_names_to_enum(df)

        df = self._set_data_types(df)

        return df

    def process_dataframe_to_records(
        self, df: pd.DataFrame
    ) -> List[Dict[str, Any]]:
        """
        Map the processed dataframe format back to records that can be jsonified.
        """
        df = self._enum_col_names_to_string(df)

        return df.to_dict("records")


class AbstractDataLoader(object):
    def __init__(self) -> None:
        pass

    @abstractmethod
    def load_noise_data(self) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def load_device_stats(self) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def load_device_ids(self) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def load_hourly_data(self) -> List[Dict[str, Any]]:
        pass


class CsvDataLoader(AbstractDataLoader):
    """
    Data loading locally from csv.
    """

    def __init__(self) -> None:
        super().__init__()

    def _load_from_file(self, file_path: str) -> List[Dict[str, Any]]:
        df = pd.read_csv(file_path)

        return df.to_dict("records")

    def load_noise_data(self, file_path: str) -> List[Dict[str, Any]]:
        return self._load_from_file(file_path)

    def load_device_stats(self, file_path: str) -> List[Dict[str, Any]]:
        return self._load_from_file(file_path)

    def load_system_stats(self, file_path: str) -> List[Dict[str, Any]]:
        return self._load_from_file(file_path)

    def load_device_ids(self, file_path: str) -> List[Dict[str, Any]]:
        return self._load_from_file(file_path)

    def load_hourly_data(self, file_path: str) -> List[Dict[str, Any]]:
        return self._load_from_file(file_path)


class WebcommandDataLoader(AbstractDataLoader):
    """
    Data loading from the webcommand API.
    """

    def __init__(self, url_builder: URLBuilder) -> None:
        super().__init__()
        self.url_builder = url_builder

    @staticmethod
    def _fetch_from_url(URL: str) -> List[Dict[str, Any]]:
        """Get the data as a list of dicts from the URL."""

        response = requests.get(URL)
        response_json = response.json()

        return response_json["contents"]

    def _load_from_query(self, query: str) -> List[Dict[str, Any]]:
        """
        Given a SQL query, make an API call and fetch the data.
        """
        base_query_url = self.url_builder._build_base_query_url()
        query_url = self.url_builder._add_query_to_base_url(
            base_query_url, query
        )

        raw_data = self._fetch_from_url(query_url)

        return raw_data

    def load_noise_data(self, **url_kwargs) -> List[Dict[str, Any]]:
        """
        Load the data from the api and clean.
        """
        url = self.url_builder.build_data_fetch_url(**url_kwargs)
        raw_data = self._fetch_from_url(url)

        self._log_data_loading(raw_data, url_kwargs)

        return raw_data

    def load_device_stats(self, **url_kwargs) -> List[Dict[str, Any]]:
        """
        Load the device stats from the API.
        """
        url = self.url_builder.build_device_stats_fetch_url(**url_kwargs)
        raw_data = self._fetch_from_url(url)

        return raw_data

    def load_hourly_data(self, **url_kwargs) -> List[Dict[str, Any]]:
        """
        Load hourly min/max aggregate data.
        """
        url = self.url_builder.build_hourly_fetch_url(**url_kwargs)
        raw_data = self._fetch_from_url(url)

        return raw_data

    def load_device_ids(self) -> List[Dict[str, Any]]:
        """
        Fetch the device IDs from the API, returns single column.
        """
        url = self.url_builder.build_device_id_fetch_url()
        raw_data = self._fetch_from_url(url)

        logger.info(f"{len(raw_data)} devices found.")

        return raw_data

    def load_system_stats(self, **url_kwargs) -> List[Dict[str, Any]]:
        """
        Load the device stats form WebCommand.
        """
        url = self.url_builder.build_system_stats_fetch_url(**url_kwargs)
        raw_data = self._fetch_from_url(url)

        return raw_data

    @staticmethod
    def _log_data_loading(raw_data: List[Dict[str, Any]], url_kwargs) -> None:
        if "device_id" in url_kwargs:
            device = url_kwargs["device_id"]
            logger.debug(
                f"{len(raw_data)} rows loaded from Webcommand for ID {device}."
            )
        else:
            logger.debug((f"{len(raw_data)} rows loaded from Webcommand."))
