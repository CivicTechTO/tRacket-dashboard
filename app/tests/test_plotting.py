from src.plotting import TimeseriesPlotter
from src.utils import DataFormatter, get_current_dir, COLUMN
import plotly.graph_objects as go
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

def test_plot_with_comments(dummy_hourly_data: pd.DataFrame):
    plotter = TimeseriesPlotter(dummy_hourly_data)
    fig = plotter.plot()

    # pick a point from the dummy data to attach a comment to
    comment_x_orig = dummy_hourly_data[COLUMN.TIMESTAMP].iloc[5]
    comment_mean_y = dummy_hourly_data[COLUMN.MEAN].iloc[5]

    # offset the marker's x slightly so it is not picked up by the
    # figure's "x unified" hover — this makes the marker's hover
    # appear only when hovering the marker itself.
    comment_x = comment_x_orig + pd.Timedelta(milliseconds=1)

    marker_y = 90

    # add a vertical line connecting the mean value to the fixed marker height
    fig.add_trace(
        go.Scatter(
            x=[comment_x, comment_x],
            y=[comment_mean_y, marker_y],
            mode="lines",
            line=dict(color="#E25100", width=2, dash="dashdot"),
            hoverinfo="skip",
            showlegend=False,
        )
    )

    # add the comment marker at fixed height; show hover text only when
    # hovering this marker (use hovertemplate) and suppress the trace name
    # in the small secondary box with <extra></extra>.
    fig.add_trace(
        go.Scatter(
            x=[comment_x],
            y=[marker_y],
            mode="markers",
            marker=dict(size=14, color="#E25100"),
            hovertemplate="Comment: motorbike<extra></extra>",
            hoverlabel=dict(namelength=0),
            showlegend=False,
        )
    )

    figure_out_path = os.path.join(CURRENT_DIR, "plots/hourly_noise_plot_with_comment.html")
    fig.write_html(figure_out_path)
