import pandas as pd
from src.utils import DataFormatter, COLUMN, date_to_string
from src.data_loading.main import AppDataManager
import pytest
from datetime import datetime, date

def test_time_comparison():
    data_manager = AppDataManager()
    limit = data_manager._get_active_time_limit()
    
    column = pd.Series(["2024-05-18T11:00:00-04:00"])

    data_formatter = DataFormatter()
    column = data_formatter._convert_tz_aware_to_est(column)

    assert (column < limit).all()


def date_to_string():
    """
    Test turning a date into datetime string.
    """
    expected = "2024-01-01T00:00:00-04:00"
    date_obj = datetime(2024, 1, 1)

    assert expected == date_to_string(date_obj)


def datetime_to_string():
    """
    Test turning a datetime into datetime string.
    """
    expected = "2024-01-01T12:02:00-04:00"
    date_obj = datetime(2024, 1, 1, 12, 2, 0)

    assert expected == date_to_string(date_obj)


@pytest.fixture
def data_formatter() -> DataFormatter:
    return DataFormatter()


def test_time_filling(data_formatter: DataFormatter):
    df = pd.DataFrame(
        {
            COLUMN.TIMESTAMP: pd.to_datetime(
                ["2024-01-01 12:00:00", "2024-01-01 14:00:00"]
            )
        }
    )
    new_df = data_formatter._fill_missing_times(df, freq="H")

    assert set(new_df[COLUMN.TIMESTAMP]) == set(
        pd.to_datetime(
            [
                "2024-01-01 12:00:00",
                "2024-01-01 13:00:00",
                "2024-01-01 14:00:00",
            ]
        )
    )
