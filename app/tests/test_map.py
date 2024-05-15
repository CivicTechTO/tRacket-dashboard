# import datetime
# import pytest
# import pandas as pd
# import numpy as np
# from plotly.graph_objects import Figure
# import plotly.graph_objects as go
# import os
# from src.plotting import (
#     COLOR_ITEM,
#     HistogramPlotter,
#     TimeseriesPlotter,
#     HeatmapPlotter,
#     MinAverageIndicatorPlotter,
#     OutlierIndicatorPlotter,
#     DeviceCountIndicatorPlotter,
#     BasePlotter,
#     TimeOfDayIndicatorPlotter,
#     TimeOfDay,
#     MapPlotter,
# )
# from src.data_loading import CsvDataLoader, DataFormatter
# from src.utils import get_current_dir, HEATMAP_VALUE, COLUMN, filter_by_date

# CURRENT_DIR = get_current_dir(__file__)


# @pytest.fixture
# def loc_data():
#     data_path = os.path.join(CURRENT_DIR, "data/location_api_sample.csv")
#     df = pd.read_csv(data_path)

#     data_formatter = DataFormatter()
#     df = data_formatter._string_col_names_to_enum(df)

#     return df


# @pytest.fixture
# def noise_data():
#     data_path = os.path.join(CURRENT_DIR, "data/location_noise_api_sample.csv")
#     df = pd.read_csv(data_path)

#     data_formatter = DataFormatter()
#     df = data_formatter._string_col_names_to_enum(df)
#     df[COLUMN.TIMESTAMP] = df[COLUMN.TIMESTAMP].apply(
#         datetime.datetime.fromisoformat
#     )

#     return df


# def test_loc_data(loc_data: pd.DataFrame):
#     print(loc_data.head())

#     assert loc_data.shape[0] > 0


# def test_noise_data(noise_data: pd.DataFrame):
#     print(noise_data.head())

#     assert noise_data.shape[0] > 0


# def test_map_plot(loc_data: pd.DataFrame, noise_data: pd.DataFrame):
#     # create base map
#     noise_plotter = TimeseriesPlotter(noise_data)
#     line_trace = noise_plotter._get_max_line_trace()

#     map_plotter = MapPlotter(loc_data)
#     figure = map_plotter.plot()

#     # figure.add_trace(line_trace)

#     # place location count indicator
#     # indicator = plotter._get_indicator_trace(loc_data.shape[0], "Locations", x_pos=[0, 0.2], y_pos=[0.8, 0.9])
#     # figure.add_trace(indicator)

#     # x_pos=[0, 0.2]
#     # y_pos=[0.8, 0.9]
#     # text = go.Scatter(
#     #     x=[0], y=[0], mode="text", text=["Test"],
#     #     domain={"x": x_pos, "y": y_pos}
#     # )
#     # figure.add_trace(text)

#     # figure.add_annotation(
#     #     xref="x domain",
#     #     yref="y domain",
#     #     text=f"{loc_data.shape[0]}<br> locations",
#     #     x=0.05,
#     #     y=0.95,
#     #     arrowside="none",
#     #     showarrow=False,
#     #     font_size=40,
#     #     font_color=map_plotter.colors[COLOR_ITEM.MAX]
#     #     )

#     # figure.update_layout(
#     #         shapes=[
#     #     dict(
#     #                 type="rect",
#     #                 xref="paper",
#     #                 yref="paper",
#     #                 x0=0.05,
#     #                 y0=0.8,
#     #                 x1=0.15,
#     #                 y1=0.95,
#     #                 fillcolor="white",
#     #                 opacity=0.5,
#     #                 layer="above",
#     #                 line_width=0,
#     #             ),
#     #         ]
#     #     )

#     # figure.add_trace(go.Scatter(x=[0,1,2,0], y=[0,2,0,0], fill="toself"))

#     figure_out_path = os.path.join(CURRENT_DIR, f"plots/new_location_map.html")
#     figure.write_html(figure_out_path)

#     assert isinstance(figure, Figure)
