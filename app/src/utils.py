"""
General utilities.
"""
import pandas as pd
import numpy as np
from enum import Enum
import os
import logging
import inspect
import requests
import configparser
import dash_bootstrap_components as dbc
from pydantic import BaseModel
from typing import List, Dict, Any
from datetime import datetime, date

### ENUMS ###


class TABLE(Enum):
    """
    API table name for data.
    """

    NOISE = "Noise"
    DEVICE = "Device"


class COLUMN(Enum):
    """
    Columns to use and their name from API call, Noise table.
    """

    # v1 API columns
    DEVICEID = "id"
    LABEL = "label"
    MIN = "min"
    MAX = "max"
    MEAN = "mean"
    LAT = "latitude"
    LON = "longitude"
    ACTIVE = "active"
    TIMESTAMP = "timestamp"
    COUNT = "count"
    START = "start"
    END = "end"
    RADIUS = "radius"
    MARKER_COLOR = "marker_color"

    # aggregate columns
    COUNT_PRIOR = "count_prior"
    MINDATE = "mindate"
    MAXDATE = "maxdate"
    MAXNOISE = "maxnoise"
    MINNOISE = "minnoise"
    DATE = "date"
    HOUR = "hour"
    AVGMIN = "min_avg"
    AVGMIN_PRIOR = "min_avg_prior"
    OUTLIERCOUNT = "outlier_count"
    OUTLIERCOUNT_PRIOR = "outlier_count_prior"


class HEATMAP_VALUE(Enum):
    """
    Valuse that can be shown in the heatmap.
    """

    MIN = COLUMN.MINNOISE
    MAX = COLUMN.MAXNOISE


### THEME UTILS ###

dbc_themes_name_to_url = {
    "BOOTSTRAP": dbc.themes.BOOTSTRAP,
    "CERULEAN": dbc.themes.CERULEAN,
    "COSMO": dbc.themes.COSMO,
    "FLATLY": dbc.themes.FLATLY,
    "JOURNAL": dbc.themes.JOURNAL,
    "LITERA": dbc.themes.LITERA,
    "LUMEN": dbc.themes.LUMEN,
    "LUX": dbc.themes.LUX,
    "MATERIA": dbc.themes.MATERIA,
    "MINTY": dbc.themes.MINTY,
    "PULSE": dbc.themes.PULSE,
    "SANDSTONE": dbc.themes.SANDSTONE,
    "SIMPLEX": dbc.themes.SIMPLEX,
    "SKETCHY": dbc.themes.SKETCHY,
    "SPACELAB": dbc.themes.SPACELAB,
    "UNITED": dbc.themes.UNITED,
    "YETI": dbc.themes.YETI,
    "CYBORG": dbc.themes.CYBORG,
    "DARKLY": dbc.themes.DARKLY,
    "SLATE": dbc.themes.SLATE,
    "SOLAR": dbc.themes.SOLAR,
    "SUPERHERO": dbc.themes.SUPERHERO,
    "QUARTZ": dbc.themes.QUARTZ,
    "MORPH": dbc.themes.MORPH,
    "VAPOR": dbc.themes.VAPOR,
    "ZEPHYR": dbc.themes.ZEPHYR,
}


### GENERAL UTILS ###


def date_to_string(date_object: date|datetime) -> str:
    """
    Turn a date or datetime object into a string following the API format.
    """
    return date_object.strftime("%Y-%m-%dT%H:%M:%S-04:00")


def get_last_time(df: pd.DataFrame) -> np.datetime64:
    """
    Get last time stamp from the dataframe.
    """

    return df[COLUMN.TIMESTAMP].max()


def load_config(config_path: str = None) -> configparser.ConfigParser:
    """
    Load a config file from the current dir or a given location.
    """
    config = configparser.ConfigParser()
    if config_path is None:
        config_path = os.path.join(get_current_dir(__file__), "config.ini")
    config.read(config_path)

    return config


def get_date_string(
    days_before_today: int = None, str_format: str = "%Y-%m-%d"
) -> str:
    """
    Create date string in "%Y-%m-%d" formate
    """
    week_ago = pd.to_datetime("today")
    if days_before_today:
        week_ago -= pd.Timedelta(days=days_before_today)

    week_ago = week_ago.strftime(str_format)

    return week_ago


def get_current_dir(__file__) -> str:
    """
    Get the path to the directory of the script.
    """
    return os.path.dirname(os.path.realpath(__file__))


### DATA PROC UTILS ###


class DataFormatter(object):
    """
    Base class for handling data formatting for the dashboard.
    """

    def __init__(self) -> None:
        pass

    @staticmethod
    def _fill_missing_times(df: pd.DataFrame, freq: str) -> pd.DataFrame:
        """
        Fill in the missing times between the min and max.
        """
        assert COLUMN.TIMESTAMP in df.columns

        start = df[COLUMN.TIMESTAMP].min()
        end = df[COLUMN.TIMESTAMP].max()
        date_range = pd.date_range(start, end, freq=freq)
        df = (
            df.set_index(COLUMN.TIMESTAMP)
            .reindex(date_range)
            .reset_index(names=[COLUMN.TIMESTAMP])
        )

        return df

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
            COLUMN.MIN: float,
            COLUMN.MAX: float,
            COLUMN.MEAN: float,
            COLUMN.COUNT: int,
            COLUMN.ACTIVE: bool,
        }

        for col, type_ in mapper.items():
            if col in df.columns:
                df[col] = df[col].astype(type_)

        if COLUMN.TIMESTAMP in df.columns:
            df[COLUMN.TIMESTAMP] = pd.to_datetime(
                df[COLUMN.TIMESTAMP]
            ).dt.tz_localize(None)

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

    def format_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Map string col names to enum and set datatypes.
        """
        df = self._string_col_names_to_enum(df)
        df = self._set_data_types(df)
        return df


def pydantic_to_pandas(models: List[BaseModel]):
    """
    Turn a list of pydantic models into pandas dataframe.
    """
    df = pd.DataFrame([data.model_dump() for data in models])
    return df


def filter_by_date(
    df: pd.DataFrame, start: pd.Timestamp = None, end: pd.Timestamp = None
) -> pd.DataFrame:
    """
    Filter the nosie data by start and end date.
    """
    time_frame_indicator = np.full(df.shape[0], True)
    if end:
        time_frame_indicator = df[COLUMN.TIMESTAMP] <= end
    if start:
        time_frame_indicator = time_frame_indicator & (
            df[COLUMN.TIMESTAMP] >= start
        )

    return df[time_frame_indicator].copy()


def get_unique_ids(df: pd.DataFrame) -> list:
    """Get the unique device ids."""

    return list(df[COLUMN.DEVICEID].unique())


def filter_outliers(df: pd.DataFrame, threshold: int) -> pd.DataFrame:
    """
    Filter observations where max level over threshold.
    """
    return df[df[COLUMN.MAX] > threshold]


### API UTILS ###


def get_url_response_status(url: str) -> bool:
    response = requests.get(url)
    response_json = response.json()

    return response_json["status"]


class Logging:
    """
    Logging utility to conveniently record run-time function calls,
    both to the console (INFO level) and a log file (DEBUG level).
    Usage:
    Each module can have its own logger initialized by:
    logger = Logging.get_console_logger()
    The main process should run the following to activate the logging:
    Logging.setup()
    """

    BASIC_CONFIG = {
        "level": logging.DEBUG,
        "format": "%(asctime)s %(name)-12s %(levelname)-8s %(message)s",
        "datefmt": "%m-%d %H:%M",
        "filename": "logs/main.log",
        "filemode": "a",
    }

    CONSOLE_CONFIG = {
        "level": logging.INFO,
        "format": "%(name)-12s %(levelname)-8s %(message)s",
    }

    @classmethod
    def setup(cls) -> None:
        """
        Main setup method for logging; needs to be run once only.
        """
        cls._create_logdir()
        cls._configure_logging()

    @classmethod
    def _create_logdir(cls) -> None:
        log_path = cls._get_log_path()
        log_dir = os.path.dirname(log_path)
        os.makedirs(log_dir, exist_ok=True)

    @classmethod
    def _get_log_path(cls) -> str:
        return cls.BASIC_CONFIG["filename"]

    @classmethod
    def _configure_logging(cls) -> None:
        logging.basicConfig(**cls.BASIC_CONFIG)
        logging.captureWarnings(capture=True)

    @classmethod
    def get_console_logger(cls, log_name=None) -> logging.Logger:
        """
        Create logger that writes INFO and higher level messages to console.
        """

        if log_name is None:
            log_name = cls._get_module_name()

        logger = logging.getLogger(log_name)

        console_handler = cls._get_console_handler()
        logger.addHandler(console_handler)

        return logger

    @staticmethod
    def _get_module_name() -> str:
        stack = inspect.stack()
        frame = stack[2]
        module = inspect.getmodule(frame[0])
        module_name = module.__name__

        return module_name

    @classmethod
    def _get_console_handler(cls) -> logging.StreamHandler:
        console_handler = logging.StreamHandler()
        console_level = cls._get_console_level()
        console_handler.setLevel(console_level)

        console_formatter = cls._get_console_formatter()
        console_handler.setFormatter(console_formatter)

        return console_handler

    @classmethod
    def _get_console_formatter(cls) -> logging.Formatter:
        console_format = cls._get_console_format()
        console_formatter = logging.Formatter(console_format)

        return console_formatter

    @classmethod
    def _get_console_format(cls) -> str:
        return cls.CONSOLE_CONFIG["format"]

    @classmethod
    def _get_console_level(cls):
        return cls.CONSOLE_CONFIG["level"]
