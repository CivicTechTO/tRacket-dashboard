import pytest
import pandas as pd
import numpy as np
from plotly.graph_objects import Figure
import os
from src.plotting import (
    HistogramPlotter,
    TimeseriesPlotter,
    HeatmapPlotter,
    MinAverageIndicatorPlotter,
    OutlierIndicatorPlotter,
    DeviceCountIndicatorPlotter,
    BasePlotter,
    TimeOfDayIndicatorPlotter,
    TimeOfDay
)
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


@pytest.fixture
def dummy_system_df(data_formatter: DataFormatter) -> pd.DataFrame:
    data_path = os.path.join(CURRENT_DIR, "data/dummy_system_data.csv")
    loader = CsvDataLoader()
    raw_data = loader.load_system_stats(data_path)
    df = data_formatter.process_records_to_dataframe(raw_data)

    return df


def test_template_loading():
    theme_name = "BOOTSTRAP"
    plotter = BasePlotter(pd.DataFrame(), bootstrap_template=theme_name)

    assert isinstance(plotter.template, dict)


def test_min_indicator_and_save(dummy_system_df: pd.DataFrame):
    plotter = MinAverageIndicatorPlotter(dummy_system_df)
    fig = plotter.plot()

    figure_out_path = os.path.join(CURRENT_DIR, "plots/min_indicator.html")
    fig.write_html(figure_out_path)

    assert isinstance(fig, Figure)


def test_count_indicator_and_save(dummy_system_df: pd.DataFrame):
    plotter = DeviceCountIndicatorPlotter(dummy_system_df)
    fig = plotter.plot()

    figure_out_path = os.path.join(CURRENT_DIR, "plots/count_indicator.html")
    fig.write_html(figure_out_path)

    assert isinstance(fig, Figure)


def test_outlier_indicator_and_save(dummy_system_df: pd.DataFrame):
    plotter = OutlierIndicatorPlotter(dummy_system_df)
    fig = plotter.plot()

    figure_out_path = os.path.join(CURRENT_DIR, "plots/outlier_indicator.html")
    fig.write_html(figure_out_path)

    assert isinstance(fig, Figure)


def test_date_filter():
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


@pytest.mark.parametrize("template", [None, "BOOTSTRAP"])
def test_histogram_and_save(dummy_df: pd.DataFrame, template):
    plotter = HistogramPlotter(dummy_df, bootstrap_template=template)

    figure = plotter.plot()

    figure_out_path = os.path.join(
        CURRENT_DIR, f"plots/noise_histogram_template={template}.html"
    )
    figure.write_html(figure_out_path)

    assert isinstance(figure, Figure)


@pytest.mark.parametrize("template", [None, "BOOTSTRAP"])
def test_noise_plot_and_save(dummy_df: pd.DataFrame, template):
    """
    Create and save the noise plot.
    """
    plotter = TimeseriesPlotter(dummy_df, bootstrap_template=template)
    figure = plotter.plot()

    figure_out_path = os.path.join(
        CURRENT_DIR, f"plots/noise_plot_template={template}.html"
    )
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


def test_extract_hourly(dummy_hourly: pd.DataFrame):
    """
    Test that the slicing returns 48 hours.
    """
    plotter = TimeOfDayIndicatorPlotter(dummy_hourly)

    current, previous = plotter._extract_last_two_days()

    assert current.shape[0] == 24
    assert previous.shape[0] == 24

@pytest.mark.parametrize("time_of_day", [TimeOfDay.DAY, TimeOfDay.EVENING, TimeOfDay.NIGHT])
def test_time_of_day_indicator(dummy_hourly: pd.DataFrame, time_of_day: TimeOfDay):
    plotter = TimeOfDayIndicatorPlotter(dummy_hourly)

    figure = plotter.plot(time_of_day=time_of_day)
    figure_out_path = os.path.join(
        CURRENT_DIR, f"plots/time_of_day_indicator_{time_of_day}.html"
    )
    figure.write_html(figure_out_path)

    assert isinstance(figure, Figure)


@pytest.mark.parametrize("template", [None, "BOOTSTRAP"])
def test_heatmap_and_save(dummy_hourly: pd.DataFrame, template: str):
    """
    Create and save the noise plot.
    """
    plotter = HeatmapPlotter(dummy_hourly, bootstrap_template=template)
    figure = plotter.plot(pivot_value=HEATMAP_VALUE.MIN, title="Ambient Noise")
    figure_out_path = os.path.join(
        CURRENT_DIR, f"plots/min_heatmap_template={template}.html"
    )
    figure.write_html(figure_out_path)

    figure = plotter.plot(pivot_value=HEATMAP_VALUE.MAX, title="Bang-bang")
    figure_out_path = os.path.join(
        CURRENT_DIR, f"plots/max_heatmap_template={template}.html"
    )
    figure.write_html(figure_out_path)

    assert isinstance(figure, Figure)
