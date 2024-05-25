import pandas as pd
from src.utils import DataFormatter, COLUMN
import pytest


@pytest.fixture
def data_formatter() -> DataFormatter:
    return DataFormatter()


def test_time_filling(data_formatter: DataFormatter):
    df = pd.DataFrame({COLUMN.TIMESTAMP: pd.to_datetime(["2024-01-01 12:00:00", "2024-01-01 14:00:00"])})
    new_df = data_formatter._fill_missing_times(df, freq="H")
 
    assert set(new_df[COLUMN.TIMESTAMP]) == set(pd.to_datetime(["2024-01-01 12:00:00", "2024-01-01 13:00:00", "2024-01-01 14:00:00"]))
