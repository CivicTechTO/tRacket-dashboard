import pytest
import pandas as pd
import numpy as np
from plotly.graph_objects import Figure
import os
from typing import List, Dict, Any
from src.plotting import HistogramPlotter, TimeseriesPlotter, HeatmapPlotter
from src.data_loading import CsvDataLoader, DataFormatter
from src.utils import get_current_dir, HEATMAP_VALUE, COLUMN, filter_by_date

CURRENT_DIR = get_current_dir(__file__)


@pytest.fixture
def data_formatter() -> DataFormatter:
    """
    Create dataformatter object.
    """
    return DataFormatter()


@pytest.fixture
def dummy_df(data_formatter: DataFormatter) -> pd.DataFrame:
    """
    Load a small data set for testing noise plots.
    """
    data_path = os.path.join(CURRENT_DIR, "data/dummy_data.csv")
    loader = CsvDataLoader()
    raw_data = loader.load_noise_data(data_path)
    df = data_formatter.process_records_to_dataframe(raw_data)

    return df


def test_date_filter(dummy_df: pd.DataFrame):
    df = pd.DataFrame(
        {
            COLUMN.TIMESTAMP: pd.date_range(
                start="2023-01-01", periods=10, freq="D"
            ),
            COLUMN.MAX: np.arange(10),
            COLUMN.MIN: np.arange(10),
        }
    )

    filtered = filter_by_date(df, start=pd.Timestamp("2023-01-01"))
    filtered2 = filter_by_date(df, end=pd.Timestamp("2023-01-05"))

    assert (filtered[COLUMN.TIMESTAMP].min() == pd.Timestamp("2023-01-01")) & (
        filtered2[COLUMN.TIMESTAMP].max() == pd.Timestamp("2023-01-05")
    )


def test_histogram_and_save(dummy_df: pd.DataFrame):
    plotter = HistogramPlotter(dummy_df)

    figure = plotter.plot()

    figure_out_path = os.path.join(CURRENT_DIR, "plots/noise_histogram.html")
    figure.write_html(figure_out_path)

    assert isinstance(figure, Figure)


def test_noise_plot_and_save(dummy_df: pd.DataFrame):
    """
    Create and save the noise plot.
    """
    plotter = TimeseriesPlotter(dummy_df)
    figure = plotter.plot()

    figure_out_path = os.path.join(CURRENT_DIR, "plots/noise_plot.html")
    figure.write_html(figure_out_path)

    assert isinstance(figure, Figure)


@pytest.fixture
def dummy_hourly(data_formatter: DataFormatter) -> pd.DataFrame:
    """
    Load a small data set for testing.
    """
    data_path = os.path.join(CURRENT_DIR, "data/dummy_hourly.csv")
    loader = CsvDataLoader()
    raw_data = loader.load_hourly_data(data_path)
    df = data_formatter.process_records_to_dataframe(raw_data)

    return df


def test_heatmap_and_save(dummy_hourly: pd.DataFrame):
    """
    Create and save the noise plot.
    """
    plotter = HeatmapPlotter(dummy_hourly)
    figure = plotter.plot(pivot_value=HEATMAP_VALUE.MIN, title="Ambient Noise")
    figure_out_path = os.path.join(CURRENT_DIR, "plots/min_heatmap.html")
    figure.write_html(figure_out_path)

    figure = plotter.plot(pivot_value=HEATMAP_VALUE.MAX, title="Bang-bang")
    figure_out_path = os.path.join(CURRENT_DIR, "plots/max_heatmap.html")
    figure.write_html(figure_out_path)

    assert isinstance(figure, Figure)
