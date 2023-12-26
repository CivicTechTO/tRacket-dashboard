from dash import callback, Input, Output, dcc
from typing import List, Dict, Any
from src.data_loading import AppDataManager
from src.utils import COLUMN, HEATMAP_VALUE
import pandas as pd
from src.plotting import (
    TimeseriesPlotter,
    HeatmapPlotter,
    HistogramPlotter,
    OutlierIndicatorPlotter,
    MinAverageIndicatorPlotter,
    DeviceCountIndicatorPlotter,
)
from plotly.graph_objects import Figure


class AbstractAppManager(object):
    app_data_manager: AppDataManager = None

    @classmethod
    def set_app_data_manager(cls, app_data_manager: AppDataManager) -> None:
        cls.app_data_manager = app_data_manager


class GraphManager(AbstractAppManager):
    """
    Class to collect and initialize the graph components for the app.
    """

    # system-level indicators
    system_count_indicator: dcc.Graph = None
    system_avg_indicator: dcc.Graph = None
    system_outlier_indicator: dcc.Graph = None

    # device level charts
    noise_line_graph: dcc.Graph = None
    heatmap: dcc.Graph = None
    histogram: dcc.Graph = None


    @classmethod
    def initialize_components(cls, app_data_manager: AppDataManager) -> None:
        """
        Main call to setup all graph components for the app.
        """
        cls.set_app_data_manager(app_data_manager)

        # system level
        cls._setup_system_indicators()
        
        # device level
        cls._setup_noise_line_graph()
        cls._setup_heatmap_graph()
        cls._setup_histogram()

    @classmethod
    def _setup_histogram(cls) -> None:
        cls.histogram = dcc.Graph(id="histogram")

    @classmethod
    def _setup_heatmap_graph(cls) -> None:
        cls.heatmap = dcc.Graph(id="heatmap")

    @classmethod
    def _setup_noise_line_graph(cls) -> None:
        cls.noise_line_graph = dcc.Graph(id="noise-level-line")

    @classmethod
    def _setup_system_indicators(cls) -> None:
        """
        Initialize system indicator graphs.
        """
        cls._setup_system_count_indicator()
        cls._setup_system_min_indicator()
        cls._setup_system_outlier_indicator()

    @classmethod
    def _setup_system_count_indicator(cls) -> None:
        indicator_plotter = DeviceCountIndicatorPlotter(
            cls.app_data_manager.system_stats_df
        )
        system_count_fig = indicator_plotter.plot()
        cls.system_count_indicator = dcc.Graph(
            id="system-count",
            figure=system_count_fig,
            style={"height": "40vh"},
        )

    @classmethod
    def _setup_system_min_indicator(cls) -> None:
        indicator_plotter = MinAverageIndicatorPlotter(
            cls.app_data_manager.system_stats_df
        )
        system_min_fig = indicator_plotter.plot()
        cls.system_avg_indicator = dcc.Graph(
            id="system-min",
            figure=system_min_fig,
            style={"height": "40vh"},
        )

    @classmethod
    def _setup_system_outlier_indicator(cls) -> None:
        indicator_plotter = OutlierIndicatorPlotter(
            cls.app_data_manager.system_stats_df
        )
        system_outlier_fig = indicator_plotter.plot()
        cls.system_outlier_indicator = dcc.Graph(
            id="system-outlier",
            figure=system_outlier_fig,
            style={"height": "40vh"},
        )


class CallbackManager(AbstractAppManager):
    """
    Class that organizes and  initializes the Dash app callbacks on app start.
    """

    @classmethod
    def initialize_callbacks(cls, app_data_manager: AppDataManager) -> None:
        cls.set_app_data_manager(app_data_manager)
        ### CARD CALLBACKS ###

        @callback(
            Output("card-text", "children"), Input("device-stats", "data")
        )
        def update_card_text(stats: List[dict]) -> str:
            """
            Insert device id into the card.
            """
            stats_dict = stats[0]

            count = stats_dict[COLUMN.COUNT.value]

            date_format = "%Y-%m-%d"
            min_date = stats_dict[COLUMN.MINDATE.value]
            formatted_min_date = pd.to_datetime(min_date).strftime(date_format)

            max_date = stats_dict[COLUMN.MAXDATE.value]
            formatted_max_date = pd.to_datetime(max_date).strftime(date_format)

            max_noise = stats_dict[COLUMN.MAXNOISE.value]

            text = (
                f"This device has recorder a total of {count} measurements between "
                f" {formatted_min_date} and {formatted_max_date}. "
                f" The loudest measurement recorded to date was at {max_noise} dBA."
            )

            return text

        @callback(
            Output("card-header", "children"), Input("id-selection", "value")
        )
        def update_card_header(device_id: str) -> str:
            """
            Insert device id into the card.
            """

            return f"Device ID: {device_id}"

        @callback(
            Output("middle-markdown", "children"),
            Input("id-selection", "value"),
        )
        def update_middle_markdown(device_id: str) -> str:
            """
            Add the text explaining what is on the line chart and how to use the heatmap.
            """
            return f"The plot shows measurements recorded by the device {device_id}, sent at 5 minute intervals. To select a different week to show click the heatmap below."

        ### DATA CALLBACKS ###

        @callback(
            Output("device-stats", "data"), Input("id-selection", "value")
        )
        def load_device_stats(device_id: str) -> List[Dict[str, Any]]:
            """
            Load the data from the API.
            """
            raw_stats = cls.app_data_manager.load_device_stats(
                device_id=device_id
            )

            return raw_stats

        @callback(
            Output("hourly-device-data", "data"),
            Input("id-selection", "value"),
        )
        def load_hourly_data(device_id: str) -> List[Dict[str, Any]]:
            """
            Load the data from the API.
            """
            raw_hourly_data = cls.app_data_manager.load_hourly_data(
                device_id=device_id
            )

            return raw_hourly_data

        @callback(
            Output("device-data", "data"),
            Input("id-selection", "value"),
            Input("device-stats", "data"),
            Input("heatmap", "clickData"),
        )
        def load_data(
            device_id: str, stats: List[dict], clickData: Dict
        ) -> List[Dict[str, Any]]:
            """
            Load the data from the API.
            """

            date_format = "%Y-%m-%d"
            if clickData:
                # user selects end date
                date_string = clickData["points"][0]["x"]
                end_date = pd.Timestamp(date_string).strftime(date_format)

            else:
                # last recorded date used as end
                stats_dict = stats[0]
                end_date = stats_dict[COLUMN.MAXDATE.value]
                end_date = pd.to_datetime(end_date).strftime(date_format)

            # look back 7 days
            start_date = pd.to_datetime(end_date) - pd.Timedelta(days=7)
            start_date = start_date.strftime(date_format)

            # load data from API
            raw_device_data = cls.app_data_manager.load_noise_data(
                device_id=device_id, end_date=end_date, start_date=start_date
            )

            return raw_device_data

        ### PLOT CALLBACKS ###

        @callback(
            Output("noise-level-line", "figure"),
            Input("device-data", "data"),
        )
        def update_noise_level_fig(data: List[Dict[str, Any]]) -> Figure:
            """
            Filter the line for a single device id.
            """
            df = cls.app_data_manager.data_formatter.process_records_to_dataframe(
                data
            )

            timeseries_plotter = TimeseriesPlotter(df)

            return timeseries_plotter.plot()

        @callback(
            Output("histogram", "figure"),
            Input("device-data", "data"),
        )
        def update_histogram(data: List[Dict[str, Any]]) -> Figure:
            """
            Histogram of min/max distribution.
            """
            df = cls.app_data_manager.data_formatter.process_records_to_dataframe(
                data
            )

            hist_plotter = HistogramPlotter(df)

            return hist_plotter.plot()

        @callback(
            Output("heatmap", "figure"),
            Input("hourly-device-data", "data"),
            Input("heatmap-toggle", "value"),
        )
        def update_heatmap(
            data: List[Dict[str, Any]], max_toggle: bool
        ) -> Figure:
            df = cls.app_data_manager.data_formatter.process_records_to_dataframe(
                data
            )
            heatmap_plotter = HeatmapPlotter(df)

            if max_toggle:
                title = (
                    "Hourly Highest Measures - click to filter for the week!"
                )
                pivot_value = HEATMAP_VALUE.MAX
            else:
                title = "Hourly Ambient Noise - click to filter for the week!"
                pivot_value = HEATMAP_VALUE.MIN

            return heatmap_plotter.plot(pivot_value=pivot_value, title=title)
