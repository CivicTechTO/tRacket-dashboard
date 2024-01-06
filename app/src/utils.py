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
import json

### ENUMS ###


class TABLE(Enum):
    """
    API table name for data.
    """

    NOISE = "Noise"


class COLUMN(Enum):
    """
    Columns to use and their name from API call, Noise table.
    """

    TIMESTAMP = "Timestamp"
    DEVICEID = "DeviceID"
    MIN = "Min"
    MAX = "Max"
    MEAN = "Mean"
    # aggregate columns
    COUNT = "count"
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


def load_config() -> configparser.ConfigParser:
    config = configparser.ConfigParser()
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
