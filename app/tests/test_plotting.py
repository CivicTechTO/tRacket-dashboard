from src.plotting import TimeseriesPlotter
from src.utils import DataFormatter, get_current_dir
import pytest
import pandas as pd
import os

CURRENT_DIR = get_current_dir(__file__)


@pytest.fixture
def dummy_hourly_data() -> pd.DataFrame:
    data_path = os.path.join(CURRENT_DIR, "data/dummy_hourly.csv")
    df = pd.read_csv(data_path)

    data_formatter = DataFormatter()
    df = data_formatter.format_dataframe(df)

    return df


def test_validate_data(dummy_hourly_data: pd.DataFrame):
    plotter = TimeseriesPlotter(dummy_hourly_data)


def test_hourly_noise_plot(dummy_hourly_data: pd.DataFrame):
    plotter = TimeseriesPlotter(dummy_hourly_data)
    fig = plotter.plot()

    figure_out_path = os.path.join(CURRENT_DIR, "plots/hourly_noise_plot.html")
    fig.write_html(figure_out_path)
