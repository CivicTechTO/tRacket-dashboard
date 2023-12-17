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
    MINDATE = "mindate"
    MAXDATE = "maxdate"
    MAXNOISE = "maxnoise"
    MINNOISE = "minnoise"
    DATE = "date"
    HOUR = "hour"


class HEATMAP_VALUE(Enum):
    """
    Valuse that can be shown in the heatmap.
    """

    MIN = COLUMN.MINNOISE
    MAX = COLUMN.MAXNOISE


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


def get_current_dir(__file__) -> str:
    """
    Get the path to the directory of the script.
    """
    return os.path.dirname(os.path.realpath(__file__))


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
