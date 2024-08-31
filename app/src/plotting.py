"""
Classes for creating the plots on the dashboard.
"""
from src.utils import (
    COLUMN,
    HEATMAP_VALUE,
    filter_outliers,
    load_config,
    get_current_dir,
    Logging,
)
import os
import json
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from typing import Optional, List, Dict
from abc import abstractmethod
import pandas.api.types as ptype
from enum import StrEnum, auto
from datetime import datetime
from dash import html

logger = Logging.get_console_logger()


class COLOR_ITEM(StrEnum):
    MIN = auto()
    MAX = auto()
    MEAN = auto()
    MAP_MARKER = auto()


class BasePlotter:
    """
    Base class for plotting - loads config.
    """

    def __init__(
        self, df: pd.DataFrame | None, bootstrap_template: str = None
    ) -> None:
        self._config = load_config()

        if df is not None:
            self._validate_data(df)
        self.df = df

        self.template = None
        self.template_name = bootstrap_template
        if self.template_name is not None:
            self.template = self._load_template(self.template_name)

        self.colors = self._set_colors()

    def _set_colors(self) -> Dict[COLOR_ITEM, str]:
        """
        Determine the main colors for the chart to show min/max measurements. Based on the template if provided or the config as a fallback.
        """
        if self.template is None:
            colors = {
                COLOR_ITEM.MIN: self._config["plot.colors"]["min"],
                COLOR_ITEM.MAX: self._config["plot.colors"]["max"],
                COLOR_ITEM.MAP_MARKER: self._config["map"]["marker_color"],
                COLOR_ITEM.MEAN: self._config["plot.colors"]["mean"],
            }
        else:
            colors = {
                COLOR_ITEM.MIN: self.template["layout"]["colorway"][0],
                COLOR_ITEM.MAX: self.template["layout"]["colorway"][1],
            }

        return colors

    def _set_background(self, fig: go.Figure) -> None:
        """
        Set background colors for the plot based on the config file.
        """
        fig.update_layout(
            paper_bgcolor=self._config["plot.colors"]["background"],
            plot_bgcolor=self._config["plot.colors"]["background"],
        )

    def _set_title_size(self, fig: go.Figure) -> None:
        """
        Set title size based on config.
        """
        fig.update_layout(
            title=dict(
                font=dict(size=int(self._config["plot.text"]["title_size"]))
            ),
        )

    @staticmethod
    def _load_template(name: str) -> dict:
        """
        Load the Plotly template from file for a Bootstrap theme by its name.
        """
        name = name.lower()
        file_name = name + ".json"
        file_path = os.path.join(
            get_current_dir(__file__), "templates", file_name
        )

        assert os.path.isfile(
            file_path
        ), f"File at {file_path} does not exist."

        with open(file_path) as f:
            template = json.load(f)

        logger.debug(f"Bootstrap plotly template loaded from {file_path}")

        return template

    def set_formatting(self, fig: go.Figure) -> None:
        """
        If template is provided, set it, otherwise run all the formatting helpers on figure.
        """
        if self.template_name is None:
            self._set_title_size(fig)
            self._set_background(fig)
        else:
            fig.update_layout(template=self.template)

    def set_start_end_date(self) -> None:
        """
        Extract the start/end date from the data.
        """
        date_format = "%Y-%m-%d"
        self.start_date = min(self.df[COLUMN.TIMESTAMP]).strftime(date_format)
        self.end_date = max(self.df[COLUMN.TIMESTAMP]).strftime(date_format)

    @abstractmethod
    def _validate_data(self, df: pd.DataFrame) -> None:
        """
        Assert that the data conforms to the plot function.
        """
        pass

    @abstractmethod
    def plot(self) -> go.Figure:
        """
        Main plotting function.
        """
        pass


class HistogramPlotter(BasePlotter):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self.set_start_end_date()

    def _validate_data(self, df: pd.DataFrame) -> None:
        for column in [COLUMN.MIN, COLUMN.MAX, COLUMN.TIMESTAMP]:
            assert (
                column in df.columns
            ), f"Column {column} missing from the data columns ({df.columns})."

    def plot(self, show_title: bool = False) -> go.Figure:
        """
        Create a histogram for the min/max values.
        """

        long_df = self._preprocess_data_for_histogram()

        fig = px.histogram(
            long_df,
            x="value",
            color="variable",
            marginal="box",
            color_discrete_map={
                "Min": self.colors[COLOR_ITEM.MIN],
                "Max": self.colors[COLOR_ITEM.MAX],
            },
            labels={
                "variable": "Measure",
            },
        )

        if show_title:
            title = (
                f"Noise Level Distribution - {self.start_date} to {self.end_date}",
            )
            fig.update_layout(title=dict(text=title))

        fig.update_traces(opacity=0.75)

        fig.update_layout(
            barmode="overlay",
            yaxis_title="Count",
            xaxis_title="Noise Level (dBA)",
        )

        # add mean vlines
        means = long_df.groupby("variable")["value"].mean()
        self._add_vlines(fig, means["Min"], means["Max"])

        self.set_formatting(fig)

        return fig

    def _preprocess_data_for_histogram(self) -> pd.DataFrame:
        """
        Pivot data into long format for histogram plotting.
        """
        long_df = pd.melt(self.df[[COLUMN.MIN, COLUMN.MAX]])
        long_df["variable"] = long_df["variable"].map(
            {COLUMN.MIN: "Min", COLUMN.MAX: "Max"}
        )

        return long_df

    @staticmethod
    def _add_vlines(fig: go.Figure, min: float, max: float) -> None:
        fig.add_vline(
            x=min,
            row=1,
            line_width=3,
            line_dash="dash",
            line_color="grey",
            annotation_text=f"Average Min = {round(min, 1)}",
            annotation_position="top left",
        )
        fig.add_vline(
            x=max,
            row=1,
            line_width=3,
            line_dash="dash",
            line_color="grey",
            annotation_text=f"Average Max = {round(max, 1)}",
            annotation_position="top right",
        )


class TimeseriesPlotter(BasePlotter):
    """
    Plotting the noise data over time.
    """

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.noise_threshold = int(
            self._config["constants"]["noise_threshold"]
        )

        self.set_start_end_date()
        self.outliers = filter_outliers(
            self.df, threshold=self.noise_threshold
        )

    def _validate_data(self, df: pd.DataFrame) -> None:
        for column in [COLUMN.MIN, COLUMN.MAX, COLUMN.MEAN, COLUMN.TIMESTAMP]:
            assert (
                column in df.columns
            ), f"Column {column} missing from the data columns ({df.columns})."

        assert ptype.is_datetime64_any_dtype(
            df[COLUMN.TIMESTAMP]
        ), f"Timestamp should be datatime data type, not {df[COLUMN.TIMESTAMP].dtype}."

    def plot(self, title: str = None, bold_line: bool = False) -> go.Figure:
        """
        Create line chart showing the noise level over time.
        Params:
        title: str - if the title is added
        bold_line: bool - if extra emphasis is put on the mean line
        """
        figure = go.Figure()

        figure.add_traces(
            [
                self._get_min_line_trace(),
                self._get_max_line_trace(),
                self._get_mean_line_trace(bold_line=bold_line),
                self._get_final_marker(),
            ]
        )

        figure.update_xaxes(rangeslider_visible=False, gridcolor="LightGray")
        figure.update_yaxes(fixedrange=True, gridcolor="LightGray")
        figure.update_layout(
            showlegend=False,
            hovermode="x unified",
            height=int(self._config["plot.sizes"]["line_chart_height"]),
            margin=dict(
                l=10,
                r=10,
                b=40,
                t=40,
            ),
            yaxis={"visible": True, "showticklabels": True},
        )
        figure.update_traces(connectgaps=False)

        if title:
            figure.update_layout(title=dict(text=title))

        self.set_formatting(figure)

        return figure

    def _get_final_marker(self) -> go.Scatter:
        """
        Add a single marker for the last observation.
        """
        last_df = self.df.sort_values(
            by=COLUMN.TIMESTAMP, ascending=False
        ).head(1)
        trace = go.Scatter(
            x=last_df[COLUMN.TIMESTAMP],
            y=last_df[COLUMN.MEAN],
            name="outlier",
            mode="markers",
            marker=dict(
                size=int(self._config["plot.sizes"]["marker"]),
                color=self.colors[COLOR_ITEM.MEAN],
            ),
            hoverinfo="none",
        )

        return trace

    def _get_outlier_trace(self) -> go.Scatter:
        trace = go.Scatter(
            x=self.outliers[COLUMN.TIMESTAMP],
            y=self.outliers[COLUMN.MAX],
            name="outlier",
            mode="markers",
            marker=dict(
                size=int(self._config["plot.sizes"]["marker"]),
                color=self.colors[COLOR_ITEM.MAX],
            ),
        )

        return trace

    def _get_max_line_trace(self) -> go.Scatter:
        trace = go.Scatter(
            x=self.df[COLUMN.TIMESTAMP],
            y=self.df[COLUMN.MAX].round(1),
            name="Max",
            mode="lines",
            line_color=self.colors[COLOR_ITEM.MAX],
            fill="tonexty",
            fillcolor=self._config["plot.colors"]["fill"],
        )

        return trace

    def _get_min_line_trace(self) -> go.Scatter:
        trace = go.Scatter(
            x=self.df[COLUMN.TIMESTAMP],
            y=self.df[COLUMN.MIN].round(1),
            name="Min",
            mode="lines",
            line_color=self.colors[COLOR_ITEM.MIN],
        )
        return trace

    def _get_mean_line_trace(self, bold_line: bool) -> go.Scatter:
        line_width = int(self._config["plot.sizes"]["mean_line_width"])
        if bold_line:
            line_width += 3

        trace = go.Scatter(
            x=self.df[COLUMN.TIMESTAMP],
            y=self.df[COLUMN.MEAN].round(1),
            name="Mean",
            mode="lines",
            line_color=self.colors[COLOR_ITEM.MEAN],
            line_width=line_width,
        )
        return trace

    def _get_indicator_trace(self) -> go.Indicator:
        """
        Outlier count indicator.
        """
        indicator = go.Indicator(
            mode="number",
            value=self.outliers.shape[0],
            number={"font_color": self.colors[COLOR_ITEM.MAX]},
            title={
                "text": "# of outliers",
                "font_color": self.colors[COLOR_ITEM.MAX],
            },
            domain={"x": [0.8, 1], "y": [0.8, 1]},
        )
        return indicator


class HeatmapPlotter(BasePlotter):
    """
    Create heatmap showing longterm trends in the data.
    """

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

    def _validate_data(self, df: pd.DataFrame) -> None:
        assert all(
            [
                col in df.columns
                for col in [
                    COLUMN.DATE,
                    COLUMN.HOUR,
                    COLUMN.MINNOISE,
                    COLUMN.MAXNOISE,
                ]
            ]
        )

    def _pivot(self, value: HEATMAP_VALUE) -> pd.DataFrame:
        """
        Transform from long to wide format with hours as indices, dates as columns.
        """
        pivot_table = pd.pivot_table(
            self.df, columns=[COLUMN.HOUR], index=[COLUMN.DATE], values=value
        )

        # add missing indices
        pivot_table = pivot_table.resample("D").asfreq()

        # transpose
        pivot_table = pivot_table.T

        # map names to string, otherwise plotly errors out
        pivot_table.index.name = COLUMN.HOUR.value
        pivot_table.columns.name = COLUMN.DATE.value

        return pivot_table

    def _get_colorscale_from_value(self, value: HEATMAP_VALUE) -> List[str]:
        """
        Construct the colorscale depending on the value to be shown.
        """
        low_color = self._config["plot.colors"]["heatmap_low"]

        if value == HEATMAP_VALUE.MIN:
            high_color = self.colors[COLOR_ITEM.MIN]
        elif value == HEATMAP_VALUE.MAX:
            high_color = self.colors[COLOR_ITEM.MAX]

        return [low_color, high_color]

    def plot(
        self,
        pivot_value: HEATMAP_VALUE,
        title: Optional[str] = None,
        show_title: bool = False,
    ) -> go.Figure:
        """
        Create a heatmap from the pivot table.
        """
        pivot_column = pivot_value.value
        pivot_table = self._pivot(value=pivot_column)

        fig = px.imshow(
            pivot_table,
            x=pivot_table.columns,
            y=pivot_table.index,
            color_continuous_scale=self._get_colorscale_from_value(
                pivot_value
            ),
            height=300,
        )

        if show_title:
            fig.update_layout(title=dict(text=title))

        fig.update_layout(
            margin=dict(t=10),
            xaxis_title="Click a column to filter the line chart!",
            yaxis_title="Hour of Day",
            coloraxis_colorbar=dict(
                title="dBA",
            ),
        )
        self.set_formatting(fig)

        return fig


class AbstractIndicatorPlotter(BasePlotter):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

    def _get_indicator(
        self,
        value: int | float,
        units: Optional[str] = None,
        delta: Optional[int | float] = None,
        title: Optional[str] = None,
    ) -> html.Div:
        """
        Create an indicator component that shows a
        value and delta in percentage.
        """
        # round numbers
        value = round(value, 2)

        elements = []

        if title:
            title_line = html.Center(
                html.Div(title, className="indicator_title")
            )
            elements.append(title_line)

        if units:
            value_text = f"{value} {units}"
        else:
            value_text = f"{value}"

        value_line = html.Center(
            html.Div(value_text, className="indicator_value")
        )
        elements.append(value_line)

        if delta:
            delta = round(delta, 2)

            # check sign to set color & logo appropriately
            if delta >= 0:
                logo = html.I(className=f"fa-solid fa-angles-up")
                color = self._config["plot.colors"]["increase_color"]
            else:
                logo = html.I(className=f"fa-solid fa-angles-down")
                color = self._config["plot.colors"]["decrease_color"]

            delta_line = html.Div(
                [
                    html.Center(
                        [
                            logo,
                            html.Span(
                                style={"display": "inline-block", "width": 15}
                            ),
                            html.Span(f"{delta} %"),
                        ]
                    ),
                ],
                className="indicator_delta",
                style={"color": color},
            )
            elements.append(delta_line)

        indicator = html.Div(elements)

        return indicator


class NumberIndicator(AbstractIndicatorPlotter):
    """
    Show the size of passed dataframe.
    """

    def __init__(self, bootstrap_template: str = None) -> None:
        super().__init__(None, bootstrap_template)

    def plot(self, value: int | float, title: str = None) -> go.Figure:
        """ """
        indicator = self._get_indicator(value=value, title=title)

        return indicator


class MeanIndicatorPlotter(AbstractIndicatorPlotter):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

    def _validate_data(self, df: pd.DataFrame) -> None:
        for col in [COLUMN.MEAN, COLUMN.TIMESTAMP]:
            assert col in df.columns

    def _get_last_mean(self) -> float:
        """
        Get the last mean from the dataset.
        """
        df_sorted = self.df.sort_values(
            by=COLUMN.TIMESTAMP, ascending=False
        ).head(1)

        return df_sorted[COLUMN.MEAN].values[0]

    def _get_reference_mean(self) -> float:
        """
        Get previous noise value, if available.
        """
        df_sorted = self.df.sort_values(
            by=COLUMN.TIMESTAMP, ascending=False
        ).head(2)

        return df_sorted[COLUMN.MEAN].values[-1]

    def _get_title(self) -> str:
        """
        Get title text for the indicator.
        """
        return None

    def plot(self) -> html.Div:
        last_mean = self._get_last_mean()
        ref_mean = self._get_reference_mean()
        delta = round((last_mean - ref_mean) / last_mean * 100, 1)

        indicator = self._get_indicator(
            value=last_mean, delta=delta, units="dBA"
        )

        return indicator
